from paho.mqtt.client import Client
from time import time
import json
from mqtt_payload_decoder import PayloadDecoder, logger
from dataclasses import dataclass
#from mlFunctions import predict, prepare_feat
from azure.iot.device import IoTHubDeviceClient, Message
import pandas as pd

@dataclass
class MessageData:
    timestamp: int
    p_l1 : float
    p_l2 : float
    p_l3 : float
    p_l123 : float
    p_l123_pred : float = None
    p_l123_real : float = None

class MlApp:
    _connection_codes = {
        0: 'mqtt connection successful',
        1: 'mqtt connection refused - incorrect protocol version',
        2: 'mqtt connection refused - invalid client identifier',
        3: 'mqtt connection refused - server unavailable',
        4: 'mqtt connection refused - bad username or password',
        5: 'mqtt connection refused - not authorized'
    }

    def __init__(self) -> None:

        self._client_id = 'data_receiver'
        self._connected = False

        self._connection_time = time()

        self._client = Client(client_id=self._client_id)

        # self._client.enable_logger(logger)

        self._client.reconnect_delay_set(
            min_delay=1,
            max_delay=300
        )

        self._client.on_disconnect = self._on_disconnect
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self.decoder = PayloadDecoder()
        # read the config.json file 
        # TODO a verifier
        with open('config.json') as f:
            config = json.load(f)

        # connect to iot hub
        self._azureClient = IoTHubDeviceClient.create_from_connection_string(config['azureConnectionString'])
        logger.info('connected to azure iot hub')

        # partie ml : 
        self._lastPrediction: MessageData = None
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        callback on connection to broker
        """

        if rc == 0:
            # connection successfull
            self._connected = True

            self._client.subscribe('ten-second/#')

            self.last_connection_time = time()
            logger.debug('connected to local mqtt server')

        else:
            # connection failed
            self._connected = False
            try:
                logger.warning('[%s] %s', self._client_id, MlApp._connection_codes[rc])
            except KeyError:
                logger.error(
                    '[%s] mqtt connection refused - invalid connection code', self._client_id)

    def _on_disconnect(self, client, userdata, rc):
        """
        callback on disconnect with broker
        """

        logger.debug('disconnected from local mqtt server...')

        self._connected = False

        if rc != 0:
            logger.warning(
                '[%s] mqtt unexpected disconnection - disconnection code: %d',
                self._client_id, rc
            )

    def _on_message(self, client, userdata, msg) -> None:
        """
        handles all messages that do not have a registered callback
        """
        # Récuperer les données
        _, msg = self.decoder.decode_feature(msg.payload)
        if msg['feature_type'] == 16:
            logger.info('received message from local mqtt server')
            if self._lastPrediction != None:
                # vérifie que la prédiction est correcte, si non envoyer un message à azure à travers le hub
                self._lastPrediction.p_l123_real = msg['p_l1']+msg['p_l2']+msg['p_l3']
                if self._lastPrediction.p_l123_real != self._lastPrediction.p_l123_pred:
                    logger.info('prediction error, sending message to azure iot hub')
                    # envoyer le message à azure
                    messageDict = self._lastPrediction.__dict__
                    messageDict['type'] = 'prediction_error'
                    message = Message(json.dumps(messageDict))
                    message.content_encoding = "utf-8"
                    message.content_type = "application/json"
                    self._azureClient.send_message(message)
                    logger.info('message sent to azure iot hub')

            self._lastPrediction = MessageData(
                timestamp=msg['timestamp'],
                p_l1=msg['p_l1'],
                p_l2=msg['p_l2'],
                p_l3=msg['p_l3'],
                p_l123=msg['p_l1']+msg['p_l2']+msg['p_l3'],
                p_l123_pred=0,
                p_l123_real=0
            )
            # Faire la prédiction, stocker le résultat en local
            tmp = {'p_l1': [msg['p_l1']], 'p_l2': [msg['p_l2']], 'p_l3': [msg['p_l3']]}
            df = pd.DataFrame(tmp)
            # Enable this when xgboost is installed and functional (needs raspberry pi OS Buster at least)
            #preds = predict(prepare_feat(df))
            #self._lastPrediction.p_l123_pred = preds[0]
            self._lastPrediction.p_l123_pred = 0
            logger.info('prediction done, waiting for next message')
        


    def start_client(self) -> None:
        """
        start mqtt service
        """

        self._client.connect_async(
            host='localhost',
            port=1883,
            keepalive=30
        )
        self._client.loop_forever()

    def stop(self) -> None:
        """
        stop mqtt service
        """

        try:
            self._client.disconnect(reasoncode=1)
        finally:
            self._client.loop_stop()
            logger.info('[%s] stopped mqtt service', self._client_id)

if __name__ == '__main__':
    mlApp = MlApp()
    mlApp.start_client()
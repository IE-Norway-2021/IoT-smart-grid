from paho.mqtt.client import Client
from time import time
import json
from dataApp.mqtt_payload_decoder import PayloadDecoder, logger
from dataclasses import dataclass
from mlFunctions import predict, prepare_feat
# import function to login into azure without the cli
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


@dataclass
class MessageData:
    timestamp: int
    p_l1 : float
    p_l2 : float
    p_l3 : float
    p_l123 : float
    # TODO ajouter les champs de la prediction, et ceux de la valeur réelle

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
        # login to azure with the given credentials
        self.blob_service_client = BlobServiceClient.from_connection_string(config['azureConnectionString'])
        
        # connect to container
        self.container_client = self.blob_service_client.get_container_client(config['containerName'])

        # connect to blob
        self.blob_client = self.blob_service_client.get_blob_client(container=config['containerName'], blob=config['blobName'])
        

        # list all the blobs in the container
        blob_list = self.container_client.list_blobs()
        for blob in blob_list:
            print("\t" + blob.name)

        # download blob file from the container into a variable
        self.blob_data = self.blob_client.download_blob().readall()
        print(self.blob_data)

        # partie ml : 
        self._dataSaver: list(MessageData) = []
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        callback on connection to broker
        """

        if rc == 0:
            # connection successfull
            self._connected = True

            self._client.subscribe('one-minute/#')

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
        # TODO completer
        # Récuperer les données
        _, msg = self.decoder.decode_feature(msg.payload)
        if msg['feature_type'] == 17:
            data = MessageData(
                timestamp=msg['timestamp'],
                p_l1=msg['p_l1'],
                p_l2=msg['p_l2'],
                p_l3=msg['p_l3'],
                p_l123=msg['p_l1']+msg['p_l2']+msg['p_l3']
                # TODO adapter pour les champs de la prediction et de la valeur réelle
            )
            # Faire la prédiction, stocker le résultat en local
            # Vérifier x minutes après si le résultat est correct
            # Si oui, next, si non, écrire les données, le résultat prédit et le résulat réel dans un bucket sur azure
        


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
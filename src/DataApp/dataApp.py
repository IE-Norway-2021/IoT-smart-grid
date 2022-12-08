###
# Receives messages fromt the broker, sends them to an influxdb instance
###

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import json
from paho.mqtt.client import Client
from mqtt_payload_decoder import PayloadDecoder, logger

class DataApp:
    _connection_codes = {
        0: 'mqtt connection successful',
        1: 'mqtt connection refused - incorrect protocol version',
        2: 'mqtt connection refused - invalid client identifier',
        3: 'mqtt connection refused - server unavailable',
        4: 'mqtt connection refused - bad username or password',
        5: 'mqtt connection refused - not authorized'
    }
    def __init__(self):
        # read the config.json file
        with open('config.json') as f:
            self._config = json.load(f)
        self._influxdbClient = InfluxDBClient(url=self._config['influxdbUrl'], token=self._config['influxdbToken'], org=self._config['influxdbOrg'])

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

    def _on_connect(self, client, userdata, flags, rc):
        """
        callback on connection to broker
        """

        if rc == 0:
            # connection successfull
            self._connected = True

            #self._client.subscribe('ten-second/#') not used
            self._client.subscribe('one-minute/#')

            self.last_connection_time = time()
            logger.debug('connected to local mqtt server')

        else:
            # connection failed
            self._connected = False
            try:
                logger.warning('[%s] %s', self._client_id, DataApp._connection_codes[rc])
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

    def _on_message(self, client, userdata, msg):
        """"
        receive messages from the broker, send them to influxdb after formatting
        """
        _, msg = self.decoder.decode_feature(msg.payload)
        if msg['feature_type'] == 17: # is a 1 min message
            data = [
                {
                    "measurement": self._config['influxdbMeasurement'],
                    "fields": {
                        "s_l1":msg['s_l1'],
                        "i_l1": msg['i_l1'],
                        "p_l1": msg['p_l1'],
                        "q_l1": msg['q_l1'],
                        "v_l1": msg['v_l1'],
                        "phi_l1": msg['phi_l1'],
                        "pf_l1": msg['pf_l1'],
                        "avg_energy_l1": msg['avg_energy_l1'],
                        "pf_l2": msg['pf_l2'],
                        "v_l2": msg['v_l2'],
                        "s_l2": msg['s_l2'],
                        "q_l2": msg['q_l2'],
                        "i_l2": msg['i_l2'],
                        "phi_l2": msg['phi_l2'],
                        "avg_energy_l2": msg['avg_energy_l2'],
                        "p_l2": msg['p_l2'],
                        "pf_l3": msg['pf_l3'],
                        "phi_l3": msg['phi_l3'],
                        "p_l3": msg['p_l3'],
                        "q_l3": msg['q_l3'],
                        "v_l3": msg['v_l3'],
                        "s_l3": msg['s_l3'],
                        "avg_energy_l3": msg['avg_energy_l3'],
                        "i_l3": msg['i_l3'],
                    }
                }
            ]

            # connect to the influxdb
            write_api = self._influxdbClient.write_api(write_options=SYNCHRONOUS)
            # write the data to the influxdb
            write_api.write(bucket=self._config['influxdbBucket'], record=data)


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
    dataApp = DataApp()
    dataApp.start_client()
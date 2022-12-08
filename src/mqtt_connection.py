from paho.mqtt.client import Client
from time import time
from mqtt_payload_decoder import PayloadDecoder, logger


class LocalMQTTHelper():
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

        self._connection_time: float = time()

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

            self._client.subscribe('ten-second/#')
            self._client.subscribe('one-minute/#')

            self.last_connection_time = time()
            logger.debug('connected to local mqtt server')

        else:
            # connection failed
            self._connected = False
            try:
                logger.warning('[%s] %s', self._client_id, LocalMQTTHelper._connection_codes[rc])
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

        logger.debug(self.decoder.decode_feature(msg.payload))

    def start_client(self) -> None:
        """
        start mqtt service
        """

        self._client.connect_async(
            host='10.0.0.200',
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
    mqtt = LocalMQTTHelper()
    mqtt.start_client()

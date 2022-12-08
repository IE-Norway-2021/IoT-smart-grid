import time
import datetime
import json
from azure.iot.device import IoTHubDeviceClient, MethodResponse


class MlApp:
    def __init__(self):
        # read the config.json file
        with open('config.json') as f:
            config = json.load(f)
        azureClient = IoTHubDeviceClient.create_from_connection_string(config['azureConnectionString'])

import json
from struct import unpack
from bson import ObjectId
from typing import Callable, Dict, Any, Tuple
import logging


def get_logger(name) -> logging.Logger:
    """
    :param name: this name will be displayed in the logs
    :return: logger
    """
    log_formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_formatter)
    log.addHandler(console_handler)
    return log


logger = get_logger('local_mqtt')


class PayloadDecoder:
    def __init__(self) -> None:
        with open('mqtt_msg_format.json', 'r') as f:
            self.format_config = json.load(f) # Dict[str, Any] 

        self.type_map  = { # Dict[str, Callable[[Any, Dict[str, str]], Any]]
            'int': self._parse_int,
            'ObjectId': self._parse_object_id,
            'float': self._parse_float,
        }

    def decode_feature(self, payload: bytes) -> Tuple[bool, Dict[str, Any]]:
        feature_type = str(payload[0])
        try:
            feature_config = \
                self.format_config['data/realtime/feature/+'][feature_type]
        except KeyError:
            logger.error('Could not find config for received feature type %s',
                         feature_type)
            return True, dict()

        try:
            msg = unpack(feature_config['encoding'], payload)

            data = { # Dict[str, Any] 
                field['label']: self.type_map[field['type']](msg[i], field)
                for i, field in enumerate(feature_config['fields'])
            }

            return False, data

        except KeyError:
            logger.exception('Invalid msg format config (ft: %s)',
                             feature_type)
            return True, dict()
        except Exception:
            logger.exception('Error while decoding mqtt message')
            return True, dict()

    @staticmethod
    def _parse_object_id(value, _) -> ObjectId:
        return ObjectId(value)

    @staticmethod
    def _parse_int(value, _) -> int:
        return int(value)

    @staticmethod
    def _parse_float(value, field) -> float:
        return float(value / int(field.get('divide_by', 1)))

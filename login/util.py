from enum import Enum, auto
import logging, json
from .models import OperationLogs

class LogType():
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class OpType():
    VISIT = 'VISIT'
    SELECT = 'SELECT'
    ADD = 'ADD'
    DELETE = 'DELETE'
    UPDATE = 'UPDATE'

class Log():

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        logging.info('enter log')

    def __del__(self):
        logging.info('delete log')

    def record(self, log_type, model_name, op_type, data):
        try:
            content = op_type + ':' + model_name + ':' + json.dumps(data, ensure_ascii=False, indent=2)
            logging.info(content)
            obj_operationlogs = OperationLogs()
            obj_operationlogs.content = content
            obj_operationlogs.type = log_type
            obj_operationlogs.save()
        except:
            logging.error('unknown')
        


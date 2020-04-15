import logging, json, hashlib
from .models import OperationLogs


# 哈希加密
def hash_code(s, salt='mysite'):  # 加点盐
    h = hashlib.md5()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()

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
            
    def logs(self, request, id, type=LogType.INFO, optype=OpType.VISIT, visit_url='/index'):
        # id = 0 权限错误
        # id = 1 obj错误
        # id = 2 function错误
        # id = 3 subfun错误
        # id = 4 visit
        # id = 5 add
        # id = 6
        lg = Log()
        if(id == 0):
            lg_data = {
                "Login_User": request.session['user_id'],
                "Exceed_Authority": 'exceed authority'
            }
        if(id == 1):
            lg_data = {
                "Login_User": 'None',
                visit_url: visit_url,
            }
        if(id == 2):
            lg_data = {
                "Login_User": 'None'
            }
        self.record(type, '', optype, lg_data)
        


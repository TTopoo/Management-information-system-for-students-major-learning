from django.http import HttpResponse, JsonResponse
from .util import *
from login.util import hash_code
from login.models import *

import json

def info(request):
    
    
    name = retName()
    ddate = retDate()
    sex = retSex()
    email = retEmail()
    idc, age = retID()
    major = retMajor()
    account = retAccount(0, major)
    psw = hash_code('123456')

    same_name_user = User.objects.filter(account=account)
    if same_name_user:  # 学号唯一
        return HttpResponse(json.dumps({'status': 'stuid1'}))
    
    # 当一切都OK的情况下，创建新用户
    new_user = User.objects.create()
    new_user.account = account
    new_user.password = psw  # 使用学号当做初始加密密码
    new_user.save()

    obj = User.objects.get(account=account)
    StudentInformationModel.objects.create(user_id=obj, email=email, name=name,
                                            sex=sex, idc=idc, age=age, major=major)
    
    return HttpResponse(name+ddate+sex+email+idc+major)

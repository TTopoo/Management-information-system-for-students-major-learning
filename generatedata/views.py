from django.http import HttpResponse, JsonResponse
from .util import *
from login.util import hash_code
from login.models import *

import json


def info(request):
    auth = 0
    name = retName()
    ddate = retDate()
    sex = retSex()
    email = retEmail()
    idc, age = retID()
    major = retMajor()
    account = retAccount(auth, major)
    psw = hash_code('123456')

    same_name_user = User.objects.filter(account=account)
    if same_name_user:  # 学号唯一
        return HttpResponse(json.dumps({'status': 'stuid1'}))

    # 当一切都OK的情况下，创建新用户
        new_user = User.objects.create()
        new_user.account = account
        new_user.password = psw
        new_user.save()

    if(auth == 0):
        obj = User.objects.get(account=account)
        StudentInformationModel.objects.create(user_id=obj, email=email, name=name,
                                               sex=sex, idc=idc, age=age, major=major)
    else:
        graduate_school = random.choice(['东华', '清华', '北师大'])
        education_experience = random.choice(['本科', '硕士', '博士'])
        obj = User.objects.get(account=account)
        TeacherInformationModel.objects.create(user_id=obj, email=email, name=name,
                                               sex=sex, idc=idc, graduate_school=age, education_experience=major)

    return HttpResponse(name+ddate+sex+email+idc+major)

from django.shortcuts import render, redirect
from . import models, forms
from .models import User, StudentInformationModel, StudentAwardsRecodeModel, MajorModel
import hashlib, json
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
import logging
from .util import LogType, OpType, Log


# 哈希加密
def hash_code(s, salt='mysite'):  # 加点盐
    h = hashlib.md5()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()


# 学生主页
def index_student(request):
    if request.session['authority'] == True:
        return redirect('/index_teacher/')
    sex_map = {
        'male': '男',
        'female': '女',
    }
    major_map = {
        '080901': "计算机科学与技术",
        '080902': "软件工程",
        '080903': "网络工程",
        '080904K': "信息安全",
    }
    user_id = request.session['user_id']
    account = request.session['account']
    stu_infos = StudentInformationModel.objects.filter(user_id=user_id)
    if not stu_infos:
        return redirect('/fill_information/')
    stu_info = stu_infos[0]
    stu_info.sex = sex_map[stu_info.sex]
    stu_info.major = major_map[stu_info.major]

    # 学生所在班级
    classes = stu_info.classmodel_set.all()
    if classes is None:
        classname = '无'
    else:
        unify_class = classes[0]
        # 班级所在专业
        major = unify_class.major_id
        # 专业所在学院
        college = major.college_id

    return render(request, 'login/index_student.html', locals())


# 教师主页
def index_teacher(request):
    pass
    return render(request, 'login/index_teacher.html', locals())


# 登录
def login(request):
    if request.method == "POST":
        login_form = forms.UserForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            account = login_form.cleaned_data['account']
            print(hash_code(account))
            password = login_form.cleaned_data['password']
            try:
                user = User.objects.get(account=account)
                if user.password == hash_code(password):  # 哈希值和数据库内的值进行比对
                    request.session['is_login'] = True
                    request.session['user_id'] = user.id
                    request.session['account'] = user.account
                    if account[0] == '0':  # 如果是教师账号
                        request.session['authority'] = True
                        return redirect('/index_teacher/')
                    else:
                        request.session['authority'] = False
                        return redirect('/index_student/')
                else:
                    message = "密码不正确！"
            except:
                message = "用户不存在！"
        return render(request, 'login/login.html', locals())

    login_form = forms.UserForm()
    return render(request, 'login/login.html', locals())


# 登出
def logout(request):
    if not request.session.get('is_login', None):  # 如果本来就未登录，也就没有登出一说
        return redirect("/login/")
    request.session.flush()
    return redirect("/login/")


# 完善学生信息
def fill_information(request):
    account = request.session['account']
    if request.method == "POST":
        fill_info_form = forms.FillInformationForm(request.POST)
        message = "信息填写有误"
        if fill_info_form.is_valid():
            password1 = fill_info_form.cleaned_data['password1']
            password2 = fill_info_form.cleaned_data['password2']
            if password1 != password2:
                message = '两次输入的密码不同!'
                return render(request, 'login/fill_information.html', locals())
            # 获取所有信息
            account = request.session['account']
            email = fill_info_form.cleaned_data['email']
            name = fill_info_form.cleaned_data['name']
            sex = fill_info_form.cleaned_data['sex']
            idc = fill_info_form.cleaned_data['idc']
            age = fill_info_form.cleaned_data['age']
            major = fill_info_form.cleaned_data['major']
            # 保存账号密码
            user = User.objects.get(account=account)
            user.password = hash_code(password1)
            user.save()
            # 报存个人信息
            new_info = StudentInformationModel.objects.create(user_id=user, email=email, name=name,
                                                              sex=sex, idc=idc, age=age, major=major)
            new_info.save()
            return redirect('/index_student/')
    fill_info_form = forms.FillInformationForm()
    return render(request, 'login/fill_information.html', locals())


##############################################################################
class Op(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):  # 所有操作的基类
    authority = False
    Student = False
    Teacher = True

    def __init__(self):
        logging.info('enter op')

    def __del__(self):
        logging.info('delete op')

    @action(methods=['post'], detail=False)
    def visit(self, request): pass

    @action(methods=['post'], detail=False)
    def add(self, request):  pass

    @action(methods=['get'], detail=False)
    def select(self, request):   pass

    @action(methods=['post'], detail=False)
    def delete(self, request):   pass

    @action(methods=['post'], detail=False)
    def update(self, request):   pass


class Stu_OP(Op):
    def __init__(self):
        logging.info('enter stu op')

    def __del__(self):
        logging.info('delete stu op')

    def add(self, request):
        pass


class Teacher_StuInfo_OP(Op):
    def __init__(self):
        logging.info('enter teacher op')

    def __del__(self):
        logging.info('delete teacher op')

    def AuthorityCheck(self, request):
        if not self.request.session.get('authority', None):
            self.authority = False
        else:
            self.authority = True

    # 访问该功能页
    def visit(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "Exceed_Authority": 'exceed authority'
            }
            lg.record(LogType.WARNING, '', OpType.VISIT, lg_data)
            return HttpResponse(json.dumps({'status': 'authority_check0'}))  # 换成一个页面好一点
        else:
            return render(request, 'login/stu_info.html', locals())

    # 添加学生信息
    def add(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误
            return HttpResponse(json.dumps({'status': 'authority_check0'}))
        else:
            logging.info("enter stu_info_add")
            username = request.POST.get("username", None)
            if username == '':  # 学号非空
                return HttpResponse(json.dumps({'status': 'stuid0'}))
            email = request.POST.get("email", None)
            if email == '':  # 邮箱非空
                return HttpResponse(json.dumps({'status': 'email0'}))
            name = request.POST.get("name", None)
            if name == '':  # 姓名非空
                return HttpResponse(json.dumps({'status': 'name0'}))
            sex = request.POST.get("sex", None)
            idc = request.POST.get("idc", None)
            if idc == '':  # 身份证号非空
                return HttpResponse(json.dumps({'status': 'idc0'}))
            age = request.POST.get("age", None)
            if age == '':  # 年龄非空
                return HttpResponse(json.dumps({'status': 'age0'}))
            major = request.POST.get("major", None)

            same_name_user = User.objects.filter(stuid=username)
            if same_name_user:  # 学号唯一
                return HttpResponse(json.dumps({'status': 'stuid1'}))

            # 当一切都OK的情况下，创建新用户
            new_user = User.objects.create()
            new_user.stuid = username
            new_user.password = hash_code(username)  # 使用学号当做初始加密密码
            new_user.save()

            obj = User.objects.get(stuid=username)
            StudentInformationModel.objects.create(stu_id=obj, email=email, name=name,
                                                   sex=sex, idc=idc, age=age, major=major)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "username": username, "email": email, "name": name,
                "sex": sex, "idc": idc, "age": age, "major": major
            }
            lg.record(LogType.INFO, str(StudentInformationModel._meta.model_name) +
                      ' & ' + str(new_user._meta.model_name), OpType.ADD, lg_data)
            logging.info("end stu_info_add")
            return HttpResponse(json.dumps({'status': 'success'}))

    # 发送学生信息
    def select(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误，TODO:补充异常报告
            return HttpResponse(json.dumps({'status': 'authority_check0'}))
        else:
            data = {}
            logging.info("enter stu_info_select")
            search_kw = request.GET.get('search', '')
            sort_kw = request.GET.get('sort', '')
            order_kw = request.GET.get('order', '')
            offset_kw = request.GET.get('offset', 0)
            limit_kw = request.GET.get('limit', 0)
            if (search_kw != ''):
                result_set = StudentInformationModel.objects.filter(
                    Q(stu_id__stuid__contains=search_kw) |
                    Q(email__contains=search_kw) |
                    Q(name__contains=search_kw) |
                    Q(sex__contains=search_kw) |
                    Q(idc__contains=search_kw) |
                    Q(age__contains=search_kw) |
                    Q(major__contains=search_kw)
                ).all()
                data['total'] = StudentInformationModel.objects.filter(
                    Q(stu_id__stuid__contains=search_kw) |
                    Q(email__contains=search_kw) |
                    Q(name__contains=search_kw) |
                    Q(sex__contains=search_kw) |
                    Q(idc__contains=search_kw) |
                    Q(age__contains=search_kw) |
                    Q(major__contains=search_kw)
                ).count()
            else:
                result_set = StudentInformationModel.objects.all()
                data['total'] = StudentInformationModel.objects.all().count()
            if (sort_kw != ''):
                if (order_kw == 'asc'):
                    result_set = result_set.order_by(sort_kw)
                else:
                    result_set = result_set.order_by(('-' + sort_kw))

            result_set = result_set.values('stu_id__stuid', 'email', 'name', 'sex', 'idc', 'age', 'major')[
                         int(offset_kw):(int(offset_kw) + int(limit_kw))]
            data['rows'] = list(result_set)

            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw}

            lg.record(LogType.INFO, StudentInformationModel._meta.model_name, OpType.SELECT, lg_data)

            logging.info("end stu_info_select")
            return JsonResponse(data)

    # 更新学生信息
    def update(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误，TODO:补充异常报告
            return HttpResponse(json.dumps({'status': 'authority_check0'}))
        else:
            logging.info("enter stu_info_update")
            username = request.POST.get("update_username", None)
            if username == '':  # 学号非空
                return HttpResponse(json.dumps({'status': 'stuid0'}))
            email = request.POST.get("update_email", None)
            if email == '':  # 邮箱非空
                return HttpResponse(json.dumps({'status': 'email0'}))
            name = request.POST.get("update_name", None)
            if name == '':  # 姓名非空
                return HttpResponse(json.dumps({'status': 'name0'}))
            sex = request.POST.get("update_sex", None)
            idc = request.POST.get("update_idc", None)
            if idc == '':  # 身份证号非空
                return HttpResponse(json.dumps({'status': 'idc0'}))
            age = request.POST.get("update_age", None)
            if age == '':  # 年龄非空
                return HttpResponse(json.dumps({'status': 'age0'}))
            major = request.POST.get("update_major", None)

            obj = User.objects.get(stuid=username)
            StudentInformationModel.objects.filter(stu_id=obj).update(stu_id=obj, email=email, name=name,
                                                                      sex=sex, idc=idc, age=age, major=major)
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "username": username, "email": email, "name": name,
                "sex": sex, "idc": idc, "age": age, "major": major
            }
            lg.record(LogType.INFO, str(StudentInformationModel._meta.model_name), OpType.UPDATE, lg_data)

            logging.info("end stu_info_update")
            return HttpResponse(json.dumps({'status': 'success'}))

    # 删除学生信息
    @csrf_exempt
    def delete(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误，TODO:补充异常报告
            return HttpResponse(json.dumps({'status': 'authority_check0'}))
        else:
            logging.info("enter stu_info_delete")
            json_receive = json.loads(request.body)
            logging.debug(json_receive)
            for i in json_receive:
                logging.debug(i.keys())
                stu_id = i['stu_id__stuid']
                logging.debug(stu_id)
                User.objects.filter(stuid=stu_id).delete()
                lg = Log()
                lg_data = {"Login_User": request.session['user_id'], "stu_id": stu_id}
                lg.record(LogType.INFO, str(StudentInformationModel._meta.model_name), OpType.DELETE, lg_data)

            logging.info("end stu_info_delete")
            return HttpResponse(json.dumps({'status': 'success'}))


##############################################################################

class Teacher_Award_OP(Op):
    def __init__(self):
        logging.info('enter teacher op')

    def __del__(self):
        logging.info('delete teacher op')

    def AuthorityCheck(self, request):
        if not self.request.session.get('authority', None):
            self.authority = False
        else:
            self.authority = True

    # 访问该功能页
    def visit(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "Exceed_Authority": 'exceed authority'
            }
            lg.record(LogType.WARNING, '', OpType.VISIT, lg_data)
            return HttpResponse(json.dumps({'status': 'authority_check0'}))  # 换成一个页面好一点
        else:
            return render(request, 'login/award.html', locals())

    # 添加奖惩信息
    def add(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误
            return HttpResponse(json.dumps({'status': 'authority_check0'}))
        else:
            logging.info("enter award_add")
            username = request.POST.get("username", None)
            if username == '':  # 学号非空
                return HttpResponse(json.dumps({'status': 'stuid0'}))
            type = request.POST.get("type", None)
            content = request.POST.get("content", None)
            if content == '':  # 奖惩详情非空
                return HttpResponse(json.dumps({'status': 'content0'}))

            date = request.POST.get("date", None)
            if date == '':  # 奖惩日期非空
                return HttpResponse(json.dumps({'status': 'date0'}))

            # 当一切都OK的情况下，创建新的奖惩记录

            obj = StudentInformationModel.objects.get(stu_id__stuid=username)
            StudentAwardsRecodeModel.objects.create(stu_id=obj, award_type=type,
                                                    award_content=content, award_date=date)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "username": username, "type": type, "content": content, "date": date}
            lg.record(LogType.INFO, str(StudentAwardsRecodeModel._meta.model_name), OpType.ADD, lg_data)
            logging.info("end award_add")
            return HttpResponse(json.dumps({'status': 'success'}))

    # 发送奖惩信息
    def select(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误，TODO:补充异常报告
            return HttpResponse(json.dumps({'status': 'authority_check0'}))
        else:
            data = {}
            logging.info("enter award_select")
            search_kw = request.GET.get('search', '')
            sort_kw = request.GET.get('sort', '')
            order_kw = request.GET.get('order', '')
            offset_kw = request.GET.get('offset', 0)
            limit_kw = request.GET.get('limit', 0)
            if (search_kw != ''):
                result_set = StudentAwardsRecodeModel.objects.filter(
                    Q(stu_id__stu_id__stuid__contains=search_kw) |
                    Q(stu_id__name__contains=search_kw) |
                    Q(award_type__contains=search_kw) |
                    Q(award_content__contains=search_kw) |
                    Q(award_date__contains=search_kw)
                ).all()
                data['total'] = StudentAwardsRecodeModel.objects.filter(
                    Q(stu_id__stu_id__stuid__contains=search_kw) |
                    Q(stu_id__name__contains=search_kw) |
                    Q(award_type__contains=search_kw) |
                    Q(award_content__contains=search_kw) |
                    Q(award_date__contains=search_kw)
                ).count()
            else:
                result_set = StudentAwardsRecodeModel.objects.all()
                logging.debug(result_set.values('stu_id__stu_id__stuid', 'stu_id__name', 'award_type', 'award_content',
                                                'award_date'))
                data['total'] = StudentAwardsRecodeModel.objects.all().count()

            if (sort_kw != ''):
                if (order_kw == 'asc'):
                    result_set = result_set.order_by(sort_kw)
                else:
                    result_set = result_set.order_by(('-' + sort_kw))

            result_set = result_set.values('id', 'stu_id__stu_id__stuid', 'stu_id__name', 'award_type', 'award_content',
                                           'award_date')[int(offset_kw):(int(offset_kw) + int(limit_kw))]
            data['rows'] = list(result_set)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw}

            lg.record(LogType.INFO, StudentAwardsRecodeModel._meta.model_name, OpType.SELECT, lg_data)

            logging.info("end award_select")
            return JsonResponse(data)

    # 更新奖惩信息
    def update(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误，TODO:补充异常报告
            return HttpResponse(json.dumps({'status': 'authority_check0'}))
        else:
            logging.info("enter award_update")
            id = request.POST.get("update_id", None)
            stu_id = request.POST.get("update_username", None)
            type = request.POST.get("update_type", None)
            content = request.POST.get("update_content", None)
            if content == '':  # 奖惩详情非空
                return HttpResponse(json.dumps({'status': 'content0'}))

            date = request.POST.get("update_date", None)
            if date == '':  # 奖惩日期非空
                return HttpResponse(json.dumps({'status': 'date0'}))
            obj = StudentInformationModel.objects.get(stu_id__stuid=stu_id)
            StudentAwardsRecodeModel.objects.filter(id=id).update(stu_id=obj, award_type=type,
                                                                  award_content=content, award_date=date)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "id": id, "stu_id": stu_id, "type": type, "content": content}
            lg.record(LogType.INFO, str(StudentAwardsRecodeModel._meta.model_name), OpType.UPDATE, lg_data)
            logging.info("end award_update")
            return HttpResponse(json.dumps({'status': 'success'}))

    # 删除奖惩信息
    @csrf_exempt
    def delete(self, request):
        self.AuthorityCheck(request)
        if (self.authority == self.Student):  # 教师权限，学生的任何请求都返回权限错误，TODO:补充异常报告
            return HttpResponse(json.dumps({'status': 'authority_check0'}))
        else:
            logging.info("enter award_delete")
            json_receive = json.loads(request.body)
            for i in json_receive:
                logging.debug(i.keys())
                award_id = i['id']
                StudentAwardsRecodeModel.objects.filter(id=award_id).delete()
                lg = Log()
                lg_data = {"Login_User": request.session['user_id'], "award_id": award_id}
                lg.record(LogType.INFO, str(StudentAwardsRecodeModel._meta.model_name), OpType.DELETE, lg_data)
            logging.info("end award_delete")
            return HttpResponse(json.dumps({'status': 'success'}))

##############################################################################

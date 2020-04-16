from django.shortcuts import render, redirect
from . import models, forms
from .models import *
import hashlib, json
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

import logging
from .util import LogType, OpType, Log, hash_code
from django.views.generic import View


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
    if not classes.exists():
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


# 填写基本信息
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
            # email = fill_info_form.cleaned_data['email']
            name = fill_info_form.cleaned_data['name']
            sex = fill_info_form.cleaned_data['sex']
            idc = fill_info_form.cleaned_data['idc']
            age = fill_info_form.cleaned_data['age']
            major = fill_info_form.cleaned_data['major']
            # 保存账号密码
            user = User.objects.get(account=account)
            user.password = hash_code(password1)
            user.save()
            # 保存个人信息
            new_info = StudentInformationModel.objects.create(user_id=user, name=name,
                                                              sex=sex, idc=idc, age=age, major=major)
            new_info.save()
            return redirect('/index_student/')
        else:
            password1 = fill_info_form.cleaned_data['password1']
            password2 = fill_info_form.cleaned_data['password2']
            # email = fill_info_form.cleaned_data['email']
            name = fill_info_form.cleaned_data['name']
            sex = fill_info_form.cleaned_data['sex']
            idc = fill_info_form.cleaned_data['idc']
            age = fill_info_form.cleaned_data['age']
            major = fill_info_form.cleaned_data['major']
            print(password1)
            print(password2)
            # print(email)
            print(name)
            print(sex)
            print(idc)
            print(age)
            print(major)
    fill_info_form = forms.FillInformationForm()
    return render(request, 'login/fill_information.html', locals())


# 修改学生个人信息
def alter_information(request):
    user_id = request.session['user_id']
    account = request.session['account']
    alter_info_form = forms.AlterInformationForm()
    if request.method == "POST":
        message = "信息填写有误"
        if alter_info_form.is_valid():
            print('合格了')
            password1 = alter_info_form.cleaned_data['password1']
            password2 = alter_info_form.cleaned_data['password2']
            if password1 != password2:
                message = '两次输入的密码不同!'
                return render(request, 'login/fill_information.html', locals())
            # 获取所有信息
            name = alter_info_form.cleaned_data['name']
            email = alter_info_form.cleaned_data['email']
            # 保存账号密码
            user = User.objects.get(account=account)
            user.password = hash_code(password1)
            user.save()
            # 保存个人信息
            new_info = StudentInformationModel.objects.create(user_id=user, email=email, name=name)
            new_info.save()
            return redirect('/index_student/')
        else:
            print('检查不合格')

    return render(request, 'login/alter_information.html', locals())


##############################################################################

class Op():  # 所有操作的基类

    visit_status = -1
    oplist = ['add', 'json', 'delete', 'update']

    def __init__(self):
        logging.info('enter op')

    def __del__(self):
        logging.info('delete op')

    #                         2          1        0
    #      status\url      teacher   student    other
    #  2 teacher              22        21       20
    #  1 student              12        11       10
    #  0 nologin              02        01       00

    def AuthorityCheck(self, request, obj, function, subfun):
        if request.session['is_login'] == True:  # 登录了
            if not self.request.session.get('authority', None):
                self.visit_status = 1  # 学生
            else:
                self.visit_status = 2  # 教师
        else:
            self.visit_status = 0
        self.visit_status *= 10
        if (obj == 'teacher'):
            self.visit_status += 2
        elif (obj == 'student'):
            self.visit_status += 1
        else:
            self.visit_status += 0
        print(self.visit_status)
        # 异常处理
        l = Log()
        if (self.visit_status == 12 or self.visit_status == 21):  # 教师和学生权限相反的任何请求都返回权限错误
            l.logs(request, 0, LogType.WARNING, OpType.VISIT)
        if (self.visit_status < 10):  # 没登陆
            l.logs(request, 1, LogType.WARNING, OpType.VISIT)
        if (self.visit_status % 10 == 0):  # 链接错误
            l.logs(request, 1, LogType.WARNING, OpType.VISIT, '/' + str(obj) + '/' + str(function) + '/' + str(subfun))

        return self.visit_status

    def listofop(self, fun):
        if (fun in self.oplist):
            return 1
        return 0

    def dictoffun(self, fun, request):
        operator = {"add": self.add, "json": self.select, "delete": self.delete, "update": self.update}
        return operator[fun](request)

    def visit(self, request):
        pass

    def add(self, request):
        pass

    def select(self, request):
        pass

    def delete(self, request):
        pass

    def update(self, request):
        pass


class Student():
    funlist = ['choose_course', '123']  # 功能列表

    def __init__(self):
        logging.info('enter student op')

    def __del__(self):
        logging.info('delete student op')

    def visit(self, request):
        return redirect("/index_student/")

    def listoffunction(self, fun):
        if (fun in self.funlist):
            return 1
        return 0


class Student_ChooseCourse_OP(Student, Op):

    def __init__(self):
        logging.info('enter stu_chooseCourse op')

    def __del__(self):
        logging.info('delete stu_chooseCourse op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/choose_course.html', locals())
        elif len(args) == 0:
            return redirect("/student/choose_course/")

    # 添加课程
    def add(self, request):
        logging.info('enter choose_course add_course')
        json_receive = json.loads(request.body)
        print('进入添加课程')
        print(json_receive)
        '''
        # 添加这门课程
        user_id = request.session['user_id']
        stu_info = StudentInformationModel.objects.get(id=user_id)
        course = CourseModel.objects.get(id=course_id)
        course.students.add(stu_info)
        '''
        # 日志

        return HttpResponse(json.dumps({'status': 'success'}))

    def remove_duplicates(self, list01):
        list02 = list()
        for i in list01:
            if i not in list02:
                list02.append(i)
        return list02

    # 发送课程
    def select(self, request):

        data = {}
        logging.info("enter stu_ChooseCourse_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)

        # 获取学生专业
        user_id = request.session['user_id']
        stu_info = StudentInformationModel.objects.get(user_id=user_id)
        unify_class = stu_info.classmodel_set.all()[0]
        major = unify_class.major_id
        # 该专业可选的课程
        course_set = major.courses
        data['total'] = course_set.count()
        # 课程中该学生的成绩和状态
        #                            a = course_set[0].studentsScore.filter(student=stu_info).score
        course_set = course_set.values('id', 'course_name', 'courseClass__teacher__name', 'courseClass__maxNum',
                                       'courseClass__studentsScore__student_id', 'courseClass__studentsScore__score',
                                       'courseClass__studentsScore__state')
        # print(course_set)
        data['rows'] = list(course_set)
        # print(data['rows'])
        for i in data['rows']:
            if i['courseClass__studentsScore__student_id'] is not None and \
                    i['courseClass__studentsScore__student_id'] != stu_info.id:
                i['courseClass__studentsScore__student_id'] = None
                i['courseClass__studentsScore__score'] = None
                i['courseClass__studentsScore__state'] = None
        data['rows'] = self.remove_duplicates(data['rows'])  # 去重
        for i in data['rows']:
            if i['courseClass__studentsScore__student_id'] == stu_info.id:
                for j in data['rows']:
                    if j['courseClass__teacher__name'] == i['courseClass__teacher__name'] and \
                            j['courseClass__studentsScore__student_id'] is None:
                        data['rows'].remove(j)
        # print(data['rows'])
        return JsonResponse(data)

    # 删除课程
    @csrf_exempt
    def delete(self, request):

        logging.info('enter choose_course remove_course')
        json_receive = json.loads(request.body)
        logging.debug(json_receive)

        print('到达删除函数')
        print(json_receive)

        '''        # 课程移除该学生
        user_id = request.session['user_id']
        stu_info = StudentInformationModel.objects.get(id=user_id)
        course = CourseModel.objects.get(id=course_id)
        course.students.remove(stu_info)
        '''
        # 日志
        logging.info("end choose_course remove_course")
        return HttpResponse(json.dumps({'status': 'success'}))


class Teacher():
    funlist = ['stu_info', 'award']

    def __init__(self):
        logging.info('enter teacher op')

    def __del__(self):
        logging.info('delete teacher op')

    def visit(self, request):
        return redirect("/index_teacher/")

    def listoffunction(self, fun):
        if (fun in self.funlist):
            return 1
        return 0


class Teacher_StuInfo_OP(Teacher, Op):

    def __init__(self):
        logging.info('enter teacher_stuinfo op')

    def __del__(self):
        logging.info('delete teacher_stuinfo op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/stu_info.html', locals())
        elif len(args) == 0:
            return redirect("/teacher/stu_info/")

    # 添加学生信息
    def add(self, request):

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

        same_name_user = User.objects.filter(account=username)
        if same_name_user:  # 学号唯一
            return HttpResponse(json.dumps({'status': 'stuid1'}))

        # 当一切都OK的情况下，创建新用户
        new_user = User.objects.create()
        new_user.account = username
        new_user.password = hash_code(username)  # 使用学号当做初始加密密码
        new_user.save()

        obj = User.objects.get(account=username)
        StudentInformationModel.objects.create(user_id=obj, email=email, name=name,
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

        data = {}
        logging.info("enter stu_info_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        if (search_kw != ''):
            result_set = StudentInformationModel.objects.filter(
                Q(user_id__account__contains=search_kw) |
                Q(email__contains=search_kw) |
                Q(name__contains=search_kw) |
                Q(sex__contains=search_kw) |
                Q(idc__contains=search_kw) |
                Q(age__contains=search_kw) |
                Q(major__contains=search_kw)
            ).all()
            data['total'] = StudentInformationModel.objects.filter(
                Q(user_id__account__contains=search_kw) |
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

        result_set = result_set.values('user_id__account', 'email', 'name', 'sex', 'idc', 'age', 'major')[
                     int(offset_kw):(int(offset_kw) + int(limit_kw))]
        print(result_set)
        data['rows'] = list(result_set)
        print(data['rows'])
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

        obj = User.objects.get(account=username)
        StudentInformationModel.objects.filter(user_id=obj).update(user_id=obj, email=email, name=name,
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
        logging.info("enter stu_info_delete")
        json_receive = json.loads(request.body)
        logging.debug(json_receive)
        for i in json_receive:
            logging.debug(i.keys())
            user_id = i['user_id__account']
            logging.debug(user_id)
            User.objects.filter(account=user_id).delete()
            lg = Log()
            lg_data = {"Login_User": request.session['user_id'], "user_id": user_id}
            lg.record(LogType.INFO, str(StudentInformationModel._meta.model_name), OpType.DELETE, lg_data)

        logging.info("end stu_info_delete")
        return HttpResponse(json.dumps({'status': 'success'}))


class Teacher_Award_OP(Teacher, Op):

    def __init__(self):
        logging.info('enter teacher_award op')

    def __del__(self):
        logging.info('delete teacher_award op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/award.html', locals())
        elif len(args) == 0:
            return redirect("/teacher/award/")

            # 添加奖惩信息

    def add(self, request):

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

        obj = StudentInformationModel.objects.get(user_id__account=username)
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

        data = {}
        logging.info("enter award_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        if (search_kw != ''):
            result_set = StudentAwardsRecodeModel.objects.filter(
                Q(stu_id__user_id__account__contains=search_kw) |
                Q(stu_id__name__contains=search_kw) |
                Q(award_type__contains=search_kw) |
                Q(award_content__contains=search_kw) |
                Q(award_date__contains=search_kw)
            ).all()
            data['total'] = StudentAwardsRecodeModel.objects.filter(
                Q(stu_id__user_id__account__contains=search_kw) |
                Q(stu_id__name__contains=search_kw) |
                Q(award_type__contains=search_kw) |
                Q(award_content__contains=search_kw) |
                Q(award_date__contains=search_kw)
            ).count()
        else:
            result_set = StudentAwardsRecodeModel.objects.all()
            logging.debug(result_set.values('stu_id__user_id__account', 'stu_id__name', 'award_type', 'award_content',
                                            'award_date'))
            data['total'] = StudentAwardsRecodeModel.objects.all().count()

        if (sort_kw != ''):
            if (order_kw == 'asc'):
                result_set = result_set.order_by(sort_kw)
            else:
                result_set = result_set.order_by(('-' + sort_kw))

        result_set = result_set.values('id', 'stu_id__user_id__account', 'stu_id__name', 'award_type', 'award_content',
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

    # 更新学生信息
    def update(self, request):

        logging.info("enter award_update")
        id = request.POST.get("update_id", None)
        user_id = request.POST.get("update_username", None)
        type = request.POST.get("update_type", None)
        content = request.POST.get("update_content", None)
        if content == '':  # 奖惩详情非空
            return HttpResponse(json.dumps({'status': 'content0'}))

        date = request.POST.get("update_date", None)
        if date == '':  # 奖惩日期非空
            return HttpResponse(json.dumps({'status': 'date0'}))
        obj = StudentInformationModel.objects.get(user_id__account=user_id)
        StudentAwardsRecodeModel.objects.filter(id=id).update(stu_id=obj, award_type=type,
                                                              award_content=content, award_date=date)
        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "id": id, "stu_id": user_id, "type": type, "content": content}
        lg.record(LogType.INFO, str(StudentAwardsRecodeModel._meta.model_name), OpType.UPDATE, lg_data)
        logging.info("end award_update")
        return HttpResponse(json.dumps({'status': 'success'}))

    # 删除学生信息
    @csrf_exempt
    def delete(self, request):
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


class deal(Op, View):  # 核心! 处理url

    def __init__(self):
        pass

    def __del__(self):
        pass

    def get(self, request, **kwargs):
        obj = kwargs.get('obj')  # 一级网址
        fun = kwargs.get('function')  # 二级网址
        subfun = kwargs.get('subfun')  # 三级网址

        # logging.debug(obj, fun, subfun)

        self.AuthorityCheck(request, obj, fun, subfun)  # 检查 登录和url权限
        print(self.visit_status)
        if (self.visit_status < 10):  # 没登陆
            return redirect("/login/")
        elif (self.visit_status == 22 or self.visit_status == 11):  # url和权限对应
            if (self.visit_status // 10 == 1):  # 学生
                t = Student()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转教师首页
                    return t.visit(request)
                else:
                    if (fun == 'choose_course'):
                        scop = Student_ChooseCourse_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return scop.visit(request)
                        elif (not scop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return scop.visit()
                        else:
                            return scop.dictoffun(subfun, request)
                    elif (fun == '123'):
                        pass
                        '''
                        xxop = Student_xxx_OP()
                        if subfun == None: # 不存在子操作就返回功能首页
                            return xxop.visit(request)
                        elif(not xxop.listofop(subfun)): # 子操作错误也返回功能首页
                            return xxop.visit()
                        else:
                            return xxop.dictoffun(subfun, request)
                        '''
            elif (self.visit_status // 10 == 2):  # 教师
                t = Teacher()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转教师首页
                    return t.visit(request)
                else:
                    if (fun == 'stu_info'):
                        tsop = Teacher_StuInfo_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return tsop.visit(request)
                        elif (not tsop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return tsop.visit()
                        else:
                            return tsop.dictoffun(subfun, request)
                    elif (fun == 'award'):
                        taop = Teacher_Award_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return taop.visit(request)
                        elif (not taop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return taop.visit()
                        else:
                            return taop.dictoffun(subfun, request)
        else:  # 此处包含了20和10、12和21，代表链接不对
            if (self.visit_status // 10 == 2):  # 登录的账号是教师
                return redirect("/index_teacher/")
            elif (self.visit_status // 10 == 1):  # 登录的账号是学生
                return redirect("/index_student/")
            else:
                return HttpResponse(404)

    # 暂时post和get内容是一样的，因为没有做方法检查，后续所有使用的功能完善后再说。目前是select和visit使用的get，其余post。
    def post(self, request, **kwargs):
        obj = kwargs.get('obj')  # 一级网址
        fun = kwargs.get('function')  # 二级网址
        subfun = kwargs.get('subfun')  # 三级网址
        # logging.debug(obj, fun, subfun)
        self.AuthorityCheck(request, obj, fun, subfun)  # 检查 登录和url权限
        print(self.visit_status)
        if (self.visit_status < 10):  # 没登陆
            return redirect("/login/")
        elif (self.visit_status == 22 or self.visit_status == 11):  # url和权限对应
            if (self.visit_status // 10 == 1):  # 学生
                t = Student()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转教师首页
                    return t.visit(request)
                else:
                    if (fun == 'choose_course'):
                        scop = Student_ChooseCourse_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return scop.visit(request)
                        elif (not scop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return scop.visit()
                        else:
                            return scop.dictoffun(subfun, request)
                    elif (fun == '123'):
                        pass
                        '''
                        xxop = Student_xxx_OP()
                        if subfun == None: # 不存在子操作就返回功能首页
                            return xxop.visit(request)
                        elif(not xxop.listofop(subfun)): # 子操作错误也返回功能首页
                            return xxop.visit()
                        else:
                            return xxop.dictoffun(subfun, request)
                        '''
            elif (self.visit_status // 10 == 2):  # 教师
                t = Teacher()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转教师首页
                    return t.visit(request)
                else:
                    if (fun == 'stu_info'):
                        tsop = Teacher_StuInfo_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return tsop.visit(request)
                        elif (not tsop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return tsop.visit()
                        else:
                            return tsop.dictoffun(subfun, request)
                    elif (fun == 'award'):
                        taop = Teacher_Award_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return taop.visit(request)
                        elif (not taop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return taop.visit()
                        else:
                            return taop.dictoffun(subfun, request)
        else:  # 此处包含了20和10、12和21，代表链接不对
            if (self.visit_status // 10 == 2):  # 登录的账号是教师
                return redirect("/index_teacher/")
            elif (self.visit_status // 10 == 1):  # 登录的账号是学生
                return redirect("/index_student/")
            else:
                return HttpResponse(404)

##############################################################################

from django.shortcuts import render, redirect
from . import models, forms
from .models import *
import hashlib
import json
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

import logging
from .util import LogType, OpType, Log, hash_code
from django.views.generic import View

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
                        request.session['authority'] = 0
                        return redirect('/manage/teacher/')
                    elif account[0] == '1':
                        request.session['authority'] = 1
                        return redirect('/manage/student/')
                    elif account[0] == '9':
                        request.session['authority'] = 9
                        return redirect('/manage/aadmin/')
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

##############################################################################


class Op():  # 所有操作的基类

    visit_status = -1
    oplist = ['add', 'json', 'delete', 'update']

    def __init__(self):
        logging.info('enter op')

    def __del__(self):
        logging.info('delete op')

    #                      3         2          1        0
    #     status \ url   admin   teacher   student    other
    #  3 admin             33       32        31       30
    #  2 teacher           23       22        21       20
    #  1 student           13       12        11       10
    #  0 nologin           03       02        01       00

    def AuthorityCheck(self, request, obj, function, subfun):
        if request.session['is_login'] == True:  # 登录了
            if self.request.session.get('authority') == 0:
                self.visit_status = 2  # 教师
            elif self.request.session.get('authority') == 1:
                self.visit_status = 1  # 学生
            elif self.request.session.get('authority') == 9:
                self.visit_status = 3  # admin
        else:
            self.visit_status = 0
        self.visit_status *= 10
        if (obj == 'aadmin'):
            self.visit_status += 3
        elif (obj == 'teacher'):
            self.visit_status += 2
        elif (obj == 'student'):
            self.visit_status += 1
        else:
            self.visit_status += 0
        print(self.visit_status)
        # 异常处理
        l = Log()
        if (self.visit_status == 12 or self.visit_status == 21 or
                self.visit_status == 13 or self.visit_status == 31):  # 教师和学生权限相反的任何请求都返回权限错误
            l.logs(request, 0, LogType.WARNING, OpType.VISIT)
        if (self.visit_status < 10):  # 没登陆
            l.logs(request, 1, LogType.WARNING, OpType.VISIT)
        if (self.visit_status % 10 == 0):  # 链接错误
            l.logs(request, 1, LogType.WARNING, OpType.VISIT, '/' +
                   str(obj) + '/' + str(function) + '/' + str(subfun))

        return self.visit_status

    def listofop(self, fun):
        if (fun in self.oplist):
            return 1
        return 0

    def dictoffun(self, fun, request):
        operator = {"add": self.add, "json": self.select,
                    "delete": self.delete, "update": self.update}
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
    funlist = ['choose_course', 'info']  # 功能列表

    def __init__(self):
        logging.info('enter student op')

    def __del__(self):
        logging.info('delete student op')

    def visit(self, request):
        sex_map = {
            'male': '男',
            'female': '女',
        }
        major_map = {
            '080901': "计算机科学与技术",
            '080902': "软件工程",
            '080903': "网络工程",
            '080904K': "信息安全",
            '000001': "纺织化学工程系",
            '000002': "应用化学系",
            '000003': "生物工程系及基础化学部",
        }
        message = ''
        user_id = request.session['user_id']
        account = request.session['account']
        stu_info = StudentInformationModel.objects.get(user_id=user_id)
        request.session['stu_info_id'] = stu_info.id
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

    def listoffunction(self, fun):
        if (fun in self.funlist):
            return 1
        return 0


class Student_Info_OP(Student, Op):

    oplist = ['award', 'alterInfo', 'alterPassword', 'alterPassword_']

    def dictoffun(self, fun, request):
        operator = {
            "award": self.award,
            "alterInfo": self.alterInfo,
            "alterPassword": self.alterPassword,
            "alterPassword_": self.alterPassword_,
        }
        return operator[fun](request)

    def __init__(self):
        logging.info('enter stu_alter_info op')

    def __del__(self):
        logging.info('enter stu_alter_info op')

    def visit(self, request):
        return render(request, 'login/alter_information.html', locals())

    def award(self, request):
        pass

    def alterInfo(self, request):
        logging.info('enter stu_alter_info alterInfo')
        name = request.POST.get("name", None)
        if name == '':  # 姓名非空
            return HttpResponse(json.dumps({'status': 'name0'}))
        email = request.POST.get("email", None)
        if email == '':  # 邮箱非空
            return HttpResponse(json.dumps({'status': 'email0'}))
        stu_info_id = request.session['stu_info_id']
        stu_info = StudentInformationModel.objects.get(id=stu_info_id)
        stu_info.name = name
        stu_info.email = email
        stu_info.save()
        return HttpResponse(json.dumps({'status': 'success'}))

    def alterPassword_(self, request):
        logging.info('enter stu_alter_info alterPassword')
        password0 = request.POST.get('password0', None)
        password1 = request.POST.get('password1', None)
        password2 = request.POST.get('password2', None)
        if password0 == '' or password1 == '' or password2 == '':
            return HttpResponse(json.dumps({'status': '0'}))
        user_id = request.session['user_id']
        user = User.objects.get(id=user_id)
        if hash_code(password0) != user.password:
            return HttpResponse(json.dumps({'status': '0f'}))
        if password1 != password2:
            return HttpResponse(json.dumps({'status': '12f'}))
        user.password = hash_code(password1)
        user.save()
        return HttpResponse(json.dumps({'status': 'success'}))

    def alterPassword(self, request):
        return render(request, 'login/alter_password.html', locals())

    def select(self, request):  # 学生奖惩信息表
        pass


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

        course_id = json_receive[0]['id']
        courseClass_id = json_receive[0]['courseClass__id']

        # 学生信息
        user_id = request.session['user_id']
        stu_info = StudentInformationModel.objects.get(user_id=user_id)

        # 课程添加该学生
        course = CourseModel.objects.get(id=course_id)
        courseClass = course.courseClass.get(id=courseClass_id)
        stu_scores = StudentScoreModel.objects.filter(
            student=stu_info, courseClass=courseClass)
        if stu_scores.exists():
            return HttpResponse(json.dumps({'status': 'exists'}))
        stu_score = StudentScoreModel.objects.create(
            student=stu_info, courseClass=courseClass, score='-', state='学习中')
        courseClass.studentsScore.add(stu_score)
        # 日志
        logging.info("end choose_course add_course")
        return HttpResponse(json.dumps({'status': 'success'}))

    def pout(self, li):
        print()
        for i in li:
            print(i)
        print()
        return

    def remove_duplicates(self, list01):
        list02 = list()
        for i in list01:
            if i not in list02:
                list02.append(i)
        return list02

    def course_filter(self, courselist, stu_info_id):

        # 设重
        for i in courselist:
            if i['courseClass__studentsScore__student_id'] is not None and \
                    i['courseClass__studentsScore__student_id'] != stu_info_id:
                print(i['courseClass__studentsScore__student_id'])
                i['courseClass__studentsScore__student_id'] = None
                i['courseClass__studentsScore__score'] = None
                i['courseClass__studentsScore__state'] = None
        # 去重
        courselist = self.remove_duplicates(courselist)
        # 去空
        for i in courselist:
            if i['courseClass__studentsScore__student_id'] == stu_info_id:
                for j in courselist:
                    if j['courseClass__id'] == i['courseClass__id'] and \
                            j['courseClass__studentsScore__student_id'] is None:
                        print(j['courseClass__id'])
                        courselist.remove(j)
        return courselist

    # 发送课程
    def select(self, request):

        data = {}
        logging.info("enter stu_ChooseCourse_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 获取学生专业
        user_id = request.session['user_id']
        stu_info = StudentInformationModel.objects.get(user_id=user_id)
        unify_class = stu_info.classmodel_set.all()[0]
        major = unify_class.major_id
        # print(user_id, stu_info, unify_class, major)
        # 该专业可选的课程
        course_set = major.courses
        data['total'] = course_set.count()
        # 课程中该学生的成绩和状态
        course_set = course_set.values('id', 'course_name', 'courseClass__id', 'courseClass__id', 'courseClass__teacher__name', 'courseClass__maxNum',
                                       'courseClass__studentsScore__student_id', 'courseClass__studentsScore__score',
                                       'courseClass__studentsScore__state')
        # print(course_set)
        data['rows'] = list(course_set)
        # self.pout(data['rows'])
        data['rows'] = self.course_filter(data['rows'], stu_info.id)
        # self.pout(data['rows'])
        return JsonResponse(data)

    # 删除课程
    @csrf_exempt
    def delete(self, request):

        logging.info('enter choose_course remove_course')
        json_receive = json.loads(request.body)
        logging.debug(json_receive)

        course_id = json_receive[0]['id']
        courseClass_id = json_receive[0]['courseClass__id']

        # 学生信息
        user_id = request.session['user_id']
        stu_info = StudentInformationModel.objects.get(user_id=user_id)

        # 课程移除该学生
        course = CourseModel.objects.get(id=course_id)
        courseClass = course.courseClass.get(id=courseClass_id)
        stu_scores = StudentScoreModel.objects.filter(
            student=stu_info, courseClass=courseClass)
        if not stu_scores.exists():
            return HttpResponse(json.dumps({'status': 'nothing'}))
        stu_score = StudentScoreModel.objects.get(
            student=stu_info, courseClass=courseClass)
        courseClass.studentsScore.remove(stu_score)
        stu_score.delete()
        # 日志
        logging.info("end choose_course remove_course")
        return HttpResponse(json.dumps({'status': 'success'}))


class Teacher():
    funlist = ['stu_info', 'award', 'college','major','class','course','course_class','score']

    def __init__(self):
        logging.info('enter teacher op')

    def __del__(self):
        logging.info('delete teacher op')

    def visit(self, request):
        return render(request, 'login/index_teacher.html', locals())

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
            return redirect("/manage/teacher/stu_info/")

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

        lg.record(LogType.INFO, StudentInformationModel._meta.model_name,
                  OpType.SELECT, lg_data)

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
        lg.record(LogType.INFO, str(
            StudentInformationModel._meta.model_name), OpType.UPDATE, lg_data)

        logging.info("end stu_info_update")
        return HttpResponse(json.dumps({'status': 'success'}))

    # 删除学生信息
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
            lg_data = {
                "Login_User": request.session['user_id'], "user_id": user_id}
            lg.record(LogType.INFO, str(
                StudentInformationModel._meta.model_name), OpType.DELETE, lg_data)

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
            return redirect("/manage/teacher/award/")

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
        lg.record(LogType.INFO, str(
            StudentAwardsRecodeModel._meta.model_name), OpType.ADD, lg_data)
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

        lg.record(LogType.INFO, StudentAwardsRecodeModel._meta.model_name,
                  OpType.SELECT, lg_data)

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
        lg.record(LogType.INFO, str(
            StudentAwardsRecodeModel._meta.model_name), OpType.UPDATE, lg_data)
        logging.info("end award_update")
        return HttpResponse(json.dumps({'status': 'success'}))

    # 删除学生信息
    def delete(self, request):
        logging.info("enter award_delete")
        json_receive = json.loads(request.body)
        for i in json_receive:
            logging.debug(i.keys())
            award_id = i['id']
            StudentAwardsRecodeModel.objects.filter(id=award_id).delete()
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'], "award_id": award_id}
            lg.record(LogType.INFO, str(
                StudentAwardsRecodeModel._meta.model_name), OpType.DELETE, lg_data)
        logging.info("end award_delete")
        return HttpResponse(json.dumps({'status': 'success'}))


<<<<<<< HEAD
<<<<<<< HEAD
class Admin():
    funlist = ['college', '123']

    def __init__(self):
        logging.info('enter admin op')

    def __del__(self):
        logging.info('delete admin op')

    def visit(self, request):
        return render(request, 'login/index_admin.html', locals())

    def listoffunction(self, fun):
        if (fun in self.funlist):
            return 1
        return 0


class Admin_College_OP(Teacher, Op):

    oplist = ['json', 'update']

    def __init__(self):
        logging.info('enter admin_college op')

    def __del__(self):
        logging.info('delete admin_college op')

    def listofop(self, fun):
        if (fun in self.oplist):
            return 1
        return 0

    def dictoffun(self, fun, request, which=None):
        operator = {"json": self.select, "update": self.update}
        return operator[fun](request, which)
=======
=======
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
class Teacher_College_OP(Teacher, Op):
    oplist = ['add', 'json', 'delete', 'update', 'enter']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                "json": self.select,
                "delete": self.delete,
                "update": self.update,
                "enter":self.enter}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter teacher_college op')

    def __del__(self):
        logging.info('delete teacher_college op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/alter_college.html', locals())
        elif len(args) == 0:
            return redirect("/teacher/college/")

    def select(self, request):
        data = {}
        logging.info("enter college select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 学院列表
        colleges = CollegeModel.objects.all()
        data['total'] = colleges.count()
        colleges = colleges.values('id', 'college_name')
        data['rows'] = list(colleges)
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter college add')
        college_name = request.POST.get("college_name", None)
        if college_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        college = CollegeModel.objects.create(college_name=college_name)
        college.save()
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter college delete")
        json_receive = json.loads(request.body)
        college_id = json_receive[0]['id']
        majors = MajorModel.objects.filter(college_id=college_id)
        if majors.exists():
            return HttpResponse(json.dumps({'status': 'have'}))
        CollegeModel.objects.get(id=college_id).delete()
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter college update')
        college_id = request.POST.get("update_id", None)
        college_name = request.POST.get("update_name", None)
        if college_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        print(college_id)
        college = CollegeModel.objects.get(id=college_id)
        college.college_name = college_name
        college.save()
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter(self, request):
        logging.info("enter college enter")
        json_receive = json.loads(request.body)
        # print(json_receive)
        college_id = json_receive['id']
        request.session['college_id']=college_id
        return redirect('/manage/teacher/major/')

class Teacher_Major_OP(Teacher,Op):

    oplist = ['add', 'json', 'delete', 'update', 'enter_class','enter_course']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                "json": self.select,
                "delete": self.delete,
                "update": self.update,
                "enter_class":self.enter_class,
                "enter_course":self.enter_course,
                }
        return operator[fun](request)

    def __init__(self):
        logging.info('enter major op')

    def __del__(self):
        logging.info('delete major op')

    # 功能主页
    def visit(self, *args):
        print(args)
        print(len(args))
        if len(args) == 1:
            return render(args[0], 'login/alter_major.html', locals())
        elif len(args) == 0:
            return redirect("/teacher/major/")

    def select(self, request):
        data = {}
        logging.info("enter major select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 学院
        college_id = request.session['college_id']
        college=CollegeModel.objects.get(id=college_id)
        # 专业
        majors = MajorModel.objects.filter(college_id=college_id)
        data['total'] = majors.count()
        majors = majors.values('id', 'major_name','college_id__college_name')
        data['rows'] = list(majors)
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter major add')
        major_name = request.POST.get("major_name", None)
        if major_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        # 学院
        college_id = request.session['college_id']
        college=CollegeModel.objects.get(id=college_id)
        # 专业
        major=MajorModel.objects.create(major_name=major_name,college_id=college)
        major.save()
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter major delete")
        json_receive = json.loads(request.body)
        major_id = json_receive[0]['id']
        major=MajorModel.objects.get(id=major_id)
        unifyclasses = ClassModel.objects.filter(major_id=major_id)
        courses=major.courses.all()
        if unifyclasses.exists() or courses.exists() :
            return HttpResponse(json.dumps({'status': 'have'}))
        major.delete()
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter major update')
        major_id=request.POST.get("major_id_update", None)
        major_name=request.POST.get("major_name_update", None)
        if major_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        major=MajorModel.objects.get(id=major_id)
        major.major_name=major_name
        major.save()
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter_class(self,request):
        logging.info("enter major enter_class")
        json_receive = json.loads(request.body)
        major_id = json_receive['id']
        request.session['major_id']=major_id
        # return redirect('/manage/teacher/class/')
        return HttpResponse(json.dumps({}))

    def enter_course(self, request):
        logging.info("enter major enter_course")
        json_receive = json.loads(request.body)
        major_id = json_receive['id']
        request.session['major_id']=major_id
        return redirect('/manage/teacher/course/')

class Teacher_Class_OP(Teacher,Op):
    pass
class Teacher_Course_OP(Teacher,Op):
    oplist = ['add', 'json', 'delete', 'update', 'enter']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                "json": self.select,
                "delete": self.delete,
                "update": self.update,
                "enter":self.enter}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter teacher_course op')

    def __del__(self):
        logging.info('delete teacher_course op')
<<<<<<< HEAD
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
=======
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
<<<<<<< HEAD
<<<<<<< HEAD
            return render(args[0], 'login/college.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/college/")

    # 发送专业信息
    def select(self, request, which):

        logging.info("enter college_select")
        # 主逻辑
        if (which == None):
            data = {}
            data['total'] = CollegeModel.objects.count()
            data['status'] = 'success'

            for i in range(CollegeModel.objects.count()):
                data[i] = {}
                data[i]['detail'] = {}
                data[i]['detail']['cname'] = CollegeModel.objects.values('college_name')[
                    i]['college_name']
            return JsonResponse(data)
        else:
            ll = ['1', '2', '3']
            for i in range(CollegeModel.objects.count()):
                data = ['1', '2']
                ll[i] = list(MajorModel.objects.filter(
                    college_id__college_name=CollegeModel.objects.values('college_name')[i]['college_name']).values('major_name'))
                print(ll[i])
                data.append(ll[i])  # bug
                data.append(['3', '4'])
                print(i, data)
            return HttpResponse(json.dumps(data))
            # data[i] = list(MajorModel.objects.filter(
            #     college_id__college_name=CollegeModel.objects.values('college_name')[i]['college_name']).values('major_name'))

        # 日志系统
        # lg = Log()
        # lg_data = {
        #     "Login_User": request.session['user_id'],
        #     "total": data
        # }

        # lg.record(LogType.INFO, StudentInformationModel._meta.model_name,
        #           OpType.SELECT, lg_data)

        logging.info("end college_select")
        return JsonResponse(data)

    # 更新专业信息
    def update(self, request):

        logging.info("enter college_update")

        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "username": username, "email": email, "name": name,
            "sex": sex, "idc": idc, "age": age, "major": major
        }
        lg.record(LogType.INFO, str(
            StudentInformationModel._meta.model_name), OpType.UPDATE, lg_data)

        logging.info("end college_update")
        return HttpResponse(json.dumps({'status': 'success'}))

=======
=======
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
            return render(args[0], 'login/alter_course.html', locals())
        elif len(args) == 0:
            return redirect("/teacher/course/")

    def select(self, request):
        data = {}
        logging.info("enter course select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 上一级 专业
        major_id = request.session['major_id']
        major = MajorModel.objects.get(id=major_id)
        courses=major.courses.all()
        courses=courses.values('id','course_name')
        data['rows']=list(courses)
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter course add')
        course_name = request.POST.get("name", None)
        if course_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        course = CourseModel.objects.create(course_name=course_name)
        course.save()
        # 反向加到专业里去
        major_id = request.session['major_id']
        major = MajorModel.objects.get(id=major_id)
        major.courses.add(course)

        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter course delete")
        json_receive = json.loads(request.body)
        course_id=json_receive[0]['id']
        course=CourseModel.objects.get(id=course_id)
        courseClasses=course.courseClass.all()
        if courseClasses.exists():
            return HttpResponse(json.dumps({'status': 'have'}))
        course.delete()
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter course update')
        course_id = request.POST.get("id_update", None)
        course_name = request.POST.get("name_update", None)
        if course_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        course = CourseModel.objects.get(id=course_id)
        course.course_name = course_name
        course.save()
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter(self, request):
        logging.info("enter course enter")
        json_receive = json.loads(request.body)
        # print(json_receive)
        course_id = json_receive['id']
        request.session['course_id']=course_id
        return HttpResponse(json.dumps({}))

class Teacher_CourseClass_OP(Teacher,Op):
    pass
class Teacher_Score_OP(Teacher,Op):
    pass
<<<<<<< HEAD
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
=======
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f

class deal(Op, View):  # 核心! 处理url

    def __init__(self):
        pass

    def __del__(self):
        pass

    def get(self, request, **kwargs):
        obj = kwargs.get('obj')  # 一级网址
        fun = kwargs.get('function')  # 二级网址
        subfun = kwargs.get('subfun')  # 三级网址
<<<<<<< HEAD
<<<<<<< HEAD
        which = kwargs.get('which')  # 三级网址
        print(obj, fun, subfun)
=======

        print('get', obj, fun, subfun)
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
=======

        print('get', obj, fun, subfun)
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f

        self.AuthorityCheck(request, obj, fun, subfun)  # 检查 登录和url权限
        print(self.visit_status)
        if (self.visit_status < 10):  # 没登陆
            return redirect("/login/")
        elif (self.visit_status == 33 or self.visit_status == 22 or self.visit_status == 11):  # url和权限对应
            if (self.visit_status // 10 == 1):  # 学生
                t = Student()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转首页
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
                    elif (fun == 'info'):
                        saop = Student_Info_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return saop.visit(request)
                        elif(not saop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return saop.visit()
                        else:
                            return saop.dictoffun(subfun, request)

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
<<<<<<< HEAD
<<<<<<< HEAD
            elif (self.visit_status // 10 == 3):  # Admin
                a = Admin()
                if (not a.listoffunction(fun)):  # 不存在这项功能就跳转管理员首页
                    return a.visit(request)
                else:
                    if (fun == 'college'):
                        acop = Admin_College_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return acop.visit(request)
                        elif (not acop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return acop.visit()
                        else:
                            return acop.dictoffun(subfun, request, which)
                    elif (fun == '123'):
                        axop = Teacher_Award_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return axop.visit(request)
                        elif (not axop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return axop.visit()
                        else:
                            return axop.dictoffun(subfun, request)
        else:  # 此处包含了30、20和10；13、12和31、21，代表链接不对
            if (self.visit_status // 10 == 3):  # 登录的账号是教师
                return redirect("/manage/aadmin/")
            elif (self.visit_status // 10 == 2):  # 登录的账号是教师
                return redirect("/manage/teacher/")
=======
=======
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
                    elif (fun == 'college'):
                        tcop = Teacher_College_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return tcop.visit(request)
                        elif (not tcop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return tcop.visit()
                        else:
                            return tcop.dictoffun(subfun, request)
                    
                    elif (fun == 'major'):
                        op = Teacher_Major_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
                    elif (fun == 'class'):
                        op = Teacher_Class_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
                    elif (fun == 'course'):
                        op = Teacher_Course_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
                    elif (fun == 'course_class'):
                        op = Teacher_CourseClass_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
                    elif (fun == 'score'):
                        op = Teacher_Score_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
        else:  # 此处包含了20和10、12和21，代表链接不对
            if (self.visit_status // 10 == 2):  # 登录的账号是教师
                return redirect("/teacher/")
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
            elif (self.visit_status // 10 == 1):  # 登录的账号是学生
                return redirect("/manage/index_student/")
            else:
                return HttpResponse(404)

    # 暂时post和get内容是一样的，因为没有做方法检查，后续所有使用的功能完善后再说。目前是select和visit使用的get，其余post。
    def post(self, request, **kwargs):
        obj = kwargs.get('obj')  # 一级网址
        fun = kwargs.get('function')  # 二级网址
        subfun = kwargs.get('subfun')  # 三级网址
<<<<<<< HEAD
<<<<<<< HEAD
        which = kwargs.get('which')  # 三级网址
        print(obj, fun, subfun)

=======
=======
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f

        print('post', obj, fun, subfun)

        # logging.debug(obj, fun, subfun)
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
        self.AuthorityCheck(request, obj, fun, subfun)  # 检查 登录和url权限
        print(self.visit_status)
        if (self.visit_status < 10):  # 没登陆
            return redirect("/login/")
        elif (self.visit_status == 33 or self.visit_status == 22 or self.visit_status == 11):  # url和权限对应
            if (self.visit_status // 10 == 1):  # 学生
                t = Student()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转首页
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
                    elif (fun == 'info'):
                        saop = Student_Info_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return saop.visit(request)
                        elif(not saop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return saop.visit()
                        else:
                            return saop.dictoffun(subfun, request)

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
<<<<<<< HEAD
<<<<<<< HEAD
            elif (self.visit_status // 10 == 3):  # Admin
                a = Admin()
                if (not a.listoffunction(fun)):  # 不存在这项功能就跳转管理员首页
                    return a.visit(request)
                else:
                    if (fun == 'college'):
                        acop = Admin_College_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return acop.visit(request)
                        elif (not acop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return acop.visit()
                        else:
                            return acop.dictoffun(subfun, request, which)
                    elif (fun == '123'):
                        axop = Teacher_Award_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return axop.visit(request)
                        elif (not axop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return axop.visit()
                        else:
                            return axop.dictoffun(subfun, request)
        else:  # 此处包含了30、20和10；13、12和31、21，代表链接不对
            if (self.visit_status // 10 == 3):  # 登录的账号是教师
                return redirect("/manage/aadmin/")
            elif (self.visit_status // 10 == 2):  # 登录的账号是教师
                return redirect("/manage/teacher/")
=======
=======
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
                    elif (fun == 'college'):
                        tcop = Teacher_College_OP()
                        if subfun == None:  # 不存在子操作就返回功能首页
                            return tcop.visit(request)
                        elif (not tcop.listofop(subfun)):  # 子操作错误也返回功能首页
                            return tcop.visit()
                        else:
                            return tcop.dictoffun(subfun, request)
                    elif (fun == 'major'):
                        op = Teacher_Major_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
                    elif (fun == 'class'):
                        op = Teacher_Class_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
                    elif (fun == 'course'):
                        op = Teacher_Course_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
                    elif (fun == 'course_class'):
                        op = Teacher_CourseClass_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
                    elif (fun == 'score'):
                        op = Teacher_Score_OP()
                        if subfun == None:  
                            return op.visit(request)
                        elif (not op.listofop(subfun)):  
                            return op.visit()
                        else:
                            return op.dictoffun(subfun, request)
                    
        else:  # 此处包含了20和10、12和21，代表链接不对
            if (self.visit_status // 10 == 2):  # 登录的账号是教师
                return redirect("/teacher/")
>>>>>>> b95b0735ecc15484fc279c92eee9a2d9542f1e8f
            elif (self.visit_status // 10 == 1):  # 登录的账号是学生
                return redirect("/manage/index_student/")
            else:
                return HttpResponse(404)

##############################################################################

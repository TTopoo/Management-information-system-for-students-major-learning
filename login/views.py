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
                    # 教师账号
                    if account[0] == '0':
                        request.session['authority'] = 0
                        return redirect('/manage/teacher/course_class/')
                    # 管理员账号
                    elif account[0] == '9':
                        request.session['authority'] = 9
                        return redirect('/manage/aadmin/')
                    # 剩下的都是学生账号
                    else:
                        request.session['authority'] = 1
                        return redirect('/manage/student/')
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
    #  4 teacher2admin     24
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

        if (self.visit_status // 10 == 2):  # teacher
            same_account = Privilege.objects.filter(
                account__user_id__account=request.session["account"])
            if same_account:  # 账号在权限表中存在
                self.visit_status = 24

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

    oplist = ['award', 'award_', 'alterInfo', 'getInfo',
              'alterPassword', 'alterPassword_']

    def dictoffun(self, fun, request):
        operator = {
            "award": self.award,
            "award_": self.award_,
            "alterInfo": self.alterInfo,
            "getInfo": self.getInfo,
            "alterPassword": self.alterPassword,
            "alterPassword_": self.alterPassword_,
        }
        return operator[fun](request)

    def __init__(self):
        logging.info('enter stu_alter_info op')

    def __del__(self):
        logging.info('delete stu_alter_info op')

    def visit(self, *args):
        if len(args) == 1:
            user_id = args[0].session['user_id']
            stu_info = StudentInformationModel.objects.get(user_id=user_id)
            return render(args[0], 'login/alter_information.html', locals())
        elif len(args) == 0:
            return redirect("/manage/student/info/")

    def award(self, request):
        logging.info("enter stu_award page")
        return render(request, 'login/stu_award.html', locals())

    def award_(self, request):
        data = {}
        logging.info("enter stu_award select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        logging.debug(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 学生信息ID
        stu_info_id = request.session['stu_info_id']
        awards = StudentAwardsRecodeModel.objects.filter(stu_id=stu_info_id)
        awards = awards.values('id', 'stu_id__name',
                               'award_type', 'award_content', 'award_date')
        data['total'] = awards.count()
        data['rows'] = list(awards)
        logging.debug(data)
        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "data": data
        }
        lg.record(LogType.INFO, str(
            StudentAwardsRecodeModel._meta.model_name), OpType.SELECT, lg_data)
        logging.info("end stu_award select")
        return JsonResponse(data)

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

        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "name": name, "email": email
        }
        lg.record(LogType.INFO, str(
            StudentInformationModel._meta.model_name), OpType.ADD, lg_data)
        logging.info('end stu_alter_info alterInfo')
        return HttpResponse(json.dumps({'status': 'success'}))

    def getInfo(self, request):
        logging.info('enter stu_alter_info getInfo')
        stu_info_id = request.session['stu_info_id']
        stu_info = StudentInformationModel.objects.get(id=stu_info_id)
        data = {
            'status': 'success',
            'name': stu_info.name,
            'email': stu_info.email,
        }
        return HttpResponse(json.dumps(data))

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

        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "password": password2
        }
        lg.record(LogType.INFO, str(
            StudentInformationModel._meta.model_name), OpType.UPDATE, lg_data)
        logging.info('enter stu_alter_info alterPassword')
        return HttpResponse(json.dumps({'status': 'success'}))

    def alterPassword(self, request):
        return render(request, 'login/alter_password.html', locals())


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
            student=stu_info, courseClass=courseClass, score='-', states='学习中')
        courseClass.studentsScore.add(stu_score)

        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "student": stu_info, "courseClass": courseClass,
        }
        lg.record(LogType.INFO, str(
            StudentScoreModel._meta.model_name), OpType.ADD, lg_data)
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
            if i['courseClass__studentsScore__student__id'] is not None and \
                    i['courseClass__studentsScore__student__id'] != stu_info_id:
                print(i['courseClass__studentsScore__student__id'])
                i['courseClass__studentsScore__student__id'] = None
                i['courseClass__studentsScore__score'] = None
                i['courseClass__studentsScore__states'] = None
        # 去重
        courselist = self.remove_duplicates(courselist)
        # 去空
        for i in courselist:
            if i['courseClass__studentsScore__student__id'] == stu_info_id:
                for j in courselist:
                    if j['courseClass__id'] == i['courseClass__id'] and \
                            j['courseClass__studentsScore__student__id'] is None:
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
        course_set = course_set.values('id', 'course_name', 'courseClass__id', 'courseClass__teacher__name', 'courseClass__maxNum',
                                       'courseClass__studentsScore__student__id', 'courseClass__studentsScore__score',
                                       'courseClass__studentsScore__states')
        logging.debug(course_set)
        data['rows'] = list(course_set)
        data['rows'] = self.course_filter(data['rows'], stu_info.id)

        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "data": data,
        }
        lg.record(LogType.INFO, str(CourseModel._meta.model_name),
                  OpType.SELECT, lg_data)
        logging.info("end stu_ChooseCourse_select")
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

        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "course_id": course_id,
            "courseClass_id": courseClass_id
        }
        lg.record(LogType.INFO, str(
            StudentScoreModel._meta.model_name), OpType.DELETE, lg_data)
        logging.info("end choose_course remove_course")
        return HttpResponse(json.dumps({'status': 'success'}))


class Teacher():
    funlist = ['stu_info', 'award', 'course_class', 'score']

    def __init__(self):
        logging.info('enter teacher op')

    def __del__(self):
        logging.info('delete teacher op')

    def visit(self, request):
        return redirect("/manage/teacher/course_class/")

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
            "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
        }
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


class Teacher_CourseClass_OP(Teacher, Op):
    oplist = ['add', 'json', 'delete', 'update', 'enter']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                    "json": self.select,
                    "delete": self.delete,
                    "update": self.update,
                    "enter": self.enter}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter teacher_courseClass op')

    def __del__(self):
        logging.info('delete teacher_courseClass op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            teachers = TeacherInformationModel.objects.all()
            return render(args[0], 'login/alter_course_class.html', locals())
        elif len(args) == 0:
            return redirect("/teacher/course_class/")

    def select(self, request):
        data = {}
        logging.info("enter course_class select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 该教师模型
        user_id = request.session['user_id']
        teacher = TeacherInformationModel.objects.get(user_id=user_id)
        # 该教师教的课
        courseClasses = CourseClassModel.objects.filter(teacher=teacher)
        data['total'] = courseClasses.count()
        courseClasses = courseClasses.values(
            'id', 'course__course_name', 'teacher__id', 'teacher__name', 'maxNum')
        data['rows'] = list(courseClasses)
        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
            "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
        }
        lg.record(LogType.INFO, str(
            CourseClassModel._meta.model_name), OpType.SELECT, lg_data)
        logging.info("end course_class select")
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter course_class add')
        teacher_id = request.POST.get("teacher_id", None)
        maxNum = request.POST.get("maxNum", None)
        if maxNum == '':
            return HttpResponse(json.dumps({'status': 'maxNum0'}))
        # 创建课程班级
        course_id = request.session['course_id']
        course = CourseModel.objects.get(id=course_id)
        teacher = TeacherInformationModel.objects.get(id=teacher_id)
        courseClass = CourseClassModel.objects.create(
            course=course, teacher=teacher, maxNum=maxNum)
        courseClass.save()
        # 添加进对应的课程
        course.courseClass.add(courseClass)
        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "teacher_id": teacher_id, "maxNum": maxNum,
            "course": course, "teacher": teacher
        }
        lg.record(LogType.INFO, str(
            CourseClassModel._meta.model_name), OpType.ADD, lg_data)
        logging.info("end course_class add")
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter course_class update')
        courseClass_id = request.POST.get("id_update", None)
        teacher_id = request.POST.get("teacher_id_update", None)
        maxNum = request.POST.get("maxNum_update", None)
        if maxNum == '':
            return HttpResponse(json.dumps({'status': 'maxNum0'}))
        courseClass = CourseClassModel.objects.get(id=courseClass_id)
        teacher = TeacherInformationModel.objects.get(id=teacher_id)
        courseClass.teacher = teacher
        courseClass.maxNum = maxNum
        courseClass.save()
        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "courseClass_id": courseClass_id, "teacher_id": teacher_id,
            "maxNum": maxNum, "teacher": teacher
        }
        lg.record(LogType.INFO, str(
            CourseClassModel._meta.model_name), OpType.UPDATE, lg_data)
        logging.info("end course_class add")
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter course_class delete")
        json_receive = json.loads(request.body)
        courseClass_id = json_receive[0]['id']
        courseClass = CourseClassModel.objects.get(id=courseClass_id)
        studentsScores = courseClass.studentsScore.all()
        if studentsScores.exists():
            return HttpResponse(json.dumps({'status': 'have'}))
        courseClass.delete()
        # 日志系统
        lg = Log()
        lg_data = {
            "Login_User": request.session['user_id'],
            "courseClass_id": courseClass_id,
        }
        lg.record(LogType.INFO, str(
            CourseClassModel._meta.model_name), OpType.DELETE, lg_data)
        logging.info("end course_class delete")
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter(self, request):
        logging.info("enter course_class enter")
        json_receive = json.loads(request.body)
        courseClass_id = json_receive['id']
        request.session['courseClass_id'] = courseClass_id
        logging.info("end course_class enter")
        return HttpResponse(json.dumps({}))


class Teacher_Score_OP(Teacher, Op):

    oplist = ['add', 'json', 'delete', 'update', 'charts']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                    "json": self.select,
                    "delete": self.delete,
                    "update": self.update,
                    "charts": self.charts}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter teacher_score op')

    def __del__(self):
        logging.info('delete teacher_score op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            students = StudentInformationModel.objects.all()
            return render(args[0], 'login/alter_score.html', locals())
        elif len(args) == 0:
            return redirect("/teacher/score/")

    def select(self, request):
        data = {}
        logging.info("enter score select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 上一级 课程班级
        courseClass_id = request.session['courseClass_id']
        courseClass = CourseClassModel.objects.get(id=courseClass_id)
        studentScore = courseClass.studentsScore.all()
        data['total'] = studentScore.count()
        studentScore = studentScore.values(
            'id', 'courseClass__course__course_name', 'student__id', 'student__name', 'score', 'states')
        data['rows'] = list(studentScore)
        try:
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
            }
            lg.record(LogType.INFO, CourseClassModel._meta.model_name,
                      OpType.SELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end score select")
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter score add')
        student_id = request.POST.get("student_id", None)
        score = request.POST.get("score", None)
        states = request.POST.get("states", None)
        if states == '':
            return HttpResponse(json.dumps({'status': 'states0'}))
        # 创建学生成绩
        courseClass_id = request.session['courseClass_id']
        try:
            courseClass = CourseClassModel.objects.get(id=courseClass_id)
            student = StudentInformationModel.objects.get(id=student_id)
            studentScore = StudentScoreModel.objects.create(
                student=student, courseClass=courseClass, score=score, states=states)
            studentScore.save()
            # 添加进对应的课程班级
            courseClass.studentsScore.add(studentScore)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "student_id": student_id, "score": score, "states": states,
                "courseClass_id": courseClass_id
            }
            lg.record(LogType.INFO, CourseClassModel._meta.model_name,
                      OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info('end score add')
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter score update')
        studentScore_id = request.POST.get("id_update", None)
        student_id = request.POST.get("student_id_update", None)
        score = request.POST.get("score_update", None)
        states = request.POST.get("states_update", None)
        logging.debug(states)
        if states == '':
            return HttpResponse(json.dumps({'status': 'states0'}))
        try:
            studentScore = StudentScoreModel.objects.get(id=studentScore_id)
            student = StudentInformationModel.objects.get(id=student_id)
            studentScore.student = student
            studentScore.score = score
            studentScore.states = states
            studentScore.save()

            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "studentScore_id": studentScore_id, "student_id": student_id,
                "score": score, "states": states
            }
            lg.record(LogType.INFO, studentScore._meta.model_name,
                      OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info('end score update')
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter score delete")
        json_receive = json.loads(request.body)
        studentScore_id = json_receive[0]['id']
        try:
            studentScore = StudentScoreModel.objects.get(id=studentScore_id)
            studentScore.delete()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "studentScore_id": studentScore_id,
            }
            lg.record(LogType.INFO, studentScore._meta.model_name,
                      OpType.DELETE, lg_data)
        except:
            logging.warning("database error")
        return HttpResponse(json.dumps({'status': 'success'}))

    def charts(self, request):
        data = {}
        logging.info("enter charts select")
        # 课程班级
        courseClass_id = request.session['courseClass_id']
        courseClass = CourseClassModel.objects.get(id=courseClass_id)
        # 学生成绩
        studentScores = courseClass.studentsScore.all()
        # 处理
        excellent = 0
        well = 0
        general = 0
        passed = 0
        fail = 0
        learning = 0
        for i in studentScores:
            print(i.score, i.states)
            if i.states == '学习中':
                learning += 1
                continue
            if int(i.score) >= 90:
                excellent += 1
            elif int(i.score) >= 80:
                well += 1
            elif int(i.score) >= 70:
                general += 1
            elif int(i.score) >= 60:
                passed += 1
            else:
                fail += 1
        data = {
            'data_pie': [
                {'value': excellent, 'name': '优秀'+str(excellent)},
                {'value': well, 'name': '良好'+str(well)},
                {'value': general, 'name': '普通'+str(general)},
                {'value': passed, 'name': '及格'+str(passed)},
                {'value': fail, 'name': '不及格'+str(fail)},
                {'value': learning, 'name': '学习中'+str(learning)},
            ]
        }
        print(data)
        return JsonResponse(data)


class Admin():
    funlist = ['teacher_info', 'privilege', 'college', 'major', 'class',
               'course', 'course_class', 'score', 'student']

    def __init__(self):
        logging.info('enter admin op')

    def __del__(self):
        logging.info('delete admin op')

    def visit(self, request):
        # return render(request, 'login/index_admin.html', locals())
        return redirect("/manage/aadmin/teacher_info/")

    def listoffunction(self, fun):
        if (fun in self.funlist):
            return 1
        return 0


class Admin_College_OP(Admin, Op):

    oplist = ['add', 'json', 'delete', 'update', 'enter']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                    "json": self.select,
                    "delete": self.delete,
                    "update": self.update,
                    "enter": self.enter}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter admin_college op')

    def __del__(self):
        logging.info('delete admin_college op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/alter_college.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/college/")

    def select(self, request):
        data = {}
        logging.info("enter admin_college_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        logging.debug(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 学院列表
        colleges = CollegeModel.objects.all()
        data['total'] = colleges.count()
        colleges = colleges.values('id', 'college_name')
        data['rows'] = list(colleges)
        try:
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
            }
            lg.record(LogType.INFO, CollegeModel._meta.model_name,
                      OpType.SELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admin_college_select")
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter admin_college_add')
        college_name = request.POST.get("college_name", None)
        if college_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        try:
            college = CollegeModel.objects.create(college_name=college_name)
            college.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "college_name": college_name,
            }
            lg.record(LogType.INFO, CollegeModel._meta.model_name,
                      OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info('end admin_college_add')
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter admin_college_delete")
        json_receive = json.loads(request.body)
        college_id = json_receive[0]['id']
        majors = MajorModel.objects.filter(college_id=college_id)
        if majors.exists():
            return HttpResponse(json.dumps({'status': 'have'}))
        try:
            CollegeModel.objects.get(id=college_id).delete()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "college_id": college_id,
            }
            lg.record(LogType.INFO, CollegeModel._meta.model_name,
                      OpType.DELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admin_college_delete")
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter admin_college_update')
        college_id = request.POST.get("update_id", None)
        college_name = request.POST.get("update_name", None)
        if college_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        logging.debug(college_id)
        try:
            college = CollegeModel.objects.get(id=college_id)
            college.college_name = college_name
            college.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "college_id": college_id,
            }
            lg.record(LogType.INFO, CollegeModel._meta.model_name,
                      OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info('end admin_college_update')
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter(self, request):
        logging.info("enter college enter")
        json_receive = json.loads(request.body)
        college_id = json_receive['id']
        request.session['college_id'] = college_id
        logging.info("end college enter")
        return redirect('/manage/aadmin/major/')


class Admin_Major_OP(Admin, Op):

    oplist = ['add', 'json', 'delete', 'update', 'enter_class', 'enter_course']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                    "json": self.select,
                    "delete": self.delete,
                    "update": self.update,
                    "enter_class": self.enter_class,
                    "enter_course": self.enter_course,
                    }
        return operator[fun](request)

    def __init__(self):
        logging.info('enter admin_major op')

    def __del__(self):
        logging.info('delete admin_major op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/alter_major.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/major/")

    def select(self, request):
        data = {}
        logging.info("enter admin_major_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 学院
        college_id = request.session['college_id']
        try:
            college = CollegeModel.objects.get(id=college_id)
            # 专业
            majors = MajorModel.objects.filter(college_id=college_id)
            data['total'] = majors.count()
            majors = majors.values(
                'id', 'major_name', 'college_id__college_name')
            data['rows'] = list(majors)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
            }
            lg.record(LogType.INFO, MajorModel._meta.model_name,
                      OpType.SELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admin_major_select")
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter admin_major_add')
        major_name = request.POST.get("major_name", None)
        if major_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        # 学院
        college_id = request.session['college_id']
        try:
            college = CollegeModel.objects.get(id=college_id)
            # 专业
            major = MajorModel.objects.create(
                major_name=major_name, college_id=college)
            major.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "major_name": major_name, "college_id": college_id
            }
            lg.record(LogType.INFO, MajorModel._meta.model_name,
                      OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info('end admin_major_add')
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter admin_major_delete")
        json_receive = json.loads(request.body)
        major_id = json_receive[0]['id']
        major = MajorModel.objects.get(id=major_id)
        unifyclasses = ClassModel.objects.filter(major_id=major_id)
        courses = major.courses.all()
        if unifyclasses.exists() or courses.exists():
            return HttpResponse(json.dumps({'status': 'have'}))
        try:
            major.delete()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "major_id": major_id,
            }
            lg.record(LogType.INFO, MajorModel._meta.model_name,
                      OpType.DELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admin_major_delete")
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter admin_major_update')
        major_id = request.POST.get("major_id_update", None)
        major_name = request.POST.get("major_name_update", None)
        if major_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        try:
            major = MajorModel.objects.get(id=major_id)
            major.major_name = major_name
            major.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "major_id": major_id, "major_name": major_name,
            }
            lg.record(LogType.INFO, MajorModel._meta.model_name,
                      OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info('end admin_major_update')
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter_class(self, request):
        logging.info("enter admin_major_enter_class")
        json_receive = json.loads(request.body)
        major_id = json_receive['id']
        request.session['major_id'] = major_id
        logging.info("end admin_major_enter_class")
        return HttpResponse(json.dumps({}))

    def enter_course(self, request):
        logging.info("enter admin_major_enter_course")
        json_receive = json.loads(request.body)
        major_id = json_receive['id']
        request.session['major_id'] = major_id
        logging.info("end admin_major_enter_course")
        return redirect('/manage/aadmin/course/')


class Admin_Class_OP(Admin, Op):
    oplist = ['add', 'json', 'delete', 'update', 'enter']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                    "json": self.select,
                    "delete": self.delete,
                    "update": self.update,
                    "enter": self.enter}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter admin_class op')

    def __del__(self):
        logging.info('delete admin_class op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/alter_class.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/class/")

    def select(self, request):
        data = {}
        logging.info("enter admin_class_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 上一级 专业
        major_id = request.session['major_id']
        classes = ClassModel.objects.filter(major_id=major_id)
        classes = classes.values('id', 'class_name', 'major_id__major_name')
        data['total'] = classes.count()
        data['rows'] = list(classes)
        try:
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
            }
            lg.record(LogType.INFO, ClassModel._meta.model_name,
                      OpType.SELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admin_class_select")
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter admin_class_add')
        class_name = request.POST.get("name", None)
        if class_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        major_id = request.session['major_id']
        try:
            major = MajorModel.objects.get(id=major_id)
            unifyclass = ClassModel.objects.create(
                class_name=class_name, major_id=major)
            unifyclass.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "class_name": class_name, "major_id": major_id
            }
            lg.record(LogType.INFO, ClassModel._meta.model_name,
                      OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info('end admin_class_add')
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter admin_class_update')
        class_id = request.POST.get("id_update", None)
        class_name = request.POST.get("name_update", None)
        if class_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        try:
            unifyclass = ClassModel.objects.get(id=class_id)
            unifyclass.class_name = class_name
            unifyclass.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "class_id": class_id, "class_name": class_name
            }
            lg.record(LogType.INFO, ClassModel._meta.model_name,
                      OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info('end admin_class_update')
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter admin_class_delete")
        json_receive = json.loads(request.body)
        class_id = json_receive[0]['id']
        try:
            unifyclass = ClassModel.objects.get(id=class_id)
            students = unifyclass.students.all()
            if students.exists():
                return HttpResponse(json.dumps({'status': 'have'}))
            unifyclass.delete()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "class_id": class_id, "class_name": class_name
            }
            lg.record(LogType.INFO, ClassModel._meta.model_name,
                      OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info('end admin_class_delete')
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter(self, request):
        logging.info("enter admin_class_enter")
        json_receive = json.loads(request.body)
        class_id = json_receive['id']
        request.session['class_id'] = class_id
        logging.info("end admin_class_enter")
        return HttpResponse(json.dumps({'status': 'aadmin'}))


class Admin_Student_OP(Admin, Op):
    def __init__(self):
        logging.info('enter admin_stu op')

    def __del__(self):
        logging.info('delete admin_stu op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            students = StudentInformationModel.objects.all()
            return render(args[0], 'login/alter_student.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/student/")

    def select(self, request):
        data = {}
        logging.info("enter admin_stu_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 上一级 班级
        class_id = request.session['class_id']
        unifyclass = ClassModel.objects.get(id=class_id)
        students = unifyclass.students.all()
        students = students.values('id', 'name', 'sex', 'age', 'email', 'idc')
        data['total'] = students.count()
        data['rows'] = list(students)
        try:
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
            }
            lg.record(LogType.INFO, MajorModel._meta.model_name,
                      OpType.SELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admin_stu_select")
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter score add')
        student_id = request.POST.get("student_id", None)
        # 获得学生和班级索引
        class_id = request.session['class_id']
        try:
            unifyclass = ClassModel.objects.get(id=class_id)
            student = StudentInformationModel.objects.get(id=student_id)
            # 班级添加学生
            unifyclass.students.add(student)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "student_id": student_id, "class_id": class_id
            }
            lg.record(LogType.INFO, MajorModel._meta.model_name,
                      OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info('end score add')
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter score delete")
        json_receive = json.loads(request.body)
        student_id = json_receive[0]['id']
        class_id = request.session['class_id']
        try:
            student = StudentInformationModel.objects.get(id=student_id)
            unifyclass = ClassModel.objects.get(id=class_id)
            unifyclass.students.remove(student)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "student_id": student_id, "class_id": class_id
            }
            lg.record(LogType.INFO, MajorModel._meta.model_name,
                      OpType.DELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end score delete")
        return HttpResponse(json.dumps({'status': 'success'}))


class Admin_Course_OP(Admin, Op):
    oplist = ['add', 'json', 'delete', 'update', 'enter', 'select']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                    "json": self.select,
                    "delete": self.delete,
                    "update": self.update,
                    "select": self.select_,
                    "enter": self.enter}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter admin_course op')

    def __del__(self):
        logging.info('delete admin_course op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            courses = CourseModel.objects.all()
            return render(args[0], 'login/alter_course.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/course/")

    def select(self, request):
        data = {}
        logging.info("enter course select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        logging.debug(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 上一级 专业
        major_id = request.session['major_id']
        major = MajorModel.objects.get(id=major_id)
        courses = major.courses.all()
        courses = courses.values('id', 'course_name')
        data['rows'] = list(courses)
        data['total'] = courses.count()
        try:
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
            }
            lg.record(LogType.INFO, MajorModel._meta.model_name,
                      OpType.SELECT, lg_data)
        except:
            logging.warning("database error")
        logging.info("end course select")
        return JsonResponse(data)

    # 新建课程
    def add(self, request):
        logging.info('enter course add')
        course_name = request.POST.get("name", None)
        if course_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        # 反向加到专业里去
        major_id = request.session['major_id']
        try:
            course = CourseModel.objects.create(course_name=course_name)
            course.save()
            major = MajorModel.objects.get(id=major_id)
            major.courses.add(course)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "course_name": course_name,
            }
            lg.record(LogType.INFO, course._meta.model_name,
                      OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info('end course add')
        return HttpResponse(json.dumps({'status': 'success'}))

    # 添加现有课程
    def select_(self, request):
        logging.info('enter course select_')
        course_id = request.POST.get("course_id", None)
        course = CourseModel.objects.get(id=course_id)
        # 反向加到专业里去
        major_id = request.session['major_id']
        major = MajorModel.objects.get(id=major_id)
        major.courses.add(course)
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter course delete")
        json_receive = json.loads(request.body)
        course_id = json_receive[0]['id']
        course = CourseModel.objects.get(id=course_id)
        courseClasses = course.courseClass.all()
        if courseClasses.exists():
            return HttpResponse(json.dumps({'status': 'have'}))
        try:
            course.delete()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "course_id": course_id,
            }
            lg.record(LogType.INFO, course._meta.model_name,
                      OpType.DELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end course delete")
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter course update')
        course_id = request.POST.get("id_update", None)
        course_name = request.POST.get("name_update", None)
        if course_name == '':
            return HttpResponse(json.dumps({'status': 'name0'}))
        try:
            course = CourseModel.objects.get(id=course_id)
            course.course_name = course_name
            course.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "course_id": course_id,
                "course_name": course_name
            }
            lg.record(LogType.INFO, course._meta.model_name,
                      OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info('end course update')
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter(self, request):
        logging.info("enter course enter")
        json_receive = json.loads(request.body)
        course_id = json_receive['id']
        request.session['course_id'] = course_id
        logging.info("end course enter")
        return HttpResponse(json.dumps({}))


class Admin_CourseClass_OP(Admin, Op):
    oplist = ['add', 'json', 'delete', 'update', 'enter']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                    "json": self.select,
                    "delete": self.delete,
                    "update": self.update,
                    "enter": self.enter}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter teacher_courseClass op')

    def __del__(self):
        logging.info('delete teacher_courseClass op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            teachers = TeacherInformationModel.objects.all()
            return render(args[0], 'login/alter_course_class.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/course_class/")

    def select(self, request):
        data = {}
        logging.info("enter course_class select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        print(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 上一级 课程
        course_id = request.session['course_id']
        course = CourseModel.objects.get(id=course_id)
        courseClasses = course.courseClass.all()
        data['total'] = courseClasses.count()
        courseClasses = courseClasses.values(
            'id', 'course__course_name', 'teacher__id', 'teacher__name', 'maxNum')
        data['rows'] = list(courseClasses)
        try:
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw
            }
            lg.record(LogType.INFO, courseClasses._meta.model_name,
                      OpType.SELECT, lg_data)
        except:
            logging.warning("database error")
        logging.info("end course_class select")
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter course_class add')
        teacher_id = request.POST.get("teacher_id", None)
        maxNum = request.POST.get("maxNum", None)
        if maxNum == '':
            return HttpResponse(json.dumps({'status': 'maxNum0'}))
        # 创建课程班级
        course_id = request.session['course_id']
        try:
            course = CourseModel.objects.get(id=course_id)
            teacher = TeacherInformationModel.objects.get(id=teacher_id)
            courseClass = CourseClassModel.objects.create(
                course=course, teacher=teacher, maxNum=maxNum)
            courseClass.save()
            # 添加进对应的课程
            course.courseClass.add(courseClass)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "teacher_id": teacher_id, "maxNum": maxNum
            }
            lg.record(LogType.INFO, courseClass._meta.model_name,
                      OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info('end course_class add')
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter course_class update')
        courseClass_id = request.POST.get("id_update", None)
        teacher_id = request.POST.get("teacher_id_update", None)
        maxNum = request.POST.get("maxNum_update", None)
        if maxNum == '':
            return HttpResponse(json.dumps({'status': 'maxNum0'}))
        try:
            courseClass = CourseClassModel.objects.get(id=courseClass_id)
            teacher = TeacherInformationModel.objects.get(id=teacher_id)
            courseClass.teacher = teacher
            courseClass.maxNum = maxNum
            courseClass.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "courseClass_id": courseClass_id,
                "teacher_id": teacher_id, "maxNum": maxNum
            }
            lg.record(LogType.INFO, courseClass._meta.model_name,
                      OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info('end course_class update')
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter course_class delete")
        json_receive = json.loads(request.body)
        courseClass_id = json_receive[0]['id']
        try:
            courseClass = CourseClassModel.objects.get(id=courseClass_id)
            studentsScores = courseClass.studentsScore.all()
            if studentsScores.exists():
                return HttpResponse(json.dumps({'status': 'have'}))
            courseClass.delete()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "courseClass_id": courseClass_id
            }
            lg.record(LogType.INFO, courseClass._meta.model_name,
                      OpType.DELETE, lg_data)
        except:
            logging.warning("database error")

        logging.info("end course_class delete")
        return HttpResponse(json.dumps({'status': 'success'}))

    def enter(self, request):
        logging.info("enter course_class enter")
        json_receive = json.loads(request.body)
        courseClass_id = json_receive['id']
        request.session['courseClass_id'] = courseClass_id
        logging.info("end course_class enter")
        return HttpResponse(json.dumps({}))


class Admin_Score_OP(Admin, Op):

    oplist = ['add', 'json', 'delete', 'update', 'charts']

    def dictoffun(self, fun, request):
        operator = {"add": self.add,
                    "json": self.select,
                    "delete": self.delete,
                    "update": self.update,
                    "charts": self.charts}
        return operator[fun](request)

    def __init__(self):
        logging.info('enter admin_score op')

    def __del__(self):
        logging.info('delete admin_score op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            students = StudentInformationModel.objects.all()
            return render(args[0], 'login/alter_score_a.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/score/")

    def select(self, request):
        data = {}
        logging.info("enter score select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        logging.debug(search_kw, sort_kw, order_kw, offset_kw, limit_kw)
        # 上一级 课程班级
        courseClass_id = request.session['courseClass_id']
        courseClass = CourseClassModel.objects.get(id=courseClass_id)
        studentScore = courseClass.studentsScore.all()
        data['total'] = studentScore.count()
        studentScore = studentScore.values(
            'id', 'courseClass__course__course_name', 'student__id', 'student__name', 'score', 'states')
        data['rows'] = list(studentScore)
        try:
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw}

            lg.record(LogType.INFO, studentScore._meta.model_name,
                      OpType.SELECT, lg_data)
        except:
            logging.warning("database error")
        logging.info("end score select")
        return JsonResponse(data)

    def add(self, request):
        logging.info('enter score add')
        student_id = request.POST.get("student_id", None)
        score = request.POST.get("score", None)
        states = request.POST.get("states", None)
        if states == '':
            return HttpResponse(json.dumps({'status': 'states0'}))
        # 创建学生成绩
        courseClass_id = request.session['courseClass_id']
        try:
            courseClass = CourseClassModel.objects.get(id=courseClass_id)
            student = StudentInformationModel.objects.get(id=student_id)
            studentScore = StudentScoreModel.objects.create(
                student=student, courseClass=courseClass, score=score, states=states)
            studentScore.save()
            # 添加进对应的课程班级
            courseClass.studentsScore.add(studentScore)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "student_id": student_id, "score": score, "states": states
            }
            lg.record(LogType.INFO, studentScore._meta.model_name,
                      OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info("end score add")
        return HttpResponse(json.dumps({'status': 'success'}))

    def update(self, request):
        logging.info('enter score update')
        studentScore_id = request.POST.get("id_update", None)
        student_id = request.POST.get("student_id_update", None)
        score = request.POST.get("score_update", None)
        states = request.POST.get("states_update", None)
        print(states)
        if states == '':
            return HttpResponse(json.dumps({'status': 'states0'}))
        try:
            studentScore = StudentScoreModel.objects.get(id=studentScore_id)
            student = StudentInformationModel.objects.get(id=student_id)
            studentScore.student = student
            studentScore.score = score
            studentScore.states = states
            studentScore.save()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "student_id": student_id, "score": score, "states": states
            }
            lg.record(LogType.INFO, studentScore._meta.model_name,
                      OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end score update")
        return HttpResponse(json.dumps({'status': 'success'}))

    def delete(self, request):
        logging.info("enter score delete")
        json_receive = json.loads(request.body)
        studentScore_id = json_receive[0]['id']
        try:
            studentScore = StudentScoreModel.objects.get(id=studentScore_id)
            studentScore.delete()
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "studentScore_id": studentScore_id,
            }
            lg.record(LogType.INFO, studentScore._meta.model_name,
                      OpType.DELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end score update")
        return HttpResponse(json.dumps({'status': 'success'}))

    def charts(self, request):
        data = {}
        logging.info("enter charts select")
        # 课程班级
        courseClass_id = request.session['courseClass_id']
        courseClass = CourseClassModel.objects.get(id=courseClass_id)
        # 学生成绩
        studentScores = courseClass.studentsScore.all()
        # 处理
        excellent = 0
        well = 0
        general = 0
        passed = 0
        fail = 0
        learning = 0
        for i in studentScores:
            print(i.score, i.states)
            if i.states == '学习中':
                learning += 1
                continue
            if int(i.score) >= 90:
                excellent += 1
            elif int(i.score) >= 80:
                well += 1
            elif int(i.score) >= 70:
                general += 1
            elif int(i.score) >= 60:
                passed += 1
            else:
                fail += 1
        data = {
            'data_pie': [
                {'value': excellent, 'name': '优秀'+str(excellent)},
                {'value': well, 'name': '良好'+str(well)},
                {'value': general, 'name': '普通'+str(general)},
                {'value': passed, 'name': '及格'+str(passed)},
                {'value': fail, 'name': '不及格'+str(fail)},
                {'value': learning, 'name': '学习中'+str(learning)},
            ]
        }
        logging.debug(data)
        logging.info("end charts select")
        return JsonResponse(data)


class Admin_Privilege_OP(Admin, Op):

    def __init__(self):
        logging.info('enter admim_privilege op')

    def __del__(self):
        logging.info('delete admim_privilege op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/admin_privilege.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/privilege/")

    # 添加管理员信息
    def add(self, request):

        logging.info("enter admim_privilege_add")
        account = request.POST.get("account", None)
        if account == '':  # 账号非空
            return HttpResponse(json.dumps({'status': 'account0'}))

        exist_account = TeacherInformationModel.objects.filter(
            user_id__account=account)
        if not exist_account:  # 教师信息不存在
            return HttpResponse(json.dumps({'status': 'account1'}))

        same_account = Privilege.objects.filter(
            account__user_id__account=account)
        if same_account:  # 账号在权限表中存在
            return HttpResponse(json.dumps({'status': 'account2'}))

        try:
            # 当一切都OK的情况下，添加新管理员
            obj = TeacherInformationModel.objects.get(user_id__account=account)
            Privilege.objects.create(account=obj, type='3')

            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "account": account,
            }
            lg.record(LogType.INFO, str(
                Privilege._meta.model_name), OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admim_privilege_add")
        return HttpResponse(json.dumps({'status': 'success'}))

    # 发送管理员信息
    def select(self, request):

        data = {}
        logging.info("enter admim_privilege_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        if (search_kw != ''):
            result_set = Privilege.objects.filter(
                Q(account__name__contains=search_kw) |
                Q(account__user_id__account__contains=search_kw)).all()
            data['total'] = Privilege.objects.filter(
                Q(account__name__contains=search_kw) |
                Q(account__user_id__account__contains=search_kw)).count()
        else:
            result_set = Privilege.objects.all()
            data['total'] = Privilege.objects.all().count()

        result_set = result_set.values("id", "account__name", "account__user_id__account")[int(
            offset_kw):(int(offset_kw) + int(limit_kw))]
        print(result_set)
        data['rows'] = list(result_set)
        print(data['rows'])
        try:
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw}

            lg.record(LogType.INFO, Privilege._meta.model_name,
                      OpType.SELECT, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admim_privilege_select")
        return JsonResponse(data)

    # 删除管理员信息
    def delete(self, request):
        logging.info("enter admim_privilege_delete")
        json_receive = json.loads(request.body)
        logging.debug(json_receive)
        try:
            for i in json_receive:
                logging.debug(i.keys())
                account = i['account__user_id__account']
                Privilege.objects.filter(
                    account__user_id__account=account).delete()
                lg = Log()
                lg_data = {
                    "Login_User": request.session['user_id'], "account": account}
                lg.record(LogType.INFO, str(Privilege._meta.model_name),
                          OpType.DELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end admim_privilege_delete")
        return HttpResponse(json.dumps({'status': 'success'}))


class Admin_TeacherInfo_OP(Admin, Op):

    def __init__(self):
        logging.info('enter admin_teacherinfo op')

    def __del__(self):
        logging.info('delete admin_teacherinfo op')

    # 功能主页
    def visit(self, *args):
        if len(args) == 1:
            return render(args[0], 'login/teacher_info.html', locals())
        elif len(args) == 0:
            return redirect("/manage/aadmin/teacher_info/")

    # 添加教师信息
    def add(self, request):

        logging.info("enter teacher_info_add")
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
        graduate = request.POST.get("graduate", None)
        if graduate == '':  # 年龄非空
            return HttpResponse(json.dumps({'status': 'graduate0'}))
        experience = request.POST.get("experience", None)

        same_name_user = User.objects.filter(account=username)
        if same_name_user:  # 学号唯一
            return HttpResponse(json.dumps({'status': 'stuid1'}))

        try:
            # 当一切都OK的情况下，创建新用户
            new_user = User.objects.create()
            new_user.account = username
            new_user.password = hash_code(username)  # 使用学号当做初始加密密码
            new_user.save()

            obj = User.objects.get(account=username)
            TeacherInformationModel.objects.create(user_id=obj, email=email, name=name,
                                                   sex=sex, idc=idc, age=age,
                                                   graduate_school=graduate, education_experience=experience)
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "username": username, "email": email, "name": name,
                "sex": sex, "idc": idc, "age": age, "graduate": graduate, "experience": experience
            }
            lg.record(LogType.INFO, str(TeacherInformationModel._meta.model_name) +
                      ' & ' + str(new_user._meta.model_name), OpType.ADD, lg_data)
        except:
            logging.warning("database error")
        logging.info("end teacher_info_add")
        return HttpResponse(json.dumps({'status': 'success'}))

    # 发送教师信息
    def select(self, request):

        data = {}
        logging.info("enter teacher_info_select")
        search_kw = request.GET.get('search', '')
        sort_kw = request.GET.get('sort', '')
        order_kw = request.GET.get('order', '')
        offset_kw = request.GET.get('offset', 0)
        limit_kw = request.GET.get('limit', 0)
        if (search_kw != ''):
            result_set = TeacherInformationModel.objects.filter(
                Q(user_id__account__contains=search_kw) |
                Q(email__contains=search_kw) |
                Q(name__contains=search_kw) |
                Q(sex__contains=search_kw) |
                Q(idc__contains=search_kw) |
                Q(age__contains=search_kw) |
                Q(graduate_school__contains=search_kw) |
                Q(education_experience__contains=search_kw)
            ).all()
            data['total'] = TeacherInformationModel.objects.filter(
                Q(user_id__account__contains=search_kw) |
                Q(email__contains=search_kw) |
                Q(name__contains=search_kw) |
                Q(sex__contains=search_kw) |
                Q(idc__contains=search_kw) |
                Q(age__contains=search_kw) |
                Q(graduate_school__contains=search_kw) |
                Q(education_experience__contains=search_kw)
            ).count()
        else:
            result_set = TeacherInformationModel.objects.all()
            data['total'] = TeacherInformationModel.objects.all().count()
        if (sort_kw != ''):
            if (order_kw == 'asc'):
                result_set = result_set.order_by(sort_kw)
            else:
                result_set = result_set.order_by(('-' + sort_kw))

        result_set = result_set.values('user_id__account', 'email', 'name', 'sex', 'idc', 'age', 'graduate_school', 'education_experience')[
            int(offset_kw):(int(offset_kw) + int(limit_kw))]
        logging.debug(result_set)
        data['rows'] = list(result_set)
        logging.debug(data['rows'])

        try:
            # 日志系统
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "total": data['total'], "search_kw": search_kw, "sort_kw": sort_kw,
                "order_kw": order_kw, "offset_kw": offset_kw, "limit_kw": limit_kw}

            lg.record(LogType.INFO, TeacherInformationModel._meta.model_name,
                      OpType.SELECT, lg_data)
        except:
            logging.warning("database error")

        logging.info("end teacher_info_select")
        return JsonResponse(data)

    # 更新教师信息
    def update(self, request):

        logging.info("enter teacher_info_update")
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
        graduate = request.POST.get("update_graduate", None)
        if graduate == '':  # 年龄非空
            return HttpResponse(json.dumps({'status': 'graduate0'}))
        experience = request.POST.get("update_experience", None)

        try:
            obj = User.objects.get(account=username)
            TeacherInformationModel.objects.filter(user_id=obj).update(user_id=obj, email=email, name=name,
                                                                       sex=sex, idc=idc, age=age,
                                                                       graduate_school=graduate, education_experience=experience)
            lg = Log()
            lg_data = {
                "Login_User": request.session['user_id'],
                "username": username, "email": email, "name": name,
                "sex": sex, "idc": idc, "age": age, "graduate": graduate, "experience": experience
            }
            lg.record(LogType.INFO, str(
                TeacherInformationModel._meta.model_name), OpType.UPDATE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end teacher_info_update")
        return HttpResponse(json.dumps({'status': 'success'}))

    # 删除教师信息
    def delete(self, request):
        logging.info("enter teacher_info_delete")
        json_receive = json.loads(request.body)
        logging.debug(json_receive)
        try:
            for i in json_receive:
                logging.debug(i.keys())
                user_id = i['user_id__account']
                logging.debug(user_id)
                User.objects.filter(account=user_id).delete()
                lg = Log()
                lg_data = {
                    "Login_User": request.session['user_id'], "user_id": user_id}
                lg.record(LogType.INFO, str(
                    TeacherInformationModel._meta.model_name), OpType.DELETE, lg_data)
        except:
            logging.warning("database error")
        logging.info("end teacher_info_delete")
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

        print('get', obj, fun, subfun)

        self.AuthorityCheck(request, obj, fun, subfun)  # 检查 登录和url权限
        print(self.visit_status)
        if (self.visit_status < 10):  # 没登陆
            return redirect("/login/")
        elif (self.visit_status == 33 or
              self.visit_status == 22 or
              self.visit_status == 11 or
              self.visit_status == 24):  # url和权限对应
            if (self.visit_status == 11):  # 学生
                t = Student()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转首页
                    return t.visit(request)
                else:
                    # 定义类实例
                    if (fun == 'choose_course'):
                        op = Student_ChooseCourse_OP()
                    elif (fun == 'info'):
                        op = Student_Info_OP()
                    # 执行类方法
                    if subfun == None:  # 不存在子操作就返回功能首页
                        return op.visit(request)
                    elif(not op.listofop(subfun)):  # 子操作错误也返回功能首页
                        return op.visit()
                    else:
                        return op.dictoffun(subfun, request)

            elif (self.visit_status == 22):  # 教师
                t = Teacher()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转教师首页
                    return t.visit(request)
                else:
                    # 定义类实例
                    if (fun == 'stu_info'):
                        op = Teacher_StuInfo_OP()
                    elif (fun == 'award'):
                        op = Teacher_Award_OP()
                    elif (fun == 'course_class'):
                        op = Teacher_CourseClass_OP()
                    elif (fun == 'score'):
                        op = Teacher_Score_OP()
                    # 执行类方法
                    if subfun == None:
                        return op.visit(request)
                    elif (not op.listofop(subfun)):
                        return op.visit()
                    else:
                        return op.dictoffun(subfun, request)

            elif (self.visit_status == 33):  # Admin
                a = Admin()
                if (not a.listoffunction(fun)):  # 不存在这项功能就跳转管理员首页
                    return a.visit(request)
                else:
                    # 定义类实例
                    if (fun == 'privilege'):
                        op = Admin_Privilege_OP()
                    elif (fun == 'college'):
                        op = Admin_College_OP()
                    elif (fun == 'major'):
                        op = Admin_Major_OP()
                    elif (fun == 'class'):
                        op = Admin_Class_OP()
                    elif (fun == 'course'):
                        op = Admin_Course_OP()
                    elif (fun == 'course_class'):
                        op = Admin_CourseClass_OP()
                    elif (fun == 'score'):
                        op = Admin_Score_OP()
                    elif (fun == 'student'):
                        op = Admin_Student_OP()
                    elif (fun == 'teacher_info'):
                        op = Admin_TeacherInfo_OP()
                    # 执行类方法
                    if subfun == None:
                        return op.visit(request)
                    elif (not op.listofop(subfun)):
                        return op.visit()
                    else:
                        return op.dictoffun(subfun, request)

            elif (self.visit_status == 24):  # teachertoadmin
                if (obj == 'teacher'):
                    O = Teacher()
                elif (obj == 'aadmin'):
                    O = Admin()
                else:
                    return redirect("/manage/teacher/")
                if (not O.listoffunction(fun)):  # 不存在这项功能就跳转管理员首页
                    return O.visit(request)
                else:
                    if (fun == 'privilege'):
                        op = Admin_Privilege_OP()
                    elif (fun == 'college'):
                        op = Admin_College_OP()
                    elif (fun == 'major'):
                        op = Admin_Major_OP()
                    elif (fun == 'class'):
                        op = Admin_Class_OP()
                    elif (fun == 'course'):
                        op = Admin_Course_OP()
                    elif (fun == 'course_class'):
                        op = Admin_CourseClass_OP()
                    elif (fun == 'score'):
                        op = Admin_Score_OP()
                    elif (fun == 'stu_info'):
                        op = Teacher_StuInfo_OP()
                    elif (fun == 'award'):
                        op = Teacher_Award_OP()
                    elif (fun == 'course_class'):
                        op = Teacher_CourseClass_OP()
                    elif (fun == 'score'):
                        op = Teacher_Score_OP()
                    elif (fun == 'teacher_info'):
                        op = Admin_TeacherInfo_OP()
                    if subfun == None:
                        return op.visit(request)
                    elif (not op.listofop(subfun)):
                        return op.visit()
                    else:
                        return op.dictoffun(subfun, request)

        else:  # 此处包含了30、20和10；13、12和31、21，代表链接不对
            if (self.visit_status // 10 == 3):  # 登录的账号是教师
                return redirect("/manage/aadmin/")
            elif (self.visit_status // 10 == 2):  # 登录的账号是教师
                return redirect("/manage/teacher/")
            elif (self.visit_status // 10 == 1):  # 登录的账号是学生
                return redirect("/manage/student/")
            else:
                return HttpResponse(404)

    # 暂时post和get内容是一样的，因为没有做方法检查，后续所有使用的功能完善后再说。目前是select和visit使用的get，其余post。
    def post(self, request, **kwargs):
        obj = kwargs.get('obj')  # 一级网址
        fun = kwargs.get('function')  # 二级网址
        subfun = kwargs.get('subfun')  # 三级网址

        print('get', obj, fun, subfun)

        self.AuthorityCheck(request, obj, fun, subfun)  # 检查 登录和url权限
        print(self.visit_status)
        if (self.visit_status < 10):  # 没登陆
            return redirect("/login/")
        elif (self.visit_status == 33 or
              self.visit_status == 22 or
              self.visit_status == 11 or
              self.visit_status == 24):  # url和权限对应
            if (self.visit_status == 11):  # 学生
                t = Student()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转首页
                    return t.visit(request)
                else:
                    # 定义类实例
                    if (fun == 'choose_course'):
                        op = Student_ChooseCourse_OP()
                    elif (fun == 'info'):
                        op = Student_Info_OP()
                    # 执行类方法
                    if subfun == None:  # 不存在子操作就返回功能首页
                        return op.visit(request)
                    elif(not op.listofop(subfun)):  # 子操作错误也返回功能首页
                        return op.visit()
                    else:
                        return op.dictoffun(subfun, request)

            elif (self.visit_status == 22):  # 教师
                t = Teacher()
                if (not t.listoffunction(fun)):  # 不存在这项功能就跳转教师首页
                    return t.visit(request)
                else:
                    # 定义类实例
                    if (fun == 'stu_info'):
                        op = Teacher_StuInfo_OP()
                    elif (fun == 'award'):
                        op = Teacher_Award_OP()
                    elif (fun == 'course_class'):
                        op = Teacher_CourseClass_OP()
                    elif (fun == 'score'):
                        op = Teacher_Score_OP()
                    # 执行类方法
                    if subfun == None:
                        return op.visit(request)
                    elif (not op.listofop(subfun)):
                        return op.visit()
                    else:
                        return op.dictoffun(subfun, request)

            elif (self.visit_status == 33):  # Admin
                a = Admin()
                if (not a.listoffunction(fun)):  # 不存在这项功能就跳转管理员首页
                    return a.visit(request)
                else:
                    # 定义类实例
                    if (fun == 'privilege'):
                        op = Admin_Privilege_OP()
                    elif (fun == 'college'):
                        op = Admin_College_OP()
                    elif (fun == 'major'):
                        op = Admin_Major_OP()
                    elif (fun == 'class'):
                        op = Admin_Class_OP()
                    elif (fun == 'course'):
                        op = Admin_Course_OP()
                    elif (fun == 'course_class'):
                        op = Admin_CourseClass_OP()
                    elif (fun == 'score'):
                        op = Admin_Score_OP()
                    elif (fun == 'student'):
                        op = Admin_Student_OP()
                    elif (fun == 'teacher_info'):
                        op = Admin_TeacherInfo_OP()
                    # 执行类方法
                    if subfun == None:
                        return op.visit(request)
                    elif (not op.listofop(subfun)):
                        return op.visit()
                    else:
                        return op.dictoffun(subfun, request)

            elif (self.visit_status == 24):  # teachertoadmin
                if (obj == 'teacher'):
                    O = Teacher()
                elif (obj == 'aadmin'):
                    O = Admin()
                else:
                    return redirect("/manage/teacher/")
                if (not O.listoffunction(fun)):  # 不存在这项功能就跳转管理员首页
                    return O.visit(request)
                else:
                    if (fun == 'privilege'):
                        op = Admin_Privilege_OP()
                    elif (fun == 'college'):
                        op = Admin_College_OP()
                    elif (fun == 'major'):
                        op = Admin_Major_OP()
                    elif (fun == 'class'):
                        op = Admin_Class_OP()
                    elif (fun == 'course'):
                        op = Admin_Course_OP()
                    elif (fun == 'course_class'):
                        op = Admin_CourseClass_OP()
                    elif (fun == 'score'):
                        op = Admin_Score_OP()
                    elif (fun == 'stu_info'):
                        op = Teacher_StuInfo_OP()
                    elif (fun == 'award'):
                        op = Teacher_Award_OP()
                    elif (fun == 'course_class'):
                        op = Teacher_CourseClass_OP()
                    elif (fun == 'score'):
                        op = Teacher_Score_OP()
                    elif (fun == 'teacher_info'):
                        op = Admin_TeacherInfo_OP()
                    if subfun == None:
                        return op.visit(request)
                    elif (not op.listofop(subfun)):
                        return op.visit()
                    else:
                        return op.dictoffun(subfun, request)

        else:  # 此处包含了30、20和10；13、12和31、21，代表链接不对
            if (self.visit_status // 10 == 3):  # 登录的账号是教师
                return redirect("/manage/aadmin/")
            elif (self.visit_status // 10 == 2):  # 登录的账号是教师
                return redirect("/manage/teacher/")
            elif (self.visit_status // 10 == 1):  # 登录的账号是学生
                return redirect("/manage/student/")
            else:
                return HttpResponse(404)
        ##############################################################################

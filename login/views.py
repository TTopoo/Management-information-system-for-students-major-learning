from django.shortcuts import render,redirect
from . import models,forms
import hashlib

def hash_code(s, salt='mysite'):# 加点盐
    h = hashlib.md5()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()

def index(request):
    pass
    return render(request,'login/index.html')

def login(request):
    if request.session.get('is_login',None):
        return redirect('/index')

    if request.method == "POST":
        login_form = forms.UserForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            try:
                user = models.User.objects.get(name=username)
                if user.password == hash_code(password):# 哈希值和数据库内的值进行比对
                    request.session['is_login'] = True
                    request.session['user_id'] = user.id
                    request.session['user_name'] = user.name
                    return redirect('/index/')
                else:
                    message = "密码不正确！"
            except:
                message = "用户不存在！"
        return render(request, 'login/login.html', locals())

    login_form = forms.UserForm()
    return render(request, 'login/login.html', locals())

def register(request):
    if request.session.get('is_login', None):
        # 登录状态不允许注册。你可以修改这条原则！
        return redirect("/index/")
    if request.method == "POST":
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():  # 获取数据
            username = register_form.cleaned_data['username']
            password1 = register_form.cleaned_data['password1']
            password2 = register_form.cleaned_data['password2']
            if password1 != password2:  # 判断两次密码是否相同
                message = "两次输入的密码不同！"
                return render(request, 'login/register.html', locals())
            else:
                same_name_user = models.User.objects.filter(name=username)
                if same_name_user:  # 用户名唯一
                    message = '用户已经存在，请重新选择用户名！'
                    return render(request, 'login/register.html', locals())
                
                # 当一切都OK的情况下，创建新用户

                new_user = models.User.objects.create()
                new_user.name = username
                new_user.password = hash_code(password1) # 使用加密密码
                new_user.save()
                return redirect('/login/')  # 自动跳转到登录页面
        return render(request, 'login/register.html', locals())
    register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())

def logout(request):
    if not request.session.get('is_login', None):
        # 如果本来就未登录，也就没有登出一说
        return redirect("/index/")
    request.session.flush()
    # 或者使用下面的方法
    # del request.session['is_login']
    # del request.session['user_id']
    # del request.session['user_name']
    return redirect("/index/")

def add(request):
    if request.method == "POST":
        add_form = forms.AddForm(request.POST)
        print(add_form)
        print(add_form.is_valid())
        message = "请检查填写的内容！"
        if add_form.is_valid():  # 获取数据
            username = add_form.cleaned_data['username']
            email = add_form.cleaned_data['email']
            name = add_form.cleaned_data['name']
            sex = add_form.cleaned_data['sex']
            idc = add_form.cleaned_data['idc']
            age = add_form.cleaned_data['age']
            major = add_form.cleaned_data['major']

            print(username)

            same_name_user = models.User.objects.filter(name=username)
            if same_name_user:  # 学号唯一
                message = '学号已经存在，请重新输入学号！'
                return render(request, 'login/add.html', locals())
            same_email_user = models.StudentInformationModel.objects.filter(email=email)
            if same_email_user:  # 邮箱地址唯一
                message = '该邮箱地址已被注册，请使用别的邮箱！'
                return render(request, 'login/add.html', locals())

            # 当一切都OK的情况下，创建新用户

            new_user = models.User.objects.create()
            new_user.name = username
            new_user.password = hash_code(username) # 使用学号当做初始加密密码
            new_user.save()

            obj = models.User.objects.get(name=username)
            models.StudentInformationModel.objects.create(stu_id=obj,
                email=email,
                name=name,
                sex=sex,
                idc=idc,
                age=age,
                major=major)
            message = '增加成功'   
            return render(request, 'login/add.html', locals())
        #return render(request, 'login/add.html', locals())
    add_form = forms.AddForm()
    return render(request, 'login/add.html', locals())

'''
# 查询
def select(request):
    if request.method == "POST":
        id = request.POST.get('stu_id')
        stu_data = StudentInformationModel.objects.get(stu_id=id)
        stu_id = stu_data.stu_id.stu_id
        stu_name = stu_data.stu_name
        stu_sex = stu_data.stu_sex
        stu_idc = stu_data.stu_idc
        stu_age = stu_data.stu_age
        stu_major = stu_data.stu_major
        #stu_course = CourseModel.objects.filter(cour_id=id)
        dct = {}
        #for stu in stu_course:
        #    dct[stu.course] = stu.grade
        context = {
            'stu_id': stu_id,
            'stu_name': stu_name,
            'stu_sex': stu_sex,
            'stu_idc': stu_idc,
            'stu_age': stu_age,
            'stu_major': stu_major,
            #'course_data': dct,
            'msg': True
        }
        return render(request, 'studentManage/select.html', context)
    else:
        root_information = request.session['user']
        id = root_information['id']
        context = {
            'msg': False,
            'id': id
        }
        return render(request, 'studentManage/select.html', context)

# 删除
def delete(request):
    if request.method == "POST":
        
        id = request.POST.get('stu_id')
        print(id)
        print(StudentInformationModel.objects.filter(stu_id=id))
        StudentInformationModel.objects.filter(stu_id=id).delete()
        context = {
            'msg': '成功删除'
        }
        return render(request, 'studentManage/delete.html', context)
    else:
        root_information = request.session['user']
        id = root_information['id']
        context = {
            'id': id
        }
        return render(request, 'studentManage/delete.html', context)

# 修改
def update(request):
    user_information = request.session['user']
    id = user_information['id']
    stu_data = StudentInformationModel.objects.get(stu_id=id)
    stu_id = stu_data.stu_id.stu_id
    stu_name = stu_data.stu_name
    stu_sex = stu_data.stu_sex
    stu_idc = stu_data.stu_idc
    stu_age = stu_data.stu_age
    stu_major = stu_data.stu_major
    context = {
        'stu_id': stu_id,
        'stu_name': stu_name,
        'stu_sex': stu_sex,
        'stu_idc': stu_idc,
        'stu_age': stu_age,
        'stu_major': stu_major,
    }
    if request.method == "POST":
        stu_id = request.POST.get('stu_id')
        stu_name = request.POST.get('stu_name')
        stu_sex = request.POST.get('stu_sex')
        stu_idc = request.POST.get('stu_idc')
        stu_age = request.POST.get('stu_age')
        stu_major = request.POST.get('stu_major')
        # StudentInformationModel.objects.filter(stu_id=id).update(stu_id=stu_id, stu_name=stu_name, stu_phone=stu_phone, str_addr=stu_addr, stu_faculty=stu_faculty, stu_major=stu_major)
        # 或者 以下这种，对单个数据进行修改
        stu_data = StudentInformationModel.objects.get(stu_id=id)
        stu_data.stu_id.stu_id = stu_id
        stu_data.stu_name = stu_name
        stu_data.stu_sex = stu_sex
        stu_data.stu_idc = stu_idc
        stu_data.stu_age = stu_age
        stu_data.stu_major = stu_major
        stu_data.save()
        context = {
            'stu_id': stu_id,
            'stu_name': stu_name,
            'stu_sex': stu_sex,
            'stu_idc': stu_idc,
            'stu_age': stu_age,
            'stu_major': stu_major,
            'msg': '修改成功'
        }
        return render(request, 'studentManage/update.html', context)
    else:
        return render(request, 'studentManage/update.html', context)
'''
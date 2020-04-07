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


def allinone(request):
    if request.is_ajax() and request.method == 'POST':
        print("ids",request.POST.getlist("id"))
        print("action", request.POST.get("action"))
    return render(request, 'login/formtest.html', locals())
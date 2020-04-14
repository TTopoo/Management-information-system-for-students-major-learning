from django import forms
from captcha.fields import CaptchaField
from django.forms import widgets


# 登录表单
class UserForm(forms.Form):
    account = forms.CharField(label="学号", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    # captcha = CaptchaField(label='验证码')


# 注册表单
class RegisterForm(forms.Form):
    username = forms.CharField(label="学号", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="确认密码", max_length=256,
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    # captcha = CaptchaField(label='验证码')


# 信息完善表单
class FillInformationForm(forms.Form):
    gender = (
        ('male', "男"),
        ('female', "女"),
    )
    majorChoice = (
        ('080901', "计算机科学与技术"),
        ('080902', "软件工程"),
        ('080903', "网络工程"),
        ('080904K', "信息安全"),
    )
    password1 = forms.CharField(label="密码", max_length=256,
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="确认密码", max_length=256,
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label="姓名", widget=forms.TextInput(attrs={'class': 'form-control'}))
    sex = forms.ChoiceField(label='性别', choices=gender)
    age = forms.CharField(label='年龄', max_length=10,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="邮箱", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    idc = forms.CharField(label='身份证', max_length=18, min_length=18,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    major = forms.ChoiceField(label='专业', choices=majorChoice)


# 信息修改表单
class AlterInformationForm(forms.Form):
    password1 = forms.CharField(label="密码", max_length=256,
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="确认密码", max_length=256,
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label="姓名", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="邮箱", widget=forms.EmailInput(attrs={'class': 'form-control'}))


# 用户添加表单
class AddForm(forms.Form):
    gender = (
        ('male', "男"),
        ('female', "女"),
    )
    majorchoice = (
        ('080901', "计算机科学与技术"),
        ('080902', "软件工程"),
        ('080903', "网络工程"),
        ('080904K', "信息安全"),
    )
    username = forms.CharField(label="学号", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="邮箱", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label="姓名", widget=forms.TextInput(attrs={'class': 'form-control'}))
    sex = forms.ChoiceField(label='性别', choices=gender)
    idc = forms.CharField(label='身份证', max_length=18, min_length=18,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    age = forms.CharField(label='年龄', max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    major = forms.ChoiceField(label='专业', choices=majorchoice)


#
class SelectForm1(forms.Form):
    stu_id = forms.CharField(label="学号", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))


#
class SelectForm2(forms.Form):
    majorchoice = (
        ('080901', "计算机科学与技术"),
        ('080902', "软件工程"),
        ('080903', "网络工程"),
        ('080904K', "信息安全"),
    )
    name = forms.CharField(label="姓名", widget=forms.TextInput(attrs={'class': 'form-control'}))
    major = forms.ChoiceField(label='专业', choices=majorchoice)

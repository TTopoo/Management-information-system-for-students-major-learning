from django import forms
from captcha.fields import CaptchaField

class UserForm(forms.Form):
    username = forms.CharField(label="学号", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    captcha = CaptchaField(label='验证码')

class RegisterForm(forms.Form):
    gender = (
        ('male', "男"),
        ('female', "女"),
    )
    username = forms.CharField(label="学号", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="确认密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    captcha = CaptchaField(label='验证码')

class AddForm(forms.Form):
    gender = (
        ('male', "男"),
        ('female', "女"),
    )
    majorchoice = (
        ('080901',"计算机科学与技术"),
        ('080902',"软件工程"),
        ('080903',"网络工程"),
        ('080904K',"信息安全"),
    )
    username = forms.CharField(label="学号", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="邮箱地址", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    name = forms.EmailField(label="姓名", min_length=2,widget=forms.TextInput(attrs={'class': 'form-control'}))
    sex = forms.ChoiceField(label='性别', choices=gender)
    idc = forms.CharField(label='身份证', max_length=18, min_length=18, widget=forms.TextInput(attrs={'class': 'form-control'}))
    age = forms.CharField(label='年龄', widget=forms.TextInput(attrs={'class': 'form-control'}))
    #major = forms.CharField(label='专业', choices=majorchoice)
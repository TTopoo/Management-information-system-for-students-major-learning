from django.db import models


# 用户账号模型
class User(models.Model):
    name = models.CharField(max_length=128, unique=True, verbose_name='学生ID')
    password = models.CharField(max_length=256, verbose_name='密码')

    # sex = models.CharField(max_length=32,choices=gender,default='男')
    c_time = models.DateTimeField(auto_now_add=True)

    # salt = models.CharField(max_length=10, verbose_name='盐')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['c_time']  # 默认排序 c_time
        verbose_name = '用户'  # 模型起名
        verbose_name_plural = '用户'  # 模型名的复数


# 学生信息模型
class StudentInformationModel(models.Model):
    gender = (
        ('male', '男'),
        ('female', '女'),
    )
    majorchoice = (
        ('080901', "计算机科学与技术"),
        ('080902', "软件工程"),
        ('080903', "网络工程"),
        ('080904K', "信息安全"),
    )
    stu_id = models.ForeignKey('User', to_field='name', on_delete=models.CASCADE)
    email = models.EmailField(verbose_name='邮箱')
    name = models.CharField(max_length=30, verbose_name='姓名', null=True)
    sex = models.CharField(max_length=32, choices=gender, default='男')
    idc = models.CharField(max_length=20, verbose_name='身份证', null=True)
    age = models.CharField(max_length=20, verbose_name='年龄', null=True)
    major = models.CharField(max_length=30, choices=majorchoice, default='计算机科学与技术')

    class Meta:
        ordering = ['stu_id']
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'


# 学生奖惩模型
class StudentAwardsRecodeModel(models.Model):
    stu_id = models.ForeignKey('User', to_field='name', on_delete=models.CASCADE)
    award_type = models.CharField(max_length=5, verbose_name='奖惩记录类别', null=True)
    award_content = models.CharField(max_length=50, verbose_name='奖惩信息', null=True)
    award_date = models.DateField(verbose_name='奖惩日期', null=True)

    class Meta:
        ordering = ['stu_id']
        verbose_name = '奖惩信息'
        verbose_name_plural = '奖惩信息'


# 课程模型
class CourseModel(models.Model):
    course_id = models.AutoField(primary_key=True, verbose_name='课程ID')
    course_name = models.CharField(max_length=64, verbose_name='课程名称')
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.course_name

    class Meta:
        ordering = ['create_date']
        verbose_name = '课程'
        verbose_name_plural = '课程'

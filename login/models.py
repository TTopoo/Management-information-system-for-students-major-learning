from django.db import models


# 用户账号模型
class User(models.Model):
    stuid = models.CharField(max_length=128, unique=True, verbose_name='学生ID')
    password = models.CharField(max_length=256, verbose_name='密码')

    c_time = models.DateTimeField(auto_now_add=True)

    # salt = models.CharField(max_length=10, verbose_name='盐')

    def __str__(self):
        return self.stuid

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
    stu_id = models.ForeignKey('User', on_delete=models.CASCADE)
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


# 教师信息模型

# 管理员信息模型


# 学生奖惩模型
class StudentAwardsRecodeModel(models.Model):
    stu_id = models.ForeignKey('StudentInformationModel', on_delete=models.CASCADE)
    award_type = models.CharField(max_length=5, verbose_name='奖惩记录类别', null=True)
    award_content = models.CharField(max_length=50, verbose_name='奖惩信息', null=True)
    award_date = models.DateField(verbose_name='奖惩日期', null=True)

    class Meta:
        ordering = ['stu_id']
        verbose_name = '奖惩信息'
        verbose_name_plural = '奖惩信息'


# 学院模型
class CollegeModel(models.Model):
    college_id = models.AutoField(primary_key=True, verbose_name='学院ID')
    college_name = models.CharField(max_length=64, verbose_name='学院名称')

    def __str__(self):
        return self.college_name

    class Meta:
        ordering = ['college_name']
        verbose_name = '学院'
        verbose_name_plural = '学院'


# 专业模型
class MajorModel(models.Model):
    major_id = models.AutoField(primary_key=True, verbose_name='专业ID')
    major_name = models.CharField(max_length=64, verbose_name='专业名称')
    college_id = models.ForeignKey('CollegeModel', on_delete=models.CASCADE)

    def __str__(self):
        return self.major_name

    class Meta:
        ordering = ['major_name']
        verbose_name = '专业'
        verbose_name_plural = '专业'


# 课程模型
class CourseModel(models.Model):
    course_id = models.AutoField(primary_key=True, verbose_name='课程ID')
    course_name = models.CharField(max_length=64, verbose_name='课程名称')
    major_id = models.ForeignKey('MajorModel', on_delete=models.CASCADE)

    def __str__(self):
        return self.course_name

    class Meta:
        ordering = ['course_name']
        verbose_name = '课程'
        verbose_name_plural = '课程'


# 班级模型
class ClassModel(models.Model):
    class_id = models.AutoField(primary_key=True, verbose_name='班级ID')
    class_name = models.CharField(max_length=64, verbose_name='班级名称')
    major_id = models.ForeignKey('MajorModel', on_delete=models.CASCADE)

    def __str__(self):
        return self.class_name

    class Meta:
        ordering = ['class_name']
        verbose_name = '班级'
        verbose_name_plural = '班级'


# 课程-学生 连接表
class CourseStudentModel(models.Model):
    course_id = models.ForeignKey('CourseModel', on_delete=models.CASCADE)
    student_id = models.ForeignKey('StudentInformationModel', on_delete=models.CASCADE)


# 课程-教师 连接表

# 班级-学生 连接表
class ClassStudentModel(models.Model):
    class_id = models.ForeignKey('ClassModel', on_delete=models.CASCADE)
    student_id = models.ForeignKey('StudentInformationModel', on_delete=models.CASCADE)

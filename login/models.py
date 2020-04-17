from django.db import models


# 用户账号模型
class User(models.Model):
    account = models.CharField(max_length=128, unique=True, verbose_name='账号')
    password = models.CharField(max_length=256, verbose_name='密码')
    edit_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.account

    class Meta:
        ordering = ['edit_time']  # 默认排序 c_time
        verbose_name = '用户'  # 模型起名
        verbose_name_plural = '用户'  # 模型名的复数


# 学生信息模型
class StudentInformationModel(models.Model):
    gender = (
        ('male', '男'),
        ('female', '女'),
    )
    majorChoice = (
        ('080901', "计算机科学与技术"),
        ('080902', "软件工程"),
        ('080903', "网络工程"),
        ('080904', "信息安全"),
        ('000001', "纺织化学工程系"),
        ('000002', "应用化学系"),
        ('000003', "生物工程系及基础化学部"),        
    )
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    name = models.CharField(max_length=30, verbose_name='姓名', null=True)
    sex = models.CharField(max_length=32, choices=gender, default='男')
    age = models.CharField(max_length=20, verbose_name='年龄', null=True)
    email = models.EmailField(verbose_name='邮箱')
    idc = models.CharField(max_length=20, verbose_name='身份证', null=True)
    major = models.CharField(
        max_length=30, choices=majorChoice, default='计算机科学与技术')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '学生信息'
        verbose_name_plural = '学生信息'


# 教师信息模型
class TeacherInformationModel(models.Model):
    gender = (
        ('male', '男'),
        ('female', '女'),
    )
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    email = models.EmailField(verbose_name='邮箱')
    name = models.CharField(max_length=30, verbose_name='姓名', null=True)
    sex = models.CharField(max_length=32, choices=gender, default='男')
    idc = models.CharField(max_length=20, verbose_name='身份证', null=True)
    age = models.CharField(max_length=20, verbose_name='年龄', null=True)
    graduate_school = models.TextField(verbose_name='毕业学校')
    education_experience = models.TextField(verbose_name='教育经历')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '教师信息'
        verbose_name_plural = '教师信息'


# 管理员信息模型


# 学生奖惩模型
class StudentAwardsRecodeModel(models.Model):
    stu_id = models.ForeignKey(
        'StudentInformationModel', on_delete=models.CASCADE)
    award_type = models.CharField(
        max_length=5, verbose_name='奖惩记录类别', null=True)
    award_content = models.CharField(
        max_length=50, verbose_name='奖惩信息', null=True)
    award_date = models.DateField(verbose_name='奖惩日期', null=True)

    class Meta:
        ordering = ['stu_id']
        verbose_name = '奖惩信息'
        verbose_name_plural = '奖惩信息'


# 学院模型
class CollegeModel(models.Model):
    college_name = models.CharField(max_length=64, verbose_name='学院名称')

    def __str__(self):
        return self.college_name

    class Meta:
        ordering = ['college_name']
        verbose_name = '学院'
        verbose_name_plural = '学院'


# 学生成绩模型
class StudentScoreModel(models.Model):
    student = models.ForeignKey(
        'StudentInformationModel', on_delete=models.CASCADE)
    courseClass = models.ForeignKey(
        'CourseClassModel', on_delete=models.CASCADE, null=True)
    score = models.CharField(max_length=16, verbose_name='分数', null=True)
    state = models.CharField(max_length=16, verbose_name='状态', null=True)

    def __str__(self):
        return self.courseClass.course.course_name+' '+ self.courseClass.teacher.name+' ' + self.student.name+' '+str(self.score)+' '+self.state

    class Meta:
        ordering = ['courseClass']
        verbose_name = '成绩'
        verbose_name_plural = '成绩'


# 课程班级模型
class CourseClassModel(models.Model):
    course = models.ForeignKey(
        'CourseModel', on_delete=models.CASCADE, null=True)
    teacher = models.ForeignKey(
        'TeacherInformationModel', on_delete=models.CASCADE)
    maxNum = models.CharField(max_length=16, verbose_name='最大人数')
    studentsScore = models.ManyToManyField(
        StudentScoreModel, null=True, blank=True)

    def __str__(self):
        return self.course.course_name+' ' + self.teacher.name+' '+self.maxNum

    class Meta:
        ordering = ['teacher']
        verbose_name = '课程班级'
        verbose_name_plural = '课程班级'


# 课程模型
class CourseModel(models.Model):
    course_name = models.CharField(max_length=64, verbose_name='课程名称')
    courseClass = models.ManyToManyField(
        CourseClassModel, null=True, blank=True)

    def __str__(self):
        return self.course_name

    class Meta:
        ordering = ['course_name']
        verbose_name = '课程'
        verbose_name_plural = '课程'


# 专业模型
class MajorModel(models.Model):
    major_name = models.CharField(max_length=64, verbose_name='专业名称')
    college_id = models.ForeignKey('CollegeModel', on_delete=models.CASCADE)
    courses = models.ManyToManyField(CourseModel, null=True, blank=True)

    def __str__(self):
        return self.major_name

    class Meta:
        ordering = ['major_name']
        verbose_name = '专业'
        verbose_name_plural = '专业'


# 班级模型
class ClassModel(models.Model):
    class_name = models.CharField(max_length=64, verbose_name='班级名称')
    major_id = models.ForeignKey('MajorModel', on_delete=models.CASCADE)
    students = models.ManyToManyField(
        StudentInformationModel, null=True, blank=True)

    def __str__(self):
        return self.class_name

    class Meta:
        ordering = ['class_name']
        verbose_name = '班级'
        verbose_name_plural = '班级'


# 日志
class OperationLogs(models.Model):
    type = models.CharField(default='info', max_length=64, verbose_name="日志类型")
    content = models.TextField(verbose_name="修改详情", null=True)

# Generated by Django 3.0.5 on 2020-04-13 20:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ClassModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_name', models.CharField(max_length=64, verbose_name='班级名称')),
            ],
            options={
                'verbose_name': '班级',
                'verbose_name_plural': '班级',
                'ordering': ['class_name'],
            },
        ),
        migrations.CreateModel(
            name='CollegeModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('college_name', models.CharField(max_length=64, verbose_name='学院名称')),
            ],
            options={
                'verbose_name': '学院',
                'verbose_name_plural': '学院',
                'ordering': ['college_name'],
            },
        ),
        migrations.CreateModel(
            name='CourseModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_name', models.CharField(max_length=64, verbose_name='课程名称')),
            ],
            options={
                'verbose_name': '课程',
                'verbose_name_plural': '课程',
                'ordering': ['course_name'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.CharField(max_length=128, unique=True, verbose_name='账号')),
                ('password', models.CharField(max_length=256, verbose_name='密码')),
                ('edit_time', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '用户',
                'verbose_name_plural': '用户',
                'ordering': ['edit_time'],
            },
        ),
        migrations.CreateModel(
            name='TeacherInformationModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, verbose_name='邮箱')),
                ('name', models.CharField(max_length=30, null=True, verbose_name='姓名')),
                ('sex', models.CharField(choices=[('male', '男'), ('female', '女')], default='男', max_length=32)),
                ('idc', models.CharField(max_length=20, null=True, verbose_name='身份证')),
                ('age', models.CharField(max_length=20, null=True, verbose_name='年龄')),
                ('graduate_school', models.TextField(verbose_name='毕业学校')),
                ('education_experience', models.TextField(verbose_name='教育经历')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.User')),
            ],
            options={
                'verbose_name': '教师信息',
                'verbose_name_plural': '教师信息',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='StudentInformationModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, null=True, verbose_name='姓名')),
                ('sex', models.CharField(choices=[('male', '男'), ('female', '女')], default='男', max_length=32)),
                ('age', models.CharField(max_length=20, null=True, verbose_name='年龄')),
                ('email', models.EmailField(max_length=254, verbose_name='邮箱')),
                ('idc', models.CharField(max_length=20, null=True, verbose_name='身份证')),
                ('major', models.CharField(choices=[('080901', '计算机科学与技术'), ('080902', '软件工程'), ('080903', '网络工程'), ('080904K', '信息安全')], default='计算机科学与技术', max_length=30)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.User')),
            ],
            options={
                'verbose_name': '学生信息',
                'verbose_name_plural': '学生信息',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='StudentAwardsRecodeModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('award_type', models.CharField(max_length=5, null=True, verbose_name='奖惩记录类别')),
                ('award_content', models.CharField(max_length=50, null=True, verbose_name='奖惩信息')),
                ('award_date', models.DateField(null=True, verbose_name='奖惩日期')),
                ('stu_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.StudentInformationModel')),
            ],
            options={
                'verbose_name': '奖惩信息',
                'verbose_name_plural': '奖惩信息',
                'ordering': ['stu_id'],
            },
        ),
        migrations.CreateModel(
            name='MajorModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('major_name', models.CharField(max_length=64, verbose_name='专业名称')),
                ('college_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.CollegeModel')),
                ('courses', models.ManyToManyField(to='login.CourseModel')),
            ],
            options={
                'verbose_name': '专业',
                'verbose_name_plural': '专业',
                'ordering': ['major_name'],
            },
        ),
        migrations.CreateModel(
            name='CourseStudentModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.CourseModel')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.StudentInformationModel')),
            ],
        ),
        migrations.AddField(
            model_name='coursemodel',
            name='teachers',
            field=models.ManyToManyField(to='login.TeacherInformationModel'),
        ),
        migrations.CreateModel(
            name='ClassStudentModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.ClassModel')),
                ('student_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.StudentInformationModel')),
            ],
        ),
        migrations.AddField(
            model_name='classmodel',
            name='major_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='login.MajorModel'),
        ),
    ]

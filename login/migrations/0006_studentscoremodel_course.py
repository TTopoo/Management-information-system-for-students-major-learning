# Generated by Django 3.0.5 on 2020-04-17 08:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0005_auto_20200416_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentscoremodel',
            name='course',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='login.CourseClassModel'),
        ),
    ]

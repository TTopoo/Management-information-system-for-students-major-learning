# Generated by Django 3.0.5 on 2020-04-17 09:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0006_studentscoremodel_course'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studentscoremodel',
            old_name='course',
            new_name='courseClass',
        ),
        migrations.AddField(
            model_name='courseclassmodel',
            name='course',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='login.CourseModel'),
        ),
    ]

# Generated by Django 3.0.5 on 2020-04-15 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0002_auto_20200415_0821'),
    ]

    operations = [
        migrations.AddField(
            model_name='classmodel',
            name='students',
            field=models.ManyToManyField(blank=True, null=True, to='login.StudentInformationModel'),
        ),
    ]

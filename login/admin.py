from django.contrib import admin

from . import models

admin.site.register(models.User)
admin.site.register(models.StudentInformationModel)
admin.site.register(models.StudentAwardsRecodeModel)
admin.site.register(models.CourseModel)
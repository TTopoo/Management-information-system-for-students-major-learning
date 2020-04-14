from django.contrib import admin
from django.conf.urls import include
from django.urls import path
from login import views
import logging
from login.util import LogType, Log

logging.basicConfig(level=logging.DEBUG)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),

    path('index_student/', views.index_student),
    path('index_teacher/', views.index_teacher),
    path('login/', views.login),
    path('logout/', views.logout),
    path('fill_information/', views.fill_information),
    path('alter_information/', views.alter_information),

    path('teacher/stu_info/',           views.Teacher_StuInfo_OP.as_view({'get': 'visit'})),
    path('teacher/stu_info/json/',      views.Teacher_StuInfo_OP.as_view({'get': 'select'})),
    path('teacher/stu_info/delete/',    views.Teacher_StuInfo_OP.as_view({'post': 'delete'})),
    path('teacher/stu_info/add/',       views.Teacher_StuInfo_OP.as_view({'post': 'add'})),
    path('teacher/stu_info/update/',    views.Teacher_StuInfo_OP.as_view({'post': 'update'})),

    path('teacher/award/',              views.Teacher_Award_OP.as_view({'get': 'visit'})),
    path('teacher/award/json/',         views.Teacher_Award_OP.as_view({'get': 'select'})),
    path('teacher/award/delete/',       views.Teacher_Award_OP.as_view({'post': 'delete'})),
    path('teacher/award/add/',          views.Teacher_Award_OP.as_view({'post': 'add'})),
    path('teacher/award/update/',       views.Teacher_Award_OP.as_view({'post': 'update'})),
]

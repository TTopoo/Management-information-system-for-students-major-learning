from django.contrib import admin
from django.conf.urls import include
from django.urls import path
from login import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index_student/', views.index_student),
    path('index_teacher/', views.index_teacher),
    path('login/', views.login),
    path('logout/', views.logout),
    path('captcha/', include('captcha.urls')),

    
    path('teacher/stu_info/', views.stu_info),
    path('teacher/stu_info/json/', views.stu_info_json),
    path('teacher/stu_info/delete/', views.stu_info_delete),
    path('teacher/stu_info/add/', views.stu_info_add),
    path('teacher/stu_info/update/', views.stu_info_update),


    path('teacher/award/', views.award),
    path('teacher/award/json/', views.award_json),
    path('teacher/award/delete/', views.award_delete),
    path('teacher/award/add/', views.award_add),
    path('teacher/award/update/', views.award_update),
]

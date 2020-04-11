from django.contrib import admin
from django.conf.urls import include
from django.urls import path
from login import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', views.index),
    path('login/', views.login),
    path('register/', views.register),
    path('logout/', views.logout),
    path('captcha/', include('captcha.urls')),
    

    path('stu/stu_info/', views.stu_info),
    path('stu/stu_info/json/', views.send_stu_info_json),
    path('stu/stu_info/delete/', views.delete),
    path('stu/stu_info/add/', views.add),
    path('stu/stu_info/update/', views.update),
]

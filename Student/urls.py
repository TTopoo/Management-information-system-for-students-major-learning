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
    path('stu_info/', views.stu_info),
    path('json/', views.sendjson),
    path('delete/', views.delete),
    path('add/', views.add),
    path('update/', views.update),
]

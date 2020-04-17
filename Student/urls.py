from django.contrib import admin
from django.conf.urls import include
from django.urls import path
from generatedata import views as dataviews
from login import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),

    path('index_student/', views.index_student),
    path('index_teacher/', views.index_teacher),
    path('login/', views.login),
    path('logout/', views.logout),
    path('fill_information/', views.fill_information),
    path('alter_information/', views.alter_information),

    path('generatedata/', dataviews.info),

    path('<obj>/',                      views.deal.as_view()),
    path('<obj>/<function>/',           views.deal.as_view()),
    path('<obj>/<function>/<subfun>/',  views.deal.as_view()),

    
]

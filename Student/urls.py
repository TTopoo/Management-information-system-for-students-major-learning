from django.contrib import admin
from django.conf.urls import include
from django.urls import path
from generatedata import views as dataviews
from login import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),

    path('login/', views.login),
    path('logout/', views.logout),

    path('test/', dataviews.dealdeal.as_view()),
    path('test/<obj>/', dataviews.dealdeal.as_view()),

    path('manage/<obj>/',                      views.deal.as_view()),
    path('manage/<obj>/<function>/',           views.deal.as_view()),
    path('manage/<obj>/<function>/<subfun>/',  views.deal.as_view()),

]

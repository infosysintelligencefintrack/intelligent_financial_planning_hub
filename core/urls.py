"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path('', views.home_page, name='home'),
    path('logout/', views.custom_logout, name="logout"),
    path('pdf/', views.pdf , name='pdf'),
    path('admin/', admin.site.urls),
    path('login/', views.login_page, name='login'),
    path('register/', views.register, name='register'),
    path('expenses/', views.expenses, name='expenses'),  # Fixed duplicate path
    path('update_expense/<int:id>/', views.update_expense, name='update_expense'),
    path('delete_expense/<int:id>/', views.delete_expense, name='delete_expense'),
    path('visualization/', views.visualize_expenses, name='visualization'),
    path('financial-overview/', views.financial_overview, name='financial_overview'),
]

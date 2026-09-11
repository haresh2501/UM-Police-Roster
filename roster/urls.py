from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/roster/officer/manage-roster/', views.upload_and_manage_roster, name='manage-roster'),
    path('', lambda request: redirect('admin/', permanent=False)),
]

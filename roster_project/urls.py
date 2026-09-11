from django.contrib import admin
from django.urls import path
from roster.views import upload_and_manage_roster

urlpatterns = [
    # 📌 CRITICAL CORRECTION: Overrides and captures the path perfectly before it falls into the admin regex loop
    path('admin/roster/officer/import-excel/', upload_and_manage_roster, name='manage-roster'),
    
    path('admin/', admin.site.urls),
]

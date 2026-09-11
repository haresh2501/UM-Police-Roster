from django.contrib import admin
from django.urls import path
from .models import Officer, DailyRoster, RosterHistory
from .views import upload_and_manage_roster

admin.site.site_header = "PORTAL PENTADBIRAN JADUAL TUGAS POLIS BANTUAN UNIVERSITI MALAYA"
admin.site.index_title = "Hab Automasi Pengurusan Syif & Penugasan Harian (27 Pos Kawalan)"
admin.site.site_title = "Portal Roster PBUM"

@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'name', 'role', 'ic_number', 'staff_group', 'shift_type')
    search_fields = ('name', 'staff_id', 'ic_number')
    list_filter = ('shift_type', 'staff_group')
    ordering = ('staff_id',)

    # 🎯 MENDAFTARKAN LALUAN URL PORTAL ROSTER UTAMA
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('manage-roster/', self.admin_site.admin_view(upload_and_manage_roster), name='manage-roster'),
        ]
        return custom_urls + urls

@admin.register(DailyRoster)
class DailyRosterAdmin(admin.ModelAdmin):
    list_display = ('officer', 'date', 'roster_type', 'override_placement')

@admin.register(RosterHistory)
class RosterHistoryAdmin(admin.ModelAdmin):
    list_display = ('officer', 'date_assigned', 'shift_code', 'placement_assigned', 'source', 'timestamp', 'changed_by_excel')
    search_fields = ('officer__name', 'shift_code', 'placement_assigned')
    list_filter = ('source', 'changed_by_excel', 'date_assigned')
    ordering = ('-date_assigned', '-timestamp')

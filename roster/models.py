from django.db import models

class Officer(models.Model):
    staff_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100, default='KONST/PB')
    ic_number = models.CharField(max_length=50, blank=True, default='')
    staff_group = models.CharField(max_length=100, blank=True, default='')
    placement = models.CharField(max_length=255, default='BELUM DITETAPKAN')
    shift_type = models.CharField(max_length=20, default='ROT')  # 'ROT' atau 'MORNING'

    class Meta:
        verbose_name = "Profil Anggota / Officer Profile"
        verbose_name_plural = "📂 1. Direktori Profil Anggota / Officers Directory"

    def __str__(self):
        return self.name

class DailyRoster(models.Model):
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE)
    date = models.DateField()
    roster_type = models.CharField(max_length=10)  # '1', '2', '3', 'X', 'EL', 'MC', 'AL'
    notes = models.TextField(blank=True, default='')
    override_placement = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Jadual Harian / Daily Roster"
        verbose_name_plural = "🗓️ 3. Jadual Tugas Harian / Daily Rosters"

    def __str__(self):
        return f"{self.officer.name} - {self.date}"

class RosterHistory(models.Model):
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE)
    date_assigned = models.DateField()
    shift_code = models.CharField(max_length=10)
    placement_assigned = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    changed_by_excel = models.BooleanField(default=False)
    source = models.CharField(max_length=50, blank=True, default='manual')

    class Meta:
        verbose_name = "Log Sejarah / Roster History"
        verbose_name_plural = "📜 2. Log Audit Pertukaran / Roster Histories"

    def __str__(self):
        return f"Log: {self.officer.name} ({self.date_assigned}) - {self.shift_code}"

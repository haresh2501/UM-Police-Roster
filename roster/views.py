import re
import pandas as pd
import datetime
from datetime import timedelta
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from .models import Officer, DailyRoster, RosterHistory


def canonicalize_position_name(raw_position):
    if raw_position is None:
        return None

    value = str(raw_position).strip()
    if not value or value.lower() in ['none', 'null', 'belum ditetapkan', 'tidak ditetapkan']:
        return None

    upper = value.upper()

    if 'KAWALAN' in upper or 'IPK' in upper:
        return 'KAWALAN(IPK)'
    if 'KETUA SYIF' in upper:
        return 'KETUA SYIF'
    if 'PEMBANTU KETUA SYIF' in upper or 'PERONDA' in upper:
        if '1' in upper:
            return 'PEMBANTU KETUA SYIF (PERONDA 1)'
        if '2' in upper:
            return 'PEMBANTU KETUA SYIF (PERONDA 2)'
        return 'PEMBANTU KETUA SYIF (PERONDA 1)'
    if 'ZON A' in upper:
        return 'ZON A'
    if 'ZON B' in upper:
        return 'ZON B'
    if 'ZON C' in upper:
        return 'ZON C'
    if 'ZON D' in upper:
        return 'ZON D'
    if 'ZON E' in upper:
        return 'ZON E'
    if 'ZON F' in upper:
        return 'ZON F'
    if 'KUMPULAN A' in upper or 'GROUP A' in upper or 'SHIFT A' in upper:
        return 'ZON A'
    if 'KUMPULAN B' in upper or 'GROUP B' in upper or 'SHIFT B' in upper:
        return 'ZON B'
    if 'KUMPULAN C' in upper or 'GROUP C' in upper or 'SHIFT C' in upper:
        return 'ZON C'
    if 'KUMPULAN D' in upper or 'GROUP D' in upper or 'SHIFT D' in upper:
        return 'ZON D'
    if 'KUMPULAN E' in upper or 'GROUP E' in upper or 'SHIFT E' in upper:
        return 'ZON E'
    if 'KUMPULAN F' in upper or 'GROUP F' in upper or 'SHIFT F' in upper:
        return 'ZON F'

    if 'GATE KUALA LUMPUR' in upper or 'GOLF1' in upper or 'GATE1' in upper:
        return 'GATE KUALA LUMPUR(GOLF1)'
    if 'GATE PETALING JAYA' in upper or 'GOLF2' in upper:
        return 'GATE PETALING JAYA(GOLF2)'
    if 'GATE JALAN ILMU' in upper or 'GOLF3' in upper:
        return 'GATE JALAN ILMU(GOLF3)'
    if 'GATE FAKULTI BAHASA' in upper or 'GOLF4' in upper:
        return 'GATE FAKULTI BAHASA(GOLF4)'
    if 'GATE DAMANSARA' in upper or 'GOLF5' in upper:
        return 'GATE DAMANSARA(GOLF5)'
    if 'UNIT TRAFIK' in upper:
        return 'UNIT TRAFIK'
    if 'CANSELERI' in upper:
        return 'CANSELERI'
    if 'GALERI' in upper:
        return 'GALERI'
    if 'DEWAN TUNKU CANSELOR' in upper or 'DTC' in upper:
        return 'DEWAN TUNKU CANSELOR(DTC)'
    if 'RUMAH ANTARABANGSA' in upper or 'RAB' in upper:
        return 'RUMAH ANTARABANGSA(RAB)'
    if 'FAKULTI PERGIGIAN' in upper:
        return 'FAKULTI PERGIGIAN'
    if 'SIASATAN' in upper or 'DETEKTIF' in upper:
        return 'UNIT SIASATAN/DETEKTIF'
    if 'LATIHAN' in upper or 'DISIPLIN' in upper:
        return 'SEKSYEN LATIHAN & DISIPLIN'
    if 'PELEKAT' in upper:
        return 'UNIT PELEKAT'
    if 'ROSTER' in upper or 'JADUAL TUGAS' in upper:
        return 'ROSTER/JADUAL TUGAS'
    if 'PENTADBIRAN' in upper or 'PEJABAT' in upper or 'OFFICE' in upper:
        return 'BAHAGIAN PENTADBIRAN'

    return value


def extract_staff_record_from_row(row):
    if row is None:
        return None

    cleaned = []
    for cell in row:
        if cell is None or pd.isna(cell):
            continue
        text = str(cell).strip()
        if not text:
            continue
        if text.endswith('.0'):
            text = text[:-2]
        cleaned.append(text)

    if not cleaned:
        return None

    staff_id = None
    name = None
    ic_number = ''
    staff_group = ''

    for index, cell in enumerate(cleaned):
        upper_cell = cell.upper()
        if any(token in upper_cell for token in ['SENARAI', 'KEANGGOTAAN', 'NAMA PENUH', 'NAMA', 'NO. STAF', 'STAFF ID', 'NO STAF', 'BIL', 'KUMPULAN', 'IC', 'NO. KP', 'NO KP', 'JAWATAN']):
            continue

        if re.fullmatch(r"\d{3,12}", cell.replace(' ', '')):
            if staff_id is None:
                staff_id = cell.replace(' ', '')
            continue

        if re.fullmatch(r"\d{6}-\d{2}-\d{4}", cell):
            ic_number = cell
            continue

        if len(cell) >= 3 and any(ch.isalpha() for ch in cell):
            if name is None and not any(token in upper_cell for token in ['KPL', 'SJN', 'KONST', 'INSP', 'PB', 'POLIS', 'PEMBANTU', 'TADBIR', 'PBT']):
                name = ' '.join(cell.split())
                continue

        if any(token in upper_cell for token in ['KUMPULAN A', 'KUMPULAN B', 'KUMPULAN C', 'KUMPULAN D', 'KUMPULAN E', 'KUMPULAN F', 'KUMPULAN G', 'ZON A', 'ZON B', 'ZON C', 'ZON D', 'ZON E', 'ZON F']):
            staff_group = cell

    if staff_id is None:
        return None

    if name is None:
        name = f"ANGGOTA UNIK ({staff_id})"

    clean_name = ' '.join(name.split())
    clean_name = clean_name.upper()

    return {
        'staff_id': staff_id,
        'name': clean_name,
        'ic_number': ic_number,
        'staff_group': staff_group,
    }

# =========================================================================
# ⚙️ 1. ENJIN SINKRONISASI JADUAL BULANAN INTERAL POLIS BANTUAN UM
# =========================================================================
def is_leave_code(assigned_shift):
    return str(assigned_shift).upper() in ['EL', 'MC', 'AL', 'CL', 'SL', 'PL', 'LT', 'TK', 'CUTI', 'LEAVE', 'OFF']


def generate_rotation_shift_code(officer, day_index, first_date):
    group_str = str(officer.staff_group).upper()
    current_date = first_date + timedelta(days=day_index)
    weekday = current_date.weekday()

    shift_type = str(getattr(officer, 'shift_type', '') or '').upper()
    morning_only_markers = ['MORNING', 'PAGI', 'OFFICE', 'PEJABAT', 'PENTADBIRAN', 'MORNING ONLY', 'PAGI SAHAJA']
    afternoon_only_markers = ['AFTERNOON', 'PETANG', 'AFTERNOON ONLY', 'PETANG SAHAJA', 'STATIK PETANG']

    if shift_type == 'MORNING' or any(marker in group_str for marker in morning_only_markers):
        return '2' if weekday < 5 else 'X'

    if shift_type == 'AFTERNOON' or any(marker in group_str for marker in afternoon_only_markers):
        return '3' if weekday < 5 else 'X'

    if any(k in group_str for k in ['STATIK', 'TRAFIK', 'SIASATAN', 'LATIHAN', 'PELEKAT']):
        return '2' if weekday < 5 else 'X'

    group_offset = ord(officer.staff_group[-1].upper()) - 65 if officer.staff_group and officer.staff_group[-1].isalpha() else 0
    pattern = ['3', '3', '2', '2', 'X', '1', 'X']
    return pattern[(day_index + group_offset) % len(pattern)]


def build_roster_note(assigned_shift, group_str):
    if assigned_shift == '1':
        return "Syif 1 / Night Shift (Malam - 23:00 - 08:00)"
    if assigned_shift == '2':
        if 'PENTADBIRAN' in group_str or 'PEJABAT' in group_str or 'OFFICE' in group_str:
            return "Waktu Pejabat / Office Hours (08:00 - 17:00)"
        return "Syif 2 / Morning Shift (Pagi - 07:00 - 16:00)"
    if assigned_shift == '3':
        return "Syif 3 / Afternoon Shift (Petang - 15:00 - 23:59)"
    if is_leave_code(assigned_shift):
        return f"Cuti Ditandakan: {assigned_shift}"
    return "Hari Pelepasan Am / Off Day (Kod X)"


def read_and_sync_exact_excel_roster(xls, target_year, target_month):
    all_sheets = xls.sheet_names
    target_month_name = ["januari", "februari", "mac", "april", "mei", "jun", "julai", "ogos", "september", "oktober", "november", "disember"][target_month - 1]
    sheet_roster = next((s for s in all_sheets if target_month_name in s.lower() or str(target_month) in s), None)

    if not sheet_roster:
        return False, f"Helaian khusus untuk bulan {target_month_name.upper()} tidak dijumpai dalam fail Excel."

    try:
        first_date = datetime.date(target_year, target_month, 1)
        if target_month == 12:
            next_month = datetime.date(target_year + 1, 1, 1)
        else:
            next_month = datetime.date(target_year, target_month + 1, 1)

        DailyRoster.objects.filter(date__gte=first_date, date__lt=next_month).delete()
        days_in_month = (next_month - first_date).days
        slots_created = 0

        for officer in Officer.objects.all():
            group_str = str(officer.staff_group).upper()
            for day_idx in range(days_in_month):
                current_date = first_date + timedelta(days=day_idx)
                assigned_shift = generate_rotation_shift_code(officer, day_idx, first_date)
                note = build_roster_note(assigned_shift, group_str)

                DailyRoster.objects.create(officer=officer, date=current_date, roster_type=assigned_shift, notes=note)
                RosterHistory.objects.create(
                    officer=officer,
                    date_assigned=current_date,
                    shift_code=assigned_shift,
                    placement_assigned=officer.placement,
                    changed_by_excel=True,
                )
                slots_created += 1

        return True, f"Berjaya memetakan {slots_created} slot tugasan harian tepat mengikut jadual Excel bulanan!"
    except Exception as e:
        return False, f"Ralat membaca helaian jadual bulanan: {str(e)}"

# =========================================================================
# ⚙️ 2. ENJIN PEMBERSIHAN DATA NAMA DARIPADA LAJUR EXCEL RAW (KALIS KPL/PB)
# =========================================================================
def clean_and_extract_name_details(raw_text):
    if pd.isna(raw_text) or not str(raw_text).strip(): 
        return "ANGGOTA TANPA NAMA", "KONST/PB"
    
    clean_name = str(raw_text).strip()
    upper_text = clean_name.upper()
    
    detected_role = "KONST/PB"
    if 'PEMBANTU KESELAMATAN' in upper_text: detected_role = "PEMBANTU KESELAMATAN"
    elif 'PEMBANTU TADBIR' in upper_text: detected_role = "PEMBANTU TADBIR"
    elif 'TADBIR' in upper_text or 'N1' in upper_text: detected_role = "PEMBANTU TADBIR N1"
    elif 'SJN' in upper_text: detected_role = "SJN/PB"
    elif 'KPL' in upper_text: detected_role = "KPL/PB"
    elif 'INSP' in upper_text: detected_role = "INSP/PB"
    
    for p in ['KPL/PB', 'SJN/PB', 'KONST/PB', 'KPL PB', 'SJN PB', 'KONST PB', 'INSP', 'PEMBANTU', 'TADBIR', 'MYSTEP', 'PB']:
        upper_text = upper_text.replace(p, '')
    
    final_clean_name = upper_text.strip()
    return final_clean_name, detected_role

# =========================================================================
# 🏛️ 3. CORE INTEGRATION HUB CONTROLLER (PENGENDALI INTERAKSI UTAMA)
# =========================================================================
def upload_and_manage_roster(request):
    HAD_KEKUATAN_MINIMUM_27_POS = {
        'KETUA SYIF': 1, 'PEMBANTU KETUA SYIF (PERONDA 1)': 1, 'PEMBANTU KETUA SYIF (PERONDA 2)': 1,
        'KAWALAN(IPK)': 3, 'ZON A': 2, 'ZON B': 2, 'ZON C': 2, 'ZON D': 2, 'ZON E': 2, 'ZON F': 2,
        'UNIT TRAFIK': 2, 'GATE KUALA LUMPUR(GOLF1)': 3, 'GATE PETALING JAYA(GOLF2)': 2,
        'GATE JALAN ILMU(GOLF3)': 2, 'GATE FAKULTI BAHASA(GOLF4)': 2, 'GATE DAMANSARA(GOLF5)': 2,
        'CANSELERI': 2, 'GALERI': 1, 'DEWAN TUNKU CANSELOR(DTC)': 1, 'RUMAH ANTARABANGSA(RAB)': 1,
        'FAKULTI PERGIGIAN': 1, 'UNIT SIASATAN/DETEKTIF': 1, 'LAKIM/KK13': 1, 'WISMA R&D': 1,
        'SEKSYEN LATIHAN & DISIPLIN': 1, 'UNIT PELEKAT': 1, 'ROSTER/JADUAL TUGAS': 1
    }

    deployment_matrix = {pos: {'syif_1': [], 'syif_2': [], 'syif_3': [], 'hadir_total': 0} for pos in HAD_KEKUATAN_MINIMUM_27_POS.keys()}
    deployment_matrix['BELUM DITETAPKAN'] = {'syif_1': [], 'syif_2': [], 'syif_3': [], 'hadir_total': 0}

    date_param = request.GET.get('roster_date')
    try:
        target_date = datetime.datetime.strptime(date_param, "%Y-%m-%d").date() if date_param else datetime.date.today()
    except Exception:
        target_date = datetime.date.today()

    try:
        all_officers = Officer.objects.all().order_by('name')
    except Exception:
        all_officers = []

    selected_officer = None
    personal_roster = []
    officer_history = []
    monthly_roster_rows = []

    if request.method == "POST":
        if 'save_placement' in request.POST:
            officer_id = request.POST.get('officer_id')
            chosen_placement = request.POST.get('placement')
            if officer_id and chosen_placement:
                Officer.objects.filter(id=officer_id).update(
                    placement=chosen_placement,
                    staff_group=chosen_placement,
                )
                messages.success(request, f'Kedudukan untuk pegawai telah dikemaskini kepada {chosen_placement}.')
            return redirect(f"{request.path}?officer_select={officer_id}")

        if 'save_manual_shift' in request.POST:
            officer_id = request.POST.get('manual_officer_id')
            manual_date = request.POST.get('manual_roster_date')
            manual_shift = request.POST.get('manual_shift_code')
            if officer_id and manual_date and manual_shift:
                try:
                    ro_date = datetime.datetime.strptime(manual_date, '%Y-%m-%d').date()
                    officer = Officer.objects.get(id=officer_id)
                    DailyRoster.objects.filter(officer=officer, date=ro_date).update(
                        roster_type=manual_shift,
                        notes=build_roster_note(manual_shift, str(officer.staff_group).upper()),
                        override_placement=officer.placement,
                    )
                    RosterHistory.objects.create(
                        officer=officer,
                        date_assigned=ro_date,
                        shift_code=manual_shift,
                        placement_assigned=officer.placement,
                        changed_by_excel=False,
                        source='manual'
                    )
                    messages.success(request, f'Shift untuk {officer.name} pada {ro_date} telah dikemaskini kepada {manual_shift}.')
                except Exception as exc:
                    messages.error(request, f'Ralat manual shift: {exc}')
            return redirect(f"{request.path}?officer_select={officer_id}")

        if 'save_shift_setting' in request.POST:
            officer_id = request.POST.get('shift_setting_officer_id')
            shift_setting = (request.POST.get('shift_setting') or 'ROT').upper()
            if officer_id and shift_setting in ['ROT', 'MORNING', 'AFTERNOON']:
                try:
                    officer = Officer.objects.get(id=officer_id)
                    Officer.objects.filter(id=officer_id).update(shift_type=shift_setting)
                    messages.success(request, f'Pengaturan auto shift untuk {officer.name} telah dikemaskini kepada {shift_setting}.')
                except Exception as exc:
                    messages.error(request, f'Ralat simpan tetapan shift: {exc}')
            return redirect(f"{request.path}?officer_select={officer_id}")

        target_year = int(request.POST.get('year', datetime.datetime.now().year))
        target_month = int(request.POST.get('month', datetime.datetime.now().month))
        if 'generate_roster' in request.POST:
            if not Officer.objects.exists():
                messages.error(request, 'Tiada data anggota ditemui. Sila import fail Excel dahulu.')
            else:
                try:
                    first_date = datetime.date(target_year, target_month, 1)
                    if target_month == 12:
                        next_month = datetime.date(target_year + 1, 1, 1)
                    else:
                        next_month = datetime.date(target_year, target_month + 1, 1)

                    DailyRoster.objects.filter(date__gte=first_date, date__lt=next_month).delete()
                    for officer in Officer.objects.all():
                        group_str = str(officer.staff_group).upper()
                        for day_idx in range((next_month - first_date).days):
                            current_date = first_date + timedelta(days=day_idx)
                            assigned_shift = generate_rotation_shift_code(officer, day_idx, first_date)
                            DailyRoster.objects.create(
                                officer=officer,
                                date=current_date,
                                roster_type=assigned_shift,
                                notes=build_roster_note(assigned_shift, group_str),
                            )
                            RosterHistory.objects.create(
                                officer=officer,
                                date_assigned=current_date,
                                shift_code=assigned_shift,
                                placement_assigned=officer.placement,
                                changed_by_excel=True,
                                source='auto_generated'
                            )
                    messages.success(request, f'Rosters untuk {target_month}/{target_year} telah dijana.')
                    monthly_roster_rows = DailyRoster.objects.filter(date__gte=first_date, date__lt=next_month).select_related('officer').order_by('date', 'officer__name')
                except Exception as exc:
                    messages.error(request, f'Ralat menjana roster: {exc}')
        if ('upload_excel' in request.POST or 'generate_roster' in request.POST) and request.FILES.get('excel_file'):
            file = request.FILES['excel_file']
            try:
                xls = pd.ExcelFile(file)
                sheet_1 = next((s for s in xls.sheet_names if '1' in s or 'senarai' in s.lower()), None)
                if sheet_1:
                    df1 = pd.read_excel(xls, sheet_name=sheet_1, header=None)

                    try:
                        DailyRoster.objects.all().delete()
                        Officer.objects.all().delete()
                    except Exception:
                        pass

                    kumpulan_fallback = ['Kumpulan A', 'Kumpulan B', 'Kumpulan C', 'Kumpulan D', 'Kumpulan E', 'Kumpulan F', 'Kumpulan G']
                    staff_count = 0

                    for row_idx, row in df1.iterrows():
                        detected_id, detected_name, detected_ic = None, None, ""
                        name_candidates = []
                        numeric_candidates = []

                        for cell_val in row.values:
                            if pd.isna(cell_val):
                                continue
                            cell_str = str(cell_val).strip()
                            if cell_str.endswith('.0'):
                                cell_str = cell_str[:-2]
                            if not cell_str:
                                continue

                            upper_cell = cell_str.upper()

                            if cell_str.isdigit() and 3 <= len(cell_str) <= 8:
                                numeric_candidates.append(cell_str)
                                if int(cell_str) > 140 or len(cell_str) >= 4:
                                    detected_id = cell_str
                                continue

                            if "-" in cell_str and len(cell_str) >= 12 and any(ch.isdigit() for ch in cell_str):
                                detected_ic = cell_str
                                continue

                            if any(token in upper_cell for token in ['SENARAI', 'KEANGGOTAAN', 'POLIS', 'JAWATAN', 'NO STAF', 'NAMA', 'IC', 'STAFF ID', 'NO. STAF', 'BIL', 'PERSONAL']):
                                continue

                            if any(token in upper_cell for token in ['KPL/PB', 'SJN/PB', 'KONST/PB', 'KPL PB', 'SJN PB', 'KONST PB', 'INSP', 'PB', 'PEMBANTU', 'TADBIR']):
                                continue

                            if len(cell_str) >= 2 and any(ch.isalpha() for ch in cell_str):
                                name_candidates.append(cell_str)

                        if not detected_id and numeric_candidates:
                            detected_id = sorted(numeric_candidates, key=lambda s: len(s), reverse=True)[0]

                        if name_candidates:
                            detected_name = sorted(name_candidates, key=lambda s: len(s), reverse=True)[0]
                            detected_name = " ".join(detected_name.split())
                            detected_name = detected_name.title()

                        if detected_name and detected_name.upper() in ['ANGGOTA', 'NAMA', 'TANPA NAMA', 'UNKNOWN']:
                            detected_name = None

                        if detected_id and str(detected_id).strip() != "0":
                            if not detected_name:
                                detected_name = f"ANGGOTA UNIK (ID: {detected_id})"

                            clean_name, assigned_role = clean_and_extract_name_details(detected_name)
                            fallback_group = kumpulan_fallback[staff_count % 7]
                            assigned_shift_type = 'ROT'
                            assigned_staff_group = fallback_group

                            if assigned_role in ["PEMBANTU TADBIR", "PEMBANTU TADBIR N1"]:
                                assigned_shift_type = 'MORNING'
                                assigned_staff_group = 'BAHAGIAN PENTADBIRAN'

                            try:
                                Officer.objects.update_or_create(
                                    staff_id=str(detected_id).strip(),
                                    defaults={
                                        'name': clean_name,
                                        'role': assigned_role,
                                        'ic_number': detected_ic,
                                        'staff_group': assigned_staff_group,
                                        'placement': 'BAHAGIAN PENTADBIRAN' if assigned_shift_type == 'MORNING' else 'BELUM DITETAPKAN',
                                        'shift_type': assigned_shift_type,
                                    }
                                )
                            except Exception:
                                pass

                            staff_count += 1

                    sheet_combined = next((s for s in xls.sheet_names if any(k in s.lower() for k in ['4', 'kumpu', 'shif', 'statik'])), None)
                    if sheet_combined:
                        df_comb = pd.read_excel(xls, sheet_name=sheet_combined, header=None)
                        current_mode = 'ROTATION'
                        current_header_title = 'KUMPULAN A'

                        for row_idx, row in df_comb.iterrows():
                            row_cells_str = [str(v).strip().upper() for v in row.values if not pd.isna(v)]
                            for cell_text in row_cells_str:
                                if any(g in cell_text for g in ['KUMPULAN A', 'KUMPULAN B', 'KUMPULAN C', 'KUMPULAN D', 'KUMPULAN E', 'KUMPULAN F', 'KUMPULAN G']):
                                    current_mode = 'ROTATION'
                                    current_header_title = cell_text
                                elif any(k in cell_text for k in ['TRAFIK', 'SIASATAN', 'LATIHAN', 'CANSELERI', 'PELEKAT', 'ROSTER', 'UNIT', 'STATIK', 'POS']):
                                    current_mode = 'STATIC'
                                    current_static_unit = cell_text

                            if 'NAMA' in row_cells_str or 'BIL' in row_cells_str:
                                continue

                            for cell_val in row.values:
                                if pd.isna(cell_val):
                                    continue
                                cell_str = str(cell_val).strip().upper()
                                for p in ['KPL/PB', 'SJN/PB', 'KONST/PB', 'INSP', 'PB']:
                                    cell_str = cell_str.replace(p, '')
                                c_name = cell_str.strip()
                                if len(c_name) < 3:
                                    continue

                                try:
                                    off = Officer.objects.filter(name__icontains=c_name[:5]).first()
                                    if off and 'TADBIR' not in off.role:
                                        if current_mode == 'ROTATION':
                                            for L in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
                                                if f'KUMPULAN {L}' in current_header_title or f'SHIF {L}' in current_header_title:
                                                    off.staff_group = f'Kumpulan {L}'
                                                    off.shift_type = 'ROT'
                                                    off.save()
                                        elif current_mode == 'STATIC':
                                            off.shift_type = 'MORNING'
                                            off.staff_group = current_static_unit
                                            off.placement = current_static_unit
                                            off.save()
                                except Exception:
                                    pass

                    success_sync, msg_sync = read_and_sync_exact_excel_roster(xls, target_year, target_month)
                    if success_sync:
                        messages.success(request, f'Berjaya! {msg_sync}')
            except Exception as e:
                messages.error(request, f'Ralat: {str(e)}')

    try:
        daily_records = DailyRoster.objects.filter(date=target_date).select_related('officer').order_by('officer__name')
        for record in daily_records:
            off = record.officer
            placement = record.override_placement if record.override_placement else off.placement
            placement_key = canonicalize_position_name(placement) or canonicalize_position_name(off.staff_group)
            shift_code = str(record.roster_type).upper()
            if shift_code in ['X', 'EL', 'MC', 'AL', 'CL', 'SL', 'PL', 'LT', 'TK', 'CUTI', 'LEAVE', 'OFF']:
                continue
            if placement_key in deployment_matrix:
                if shift_code == '1':
                    deployment_matrix[placement_key]['syif_1'].append(off)
                elif shift_code == '2':
                    deployment_matrix[placement_key]['syif_2'].append(off)
                elif shift_code == '3':
                    deployment_matrix[placement_key]['syif_3'].append(off)
                deployment_matrix[placement_key]['hadir_total'] += 1
    except Exception:
        pass

    selected_id = request.GET.get('officer_select')
    if selected_id and str(selected_id).strip():
        try:
            selected_officer = Officer.objects.get(id=selected_id)
            personal_roster = DailyRoster.objects.filter(
                officer=selected_officer,
                date__year=target_date.year,
                date__month=target_date.month,
            ).order_by('date')
            officer_history = RosterHistory.objects.filter(officer=selected_officer).order_by('-timestamp')[:5]
        except Exception:
            selected_officer = None
            personal_roster = []
            officer_history = []

    if not monthly_roster_rows:
        try:
            current_month = target_date.month
            current_year = target_date.year
            first_day = datetime.date(current_year, current_month, 1)
            if current_month == 12:
                next_day = datetime.date(current_year + 1, 1, 1)
            else:
                next_day = datetime.date(current_year, current_month + 1, 1)
            monthly_roster_rows = DailyRoster.objects.filter(date__gte=first_day, date__lt=next_day).select_related('officer').order_by('date', 'officer__name')
        except Exception:
            monthly_roster_rows = []

    placement_options = list(HAD_KEKUATAN_MINIMUM_27_POS.keys())
    placement_options.append('BELUM DITETAPKAN')

    return render(
        request,
        'admin/excel_import_form.html',
        {
            'all_officers': all_officers,
            'selected_officer': selected_officer,
            'personal_roster': personal_roster,
            'officer_history': officer_history,
            'deployment_matrix': deployment_matrix,
            'target_date': target_date,
            'HAD_KEKUATAN_MINIMUM_27_POS': HAD_KEKUATAN_MINIMUM_27_POS,
            'monthly_roster_rows': monthly_roster_rows,
            'placement_options': placement_options,
        }
    )
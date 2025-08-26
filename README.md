"""
Patient Health Assistant System (Final)
Author: Your Name
GitHub: https://github.com/yourusername
Description:
Hospital-side console assistant that:
- Admits patients and stores doctor contact
- Tracks medicine reminders
- Records vitals (BP sys/dia + pulse)
- Classifies risk (LOW/MEDIUM/HIGH) using rule-based thresholds
- Notifies doctor automatically on HIGH risk
- Persists data to JSON and writes alerts to a logfile

NOTE:
- "Notifications" are simulated: printed to console and appended to alerts.log
- You can later replace notify_doctor() with real Email/SMS/WhatsApp integrations
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# ----------------- Files -----------------
DATA_FILE = "patients.json"
ALERT_LOG = "alerts.log"

# ----------------- Helpers -----------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_patients():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # migrate minimal structure if needed
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_patients(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def log_alert(message: str):
    line = f"[{now_str()}] {message}\n"
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(line)

def notify_doctor(patient: dict, risk_level: str, reason: str):
    """
    Simulated notification: print to console + log to file.
    Replace this with real integrations later.
    """
    doctor = patient.get("doctor", {})
    msg = (
        f"ALERT → HIGH RISK!\n"
        f"Patient: {patient.get('name')} (ID: {patient.get('id')})\n"
        f"Disease: {patient.get('disease')}\n"
        f"Risk: {risk_level}\n"
        f"Reason: {reason}\n"
        f"Doctor: {doctor.get('name','N/A')} | Phone: {doctor.get('phone','N/A')} | Email: {doctor.get('email','N/A')}\n"
        f"Time: {now_str()}"
    )
    print("\n" + "="*60)
    print(msg)
    print("="*60 + "\n")
    log_alert(msg.replace("\n", " | "))

# ----------------- Risk Engine -----------------
def classify_bp(sys: int, dia: int):
    """
    Returns (risk_level, reason) for BP only.
    Rules (simplified clinical ranges):
      - LOW (Normal): sys 90-120 and dia 60-80
      - MEDIUM: mild elevation (sys 121-139 or dia 81-89) or mild low (sys 80-89 or dia 50-59)
      - HIGH: hypertensive crisis (sys >=180 or dia >=120) or severe hypotension (sys <80 or dia <50)
    """
    if sys >= 180 or dia >= 120:
        return "HIGH", f"Hypertensive crisis: {sys}/{dia} mmHg"
    if sys < 80 or dia < 50:
        return "HIGH", f"Severe hypotension: {sys}/{dia} mmHg"
    if (121 <= sys <= 139) or (81 <= dia <= 89) or (80 <= sys <= 89) or (50 <= dia <= 59):
        return "MEDIUM", f"Abnormal BP: {sys}/{dia} mmHg"
    if 90 <= sys <= 120 and 60 <= dia <= 80:
        return "LOW", f"Normal BP: {sys}/{dia} mmHg"
    # Anything else not covered: treat as MEDIUM
    return "MEDIUM", f"Borderline BP: {sys}/{dia} mmHg"

def classify_pulse(pulse: int):
    """
    Returns (risk_level, reason) for pulse only.
    Rules:
      - LOW (Normal): 60-100 bpm
      - MEDIUM: 40-59 bpm (brady) or 101-129 bpm (tachy)
      - HIGH: <=39 bpm (severe brady) or >=130 bpm (severe tachy)
    """
    if pulse <= 39:
        return "HIGH", f"Severe bradycardia: {pulse} bpm"
    if pulse >= 130:
        return "HIGH", f"Severe tachycardia: {pulse} bpm"
    if 40 <= pulse <= 59:
        return "MEDIUM", f"Bradycardia: {pulse} bpm"
    if 101 <= pulse <= 129:
        return "MEDIUM", f"Tachycardia: {pulse} bpm"
    if 60 <= pulse <= 100:
        return "LOW", f"Normal pulse: {pulse} bpm"
    # Fallback
    return "MEDIUM", f"Borderline pulse: {pulse} bpm"

def combine_risk(bp_risk: str, pulse_risk: str):
    """
    Combine two risk levels into overall: HIGH > MEDIUM > LOW
    """
    order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    ranks = [order.get(bp_risk, 1), order.get(pulse_risk, 1)]
    max_rank = max(ranks)
    for k, v in order.items():
        if v == max_rank:
            return k

def risk_assessment(sys: int, dia: int, pulse: int):
    bp_level, bp_reason = classify_bp(sys, dia)
    pulse_level, pulse_reason = classify_pulse(pulse)
    overall = combine_risk(bp_level, pulse_level)
    reasons = []
    if bp_reason:
        reasons.append(bp_reason)
    if pulse_reason:
        reasons.append(pulse_reason)
    reason_txt = " | ".join(reasons)
    return overall, reason_txt

# ----------------- Core Operations -----------------
def admit_patient():
    patients = load_patients()
    pid = input("Enter Patient ID: ").strip()
    if not pid:
        print("Patient ID cannot be empty.")
        return
    if pid in patients:
        print("A patient with this ID already exists.")
        return

    name = input("Enter Name: ").strip()
    disease = input("Enter Disease: ").strip()
    medicine = input("Enter Medicine: ").strip()
    try:
        interval = int(input("Enter medicine interval (in hours): ").strip())
    except ValueError:
        print("Invalid interval. Must be an integer.")
        return

    # doctor info
    doc_name = input("Doctor Name: ").strip()
    doc_phone = input("Doctor Phone: ").strip()
    doc_email = input("Doctor Email: ").strip()

    patients[pid] = {
        "id": pid,
        "name": name,
        "disease": disease,
        "medicine": medicine,
        "interval_hours": interval,
        "next_dose": (datetime.now() + timedelta(hours=interval)).strftime("%Y-%m-%d %H:%M:%S"),
        "doctor": {"name": doc_name, "phone": doc_phone, "email": doc_email},
        "vitals": {
            "bp_sys": None,
            "bp_dia": None,
            "pulse": None,
            "measured_at": None
        },
        "last_risk": {
            "level": None,
            "reason": None,
            "assessed_at": None
        },
        "created_at": now_str(),
        "updated_at": now_str()
    }

    save_patients(patients)
    print(f"[INFO] Patient {name} admitted successfully.")

def show_patients():
    patients = load_patients()
    if not patients:
        print("No patients admitted yet.")
        return
    for pid, p in patients.items():
        print("-"*70)
        print(f"ID: {pid} | Name: {p['name']} | Disease: {p['disease']}")
        print(f"Medicine: {p['medicine']} | Next Dose: {p['next_dose']} (every {p['interval_hours']}h)")
        v = p.get("vitals", {})
        print(f"Vitals: BP {v.get('bp_sys')}/{v.get('bp_dia')} mmHg, Pulse {v.get('pulse')} bpm"
              f" @ {v.get('measured_at')}")
        r = p.get("last_risk", {})
        print(f"Risk: {r.get('level')} ({r.get('reason')}) @ {r.get('assessed_at')}")
        d = p.get("doctor", {})
        print(f"Doctor: {d.get('name')} | {d.get('phone')} | {d.get('email')}")
    print("-"*70)

def update_vitals():
    patients = load_patients()
    pid = input("Enter Patient ID to update vitals: ").strip()
    if pid not in patients:
        print("Patient not found.")
        return
    try:
        sys = int(input("Enter Systolic BP (mmHg): ").strip())
        dia = int(input("Enter Diastolic BP (mmHg): ").strip())
        pulse = int(input("Enter Pulse (bpm): ").strip())
    except ValueError:
        print("Invalid input. Please enter integers.")
        return

    overall, reason_txt = risk_assessment(sys, dia, pulse)
    patients[pid]["vitals"] = {
        "bp_sys": sys,
        "bp_dia": dia,
        "pulse": pulse,
        "measured_at": now_str()
    }
    patients[pid]["last_risk"] = {
        "level": overall,
        "reason": reason_txt,
        "assessed_at": now_str()
    }
    patients[pid]["updated_at"] = now_str()
    save_patients(patients)

    print(f"[RISK] {patients[pid]['name']} → {overall} | {reason_txt}")
    if overall == "HIGH":
        notify_doctor(patients[pid], overall, reason_txt)

def run_medicine_reminders():
    print("Running medicine reminders... (Press Ctrl+C to stop)")
    try:
        while True:
            patients = load_patients()
            current_time = datetime.now()
            changed = False

            for pid, details in patients.items():
                next_dose_time = datetime.strptime(details["next_dose"], "%Y-%m-%d %H:%M:%S")
                if current_time >= next_dose_time:
                    print(f"[REMINDER] {details['name']} ({details['disease']}) "
                          f"must take {details['medicine']} now! ({now_str()})")
                    # reschedule next dose
                    details["next_dose"] = (current_time + timedelta(hours=details["interval_hours"]))\
                        .strftime("%Y-%m-%d %H:%M:%S")
                    details["updated_at"] = now_str()
                    changed = True

            if changed:
                save_patients(patients)
            time.sleep(10)  # check every 10 seconds
    except KeyboardInterrupt:
        print("\nStopped reminder service.")

def monitor_risk_loop():
    """
    Optional background loop to re-evaluate risk from last known vitals
    and alert if still HIGH. Useful if you want continuous monitoring.
    """
    print("Risk monitor running... (Press Ctrl+C to stop)")
    try:
        while True:
            patients = load_patients()
            for pid, p in patients.items():
                v = p.get("vitals", {})
                if v and all(v.get(k) is not None for k in ("bp_sys", "bp_dia", "pulse")):
                    overall, reason_txt = risk_assessment(v["bp_sys"], v["bp_dia"], v["pulse"])
                    prev = p.get("last_risk", {}).get("level")
                    if overall != prev:
                        p["last_risk"] = {
                            "level": overall,
                            "reason": reason_txt,
                            "assessed_at": now_str()
                        }
                        p["updated_at"] = now_str()
                        print(f"[RISK-UPDATE] {p['name']} → {overall} | {reason_txt}")
                        if overall == "HIGH":
                            notify_doctor(p, overall, reason_txt)
            save_patients(patients)
            time.sleep(15)
    except KeyboardInterrupt:
        print("\nStopped risk monitor.")

def edit_patient():
    patients = load_patients()
    pid = input("Enter Patient ID to edit: ").strip()
    if pid not in patients:
        print("Patient not found.")
        return
    p = patients[pid]
    print("Leave blank to keep existing value.")
    name = input(f"Name [{p['name']}]: ").strip() or p['name']
    disease = input(f"Disease [{p['disease']}]: ").strip() or p['disease']
    medicine = input(f"Medicine [{p['medicine']}]: ").strip() or p['medicine']
    interval = input(f"Interval hours [{p['interval_hours']}]: ").strip()
    try:
        interval = int(interval) if interval else p['interval_hours']
    except ValueError:
        interval = p['interval_hours']

    # doctor
    d = p.get("doctor", {})
    doc_name = input(f"Doctor Name [{d.get('name','')}]: ").strip() or d.get('name','')
    doc_phone = input(f"Doctor Phone [{d.get('phone','')}]: ").strip() or d.get('phone','')
    doc_email = input(f"Doctor Email [{d.get('email','')}]: ").strip() or d.get('email','')

    p.update({
        "name": name,
        "disease": disease,
        "medicine": medicine,
        "interval_hours": interval,
        "doctor": {"name": doc_name, "phone": doc_phone, "email": doc_email},
        "updated_at": now_str()
    })
    save_patients(patients)
    print("[INFO] Patient updated.")

def delete_patient():
    patients = load_patients()
    pid = input("Enter Patient ID to delete: ").strip()
    if pid not in patients:
        print("Patient not found.")
        return
    confirm = input(f"Type 'DELETE {pid}' to confirm: ").strip()
    if confirm == f"DELETE {pid}":
        patients.pop(pid)
        save_patients(patients)
        print("[INFO] Patient deleted.")
    else:
        print("Delete cancelled.")

# ----------------- Main Menu -----------------
def ensure_files_exist():
    if not Path(DATA_FILE).exists():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write("{}")
    if not Path(ALERT_LOG).exists():
        Path(ALERT_LOG).touch()

def main():
    ensure_files_exist()
    while True:
        print("\n🏥 Patient Health Assistant System")
        print("1. Admit Patient")
        print("2. Show Patients")
        print("3. Update Vitals (BP + Pulse)")
        print("4. Run Medicine Reminders (loop)")
        print("5. Run Risk Monitor (loop)")
        print("6. Edit Patient")
        print("7. Delete Patient")
        print("0. Exit")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            admit_patient()
        elif choice == "2":
            show_patients()
        elif choice == "3":
            update_vitals()
        elif choice == "4":
            run_medicine_reminders()
        elif choice == "5":
            monitor_risk_loop()
        elif choice == "6":
            edit_patient()
        elif choice == "7":
            delete_patient()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()



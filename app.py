from flask import Flask, render_template, request, redirect, url_for
import json, os, datetime

app = Flask(__name__)

PATIENTS_FILE = "patients.json"
ALERTS_FILE = "alerts.log"

# Utility Functions
def load_patients():
    if not os.path.exists(PATIENTS_FILE):
        return {}
    with open(PATIENTS_FILE, "r") as f:
        return json.load(f)

def save_patients(data):
    with open(PATIENTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log_alert(message):
    with open(ALERTS_FILE, "a") as f:
        f.write(f"{datetime.datetime.now()} - {message}\n")

def assess_risk(bp_sys, bp_dia, pulse):
    if bp_sys > 160 or bp_dia > 100 or pulse > 120:
        return "HIGH"
    elif 140 <= bp_sys <= 160 or 90 <= bp_dia <= 100 or 100 <= pulse <= 120:
        return "MEDIUM"
    else:
        return "LOW"

# Routes
@app.route("/")
def index():
    patients = load_patients()
    return render_template("index.html", patients=patients)

@app.route("/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        patients = load_patients()
        name = request.form["name"]
        doctor = request.form["doctor"]
        disease = request.form["disease"]
        medicines = request.form["medicines"].split(",")
        tests = request.form["tests"]

        patients[name] = {
            "doctor": doctor,
            "disease": disease,
            "medicines": medicines,
            "tests": tests,
            "vitals": []
        }
        save_patients(patients)
        return redirect(url_for("index"))
    return render_template("add_patient.html")

@app.route("/patient/<name>", methods=["GET", "POST"])
def patient_details(name):
    patients = load_patients()
    patient = patients.get(name, {})

    if request.method == "POST":
        bp_sys = int(request.form["bp_sys"])
        bp_dia = int(request.form["bp_dia"])
        pulse = int(request.form["pulse"])
        risk = assess_risk(bp_sys, bp_dia, pulse)

        vitals = {"bp_sys": bp_sys, "bp_dia": bp_dia, "pulse": pulse, "risk": risk}
        patient["vitals"].append(vitals)

        if risk == "HIGH":
            log_alert(f"High Risk Alert for {name}! Notify Doctor: {patient['doctor']}")

        patients[name] = patient
        save_patients(patients)
        return redirect(url_for("patient_details", name=name))

    return render_template("patient_details.html", name=name, patient=patient)

@app.route("/alerts")
def view_alerts():
    if not os.path.exists(ALERTS_FILE):
        return render_template("alerts.html", alerts=[])
    with open(ALERTS_FILE, "r") as f:
        alerts = f.readlines()
    return render_template("alerts.html", alerts=alerts)

if __name__ == "__main__":
    app.run(debug=True)

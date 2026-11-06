import math

CLINIC_CONFIG = {
    "currency": "$",
    "senior_age_threshold": 60,
    "senior_discount_rate": 0.10,
    "insurance_consultation_coverage": 0.20,
    "insurance_test_coverage": 0.50,
    "tax_rate": 0.0,
}

patients = {
    "P001": {"name": "Ali Khan", "age": 32, "city": "Lahore", "insurance": True},
    "P002": {"name": "Ahmed Raza", "age": 45, "city": "Multan", "insurance": False},
    "P003": {"name": "Sara Ahmed", "age": 28, "city": "Lahore", "insurance": True},
    "P004": {"name": "Usman Ali", "age": 67, "city": "Islamabad", "insurance": False},
}

doctors = {
    "D001": {"name": "Dr. Hassan", "specialization": "Cardiology", "fee": 5000, "available": True},
    "D002": {"name": "Dr. Sara", "specialization": "Dermatology", "fee": 3000, "available": True},
    "D003": {"name": "Dr. Ahmed", "specialization": "General", "fee": 2000, "available": True},
}

appointments = [
    {
        "appointment_id": "A001",
        "patient_id": "P001",
        "doctor_id": "D001",
        "status": "completed",
        "tests": ["ECG", "Blood Test"],
    },
    {
        "appointment_id": "A002",
        "patient_id": "P002",
        "doctor_id": "D003",
        "status": "completed",
        "tests": [],
    },
    {
        "appointment_id": "A003",
        "patient_id": "P003",
        "doctor_id": "D002",
        "status": "cancelled",
        "tests": [],
    },
    {
        "appointment_id": "A004",
        "patient_id": "P004",
        "doctor_id": "D001",
        "status": "completed",
        "tests": ["ECG"],
    },
]

test_prices = {
    "ECG": 1500,
    "Blood Test": 1000,
    "X-Ray": 2500,
    "MRI": 8000,
}


def calculate_total(*charges):
    total = 0.0
    for charge in charges:
        if isinstance(charge, bool) or not isinstance(charge, (int, float)):
            raise TypeError(f"Invalid charge type: {type(charge).__name__}. Charges must be numeric.")
        if math.isnan(charge) or math.isinf(charge):
            raise ValueError("Invalid charge amount: charges cannot be NaN or infinite.")
        if charge < 0:
            raise ValueError(f"Invalid charge amount: {charge}. Charges cannot be negative.")
        total += float(charge)
    return total


def calculate_test_charges(test_list, prices=test_prices):
    if not isinstance(test_list, (list, tuple, set)):
        return 0.0, ["Invalid test list format: must be a list"]

    if not test_list:
        return 0.0, []

    normalized_prices = {k.strip().upper(): (v, k) for k, v in prices.items()}
    seen_tests = set()
    valid_charges = []
    invalid_tests = []

    for test in test_list:
        if not isinstance(test, str) or not test.strip():
            invalid_tests.append(f"Invalid test entry: {test}")
            continue

        normalized = test.strip().upper()
        if normalized in seen_tests:
            invalid_tests.append(f"Duplicate test requested: {test}")
            continue
        seen_tests.add(normalized)

        if normalized in normalized_prices:
            fee, _ = normalized_prices[normalized]
            valid_charges.append(fee)
        else:
            invalid_tests.append(test)

    if invalid_tests:
        return 0.0, invalid_tests

    total_cost = calculate_total(*valid_charges)
    return total_cost, []


def calculate_bill(consultation_fee, test_charges=0.0, **kwargs):
    allowed_keys = {"insurance", "senior_discount"}
    unknown_keys = set(kwargs.keys()) - allowed_keys
    if unknown_keys:
        raise ValueError(f"Unknown billing option(s): {', '.join(unknown_keys)}")

    has_insurance = kwargs.get("insurance", False)
    if not isinstance(has_insurance, bool):
        raise TypeError(f"Option 'insurance' must be a boolean, got {type(has_insurance).__name__}")

    is_senior = kwargs.get("senior_discount", False)
    if not isinstance(is_senior, bool):
        raise TypeError(f"Option 'senior_discount' must be a boolean, got {type(is_senior).__name__}")

    subtotal = calculate_total(consultation_fee, test_charges)

    insurance_covered = 0.0
    if has_insurance:
        doc_coverage = consultation_fee * CLINIC_CONFIG["insurance_consultation_coverage"]
        test_coverage = test_charges * CLINIC_CONFIG["insurance_test_coverage"]
        insurance_covered = doc_coverage + test_coverage

    after_insurance = subtotal - insurance_covered

    senior_discount = 0.0
    if is_senior:
        senior_discount = after_insurance * CLINIC_CONFIG["senior_discount_rate"]
        after_insurance -= senior_discount

    tax = after_insurance * CLINIC_CONFIG["tax_rate"]
    total = after_insurance + tax

    return {
        "consultation_fee": round(float(consultation_fee), 2),
        "test_charges": round(float(test_charges), 2),
        "subtotal": round(subtotal, 2),
        "insurance_covered": round(insurance_covered, 2),
        "after_insurance": round(after_insurance, 2),
        "senior_discount": round(senior_discount, 2),
        "tax": round(tax, 2),
        "total": round(total, 2),
    }


def validate_appointment(
    appointment,
    patients_data=patients,
    doctors_data=doctors,
    prices_data=test_prices,
):
    if not isinstance(appointment, dict):
        return False, "Appointment must be a valid dictionary"

    p_id = appointment.get("patient_id")
    d_id = appointment.get("doctor_id")
    status = appointment.get("status")
    tests = appointment.get("tests", [])

    if isinstance(p_id, str):
        p_id = p_id.strip().upper()
    if isinstance(d_id, str):
        d_id = d_id.strip().upper()
    if isinstance(status, str):
        status = status.strip().lower()

    if not isinstance(p_id, str) or p_id not in patients_data:
        return False, f"Patient {p_id} does not exist"

    patient = patients_data[p_id]
    if not isinstance(patient, dict):
        return False, f"Patient {p_id} record is corrupt"

    age = patient.get("age")
    if isinstance(age, bool) or not isinstance(age, int) or age <= 0:
        return False, f"Patient {p_id} has invalid age: {age}"

    insurance = patient.get("insurance")
    if not isinstance(insurance, bool):
        return False, f"Patient {p_id} has invalid insurance flag: {insurance}"

    if not isinstance(d_id, str) or d_id not in doctors_data:
        return False, f"Doctor {d_id} does not exist"

    doctor = doctors_data[d_id]
    if not isinstance(doctor, dict):
        return False, f"Doctor {d_id} record is corrupt"

    fee = doctor.get("fee")
    if (
        isinstance(fee, bool)
        or not isinstance(fee, (int, float))
        or math.isnan(fee)
        or math.isinf(fee)
        or fee < 0
    ):
        return False, f"Doctor {d_id} has invalid consultation fee: {fee}"

    available = doctor.get("available")
    if available is not True:
        return False, f"Doctor {doctor.get('name', d_id)} is currently unavailable"

    valid_statuses = {"completed", "pending", "cancelled"}
    if status not in valid_statuses:
        return False, f"Invalid appointment status: {status}"

    if not isinstance(tests, (list, tuple, set)):
        return False, "Appointment tests must be a list"

    _, invalid_tests = calculate_test_charges(tests, prices_data)
    if invalid_tests:
        return False, f"Invalid tests requested: {', '.join(invalid_tests)}"

    return True, "Valid"


def cancel_appointment(app_id, appointments_list=appointments):
    if not isinstance(appointments_list, list):
        return False, "Appointments list must be a list"

    app = None
    for item in appointments_list:
        if isinstance(item, dict) and item.get("appointment_id") == app_id:
            app = item
            break

    if not app:
        return False, f"Appointment {app_id} does not exist"

    status = app.get("status")
    if status == "completed":
        return False, f"Appointment {app_id} is completed and cannot be cancelled"

    if status == "cancelled":
        return False, f"Appointment {app_id} is already cancelled"

    if status == "pending":
        app["status"] = "cancelled"
        return True, f"Appointment {app_id} has been successfully cancelled"

    return False, f"Unknown status: {status}"


def process_appointment(
    app_id,
    appointment_list=appointments,
    patients_data=patients,
    doctors_data=doctors,
    prices_data=test_prices,
    processed_ids=None,
):
    if processed_ids is None:
        processed_ids = set()

    if not isinstance(appointment_list, list):
        return False, "Appointments list must be a list"

    app = None
    for item in appointment_list:
        if isinstance(item, dict) and item.get("appointment_id") == app_id:
            app = item
            break

    if not app:
        return False, f"Appointment {app_id} does not exist"

    if app_id in processed_ids:
        return False, f"Appointment {app_id} has already been processed"

    if app.get("status") == "cancelled":
        return False, f"Appointment {app_id} is cancelled and cannot be processed"

    is_valid, reason = validate_appointment(app, patients_data, doctors_data, prices_data)
    if not is_valid:
        return False, f"REJECTED | Reason: {reason}"

    p_id = app["patient_id"]
    d_id = app["doctor_id"]
    if isinstance(p_id, str):
        p_id = p_id.strip().upper()
    if isinstance(d_id, str):
        d_id = d_id.strip().upper()
    doctor_fee = doctors_data[d_id]["fee"]
    test_charges, _ = calculate_test_charges(app.get("tests", []), prices_data)

    has_insurance = patients_data[p_id]["insurance"]
    is_senior = patients_data[p_id]["age"] >= CLINIC_CONFIG["senior_age_threshold"]

    bill = calculate_bill(
        doctor_fee,
        test_charges,
        insurance=has_insurance,
        senior_discount=is_senior,
    )

    app["status"] = "completed"
    app["bill"] = bill
    processed_ids.add(app_id)

    return True, {
        "appointment_id": app_id,
        "patient_name": patients_data[p_id]["name"],
        "doctor_name": doctors_data[d_id]["name"],
        "bill": bill,
    }


def generate_doctor_report(doctors_data=doctors, appointments_list=appointments):
    doc_stats = {}
    spec_counts = {}

    for d_id, d_info in doctors_data.items():
        if not isinstance(d_info, dict):
            continue

        doc_apps = [a for a in appointments_list if isinstance(a, dict) and a.get("doctor_id") == d_id]
        completed = [a for a in doc_apps if a.get("status") == "completed"]
        cancelled = [a for a in doc_apps if a.get("status") == "cancelled"]

        total_rev = calculate_total(*[a.get("bill", {}).get("total", 0.0) for a in completed])
        avg_bill = round(total_rev / len(completed), 2) if completed else 0.0

        doc_stats[d_id] = {
            "name": d_info.get("name", d_id),
            "specialization": d_info.get("specialization", "General"),
            "total_appointments": len(doc_apps),
            "completed": len(completed),
            "cancelled": len(cancelled),
            "revenue": total_rev,
            "average_bill": avg_bill,
        }

        spec = d_info.get("specialization", "General")
        spec_counts[spec] = spec_counts.get(spec, 0) + len(doc_apps)

    sorted_doctors = sorted(doc_stats.values(), key=lambda d: d["total_appointments"], reverse=True)
    if sorted_doctors and sorted_doctors[0]["total_appointments"] > 0:
        max_apps = sorted_doctors[0]["total_appointments"]
        most_requested_doctors = [d["name"] for d in sorted_doctors if d["total_appointments"] == max_apps]
    else:
        most_requested_doctors = []

    sorted_specs = sorted(spec_counts.items(), key=lambda s: s[1], reverse=True)
    if sorted_specs and sorted_specs[0][1] > 0:
        max_spec = sorted_specs[0][1]
        most_requested_specs = [s[0] for s in sorted_specs if s[1] == max_spec]
    else:
        most_requested_specs = []

    return {
        "doctor_details": doc_stats,
        "most_requested_doctor": ", ".join(most_requested_doctors) if most_requested_doctors else "None",
        "most_requested_specialization": ", ".join(most_requested_specs) if most_requested_specs else "None",
    }


def generate_patient_report(patients_data=patients, appointments_list=appointments):
    patient_stats = {}

    for p_id, p_info in patients_data.items():
        if not isinstance(p_info, dict):
            continue

        p_apps = [a for a in appointments_list if isinstance(a, dict) and a.get("patient_id") == p_id]
        completed = [a for a in p_apps if a.get("status") == "completed"]
        cancelled = [a for a in p_apps if a.get("status") == "cancelled"]

        total_charges = calculate_total(*[a.get("bill", {}).get("subtotal", 0.0) for a in completed])
        insurance_paid = calculate_total(*[a.get("bill", {}).get("insurance_covered", 0.0) for a in completed])
        patient_paid = calculate_total(*[a.get("bill", {}).get("total", 0.0) for a in completed])

        patient_stats[p_id] = {
            "name": p_info.get("name", p_id),
            "age": p_info.get("age", 0),
            "has_insurance": bool(p_info.get("insurance", False)),
            "total_appointments": len(p_apps),
            "completed": len(completed),
            "cancelled": len(cancelled),
            "total_charges": total_charges,
            "insurance_paid": insurance_paid,
            "patient_paid": patient_paid,
        }

    sorted_by_spending = sorted(patient_stats.values(), key=lambda p: p["patient_paid"], reverse=True)
    if sorted_by_spending and sorted_by_spending[0]["patient_paid"] > 0:
        max_paid = sorted_by_spending[0]["patient_paid"]
        highest_spenders = [p["name"] for p in sorted_by_spending if p["patient_paid"] == max_paid]
    else:
        highest_spenders = []

    sorted_by_apps = sorted(patient_stats.values(), key=lambda p: p["total_appointments"], reverse=True)
    if sorted_by_apps and sorted_by_apps[0]["total_appointments"] > 0:
        max_p_apps = sorted_by_apps[0]["total_appointments"]
        most_apps_patients = [p["name"] for p in sorted_by_apps if p["total_appointments"] == max_p_apps]
    else:
        most_apps_patients = []

    no_completed_patients = [p["name"] for p in patient_stats.values() if p["completed"] == 0]
    insured_patients = [
        p_info["name"]
        for p_info in patients_data.values()
        if isinstance(p_info, dict) and p_info.get("insurance") is True
    ]
    senior_patients = [
        p_info["name"]
        for p_info in patients_data.values()
        if isinstance(p_info, dict)
        and isinstance(p_info.get("age"), int)
        and not isinstance(p_info.get("age"), bool)
        and p_info.get("age") >= CLINIC_CONFIG["senior_age_threshold"]
    ]

    return {
        "patient_details": patient_stats,
        "highest_spending_patient": ", ".join(highest_spenders) if highest_spenders else "None",
        "patient_with_most_appointments": ", ".join(most_apps_patients) if most_apps_patients else "None",
        "no_completed_appointments": no_completed_patients,
        "insured_patients": insured_patients,
        "senior_patients": senior_patients,
    }


def generate_clinic_dashboard(
    patients_data=patients,
    doctors_data=doctors,
    appointments_list=appointments,
):
    doc_report = generate_doctor_report(doctors_data, appointments_list)
    pat_report = generate_patient_report(patients_data, appointments_list)

    total_patients = len(patients_data)
    total_doctors = len(doctors_data)
    total_appointments = len(appointments_list)

    completed_apps = [a for a in appointments_list if isinstance(a, dict) and a.get("status") == "completed"]
    cancelled_apps = [a for a in appointments_list if isinstance(a, dict) and a.get("status") == "cancelled"]
    pending_apps = [a for a in appointments_list if isinstance(a, dict) and a.get("status") == "pending"]

    consultation_rev = 0.0
    test_rev = 0.0
    insurance_cov = 0.0
    senior_disc_total = 0.0
    patient_rev = 0.0

    for a in completed_apps:
        bill = a.get("bill")
        if isinstance(bill, dict):
            consultation_rev += bill.get("consultation_fee", 0.0)
            test_rev += bill.get("test_charges", 0.0)
            insurance_cov += bill.get("insurance_covered", 0.0)
            senior_disc_total += bill.get("senior_discount", 0.0)
            patient_rev += bill.get("total", 0.0)

    dashboard_data = {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": total_appointments,
        "completed_count": len(completed_apps),
        "cancelled_count": len(cancelled_apps),
        "pending_count": len(pending_apps),
        "total_consultation_revenue": consultation_rev,
        "total_test_revenue": test_rev,
        "total_insurance_coverage": insurance_cov,
        "total_senior_discount": senior_disc_total,
        "total_patient_revenue": patient_rev,
        "most_requested_specialization": doc_report["most_requested_specialization"],
        "highest_spending_patient": pat_report["highest_spending_patient"],
    }

    return dashboard_data


def display_clinic_dashboard(dashboard_data, currency=None):
    if currency is None:
        currency = CLINIC_CONFIG["currency"]

    print("=" * 40)
    print("           CLINIC DASHBOARD")
    print("=" * 40)
    print(f"Total Patients: {dashboard_data['total_patients']}")
    print(f"Total Doctors: {dashboard_data['total_doctors']}")
    print(f"Total Appointments: {dashboard_data['total_appointments']}")
    print(f"Completed: {dashboard_data['completed_count']}")
    print(f"Cancelled: {dashboard_data['cancelled_count']}")
    print(f"Pending: {dashboard_data['pending_count']}")
    print(f"Total Consultation Revenue: {currency}{dashboard_data['total_consultation_revenue']:,.2f}")
    print(f"Total Test Revenue: {currency}{dashboard_data['total_test_revenue']:,.2f}")
    print(f"Total Insurance Coverage: {currency}{dashboard_data['total_insurance_coverage']:,.2f}")
    print(f"Total Senior Discount: {currency}{dashboard_data['total_senior_discount']:,.2f}")
    print(f"Total Patient Revenue: {currency}{dashboard_data['total_patient_revenue']:,.2f}")
    print(f"Most Requested Specialization: {dashboard_data['most_requested_specialization']}")
    print(f"Highest Spending Patient: {dashboard_data['highest_spending_patient']}")
    print("=" * 40)


if __name__ == "__main__":
    print("\n" + "=" * 40)
    print("      PROCESSING APPOINTMENTS")
    print("=" * 40)

    processed_ids = set()
    for app in list(appointments):
        app_id = app["appointment_id"]
        success, result = process_appointment(app_id, appointments, patients, doctors, test_prices, processed_ids)
        if success:
            bill = result["bill"]
            curr = CLINIC_CONFIG["currency"]
            print(
                f"[SUCCESS] App ID: {app_id} | Patient: {result['patient_name']} | Doctor: {result['doctor_name']}"
            )
            print(
                f"          Subtotal: {curr}{bill['subtotal']:,.2f} | Insurance: {curr}{bill['insurance_covered']:,.2f} | Senior Disc: {curr}{bill['senior_discount']:,.2f} | Paid: {curr}{bill['total']:,.2f}"
            )
        else:
            print(f"[REJECTED] App ID: {app_id} | {result}")

    print("\n")
    dashboard = generate_clinic_dashboard(patients, doctors, appointments)
    display_clinic_dashboard(dashboard)

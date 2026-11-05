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

processed_appointments = set()


def calculate_total(*charges):
    total = 0
    for charge in charges:
        if isinstance(charge, (int, float)) and charge >= 0:
            total += charge
        else:
            print(f"Warning: Invalid charge skipped: {charge}")
    return total


def calculate_test_charges(test_list, prices=test_prices):
    if not test_list:
        return 0, []

    unique_tests = set(test_list)
    valid_charges = []
    invalid_tests = []

    for test in unique_tests:
        if test in prices:
            valid_charges.append(prices[test])
        else:
            invalid_tests.append(test)

    total_cost = calculate_total(*valid_charges)
    return total_cost, invalid_tests


def calculate_bill(consultation_fee, test_charges=0, **kwargs):
    has_insurance = kwargs.get("insurance", False)
    is_senior = kwargs.get("senior_discount", False)

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
    p_id = appointment.get("patient_id")
    d_id = appointment.get("doctor_id")
    status = appointment.get("status")
    tests = appointment.get("tests", [])

    if p_id not in patients_data:
        return False, f"Patient {p_id} does not exist"

    if patients_data[p_id].get("age", 0) <= 0:
        return False, f"Patient {p_id} has invalid age"

    if d_id not in doctors_data:
        return False, f"Doctor {d_id} does not exist"

    if not doctors_data[d_id].get("available", False):
        return False, f"Doctor {doctors_data[d_id]['name']} is currently unavailable"

    valid_statuses = {"completed", "pending", "cancelled"}
    if status not in valid_statuses:
        return False, f"Invalid appointment status: {status}"

    _, invalid_tests = calculate_test_charges(tests, prices_data)
    if invalid_tests:
        return False, f"Invalid tests requested: {', '.join(invalid_tests)}"

    return True, "Valid"


def cancel_appointment(app_id, appointments_list=appointments):
    app = None
    for item in appointments_list:
        if item.get("appointment_id") == app_id:
            app = item
            break

    if not app:
        return False, f"Appointment {app_id} does not exist"

    if app.get("status") == "completed":
        return False, f"Appointment {app_id} is completed and cannot be cancelled"

    if app.get("status") == "cancelled":
        return False, f"Appointment {app_id} is already cancelled"

    if app.get("status") == "pending":
        app["status"] = "cancelled"
        return True, f"Appointment {app_id} has been successfully cancelled"

    return False, f"Unknown status: {app.get('status')}"


def process_appointment(
    app_id,
    appointment_list=appointments,
    patients_data=patients,
    doctors_data=doctors,
    prices_data=test_prices,
):
    app = None
    for item in appointment_list:
        if item.get("appointment_id") == app_id:
            app = item
            break

    if not app:
        return False, f"Appointment {app_id} does not exist"

    if app_id in processed_appointments:
        return False, f"Appointment {app_id} has already been processed"

    if app.get("status") == "cancelled":
        return False, f"Appointment {app_id} is cancelled and cannot be processed"

    is_valid, reason = validate_appointment(app, patients_data, doctors_data, prices_data)
    if not is_valid:
        return False, f"REJECTED | Reason: {reason}"

    p_id = app["patient_id"]
    d_id = app["doctor_id"]
    doctor_fee = doctors_data[d_id]["fee"]
    test_charges, _ = calculate_test_charges(app.get("tests", []), prices_data)

    has_insurance = patients_data[p_id].get("insurance", False)
    is_senior = patients_data[p_id].get("age", 0) >= CLINIC_CONFIG["senior_age_threshold"]

    bill = calculate_bill(
        doctor_fee,
        test_charges,
        insurance=has_insurance,
        senior_discount=is_senior,
    )

    app["status"] = "completed"
    app["bill"] = bill
    processed_appointments.add(app_id)

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
        doc_apps = [a for a in appointments_list if a.get("doctor_id") == d_id]
        completed = [a for a in doc_apps if a.get("status") == "completed"]
        cancelled = [a for a in doc_apps if a.get("status") == "cancelled"]

        total_rev = calculate_total(*[a.get("bill", {}).get("total", 0) for a in completed])
        avg_bill = round(total_rev / len(completed), 2) if completed else 0.0

        doc_stats[d_id] = {
            "name": d_info["name"],
            "specialization": d_info["specialization"],
            "total_appointments": len(doc_apps),
            "completed": len(completed),
            "cancelled": len(cancelled),
            "revenue": total_rev,
            "average_bill": avg_bill,
        }

        spec = d_info["specialization"]
        spec_counts[spec] = spec_counts.get(spec, 0) + len(doc_apps)

    sorted_doctors = sorted(
        doc_stats.values(),
        key=lambda d: d["total_appointments"],
        reverse=True,
    )
    most_requested_doctor = (
        sorted_doctors[0]["name"]
        if sorted_doctors and sorted_doctors[0]["total_appointments"] > 0
        else "None"
    )

    sorted_specs = sorted(spec_counts.items(), key=lambda s: s[1], reverse=True)
    most_requested_spec = (
        sorted_specs[0][0]
        if sorted_specs and sorted_specs[0][1] > 0
        else "None"
    )

    return {
        "doctor_details": doc_stats,
        "most_requested_doctor": most_requested_doctor,
        "most_requested_specialization": most_requested_spec,
    }


def generate_patient_report(patients_data=patients, appointments_list=appointments):
    patient_stats = {}

    for p_id, p_info in patients_data.items():
        p_apps = [a for a in appointments_list if a.get("patient_id") == p_id]
        completed = [a for a in p_apps if a.get("status") == "completed"]
        cancelled = [a for a in p_apps if a.get("status") == "cancelled"]

        total_charges = calculate_total(*[a.get("bill", {}).get("subtotal", 0) for a in completed])
        insurance_paid = calculate_total(*[a.get("bill", {}).get("insurance_covered", 0) for a in completed])
        patient_paid = calculate_total(*[a.get("bill", {}).get("total", 0) for a in completed])

        patient_stats[p_id] = {
            "name": p_info["name"],
            "age": p_info["age"],
            "has_insurance": p_info.get("insurance", False),
            "total_appointments": len(p_apps),
            "completed": len(completed),
            "cancelled": len(cancelled),
            "total_charges": total_charges,
            "insurance_paid": insurance_paid,
            "patient_paid": patient_paid,
        }

    sorted_by_spending = sorted(
        patient_stats.values(),
        key=lambda p: p["patient_paid"],
        reverse=True,
    )
    highest_spender = (
        sorted_by_spending[0]["name"]
        if sorted_by_spending and sorted_by_spending[0]["patient_paid"] > 0
        else "None"
    )

    sorted_by_apps = sorted(
        patient_stats.values(),
        key=lambda p: p["total_appointments"],
        reverse=True,
    )
    most_appointments_patient = (
        sorted_by_apps[0]["name"]
        if sorted_by_apps and sorted_by_apps[0]["total_appointments"] > 0
        else "None"
    )

    no_completed_patients = [p["name"] for p in patient_stats.values() if p["completed"] == 0]
    insured_patients = [
        p_info["name"]
        for p_info in patients_data.values()
        if p_info.get("insurance", False)
    ]
    senior_patients = [
        p_info["name"]
        for p_info in patients_data.values()
        if p_info.get("age", 0) >= CLINIC_CONFIG["senior_age_threshold"]
    ]

    return {
        "patient_details": patient_stats,
        "highest_spending_patient": highest_spender,
        "patient_with_most_appointments": most_appointments_patient,
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

    completed_apps = [a for a in appointments_list if a.get("status") == "completed"]
    cancelled_apps = [a for a in appointments_list if a.get("status") == "cancelled"]
    pending_apps = [a for a in appointments_list if a.get("status") == "pending"]

    consultation_rev = 0.0
    test_rev = 0.0
    insurance_cov = 0.0
    patient_rev = 0.0

    for a in completed_apps:
        bill = a.get("bill", {})
        if bill:
            d_fee = doctors_data.get(a["doctor_id"], {}).get("fee", 0)
            t_fee, _ = calculate_test_charges(a.get("tests", []))
            consultation_rev += d_fee
            test_rev += t_fee
            insurance_cov += bill.get("insurance_covered", 0.0)
            patient_rev += bill.get("total", 0.0)

    currency = CLINIC_CONFIG["currency"]

    print("=" * 40)
    print("           CLINIC DASHBOARD")
    print("=" * 40)
    print(f"Total Patients: {total_patients}")
    print(f"Total Doctors: {total_doctors}")
    print(f"Total Appointments: {total_appointments}")
    print(f"Completed: {len(completed_apps)}")
    print(f"Cancelled: {len(cancelled_apps)}")
    print(f"Pending: {len(pending_apps)}")
    print(f"Total Consultation Revenue: {currency}{consultation_rev:.2f}")
    print(f"Total Test Revenue: {currency}{test_rev:.2f}")
    print(f"Total Insurance Coverage: {currency}{insurance_cov:.2f}")
    print(f"Total Patient Revenue: {currency}{patient_rev:.2f}")
    print(f"Most Requested Specialization: {doc_report['most_requested_specialization']}")
    print(f"Highest Spending Patient: {pat_report['highest_spending_patient']}")
    print("=" * 40)


def run_edge_case_tests():
    print("\n" + "=" * 40)
    print("      RUNNING EDGE CASE TEST SUITE")
    print("=" * 40)

    t1 = {
        "appointment_id": "T001",
        "patient_id": "P999",
        "doctor_id": "D001",
        "status": "completed",
        "tests": [],
    }
    valid, msg = validate_appointment(t1)
    print(f"Test 01 - Invalid Patient: {'PASS' if not valid else 'FAIL'} | {msg}")

    t2 = {
        "appointment_id": "T002",
        "patient_id": "P001",
        "doctor_id": "D999",
        "status": "completed",
        "tests": [],
    }
    valid, msg = validate_appointment(t2)
    print(f"Test 02 - Invalid Doctor: {'PASS' if not valid else 'FAIL'} | {msg}")

    mock_doctors = {
        "D998": {
            "name": "Dr. Busy",
            "specialization": "Cardiology",
            "fee": 5000,
            "available": False,
        }
    }
    t3 = {
        "appointment_id": "T003",
        "patient_id": "P001",
        "doctor_id": "D998",
        "status": "completed",
        "tests": [],
    }
    valid, msg = validate_appointment(t3, doctors_data=mock_doctors)
    print(f"Test 03 - Doctor Unavailable: {'PASS' if not valid else 'FAIL'} | {msg}")

    t4 = {
        "appointment_id": "T004",
        "patient_id": "P001",
        "doctor_id": "D001",
        "status": "completed",
        "tests": ["NonExistentTest"],
    }
    valid, msg = validate_appointment(t4)
    print(f"Test 04 - Invalid Test: {'PASS' if not valid else 'FAIL'} | {msg}")

    cost, invalids = calculate_test_charges(["ECG", "ECG"])
    print(
        f"Test 05 - Duplicate Test Deduplication: {'PASS' if cost == 1500 and not invalids else 'FAIL'} | Cost: {cost}"
    )

    cost, invalids = calculate_test_charges([])
    print(
        f"Test 06 - Empty Test List: {'PASS' if cost == 0 and not invalids else 'FAIL'} | Cost: {cost}"
    )

    mock_patients = {
        "P998": {
            "name": "Invalid Age",
            "age": -5,
            "city": "Lahore",
            "insurance": False,
        }
    }
    t7 = {
        "appointment_id": "T007",
        "patient_id": "P998",
        "doctor_id": "D001",
        "status": "completed",
        "tests": [],
    }
    valid, msg = validate_appointment(t7, patients_data=mock_patients)
    print(f"Test 07 - Negative Age: {'PASS' if not valid else 'FAIL'} | {msg}")

    t8 = {
        "appointment_id": "T008",
        "patient_id": "P001",
        "doctor_id": "D001",
        "status": "unknown_status",
        "tests": [],
    }
    valid, msg = validate_appointment(t8)
    print(f"Test 08 - Invalid Status: {'PASS' if not valid else 'FAIL'} | {msg}")

    success, msg = cancel_appointment("A001")
    print(f"Test 09 - Cancel Completed: {'PASS' if not success else 'FAIL'} | {msg}")

    success, msg = process_appointment("A003")
    print(f"Test 10 - Process Cancelled: {'PASS' if not success else 'FAIL'} | {msg}")

    success, msg = process_appointment("A001")
    print(f"Test 11 - Re-process Duplicate: {'PASS' if not success else 'FAIL'} | {msg}")

    empty_apps = []
    doc_rep = generate_doctor_report(doctors_data=doctors, appointments_list=empty_apps)
    pat_rep = generate_patient_report(patients_data=patients, appointments_list=empty_apps)
    avg_bill = doc_rep["doctor_details"]["D001"]["average_bill"]
    print(
        f"Test 12 - Zero Appointments Safety: {'PASS' if avg_bill == 0.0 else 'FAIL'} | Avg Bill: {avg_bill}"
    )

    empty_doc_rep = generate_doctor_report(doctors_data={}, appointments_list=[])
    empty_pat_rep = generate_patient_report(patients_data={}, appointments_list=[])
    print(
        f"Test 13 - Empty Datasets: {'PASS' if empty_doc_rep['most_requested_doctor'] == 'None' else 'FAIL'}"
    )

    print("=" * 40)


if __name__ == "__main__":
    print("\n" + "=" * 40)
    print("      PROCESSING APPOINTMENTS")
    print("=" * 40)

    for app in list(appointments):
        app_id = app["appointment_id"]
        success, result = process_appointment(app_id)
        if success:
            bill = result["bill"]
            curr = CLINIC_CONFIG["currency"]
            print(
                f"[SUCCESS] App ID: {app_id} | Patient: {result['patient_name']} | Doctor: {result['doctor_name']}"
            )
            print(
                f"          Subtotal: {curr}{bill['subtotal']} | Insurance Covered: {curr}{bill['insurance_covered']} | Paid: {curr}{bill['total']}"
            )
        else:
            print(f"[REJECTED] App ID: {app_id} | {result}")

    print("\n")
    generate_clinic_dashboard()
    run_edge_case_tests()

import copy
import sys
from main import (
    CLINIC_CONFIG,
    calculate_bill,
    calculate_test_charges,
    calculate_total,
    cancel_appointment,
    generate_clinic_dashboard,
    generate_doctor_report,
    generate_patient_report,
    process_appointment,
    validate_appointment,
)


def get_test_data():
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
    return patients, doctors, appointments, test_prices


def test_calculate_total_valid_charges():
    assert calculate_total(5000, 1500, 1000) == 7500.0


def test_calculate_total_rejects_negative_and_non_numeric():
    try:
        calculate_total(5000, -100)
        assert False
    except ValueError:
        pass

    try:
        calculate_total(5000, "1500")
        assert False
    except TypeError:
        pass

    try:
        calculate_total(5000, True)
        assert False
    except TypeError:
        pass


def test_calculate_bill_standard_and_senior():
    bill_normal = calculate_bill(5000, 2500, insurance=True, senior_discount=False)
    assert bill_normal["subtotal"] == 7500.0
    assert bill_normal["insurance_covered"] == 2250.0
    assert bill_normal["total"] == 5250.0

    bill_senior = calculate_bill(5000, 2500, insurance=True, senior_discount=True)
    assert bill_senior["insurance_covered"] == 2250.0
    assert bill_senior["senior_discount"] == 525.0
    assert bill_senior["total"] == 4725.0


def test_calculate_bill_rejects_invalid_kwargs():
    try:
        calculate_bill(5000, insurence=True)
        assert False
    except ValueError:
        pass

    try:
        calculate_bill(5000, insurance="no")
        assert False
    except TypeError:
        pass

    try:
        calculate_bill(5000, senior_discount="yes")
        assert False
    except TypeError:
        pass


def test_calculate_test_charges_case_insensitive():
    _, _, _, prices = get_test_data()
    cost, invalids = calculate_test_charges(["ecg", "blood test"], prices)
    assert cost == 2500.0
    assert invalids == []


def test_calculate_test_charges_rejects_duplicates():
    _, _, _, prices = get_test_data()
    cost, invalids = calculate_test_charges(["ECG", "ECG"], prices)
    assert cost == 0.0
    assert any("Duplicate" in x for x in invalids)


def test_calculate_test_charges_rejects_non_list():
    _, _, _, prices = get_test_data()
    cost, invalids = calculate_test_charges("ECG", prices)
    assert cost == 0.0
    assert len(invalids) > 0


def test_validate_appointment_type_guards():
    patients, doctors, appointments, prices = get_test_data()

    valid, _ = validate_appointment(None)
    assert not valid

    corrupt_patients = copy.deepcopy(patients)
    corrupt_patients["P001"]["age"] = True
    t_app = copy.deepcopy(appointments[0])
    valid, msg = validate_appointment(t_app, corrupt_patients, doctors, prices)
    assert not valid
    assert "invalid age" in msg

    corrupt_patients["P001"]["age"] = "32"
    valid, _ = validate_appointment(t_app, corrupt_patients, doctors, prices)
    assert not valid

    corrupt_patients["P001"]["age"] = 32
    corrupt_patients["P001"]["insurance"] = "no"
    valid, msg = validate_appointment(t_app, corrupt_patients, doctors, prices)
    assert not valid
    assert "invalid insurance flag" in msg

    corrupt_doctors = copy.deepcopy(doctors)
    corrupt_doctors["D001"]["fee"] = "5000"
    valid, msg = validate_appointment(t_app, patients, corrupt_doctors, prices)
    assert not valid
    assert "invalid consultation fee" in msg

    corrupt_doctors["D001"]["fee"] = -100
    valid, _ = validate_appointment(t_app, patients, corrupt_doctors, prices)
    assert not valid

    corrupt_doctors["D001"]["fee"] = 5000
    corrupt_doctors["D001"]["available"] = "no"
    valid, msg = validate_appointment(t_app, patients, corrupt_doctors, prices)
    assert not valid
    assert "currently unavailable" in msg


def test_cancellation_rules():
    _, _, appointments, _ = get_test_data()
    test_apps = copy.deepcopy(appointments)
    test_apps.append({
        "appointment_id": "A099",
        "patient_id": "P001",
        "doctor_id": "D001",
        "status": "pending",
        "tests": [],
    })

    success, _ = cancel_appointment("A099", test_apps)
    assert success

    success, msg = cancel_appointment("A001", test_apps)
    assert not success
    assert "completed and cannot be cancelled" in msg

    success, msg = cancel_appointment("A003", test_apps)
    assert not success
    assert "already cancelled" in msg


def test_process_appointment_isolated():
    patients, doctors, appointments, prices = get_test_data()
    test_apps = copy.deepcopy(appointments)
    processed = set()

    success, res = process_appointment("A001", test_apps, patients, doctors, prices, processed)
    assert success
    assert res["bill"]["total"] == 5250.0

    success_dup, msg_dup = process_appointment("A001", test_apps, patients, doctors, prices, processed)
    assert not success_dup
    assert "already been processed" in msg_dup


def test_dashboard_history_and_ledger_balance():
    patients, doctors, appointments, prices = get_test_data()
    test_apps = copy.deepcopy(appointments)
    doctors_copy = copy.deepcopy(doctors)
    processed = set()

    for a in test_apps:
        process_appointment(a["appointment_id"], test_apps, patients, doctors_copy, prices, processed)

    doctors_copy["D001"]["fee"] = 99999

    dashboard = generate_clinic_dashboard(patients, doctors_copy, test_apps)

    assert dashboard["total_consultation_revenue"] == 12000.0
    assert dashboard["total_test_revenue"] == 4000.0
    assert dashboard["total_insurance_coverage"] == 2250.0
    assert dashboard["total_senior_discount"] == 650.0
    assert dashboard["total_patient_revenue"] == 13100.0

    calculated_revenue = (
        dashboard["total_consultation_revenue"]
        + dashboard["total_test_revenue"]
        - dashboard["total_insurance_coverage"]
        - dashboard["total_senior_discount"]
    )
    assert round(calculated_revenue, 2) == round(dashboard["total_patient_revenue"], 2)


def test_report_ties_are_not_hidden():
    patients, doctors, appointments, prices = get_test_data()
    test_apps = copy.deepcopy(appointments)
    processed = set()
    for a in test_apps:
        process_appointment(a["appointment_id"], test_apps, patients, doctors, prices, processed)

    doc_rep = generate_doctor_report(doctors, test_apps)
    pat_rep = generate_patient_report(patients, test_apps)

    assert "Dr. Hassan" in doc_rep["most_requested_doctor"]
    assert "Usman Ali" in pat_rep["highest_spending_patient"]


def run_all_tests():
    tests = [
        test_calculate_total_valid_charges,
        test_calculate_total_rejects_negative_and_non_numeric,
        test_calculate_bill_standard_and_senior,
        test_calculate_bill_rejects_invalid_kwargs,
        test_calculate_test_charges_case_insensitive,
        test_calculate_test_charges_rejects_duplicates,
        test_calculate_test_charges_rejects_non_list,
        test_validate_appointment_type_guards,
        test_cancellation_rules,
        test_process_appointment_isolated,
        test_dashboard_history_and_ledger_balance,
        test_report_ties_are_not_hidden,
    ]

    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAILED: {test.__name__} - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {test.__name__} - {e}")
            sys.exit(1)

    print(f"All {passed} unit tests passed successfully with zero failures.")
    sys.exit(0)


if __name__ == "__main__":
    run_all_tests()

import copy
import math
import unittest
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


def get_test_fixtures():
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


class TestHospitalSystem(unittest.TestCase):

    def test_calculate_total_valid_charges(self):
        self.assertEqual(calculate_total(100, 200, 300), 600.0)
        self.assertEqual(calculate_total(), 0.0)
        self.assertEqual(calculate_total(50.5, 49.5), 100.0)

    def test_calculate_total_type_fuzzing(self):
        for bad in ("100", None, True, False, [100], {"fee": 100}):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    calculate_total(bad)

        for bad_num in (-10, -0.01, float("nan"), float("inf")):
            with self.subTest(bad_num=bad_num):
                with self.assertRaises(ValueError):
                    calculate_total(bad_num)

    def test_calculate_bill_standard_and_senior(self):
        bill_standard = calculate_bill(5000, 2500, insurance=True, senior_discount=False)
        self.assertEqual(bill_standard["subtotal"], 7500.0)
        self.assertEqual(bill_standard["insurance_covered"], 2250.0)
        self.assertEqual(bill_standard["after_insurance"], 5250.0)
        self.assertEqual(bill_standard["senior_discount"], 0.0)
        self.assertEqual(bill_standard["total"], 5250.0)

        bill_senior = calculate_bill(5000, 1500, insurance=False, senior_discount=True)
        self.assertEqual(bill_senior["subtotal"], 6500.0)
        self.assertEqual(bill_senior["insurance_covered"], 0.0)
        self.assertEqual(bill_senior["after_insurance"], 5850.0)
        self.assertEqual(bill_senior["senior_discount"], 650.0)
        self.assertEqual(bill_senior["total"], 5850.0)

    def test_calculate_bill_rejects_invalid_kwargs(self):
        with self.assertRaises(ValueError):
            calculate_bill(5000, 1000, bogus_discount=0.5)

        with self.assertRaises(TypeError):
            calculate_bill(5000, 1000, insurance="yes")

        with self.assertRaises(TypeError):
            calculate_bill(5000, 1000, senior_discount="true")

    def test_calculate_test_charges_case_and_whitespace_normalization(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        cost, errors = calculate_test_charges([" ecg ", "BLOOD TEST"], prices)
        self.assertEqual(cost, 2500.0)
        self.assertEqual(errors, [])

    def test_calculate_test_charges_rejects_duplicates(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        cost, errors = calculate_test_charges(["ECG", "ecg"], prices)
        self.assertEqual(cost, 0.0)
        self.assertTrue(any("Duplicate test" in e for e in errors))

    def test_calculate_test_charges_rejects_non_list(self):
        cost, errors = calculate_test_charges("ECG")
        self.assertEqual(cost, 0.0)
        self.assertTrue(len(errors) > 0)

    def test_validate_appointment_type_guards(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        valid_appt = copy.deepcopy(appointments[0])

        valid, msg = validate_appointment(valid_appt, patients, doctors, prices)
        self.assertTrue(valid)

        bad_patient = copy.deepcopy(patients)
        bad_patient["P001"]["age"] = True
        valid, msg = validate_appointment(valid_appt, bad_patient, doctors, prices)
        self.assertFalse(valid)

        bad_patient["P001"]["age"] = -5
        valid, msg = validate_appointment(valid_appt, bad_patient, doctors, prices)
        self.assertFalse(valid)

        bad_patient["P001"]["insurance"] = "yes"
        valid, msg = validate_appointment(valid_appt, bad_patient, doctors, prices)
        self.assertFalse(valid)

        bad_doctor = copy.deepcopy(doctors)
        bad_doctor["D001"]["fee"] = True
        valid, msg = validate_appointment(valid_appt, patients, bad_doctor, prices)
        self.assertFalse(valid)

        bad_doctor["D001"]["fee"] = -1000
        valid, msg = validate_appointment(valid_appt, patients, bad_doctor, prices)
        self.assertFalse(valid)

        bad_doctor["D001"]["fee"] = float("nan")
        valid, msg = validate_appointment(valid_appt, patients, bad_doctor, prices)
        self.assertFalse(valid)

        whitespace_appt = copy.deepcopy(valid_appt)
        whitespace_appt["patient_id"] = " p001 "
        whitespace_appt["doctor_id"] = " d001 "
        valid, msg = validate_appointment(whitespace_appt, patients, doctors, prices)
        self.assertTrue(valid)

        bad_doctor["D001"]["available"] = "yes"
        valid, msg = validate_appointment(valid_appt, patients, bad_doctor, prices)
        self.assertFalse(valid)

        bad_appt = copy.deepcopy(valid_appt)
        bad_appt["status"] = "unknown_status"
        valid, msg = validate_appointment(bad_appt, patients, doctors, prices)
        self.assertFalse(valid)

    def test_cancellation_rules_and_terminal_immutability(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)

        pending_appt = {
            "appointment_id": "A009",
            "patient_id": "P001",
            "doctor_id": "D001",
            "status": "pending",
            "tests": [],
        }
        test_apps.append(pending_appt)

        ok, msg = cancel_appointment("A009", test_apps)
        self.assertTrue(ok)
        self.assertEqual(pending_appt["status"], "cancelled")

        ok, msg = cancel_appointment("A009", test_apps)
        self.assertFalse(ok)

        ok, msg = cancel_appointment("A001", test_apps)
        self.assertFalse(ok)

        ok, msg = cancel_appointment("NON_EXISTENT", test_apps)
        self.assertFalse(ok)

    def test_process_appointment_isolated_and_duplicate_guard(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)
        processed = set()

        ok, res = process_appointment("A001", test_apps, patients, doctors, prices, processed)
        self.assertTrue(ok)
        self.assertIn("A001", processed)
        self.assertIn("bill", test_apps[0])

        ok, res = process_appointment("A001", test_apps, patients, doctors, prices, processed)
        self.assertFalse(ok)

        ok, res = process_appointment("A003", test_apps, patients, doctors, prices, processed)
        self.assertFalse(ok)

    def test_dashboard_history_and_ledger_balance(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)
        processed = set()

        for a in test_apps:
            process_appointment(a["appointment_id"], test_apps, patients, doctors, prices, processed)

        dashboard = generate_clinic_dashboard(patients, doctors, test_apps)

        self.assertEqual(dashboard["completed_count"], 3)
        self.assertEqual(dashboard["cancelled_count"], 1)
        self.assertEqual(dashboard["total_patient_revenue"], 13100.0)
        self.assertEqual(dashboard["total_senior_discount"], 650.0)
        self.assertEqual(dashboard["total_insurance_coverage"], 2250.0)

        calculated_revenue = (
            dashboard["total_consultation_revenue"]
            + dashboard["total_test_revenue"]
            - dashboard["total_insurance_coverage"]
            - dashboard["total_senior_discount"]
        )
        self.assertEqual(round(calculated_revenue, 2), round(dashboard["total_patient_revenue"], 2))

    def test_report_ties_are_not_hidden(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)
        processed = set()
        for a in test_apps:
            process_appointment(a["appointment_id"], test_apps, patients, doctors, prices, processed)

        doc_rep = generate_doctor_report(doctors, test_apps)
        pat_rep = generate_patient_report(patients, test_apps)

        self.assertIn("Dr. Hassan", doc_rep["most_requested_doctor"])
        self.assertIn("Usman Ali", pat_rep["highest_spending_patient"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

import copy
import math
import unittest
from main import (
    CLINIC_CONFIG,
    calculate_bill,
    calculate_insurance_coverage,
    calculate_test_charges,
    calculate_total,
    cancel_appointment,
    find_duplicate_appointment_ids,
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

        bad_patient["P001"]["age"] = 500
        valid, msg = validate_appointment(valid_appt, bad_patient, doctors, prices)
        self.assertFalse(valid)

        bad_patient["P001"]["age"] = 131
        valid, msg = validate_appointment(valid_appt, bad_patient, doctors, prices)
        self.assertFalse(valid)

        boundary_patient = copy.deepcopy(patients)
        boundary_patient["P001"]["age"] = 130
        valid, msg = validate_appointment(copy.deepcopy(valid_appt), boundary_patient, doctors, prices)
        self.assertTrue(valid)

        bad_patient["P001"]["age"] = 32
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
        whitespace_appt["appointment_id"] = " a001 "
        whitespace_appt["patient_id"] = " p001 "
        whitespace_appt["doctor_id"] = " d001 "
        whitespace_appt["status"] = " COMPLETED "
        valid, msg = validate_appointment(whitespace_appt, patients, doctors, prices)
        self.assertTrue(valid)
        self.assertEqual(whitespace_appt["appointment_id"], "A001")
        self.assertEqual(whitespace_appt["patient_id"], "P001")
        self.assertEqual(whitespace_appt["doctor_id"], "D001")
        self.assertEqual(whitespace_appt["status"], "completed")

        bad_doctor["D001"]["available"] = "yes"
        valid, msg = validate_appointment(valid_appt, patients, bad_doctor, prices)
        self.assertFalse(valid)

        bad_appt = copy.deepcopy(valid_appt)
        bad_appt["status"] = "unknown_status"
        valid, msg = validate_appointment(bad_appt, patients, doctors, prices)
        self.assertFalse(valid)

        blank_id_appt = copy.deepcopy(valid_appt)
        blank_id_appt["appointment_id"] = "   "
        valid, msg = validate_appointment(blank_id_appt, patients, doctors, prices)
        self.assertFalse(valid)

        unhashable_id_appt = copy.deepcopy(valid_appt)
        unhashable_id_appt["patient_id"] = ["P001"]
        unhashable_id_appt["doctor_id"] = {"id": "D001"}
        valid, msg = validate_appointment(unhashable_id_appt, patients, doctors, prices)
        self.assertFalse(valid)

    def test_cancellation_rules_and_terminal_immutability(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)

        pending_appt = {
            "appointment_id": "A009",
            "patient_id": "P001",
            "doctor_id": "D001",
            "status": "Pending",
            "tests": [],
        }
        test_apps.append(pending_appt)

        ok, msg = cancel_appointment(" a009 ", test_apps)
        self.assertTrue(ok)
        self.assertEqual(pending_appt["status"], "cancelled")

        ok, msg = cancel_appointment("A009", test_apps)
        self.assertFalse(ok)

        ok, msg = cancel_appointment("A001", test_apps)
        self.assertFalse(ok)

        ok, msg = cancel_appointment("NON_EXISTENT", test_apps)
        self.assertFalse(ok)

    def test_mixed_case_cancelled_appointment_not_billed(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        for raw_status in ("Cancelled", " cancelled ", "CANCELLED"):
            with self.subTest(raw_status=raw_status):
                test_apps = [
                    {
                        "appointment_id": "C001",
                        "patient_id": "P001",
                        "doctor_id": "D001",
                        "status": raw_status,
                        "tests": ["ECG"],
                    }
                ]
                ok, res = process_appointment("C001", test_apps, patients, doctors, prices)
                self.assertFalse(ok)
                self.assertIn("cancelled", res.lower())
                self.assertNotIn("bill", test_apps[0])
                self.assertEqual(test_apps[0]["status"], "cancelled")

    def test_padded_ids_reconcile_across_reports_and_dashboard(self):
        patients, doctors, _, prices = get_test_fixtures()
        test_apps = [
            {
                "appointment_id": " a001 ",
                "patient_id": " p001 ",
                "doctor_id": " d001 ",
                "status": " completed ",
                "tests": ["ECG", "Blood Test"],
            }
        ]
        ok, res = process_appointment("A001", test_apps, patients, doctors, prices)
        self.assertTrue(ok)
        self.assertEqual(test_apps[0]["patient_id"], "P001")
        self.assertEqual(test_apps[0]["doctor_id"], "D001")

        doc_rep = generate_doctor_report(doctors, test_apps)
        pat_rep = generate_patient_report(patients, test_apps)
        dash = generate_clinic_dashboard(patients, doctors, test_apps)

        self.assertEqual(doc_rep["doctor_details"]["D001"]["completed"], 1)
        self.assertEqual(doc_rep["doctor_details"]["D001"]["revenue"], 5250.0)
        self.assertEqual(pat_rep["patient_details"]["P001"]["completed"], 1)
        self.assertEqual(pat_rep["patient_details"]["P001"]["patient_paid"], 5250.0)
        self.assertNotIn("Ali Khan", pat_rep["no_completed_appointments"])
        self.assertEqual(dash["total_patient_revenue"], 5250.0)

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

    def test_reprocessing_without_set_blocked_by_saved_bill(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)

        ok1, res1 = process_appointment("A001", test_apps, patients, doctors, prices)
        self.assertTrue(ok1)
        self.assertEqual(test_apps[0]["bill"]["total"], 5250.0)

        doctors["D001"]["fee"] = 99999
        ok2, res2 = process_appointment("A001", test_apps, patients, doctors, prices)
        self.assertFalse(ok2)
        self.assertIn("already been processed", res2)
        self.assertEqual(test_apps[0]["bill"]["total"], 5250.0)

    def test_unbilled_rejected_visit_not_counted_as_completed(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)
        doctors["D003"]["available"] = False
        processed = set()

        for a in test_apps:
            process_appointment(a["appointment_id"], test_apps, patients, doctors, prices, processed)

        doc_rep = generate_doctor_report(doctors, test_apps)
        pat_rep = generate_patient_report(patients, test_apps)
        dash = generate_clinic_dashboard(patients, doctors, test_apps)

        self.assertEqual(dash["completed_count"], 2)
        self.assertEqual(dash["unbilled_count"], 1)
        self.assertEqual(dash["total_patient_revenue"], 11100.0)
        self.assertEqual(doc_rep["doctor_details"]["D003"]["completed"], 0)
        self.assertEqual(doc_rep["doctor_details"]["D003"]["unbilled"], 1)
        self.assertEqual(doc_rep["doctor_details"]["D003"]["revenue"], 0.0)
        self.assertEqual(doc_rep["doctor_details"]["D003"]["average_bill"], 0.0)
        self.assertEqual(pat_rep["patient_details"]["P002"]["completed"], 0)
        self.assertIn("Ahmed Raza", pat_rep["no_completed_appointments"])

    def test_duplicate_appointment_id_in_batch_rejected(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)
        test_apps.append(
            {
                "appointment_id": " a001 ",
                "patient_id": "P002",
                "doctor_id": "D002",
                "status": "completed",
                "tests": ["MRI"],
            }
        )

        self.assertEqual(find_duplicate_appointment_ids(test_apps), {"A001"})
        ok_dup, msg_dup = process_appointment("A001", test_apps, patients, doctors, prices)
        self.assertFalse(ok_dup)
        self.assertIn("Duplicate appointment ID", msg_dup)
        self.assertNotIn("already been processed", msg_dup)

        ok_other, _ = process_appointment("A002", test_apps, patients, doctors, prices)
        self.assertTrue(ok_other)

    def test_dashboard_history_and_ledger_balance(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)
        processed = set()

        for a in test_apps:
            process_appointment(a["appointment_id"], test_apps, patients, doctors, prices, processed)

        dashboard = generate_clinic_dashboard(patients, doctors, test_apps)

        self.assertEqual(dashboard["completed_count"], 3)
        self.assertEqual(dashboard["unbilled_count"], 0)
        self.assertEqual(dashboard["cancelled_count"], 1)
        self.assertEqual(dashboard["total_patient_revenue"], 13100.0)
        self.assertEqual(dashboard["total_senior_discount"], 650.0)
        self.assertEqual(dashboard["total_insurance_coverage"], 2250.0)
        self.assertEqual(dashboard["total_tax"], 0.0)

        calculated_revenue = (
            dashboard["total_consultation_revenue"]
            + dashboard["total_test_revenue"]
            - dashboard["total_insurance_coverage"]
            - dashboard["total_senior_discount"]
            + dashboard["total_tax"]
        )
        self.assertEqual(round(calculated_revenue, 2), round(dashboard["total_patient_revenue"], 2))

    def test_nonzero_tax_rate_reconciles_dashboard(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = [copy.deepcopy(appointments[1])]
        original_tax = CLINIC_CONFIG["tax_rate"]
        try:
            CLINIC_CONFIG["tax_rate"] = 0.10
            ok, res = process_appointment("A002", test_apps, patients, doctors, prices)
            self.assertTrue(ok)
            dash = generate_clinic_dashboard(patients, doctors, test_apps)
            self.assertEqual(dash["total_tax"], 200.0)
            self.assertEqual(dash["total_patient_revenue"], 2200.0)
        finally:
            CLINIC_CONFIG["tax_rate"] = original_tax

    def test_report_ties_are_not_hidden(self):
        patients, doctors, appointments, prices = get_test_fixtures()
        test_apps = copy.deepcopy(appointments)
        processed = set()
        for a in test_apps:
            process_appointment(a["appointment_id"], test_apps, patients, doctors, prices, processed)

        doc_rep = generate_doctor_report(doctors, test_apps)
        pat_rep = generate_patient_report(patients, test_apps)

        for name in ("Ali Khan", "Ahmed Raza", "Sara Ahmed", "Usman Ali"):
            self.assertIn(name, pat_rep["patient_with_most_appointments"])

        tied_doctors = {
            "D001": {"name": "Dr. Hassan", "specialization": "Cardiology", "fee": 3000, "available": True},
            "D002": {"name": "Dr. Sara", "specialization": "Dermatology", "fee": 3000, "available": True},
        }
        tied_patients = {
            "P001": {"name": "Ali Khan", "age": 32, "city": "Lahore", "insurance": False},
            "P002": {"name": "Ahmed Raza", "age": 45, "city": "Multan", "insurance": False},
        }
        tied_apps = [
            {"appointment_id": "T1", "patient_id": "P001", "doctor_id": "D001", "status": "completed", "tests": []},
            {"appointment_id": "T2", "patient_id": "P002", "doctor_id": "D002", "status": "completed", "tests": []},
        ]
        for a in tied_apps:
            process_appointment(a["appointment_id"], tied_apps, tied_patients, tied_doctors, prices)

        tied_doc_rep = generate_doctor_report(tied_doctors, tied_apps)
        tied_pat_rep = generate_patient_report(tied_patients, tied_apps)
        self.assertIn("Dr. Hassan", tied_doc_rep["most_requested_doctor"])
        self.assertIn("Dr. Sara", tied_doc_rep["most_requested_doctor"])
        self.assertIn("Ali Khan", tied_pat_rep["highest_spending_patient"])
        self.assertIn("Ahmed Raza", tied_pat_rep["highest_spending_patient"])

    def test_calculate_bill_include_tests_and_insurance_helper(self):
        self.assertEqual(calculate_insurance_coverage(5000, 2500, True), 2250.0)
        self.assertEqual(calculate_insurance_coverage(5000, 2500, False), 0.0)

        bill_default = calculate_bill(5000, insurance=True, senior_discount=True, include_tests=True)
        self.assertEqual(bill_default["total"], 3600.0)

        bill_excluded = calculate_bill(5000, 2500, insurance=True, senior_discount=False, include_tests=False)
        self.assertEqual(bill_excluded["test_charges"], 0.0)
        self.assertEqual(bill_excluded["total"], 4000.0)

        with self.assertRaises(TypeError):
            calculate_bill(5000, 2500, include_tests="yes")

    def test_corrupt_test_catalog_and_empty_structures(self):
        patients, doctors, appointments, _ = get_test_fixtures()
        bad_prices = {"ECG": "free", "MRI": -500}
        cost, errors = calculate_test_charges(["ECG"], bad_prices)
        self.assertEqual(cost, 0.0)
        self.assertTrue(len(errors) > 0)

        valid, reason = validate_appointment(copy.deepcopy(appointments[0]), patients, doctors, bad_prices)
        self.assertFalse(valid)

        empty_doc = generate_doctor_report({}, [])
        empty_pat = generate_patient_report({}, [])
        empty_dash = generate_clinic_dashboard({}, {}, [])
        self.assertEqual(empty_doc["most_requested_doctor"], "None")
        self.assertEqual(empty_pat["highest_spending_patient"], "None")
        self.assertEqual(empty_dash["total_patient_revenue"], 0.0)

    def test_patient_report_and_dashboard_strict_types(self):
        bad_patients = {"P001": {"name": "Ali", "age": 30, "city": "Lahore", "insurance": "no"}}
        pat_rep = generate_patient_report(bad_patients, [])
        self.assertFalse(pat_rep["patient_details"]["P001"]["has_insurance"])
        self.assertEqual(pat_rep["insured_patients"], [])

        corrupt_bill_appts = [
            {
                "appointment_id": "A1",
                "patient_id": "P001",
                "doctor_id": "D001",
                "status": "completed",
                "bill": {
                    "consultation_fee": True,
                    "test_charges": 0.0,
                    "insurance_covered": 0.0,
                    "senior_discount": 0.0,
                    "tax": 0.0,
                    "total": 100.0,
                },
            }
        ]
        with self.assertRaises(TypeError):
            generate_clinic_dashboard(bad_patients, {}, corrupt_bill_appts)


if __name__ == "__main__":
    unittest.main(verbosity=2)

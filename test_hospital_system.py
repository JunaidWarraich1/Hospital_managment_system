import copy
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


class TestHospitalManagementSystem(unittest.TestCase):

    def setUp(self):
        self.patients = {
            "P001": {"name": "Ali Khan", "age": 32, "city": "Lahore", "insurance": True},
            "P002": {"name": "Ahmed Raza", "age": 45, "city": "Multan", "insurance": False},
            "P003": {"name": "Sara Ahmed", "age": 28, "city": "Lahore", "insurance": True},
            "P004": {"name": "Usman Ali", "age": 67, "city": "Islamabad", "insurance": False},
        }

        self.doctors = {
            "D001": {"name": "Dr. Hassan", "specialization": "Cardiology", "fee": 5000, "available": True},
            "D002": {"name": "Dr. Sara", "specialization": "Dermatology", "fee": 3000, "available": True},
            "D003": {"name": "Dr. Ahmed", "specialization": "General", "fee": 2000, "available": True},
        }

        self.appointments = [
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

        self.test_prices = {
            "ECG": 1500,
            "Blood Test": 1000,
            "X-Ray": 2500,
            "MRI": 8000,
        }

    # 1. Charge Calculation & Args Safety
    def test_calculate_total_valid_charges(self):
        self.assertEqual(calculate_total(5000, 1500, 1000), 7500.0)

    def test_calculate_total_rejects_negative_and_non_numeric(self):
        with self.assertRaises(ValueError):
            calculate_total(5000, -100)
        with self.assertRaises(TypeError):
            calculate_total(5000, "1500")
        with self.assertRaises(TypeError):
            calculate_total(5000, True)

    # 2. Kwargs Validation in calculate_bill
    def test_calculate_bill_standard_and_senior(self):
        bill_normal = calculate_bill(5000, 2500, insurance=True, senior_discount=False)
        self.assertEqual(bill_normal["subtotal"], 7500.0)
        self.assertEqual(bill_normal["insurance_covered"], 2250.0)
        self.assertEqual(bill_normal["total"], 5250.0)

        bill_senior = calculate_bill(5000, 2500, insurance=True, senior_discount=True)
        self.assertEqual(bill_senior["insurance_covered"], 2250.0)
        self.assertEqual(bill_senior["senior_discount"], 525.0)
        self.assertEqual(bill_senior["total"], 4725.0)

    def test_calculate_bill_rejects_invalid_kwargs(self):
        with self.assertRaises(ValueError):
            calculate_bill(5000, insurence=True)
        with self.assertRaises(TypeError):
            calculate_bill(5000, insurance="no")
        with self.assertRaises(TypeError):
            calculate_bill(5000, senior_discount="yes")

    # 3. Test Pricing, Deduplication, and Case-Insensitivity
    def test_calculate_test_charges_case_insensitive(self):
        cost, invalids = calculate_test_charges(["ecg", "blood test"], self.test_prices)
        self.assertEqual(cost, 2500.0)
        self.assertEqual(invalids, [])

    def test_calculate_test_charges_rejects_duplicates(self):
        cost, invalids = calculate_test_charges(["ECG", "ECG"], self.test_prices)
        self.assertEqual(cost, 0.0)
        self.assertIn("Duplicate test requested: ECG", invalids[0])

    def test_calculate_test_charges_rejects_non_list(self):
        cost, invalids = calculate_test_charges("ECG", self.test_prices)
        self.assertEqual(cost, 0.0)
        self.assertTrue(len(invalids) > 0)

    # 4. Input Shape & Type Validation in validate_appointment
    def test_validate_appointment_type_guards(self):
        valid, msg = validate_appointment(None)
        self.assertFalse(valid)

        corrupt_patients = copy.deepcopy(self.patients)
        corrupt_patients["P001"]["age"] = True
        t_age_bool = copy.deepcopy(self.appointments[0])
        valid, msg = validate_appointment(t_age_bool, corrupt_patients, self.doctors, self.test_prices)
        self.assertFalse(valid)
        self.assertIn("invalid age", msg)

        corrupt_patients["P001"]["age"] = "32"
        valid, msg = validate_appointment(t_age_bool, corrupt_patients, self.doctors, self.test_prices)
        self.assertFalse(valid)

        corrupt_patients["P001"]["age"] = 32
        corrupt_patients["P001"]["insurance"] = "no"
        valid, msg = validate_appointment(t_age_bool, corrupt_patients, self.doctors, self.test_prices)
        self.assertFalse(valid)
        self.assertIn("invalid insurance flag", msg)

        corrupt_doctors = copy.deepcopy(self.doctors)
        corrupt_doctors["D001"]["fee"] = "5000"
        valid, msg = validate_appointment(t_age_bool, self.patients, corrupt_doctors, self.test_prices)
        self.assertFalse(valid)
        self.assertIn("invalid consultation fee", msg)

        corrupt_doctors["D001"]["fee"] = -100
        valid, msg = validate_appointment(t_age_bool, self.patients, corrupt_doctors, self.test_prices)
        self.assertFalse(valid)

        corrupt_doctors["D001"]["fee"] = 5000
        corrupt_doctors["D001"]["available"] = "no"
        valid, msg = validate_appointment(t_age_bool, self.patients, corrupt_doctors, self.test_prices)
        self.assertFalse(valid)
        self.assertIn("currently unavailable", msg)

    # 5. State Machine & Cancellation Rules
    def test_cancellation_rules(self):
        test_apps = copy.deepcopy(self.appointments)
        test_apps.append({
            "appointment_id": "A099",
            "patient_id": "P001",
            "doctor_id": "D001",
            "status": "pending",
            "tests": [],
        })

        success, msg = cancel_appointment("A099", test_apps)
        self.assertTrue(success)

        success, msg = cancel_appointment("A001", test_apps)
        self.assertFalse(success)
        self.assertIn("completed and cannot be cancelled", msg)

        success, msg = cancel_appointment("A003", test_apps)
        self.assertFalse(success)
        self.assertIn("already cancelled", msg)

    # 6. Isolated Processing & Double Billing Prevention
    def test_process_appointment_isolated(self):
        test_apps = copy.deepcopy(self.appointments)
        processed = set()

        success, res = process_appointment("A001", test_apps, self.patients, self.doctors, self.test_prices, processed)
        self.assertTrue(success)
        self.assertEqual(res["bill"]["total"], 5250.0)

        success_dup, msg_dup = process_appointment("A001", test_apps, self.patients, self.doctors, self.test_prices, processed)
        self.assertFalse(success_dup)
        self.assertIn("already been processed", msg_dup)

    # 7. Dashboard History Immutability & Ledger Balance
    def test_dashboard_history_and_ledger_balance(self):
        test_apps = copy.deepcopy(self.appointments)
        doctors_copy = copy.deepcopy(self.doctors)
        processed = set()

        for a in test_apps:
            process_appointment(a["appointment_id"], test_apps, self.patients, doctors_copy, self.test_prices, processed)

        # Mutate doctor fee after processing
        doctors_copy["D001"]["fee"] = 99999

        dashboard = generate_clinic_dashboard(self.patients, doctors_copy, test_apps)

        # Consultation revenue must stay 12,000 from historical snapshot, NOT jump to 200k+
        self.assertEqual(dashboard["total_consultation_revenue"], 12000.0)
        self.assertEqual(dashboard["total_test_revenue"], 4000.0)
        self.assertEqual(dashboard["total_insurance_coverage"], 2250.0)
        self.assertEqual(dashboard["total_senior_discount"], 650.0)
        self.assertEqual(dashboard["total_patient_revenue"], 13100.0)

        # Ledger Balance Sheet Invariant:
        # Consultation + Tests - Insurance - Senior Discount == Patient Revenue
        calculated_patient_revenue = (
            dashboard["total_consultation_revenue"]
            + dashboard["total_test_revenue"]
            - dashboard["total_insurance_coverage"]
            - dashboard["total_senior_discount"]
        )
        self.assertAlmostEqual(calculated_patient_revenue, dashboard["total_patient_revenue"], places=2)

    # 8. Report Ties Handling
    def test_report_ties_are_not_hidden(self):
        test_apps = copy.deepcopy(self.appointments)
        processed = set()
        for a in test_apps:
            process_appointment(a["appointment_id"], test_apps, self.patients, self.doctors, self.test_prices, processed)

        doc_rep = generate_doctor_report(self.doctors, test_apps)
        pat_rep = generate_patient_report(self.patients, test_apps)

        self.assertIn("Dr. Hassan", doc_rep["most_requested_doctor"])
        self.assertIn("Usman Ali", pat_rep["highest_spending_patient"])


if __name__ == "__main__":
    unittest.main()

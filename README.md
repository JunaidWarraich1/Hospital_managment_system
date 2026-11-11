# Hospital Appointment & Billing Management System
Real-World Problem-Solving Assessment | Python Core Logic

---

## 1. Project Overview
This project implements the core business logic for a clinic appointment and billing management system in pure Python. The system handles patient scheduling, doctor consultations, medical tests, insurance coverage rules, senior citizen discounts, state-machine cancellation workflows, analytical reporting, and executive dashboards.

---

## 2. Architecture & Design Decisions

### 2.1 Pure Functional Core (Zero OOP in Domain Logic)
Per assignment restrictions, the clinic system in `main.py` uses zero classes or external packages and communicates strictly via native Python data structures (while `test_hospital_system.py` uses Python's built-in `unittest.TestCase` harness):
- **Canonical Input Normalization:** `normalize_id`, `normalize_status`, and `normalize_appointment` normalize IDs (`.strip().upper()`) and statuses (`.strip().lower()`) consistently across validation, processing, cancellation, and reporting.
- **No Global State Mutation & Dual Idempotency:** Functions accept state collections explicitly (`processed_ids` parameter), and `process_appointment` also refuses re-processing whenever an appointment already contains a `"bill"`, guaranteeing protection even if a caller omits `processed_ids`.
- **Duplicate Batch ID Guard:** `find_duplicate_appointment_ids` and `process_appointment` detect and reject duplicate `appointment_id` entries across the appointment list rather than silently processing one and hiding the rest.
- **Historical Billing Snapshot & Billed Completion Counting:** Processed visits store immutable bill dictionaries, and reports/dashboards count a visit as `completed` only when it carries a valid saved `"bill"` (rejected visits with seeded `"completed"` status are tracked under `unbilled`).

### 2.2 LEGB Scope Design
Python's LEGB (Local, Enclosing, Global, Built-in) resolution order is respected:
- **Global Scope (`CLINIC_CONFIG`):** Centralizes clinic settings including `"currency": "PKR "`, `"senior_age_threshold": 60`, `"senior_discount_rate": 0.10`, `"insurance_consultation_coverage": 0.20`, `"insurance_test_coverage": 0.50`, and `"tax_rate": 0.0` (an extensible `0.0` placeholder representing tax-exempt healthcare billing; if modified to a positive rate, `calculate_bill` and `generate_clinic_dashboard` automatically apply and reconcile `total_tax`).
- **Immutability:** Functions read configuration parameters without using the `global` keyword.

### 2.3 Python Fundamentals
- **`*args` Aggregator (`calculate_total`):** Accepts arbitrary numbers of charges, strictly verifies numeric types, rejects booleans, negatives, `NaN`, and `inf`, and returns a validated sum.
- **`**kwargs` Configurable Billing Engine (`calculate_bill`):** Delegates coverage computation to `calculate_insurance_coverage` and accepts validated keyword arguments (`insurance=True`, `senior_discount=True`, `include_tests=True`), rejecting unknown keys and non-boolean options.
- **`lambda` Expressions:** Used in doctor and patient reports to sort records by appointment frequency, revenue, and spending.
- **Comprehensions:** List and dictionary comprehensions filter billed completed visits, unbilled visits, cancellations, insured patients, and senior citizens cleanly.
- **Tie Handling:** Reporting functions detect ties (e.g., all four patients sharing the maximum appointment count) and return all qualifying names.

---

## 3. Core Business & Billing Rules

1. **Subtotal:** Consultation fee + Medical test charges.
2. **Insurance Coverage:**
   - 20% of doctor consultation fee.
   - 50% of medical test charges.
   - Total Covered = `(Doctor Fee * 0.20) + (Test Charges * 0.50)`
3. **Senior Citizen Discount (Age >= 60):**
   - Applies an additional 10% discount strictly after insurance coverage is deducted:
   - `Senior Discount = (Subtotal - Insurance Covered) * 0.10`
4. **Ledger Balance Sheet Invariant:**
   - `Patient Revenue = Consultation Revenue + Test Revenue - Insurance Coverage - Senior Discount + Tax`
5. **State-Machine Transition & Cancellation:**
   - Completed appointments cannot be cancelled.
   - Cancelled appointments (including mixed-case/padded values like `"Cancelled"`) cannot be billed or re-cancelled.
   - Processing an already-billed appointment twice is strictly blocked regardless of whether `processed_ids` is passed.

---

## 4. Input Validation & Edge Case Protections

| Edge Case / Probe | Handling Mechanism |
|---|---|
| Non-numeric, boolean, `NaN`, or `inf` fee (`"5000"`, `True`) | `validate_appointment` returns `(False, reason)`; `calculate_total` and `calculate_bill` raise `TypeError` / `ValueError` |
| Negative fee or charges (`-5000`) | `validate_appointment` returns `(False, reason)`; `calculate_total` and `calculate_bill` raise `ValueError` |
| Invalid or unrealistic age (`True`, `"30"`, `0`, `500`) | Checked via `not isinstance(age, bool) and isinstance(age, int) and 0 < age <= 130`; `validate_appointment` returns `(False, reason)` |
| String boolean flags (`insurance="no"`, `available="yes"`) | `validate_appointment` returns `(False, reason)`; `calculate_bill` raises `TypeError` |
| Unhashable ID payloads (`["P001"]`, `{"id": "D001"}`) | Guarded in `resolve_record` / `normalize_id`; safely returns `(False, reason)` without raising `TypeError` |
| Non-list test payload (`tests="ECG"`) | `calculate_test_charges` returns `(0.0, errors)`; `validate_appointment` returns `(False, reason)` |
| Duplicate or unknown test requests | Case-insensitively detected and rejected cleanly |
| Messy casing / whitespace (`"Cancelled"`, `"Pending"`, `" p001 "`) | Normalized cleanly across validation, cancellation, billing, and all reports |
| Duplicate `appointment_id` in batch | Detected by `find_duplicate_appointment_ids` and rejected by `process_appointment` / `cancel_appointment` |
| Typo in `**kwargs` (`insurence=True`) | Checked against allowed keys set in `calculate_bill`; raises `ValueError` |
| Doctor fee raised after billing or second call without `processed_ids` | Blocked by saved `"bill"` guard; dashboard revenue uses historical bill snapshots |
| Zero appointments safety | Guarded with conditional length checks to prevent `ZeroDivisionError` |

---

## 5. Live Execution & Sample Output

### Main Application Run (`python main.py`)
```text
========================================
      PROCESSING APPOINTMENTS
========================================
[SUCCESS] App ID: A001 | Patient: Ali Khan | Doctor: Dr. Hassan
          Subtotal: PKR 7,500.00 | Insurance: PKR 2,250.00 | Senior Disc: PKR 0.00 | Paid: PKR 5,250.00
[SUCCESS] App ID: A002 | Patient: Ahmed Raza | Doctor: Dr. Ahmed
          Subtotal: PKR 2,000.00 | Insurance: PKR 0.00 | Senior Disc: PKR 0.00 | Paid: PKR 2,000.00
[REJECTED] App ID: A003 | Appointment A003 is cancelled and cannot be processed
[SUCCESS] App ID: A004 | Patient: Usman Ali | Doctor: Dr. Hassan
          Subtotal: PKR 6,500.00 | Insurance: PKR 0.00 | Senior Disc: PKR 650.00 | Paid: PKR 5,850.00


========================================
            DOCTOR REPORT
========================================
D001 | Dr. Hassan (Cardiology) | Total: 2 | Completed: 2 | Unbilled: 0 | Cancelled: 0 | Revenue: PKR 11,100.00 | Avg Bill: PKR 5,550.00
D002 | Dr. Sara (Dermatology) | Total: 1 | Completed: 0 | Unbilled: 0 | Cancelled: 1 | Revenue: PKR 0.00 | Avg Bill: PKR 0.00
D003 | Dr. Ahmed (General) | Total: 1 | Completed: 1 | Unbilled: 0 | Cancelled: 0 | Revenue: PKR 2,000.00 | Avg Bill: PKR 2,000.00
Most Requested Doctor: Dr. Hassan
Most Requested Specialization: Cardiology
========================================


========================================
            PATIENT REPORT
========================================
P001 | Ali Khan (Age: 32, Insured) | Total: 1 | Completed: 1 | Unbilled: 0 | Cancelled: 0 | Charges: PKR 7,500.00 | Insurance: PKR 2,250.00 | Paid: PKR 5,250.00
P002 | Ahmed Raza (Age: 45, Self-Pay) | Total: 1 | Completed: 1 | Unbilled: 0 | Cancelled: 0 | Charges: PKR 2,000.00 | Insurance: PKR 0.00 | Paid: PKR 2,000.00
P003 | Sara Ahmed (Age: 28, Insured) | Total: 1 | Completed: 0 | Unbilled: 0 | Cancelled: 1 | Charges: PKR 0.00 | Insurance: PKR 0.00 | Paid: PKR 0.00
P004 | Usman Ali (Age: 67, Self-Pay) | Total: 1 | Completed: 1 | Unbilled: 0 | Cancelled: 0 | Charges: PKR 6,500.00 | Insurance: PKR 0.00 | Paid: PKR 5,850.00
Highest Spending Patient: Usman Ali
Patient with Most Appointments: Ali Khan, Ahmed Raza, Sara Ahmed, Usman Ali
No Completed Appointments: Sara Ahmed
Insured Patients: Ali Khan, Sara Ahmed
Senior Patients: Usman Ali
========================================


========================================
           CLINIC DASHBOARD
========================================
Total Patients: 4
Total Doctors: 3
Total Appointments: 4
Completed: 3
Unbilled: 0
Cancelled: 1
Pending: 0
Total Consultation Revenue: PKR 12,000.00
Total Test Revenue: PKR 4,000.00
Total Insurance Coverage: PKR 2,250.00
Total Senior Discount: PKR 650.00
Total Tax: PKR 0.00
Total Patient Revenue: PKR 13,100.00
Most Requested Specialization: Cardiology
Highest Spending Patient: Usman Ali
========================================
```

### Automated Unit Test Suite (`python -m unittest`)
```text
.....................
----------------------------------------------------------------------
Ran 21 tests in 0.016s

OK
```

---

## 6. How to Run

### Run the Clinic Application:
```bash
python main.py
```

### Run the Automated Test Suite (unittest):
```bash
python -m unittest
# or
python test_hospital_system.py
```

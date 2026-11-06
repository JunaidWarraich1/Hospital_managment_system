# Hospital Appointment & Billing Management System
Real-World Problem-Solving Assessment | Python Core Logic

---

## 1. Project Overview
This project implements the core business logic for a clinic appointment and billing management system in pure Python. The system handles patient scheduling, doctor consultations, medical tests, insurance coverage rules, senior citizen discounts, state-machine cancellation workflows, analytical reporting, and executive dashboards.

---

## 2. Architecture & Design Decisions

### 2.1 Pure Functional Architecture (Zero OOP & Zero Global State)
Per assignment restrictions, no classes or external packages are used. The architecture is structured into pure, deterministic functions that communicate via native Python data structures:
- **No Global Mutation:** Functions do not depend on or mutate global module state. State tracking (`processed_ids`) is injected as a parameter, ensuring complete test isolation.
- **Historical Billing Snapshot:** When an appointment is processed, the consultation fee, test charges, insurance coverage, and senior discounts are preserved directly inside the bill dictionary. The dashboard aggregates revenue strictly from historical bill snapshots rather than recalculating from live doctor fees.

### 2.2 LEGB Scope Design
Python's LEGB (Local, Enclosing, Global, Built-in) resolution order is respected:
- **Global Scope (`CLINIC_CONFIG`):** A centralized configuration dictionary defines business constants (tax rate, senior discount percentage, age threshold, insurance coverage percentages, currency).
- **Immutability:** Functions read configuration parameters without modifying global state or using the `global` keyword.

### 2.3 Python Fundamentals
- **`*args` Aggregator (`calculate_total`):** Accepts arbitrary numbers of charges, strictly verifies numeric types, rejects negative numbers and booleans, and returns a validated sum.
- **`**kwargs` Configurable Billing Engine (`calculate_bill`):** Accepts validated keyword arguments (`insurance=True`, `senior_discount=True`), rejecting unknown keys and type anomalies.
- **`lambda` Expressions:** Used in doctor and patient reports to sort records by appointment frequency, revenue, and spending.
- **Comprehensions:** List and dictionary comprehensions filter completed visits, cancellations, insured patients, and senior citizens cleanly.
- **Tie Handling:** Reporting functions detect ties (e.g., multiple patients with the same maximum appointments) and return all qualifying names.

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
   - `Patient Revenue = Consultation Revenue + Test Revenue - Insurance Coverage - Senior Discount`
5. **State-Machine Transition & Cancellation:**
   - Completed appointments cannot be cancelled.
   - Cancelled appointments cannot be re-processed.
   - Processing an appointment twice is strictly blocked.

---

## 4. Input Validation & Edge Case Protections

| Edge Case / Probe | Handling Mechanism |
|---|---|
| Non-numeric or boolean fee (`"5000"`, `True`) | Rejected in `validate_appointment` and `calculate_total` with `TypeError` |
| Negative fee or charges (`-5000`) | Rejected with `ValueError` |
| Non-boolean age (`True`, `"30"`) | Checked with `isinstance(age, int) and not isinstance(age, bool) and age > 0` |
| String boolean flags (`insurance="no"`) | Rejected with `TypeError` in `calculate_bill` and `validate_appointment` |
| Non-list test payload (`tests="ECG"`) | Rejected with clear formatting error |
| Duplicate test requests | Case-insensitively identified and rejected |
| Case-insensitive test lookup | Normalized lookup matches `"ecg"` to `"ECG"` at correct price |
| Typo in `**kwargs` (`insurence=True`) | Checked against allowed keys set; raises `ValueError` |
| Doctor fee raised after billing | Historical bills preserve snapshot fees; dashboard revenue is immutable |
| Zero appointments safety | Guarded with conditional length checks to prevent `ZeroDivisionError` |

---

## 5. Live Execution & Sample Output

### Main Application Run (`python main.py`)
```text
========================================
      PROCESSING APPOINTMENTS
========================================
[SUCCESS] App ID: A001 | Patient: Ali Khan | Doctor: Dr. Hassan
          Subtotal: $7,500.00 | Insurance: $2,250.00 | Senior Disc: $0.00 | Paid: $5,250.00
[SUCCESS] App ID: A002 | Patient: Ahmed Raza | Doctor: Dr. Ahmed
          Subtotal: $2,000.00 | Insurance: $0.00 | Senior Disc: $0.00 | Paid: $2,000.00
[REJECTED] App ID: A003 | Appointment A003 is cancelled and cannot be processed
[SUCCESS] App ID: A004 | Patient: Usman Ali | Doctor: Dr. Hassan
          Subtotal: $6,500.00 | Insurance: $0.00 | Senior Disc: $650.00 | Paid: $5,850.00


========================================
           CLINIC DASHBOARD
========================================
Total Patients: 4
Total Doctors: 3
Total Appointments: 4
Completed: 3
Cancelled: 1
Pending: 0
Total Consultation Revenue: $12,000.00
Total Test Revenue: $4,000.00
Total Insurance Coverage: $2,250.00
Total Senior Discount: $650.00
Total Patient Revenue: $13,100.00
Most Requested Specialization: Cardiology
Highest Spending Patient: Usman Ali
========================================
```

### Automated Unit Test Suite (`python -m unittest`)
```text
............
----------------------------------------------------------------------
Ran 12 tests in 0.005s

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

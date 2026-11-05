# Hospital Appointment & Billing Management System
**Real-World Problem-Solving Assessment | Python Core Logic**

---

## 1. Project Overview
This project implements the core business logic for a clinic appointment and billing management system in pure Python. The system handles patient scheduling, doctor consultations, medical tests, insurance coverage rules, senior citizen discounts, state-machine cancellation workflows, analytical reporting, and executive dashboards.

---

## 2. Architecture & Design Decisions

### 2.1 Pure Functional / Procedural Architecture (Zero OOP)
Per assignment restrictions, no classes (`class`) or external packages were used. The architecture is structured into pure, deterministic functions that communicate via native Python data structures (`dict`, `list`, `tuple`, `set`).

### 2.2 LEGB Scope Design
Python's LEGB (Local, Enclosing, Global, Built-in) resolution order was leveraged cleanly:
- **Global Scope (`CLINIC_CONFIG`):** A centralized configuration dictionary defines business constants (tax rate, senior discount percentage, age threshold, insurance coverage percentages, currency).
- **No Global Mutations:** Functions read from `CLINIC_CONFIG` without modifying global state or using the `global` keyword, maintaining immutability and testability.

### 2.3 Advanced Python Fundamentals
- **`*args` Aggregator (`calculate_total`):** Accepts arbitrary numbers of numerical charges, filters invalid/negative values, and returns a safe total sum.
- **`**kwargs` Configurable Billing Engine (`calculate_bill`):** Accepts dynamic keyword arguments (`insurance=True`, `senior_discount=True`) to configure calculations dynamically without rigid function signatures.
- **`lambda` Expressions:** Used in `generate_doctor_report` and `generate_patient_report` to sort nested dictionary records by total appointments, revenue, and spending.
- **Comprehensions:** List comprehensions filter completed/cancelled appointments, insured patients, and senior citizens cleanly and declaratively.

---

## 3. Core Business & Billing Rules

1. **Subtotal:** Consultation fee + Medical test charges.
2. **Insurance Coverage:**
   - 20% of doctor consultation fee.
   - 50% of test charges.
   - Total Covered = `(Doctor Fee * 0.20) + (Test Charges * 0.50)`
3. **Senior Citizen Discount (Age >= 60):**
   - Applies an additional **10% discount** strictly **after** insurance coverage is deducted:
   $$\text{Senior Discount} = (\text{Subtotal} - \text{Insurance Covered}) \times 0.10$$
4. **State-Machine Transition & Cancellation:**
   - Completed appointments cannot be cancelled.
   - Cancelled appointments cannot be re-processed.
   - Duplicate appointment IDs are intercepted and rejected.

---

## 4. Edge Cases Handled

| # | Edge Case | Handling Mechanism |
|---|---|---|
| 1 | Nonexistent Patient ID | Caught by `validate_appointment`; returns descriptive rejection. |
| 2 | Nonexistent Doctor ID | Validated against `doctors` dataset before scheduling. |
| 3 | Doctor Unavailable | Checks `doctor["available"]`; rejects if `False`. |
| 4 | Invalid Test Requested | Cross-referenced with `test_prices`; flagged and rejected. |
| 5 | Duplicate Tests | Automatically deduplicated via `set(test_list)` to avoid double-billing. |
| 6 | Empty Test List | Safely returns `0, []` charges without unpacking errors. |
| 7 | Negative / Zero Age | Rejected during validation before any billing calculation. |
| 8 | Invalid Appointment Status | Enforces membership in `{"completed", "pending", "cancelled"}`. |
| 9 | Cancel Completed Visit | Rejected: completed visits are immutable. |
| 10 | Process Cancelled Visit | Rejected: cancelled appointments cannot be re-processed. |
| 11 | Duplicate Processing | Tracked via `processed_appointments` set; prevents duplicate billing. |
| 12 | Zero Appointments Safety | Guarded with conditional denominators (`len(completed) if completed else 0.0`) to avoid `ZeroDivisionError`. |
| 13 | Empty Datasets | Safe fallbacks returning `"None"` or empty aggregates. |

---

## 5. Live Execution & Sample Output

```text
========================================
      PROCESSING APPOINTMENTS
========================================
[SUCCESS] App ID: A001 | Patient: Ali Khan | Doctor: Dr. Hassan
          Subtotal: $7500 | Insurance Covered: $2250.0 | Paid: $5250.0
[SUCCESS] App ID: A002 | Patient: Ahmed Raza | Doctor: Dr. Ahmed
          Subtotal: $2000 | Insurance Covered: $0.0 | Paid: $2000.0
[REJECTED] App ID: A003 | Appointment A003 is cancelled and cannot be processed
[SUCCESS] App ID: A004 | Patient: Usman Ali | Doctor: Dr. Hassan
          Subtotal: $6500 | Insurance Covered: $0.0 | Paid: $5850.0


========================================
           CLINIC DASHBOARD
========================================
Total Patients: 4
Total Doctors: 3
Total Appointments: 4
Completed: 3
Cancelled: 1
Pending: 0
Total Consultation Revenue: $12000.00
Total Test Revenue: $4000.00
Total Insurance Coverage: $2250.00
Total Patient Revenue: $13100.00
Most Requested Specialization: Cardiology
Highest Spending Patient: Usman Ali
========================================

========================================
      RUNNING EDGE CASE TEST SUITE
========================================
Test 01 - Invalid Patient: PASS | Patient P999 does not exist
Test 02 - Invalid Doctor: PASS | Doctor D999 does not exists
Test 03 - Doctor Unavailable: PASS | Doctor Dr. Busy is currently unavailable
Test 04 - Invalid Test: PASS | Invalid tests requested: NonExistentTest
Test 05 - Duplicate Test Deduplication: PASS | Cost: 1500
Test 06 - Empty Test List: PASS | Cost: 0
Test 07 - Negative Age: PASS | patient P998 has invalid age
Test 08 - Invalid Status: PASS | Invalid appointment status: unknown_status
Test 09 - Cancel Completed: PASS | Appointment A001 is completed and cannot be cancelled
Test 10 - Process Cancelled: PASS | Appointment A003 is cancelled and cannot be processed
Test 11 - Re-process Duplicate: PASS | Appointment A001 has already been processed
Test 12 - Zero Appointments Safety: PASS | Avg Bill: 0.0
Test 13 - Empty Datasets: PASS
========================================
```

---

## 6. How to Run
Ensure Python 3.10+ is installed. Run directly from the terminal:
```bash
python main.py
```

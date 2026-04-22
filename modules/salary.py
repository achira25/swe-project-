"""
Salary Calculation Engine
Handles all payroll computations: allowances, deductions, taxes, LOP.
"""

# ─────────────────────────────────────────────
#  ALLOWANCE STRUCTURE (% of Basic)
# ─────────────────────────────────────────────

HRA_PERCENT = 0.40          # 40% of basic (metro; adjust as needed)
DA_PERCENT = 0.10           # 10% of basic
MEDICAL_ALLOWANCE = 1250    # Fixed ₹1,250/month
TRANSPORT_ALLOWANCE = 1600  # Fixed ₹1,600/month (tax-exempt up to ₹1,600)
OVERTIME_RATE_MULTIPLIER = 2.0  # 2x hourly rate for overtime

# ─────────────────────────────────────────────
#  DEDUCTION STRUCTURE
# ─────────────────────────────────────────────

PF_EMPLOYEE_PERCENT = 0.12   # 12% of basic
PF_EMPLOYER_PERCENT = 0.12   # 12% of basic (employer share, informational)
PF_CEILING = 15000           # PF calculated on max ₹15,000 basic
ESI_EMPLOYEE_PERCENT = 0.0075  # 0.75% of gross (if gross <= ₹21,000)
ESI_CEILING = 21000           # ESI applicable if gross <= ₹21,000
PROFESSIONAL_TAX_SLABS = [    # Monthly professional tax slabs (generic)
    (10000, 0),
    (15000, 150),
    (20000, 200),
    (float("inf"), 200),
]

# Annual income tax slabs (new regime FY 2024-25)
INCOME_TAX_SLABS = [
    (300000, 0.00),
    (600000, 0.05),
    (900000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float("inf"), 0.30),
]
STANDARD_DEDUCTION = 50000
BASIC_EXEMPTION = 300000


def calculate_allowances(basic: float) -> dict:
    hra = round(basic * HRA_PERCENT, 2)
    da = round(basic * DA_PERCENT, 2)
    medical = MEDICAL_ALLOWANCE
    transport = TRANSPORT_ALLOWANCE
    return {
        "hra": hra,
        "da": da,
        "medical_allowance": medical,
        "transport_allowance": transport,
    }


def calculate_overtime(basic: float, overtime_hours: float, working_days: int = 26) -> float:
    if overtime_hours <= 0:
        return 0.0
    daily_rate = basic / working_days
    hourly_rate = daily_rate / 8
    return round(hourly_rate * overtime_hours * OVERTIME_RATE_MULTIPLIER, 2)


def calculate_lop_deduction(basic: float, lop_days: int, working_days: int = 26) -> float:
    if lop_days <= 0:
        return 0.0
    return round((basic / working_days) * lop_days, 2)


def calculate_pf(basic: float, pf_applicable: bool = True) -> dict:
    if not pf_applicable:
        return {"pf_employee": 0, "pf_employer": 0}
    pf_base = min(basic, PF_CEILING)
    pf_employee = round(pf_base * PF_EMPLOYEE_PERCENT, 2)
    pf_employer = round(pf_base * PF_EMPLOYER_PERCENT, 2)
    return {"pf_employee": pf_employee, "pf_employer": pf_employer}


def calculate_esi(gross: float) -> float:
    if gross <= ESI_CEILING:
        return round(gross * ESI_EMPLOYEE_PERCENT, 2)
    return 0.0


def calculate_professional_tax(gross: float) -> float:
    for limit, tax in PROFESSIONAL_TAX_SLABS:
        if gross <= limit:
            return float(tax)
    return 200.0


def calculate_income_tax(annual_gross: float, pf_annual: float) -> float:
    """Simple new-regime tax calculation (monthly deduction = annual / 12)."""
    taxable = max(annual_gross - STANDARD_DEDUCTION - pf_annual - BASIC_EXEMPTION, 0)
    tax = 0.0
    prev_limit = 0
    for limit, rate in INCOME_TAX_SLABS:
        if taxable <= 0:
            break
        slab_income = min(taxable, limit - prev_limit) if limit != float("inf") else taxable
        tax += slab_income * rate
        taxable -= slab_income
        prev_limit = limit
    # Rebate u/s 87A: no tax if taxable income <= ₹7L (new regime)
    if (annual_gross - STANDARD_DEDUCTION - pf_annual) <= 700000:
        tax = 0.0
    monthly_tax = round(tax / 12, 2)
    return monthly_tax


def calculate_full_salary(
    basic: float,
    working_days: int,
    present_days: int,
    overtime_hours: float,
    leaves_taken: int,
    paid_leave_balance: int,
    other_allowances: float,
    other_deductions: float,
    pf_applicable: bool,
) -> dict:
    """
    Master salary calculation function.
    Returns a complete breakdown of earnings and deductions.
    """

    # --- Attendance ---
    paid_leaves_used = min(leaves_taken, paid_leave_balance)
    lop_days = max(leaves_taken - paid_leaves_used, 0)
    paid_days = present_days + paid_leaves_used
    attendance_pct = round((paid_days / working_days) * 100, 2) if working_days else 100

    # --- Basic after LOP ---
    lop_deduction = calculate_lop_deduction(basic, lop_days, working_days)
    adjusted_basic = round(basic - lop_deduction, 2)

    # --- Allowances ---
    allowances = calculate_allowances(adjusted_basic)
    overtime_pay = calculate_overtime(adjusted_basic, overtime_hours, working_days)

    gross_salary = round(
        adjusted_basic
        + allowances["hra"]
        + allowances["da"]
        + allowances["medical_allowance"]
        + allowances["transport_allowance"]
        + overtime_pay
        + other_allowances,
        2,
    )

    # --- Deductions ---
    pf = calculate_pf(adjusted_basic, pf_applicable)
    esi = calculate_esi(gross_salary)
    prof_tax = calculate_professional_tax(gross_salary)

    annual_gross = gross_salary * 12
    annual_pf = pf["pf_employee"] * 12
    income_tax = calculate_income_tax(annual_gross, annual_pf)

    total_deductions = round(
        pf["pf_employee"] + esi + prof_tax + income_tax + other_deductions,
        2,
    )
    net_salary = round(gross_salary - total_deductions, 2)

    return {
        # Basic info
        "basic_salary": adjusted_basic,
        # Earnings
        "hra": allowances["hra"],
        "da": allowances["da"],
        "medical_allowance": allowances["medical_allowance"],
        "transport_allowance": allowances["transport_allowance"],
        "other_allowances": other_allowances,
        "overtime_hours": overtime_hours,
        "overtime_pay": overtime_pay,
        "gross_salary": gross_salary,
        # Deductions
        "pf_employee": pf["pf_employee"],
        "pf_employer": pf["pf_employer"],
        "esi": esi,
        "income_tax": income_tax,
        "professional_tax": prof_tax,
        "other_deductions": other_deductions,
        "total_deductions": total_deductions,
        "net_salary": net_salary,
        # Attendance
        "working_days": working_days,
        "present_days": present_days,
        "leaves_taken": leaves_taken,
        "paid_leaves_used": paid_leaves_used,
        "lop_days": lop_days,
        "lop_deduction": lop_deduction,
        "attendance_percentage": attendance_pct,
    }

import sqlite3
import os
from datetime import datetime

DB_PATH = "payroll.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            date_of_joining TEXT NOT NULL,
            basic_salary REAL NOT NULL,
            pan_number TEXT,
            bank_account TEXT,
            bank_name TEXT,
            ifsc_code TEXT,
            pf_applicable INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Payroll records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payroll_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            basic_salary REAL NOT NULL,
            hra REAL DEFAULT 0,
            da REAL DEFAULT 0,
            medical_allowance REAL DEFAULT 0,
            transport_allowance REAL DEFAULT 0,
            other_allowances REAL DEFAULT 0,
            overtime_hours REAL DEFAULT 0,
            overtime_pay REAL DEFAULT 0,
            gross_salary REAL NOT NULL,
            pf_employee REAL DEFAULT 0,
            pf_employer REAL DEFAULT 0,
            esi REAL DEFAULT 0,
            income_tax REAL DEFAULT 0,
            professional_tax REAL DEFAULT 0,
            other_deductions REAL DEFAULT 0,
            total_deductions REAL NOT NULL,
            net_salary REAL NOT NULL,
            working_days INTEGER DEFAULT 26,
            present_days INTEGER DEFAULT 26,
            leaves_taken INTEGER DEFAULT 0,
            paid_leaves_used INTEGER DEFAULT 0,
            lop_days INTEGER DEFAULT 0,
            attendance_percentage REAL DEFAULT 100,
            status TEXT DEFAULT 'Processed',
            processed_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
            UNIQUE(emp_id, month, year)
        )
    """)

    # Departments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            head TEXT,
            budget REAL DEFAULT 0
        )
    """)

    # Leave records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            days INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Approved',
            applied_on TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
    """)

    # Insert default departments
    default_departments = [
        ("Engineering",), ("Human Resources",), ("Finance",),
        ("Marketing",), ("Operations",), ("Sales",), ("IT",), ("Legal",)
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO departments (name) VALUES (?)",
        default_departments
    )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  EMPLOYEE CRUD
# ─────────────────────────────────────────────

def add_employee(data: dict) -> tuple[bool, str]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employees
            (emp_id, name, department, designation, email, phone,
             date_of_joining, basic_salary, pan_number, bank_account,
             bank_name, ifsc_code, pf_applicable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["emp_id"], data["name"], data["department"],
            data["designation"], data["email"], data.get("phone", ""),
            data["date_of_joining"], data["basic_salary"],
            data.get("pan_number", ""), data.get("bank_account", ""),
            data.get("bank_name", ""), data.get("ifsc_code", ""),
            int(data.get("pf_applicable", True))
        ))
        conn.commit()
        conn.close()
        return True, "Employee added successfully!"
    except sqlite3.IntegrityError as e:
        return False, f"Employee ID or Email already exists: {str(e)}"
    except Exception as e:
        return False, str(e)


def get_all_employees(status: str = "Active") -> list:
    conn = get_connection()
    cursor = conn.cursor()
    if status == "All":
        cursor.execute("SELECT * FROM employees ORDER BY name")
    else:
        cursor.execute("SELECT * FROM employees WHERE status=? ORDER BY name", (status,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_employee_by_id(emp_id: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_employee(emp_id: str, data: dict) -> tuple[bool, str]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees SET
                name=?, department=?, designation=?, email=?, phone=?,
                basic_salary=?, pan_number=?, bank_account=?, bank_name=?,
                ifsc_code=?, pf_applicable=?, status=?
            WHERE emp_id=?
        """, (
            data["name"], data["department"], data["designation"],
            data["email"], data.get("phone", ""), data["basic_salary"],
            data.get("pan_number", ""), data.get("bank_account", ""),
            data.get("bank_name", ""), data.get("ifsc_code", ""),
            int(data.get("pf_applicable", True)), data.get("status", "Active"),
            emp_id
        ))
        conn.commit()
        conn.close()
        return True, "Employee updated successfully!"
    except Exception as e:
        return False, str(e)


def delete_employee(emp_id: str) -> tuple[bool, str]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE employees SET status='Inactive' WHERE emp_id=?", (emp_id,))
        conn.commit()
        conn.close()
        return True, "Employee deactivated successfully!"
    except Exception as e:
        return False, str(e)


def get_next_emp_id() -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id FROM employees ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        last_id = row["emp_id"]
        try:
            num = int(last_id.replace("EMP", "")) + 1
            return f"EMP{num:04d}"
        except Exception:
            pass
    return "EMP0001"


# ─────────────────────────────────────────────
#  PAYROLL CRUD
# ─────────────────────────────────────────────

def save_payroll(data: dict) -> tuple[bool, str]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO payroll_records
            (emp_id, month, year, basic_salary, hra, da, medical_allowance,
             transport_allowance, other_allowances, overtime_hours, overtime_pay,
             gross_salary, pf_employee, pf_employer, esi, income_tax,
             professional_tax, other_deductions, total_deductions, net_salary,
             working_days, present_days, leaves_taken, paid_leaves_used,
             lop_days, attendance_percentage, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["emp_id"], data["month"], data["year"],
            data["basic_salary"], data["hra"], data["da"],
            data["medical_allowance"], data["transport_allowance"],
            data["other_allowances"], data["overtime_hours"], data["overtime_pay"],
            data["gross_salary"], data["pf_employee"], data["pf_employer"],
            data["esi"], data["income_tax"], data["professional_tax"],
            data["other_deductions"], data["total_deductions"], data["net_salary"],
            data["working_days"], data["present_days"], data["leaves_taken"],
            data["paid_leaves_used"], data["lop_days"], data["attendance_percentage"],
            "Processed"
        ))
        conn.commit()
        conn.close()
        return True, "Payroll processed successfully!"
    except Exception as e:
        return False, str(e)


def get_payroll_record(emp_id: str, month: int, year: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM payroll_records WHERE emp_id=? AND month=? AND year=?",
        (emp_id, month, year)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_payroll_by_month(month: int, year: int) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pr.*, e.name, e.department, e.designation
        FROM payroll_records pr
        JOIN employees e ON pr.emp_id = e.emp_id
        WHERE pr.month=? AND pr.year=?
        ORDER BY e.name
    """, (month, year))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_employee_payroll_history(emp_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM payroll_records
        WHERE emp_id=?
        ORDER BY year DESC, month DESC
    """, (emp_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ─────────────────────────────────────────────
#  DASHBOARD STATS
# ─────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE status='Active'")
    total_employees = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(DISTINCT name) as cnt FROM departments")
    total_departments = cursor.fetchone()["cnt"]

    now = datetime.now()
    cursor.execute("""
        SELECT SUM(net_salary) as total, COUNT(*) as cnt
        FROM payroll_records
        WHERE month=? AND year=?
    """, (now.month, now.year))
    row = cursor.fetchone()
    monthly_payroll = row["total"] or 0
    processed_this_month = row["cnt"] or 0

    cursor.execute("""
        SELECT department, COUNT(*) as cnt
        FROM employees WHERE status='Active'
        GROUP BY department ORDER BY cnt DESC
    """)
    dept_dist = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT month, year, SUM(net_salary) as total
        FROM payroll_records
        GROUP BY year, month
        ORDER BY year DESC, month DESC
        LIMIT 6
    """)
    monthly_trend = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "total_employees": total_employees,
        "total_departments": total_departments,
        "monthly_payroll": monthly_payroll,
        "processed_this_month": processed_this_month,
        "dept_distribution": dept_dist,
        "monthly_trend": monthly_trend,
    }


def get_departments() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM departments ORDER BY name")
    rows = [r["name"] for r in cursor.fetchall()]
    conn.close()
    return rows

# 💼 PayrollPro — Payroll Management System

A full-featured HR & Payroll Management System built with **Python + Streamlit + SQLite**.
Designed as a BTech Software Engineering project with production-quality code.

---

## 🚀 Features

| Feature | Description |
|---|---|
| **Employee Management** | Add, edit, deactivate employees with full details |
| **Salary Calculation** | Auto-compute HRA, DA, PF, ESI, Income Tax, LOP |
| **Attendance Tracking** | Present days, leaves, LOP, overtime input |
| **PDF Payslips** | Professional, downloadable salary slips |
| **Dashboard** | Live KPIs, department distribution, trend charts |
| **Reports** | Monthly payroll reports, per-employee history, CSV export |
| **Settings** | View salary policy slabs and tax structure |

---

## 🧮 Salary Calculation Logic

### Earnings
- **Basic Salary** — user-defined (adjusted for LOP)
- **HRA** — 40% of Basic
- **DA** — 10% of Basic
- **Medical Allowance** — ₹1,250 (fixed)
- **Transport Allowance** — ₹1,600 (fixed)
- **Overtime Pay** — (Basic / Working Days / 8) × OT Hours × 2

### Deductions
- **PF (Employee)** — 12% of Basic (capped at ₹15,000)
- **ESI** — 0.75% of Gross (if gross ≤ ₹21,000)
- **Professional Tax** — as per state slabs
- **Income Tax (TDS)** — New Regime FY 2024–25 slabs ÷ 12

### LOP (Loss of Pay)
> LOP days = Leaves Taken − Paid Leave Balance  
> LOP Deduction = (Basic / Working Days) × LOP Days

---

## 📁 Project Structure

```
payroll-management-system/
├── app.py                   ← Main Streamlit app (entry point)
├── requirements.txt
├── .gitignore
├── README.md
├── .streamlit/
│   └── config.toml          ← Theme & server config
├── database/
│   ├── __init__.py
│   └── db_manager.py        ← SQLite CRUD operations
├── modules/
│   ├── __init__.py
│   ├── salary.py            ← Salary calculation engine
│   └── payslip.py           ← PDF payslip generator
├── utils/
│   ├── __init__.py
│   └── helpers.py           ← Utility functions
└── assets/
    └── style.css            ← Custom UI styling
```

---

## ⚙️ Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/payroll-management-system.git
cd payroll-management-system
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New App**
4. Select your repo → Branch: `main` → Main file: `app.py`
5. Click **Deploy** — your app is live in ~2 minutes!

> ⚠️ The SQLite `.db` file is **not committed** (see `.gitignore`).  
> On Streamlit Cloud, the database is created fresh on first run.  
> For persistent data, use [Streamlit's secrets + PostgreSQL](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) for production.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, Plotly, Custom CSS |
| Backend | Python 3.10+ |
| Database | SQLite (via `sqlite3` stdlib) |
| PDF Engine | ReportLab |
| Charts | Plotly Express + Graph Objects |

---

## 📝 Notes for Evaluators

- All salary formulas are based on real Indian payroll rules (PF Act, ESI Act, Income Tax Act)
- The system handles edge cases: LOP calculations, ESI ceiling, PF ceiling, 87A rebate
- SQLite is used for simplicity and zero-config deployment — can be swapped with PostgreSQL easily
- PDF payslips use ReportLab for professional formatting

---

## 👨‍💻 Author

**[Your Name]** — BTech [Branch], [Year]  
Project: Payroll Management System — Software Engineering Lab

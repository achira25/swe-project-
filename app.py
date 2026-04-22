"""
PayrollPro — Payroll Management System
Streamlit multi-page app | Professional Edition
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
import os
from datetime import datetime, date

from database.db_manager import (
    initialize_database, add_employee, get_all_employees,
    get_employee_by_id, update_employee, delete_employee,
    get_next_emp_id, save_payroll, get_payroll_record,
    get_all_payroll_by_month, get_employee_payroll_history,
    get_dashboard_stats, get_departments,
)
from modules.salary import calculate_full_salary
from modules.payslip import generate_payslip_pdf
from utils.helpers import (
    format_currency, get_current_month_year,
    validate_pan, validate_ifsc, MONTH_NAMES
)

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="PayrollPro",
    page_icon="assets/favicon.png" if os.path.exists("assets/favicon.png") else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Custom CSS ──────────────────────────────────────────────────
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

initialize_database()


# ════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='padding: 24px 0 28px 0;'>
        <div style='font-family: Georgia, serif; font-size: 1.5rem;
                    font-weight: 700; color: #ffffff; letter-spacing: 0.5px;'>
            PayrollPro
        </div>
        <div style='font-size: 0.7rem; color: #9fa8da; margin-top: 4px;
                    letter-spacing: 1.5px; text-transform: uppercase;'>
            HR &amp; Payroll Management
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Employees",
            "Process Payroll",
            "Payslips",
            "Reports",
            "Settings",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    now = datetime.now()
    st.markdown(f"""
    <div style='font-size: 0.72rem; color: #9fa8da;'>
        {now.strftime('%A, %d %B %Y')}
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  SHARED HELPERS
# ════════════════════════════════════════════════════════════════════

def section(title: str, subtitle: str = ""):
    st.markdown(f"<h2 class='page-title'>{title}</h2>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p class='page-sub'>{subtitle}</p>", unsafe_allow_html=True)
    st.divider()


# ════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════════════

def page_dashboard():
    section("Dashboard", "Real-time overview of workforce and payroll.")

    stats = get_dashboard_stats()
    cur_month, cur_year = get_current_month_year()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Employees",       stats["total_employees"])
    c2.metric("Departments",           stats["total_departments"])
    c3.metric(
        f"{MONTH_NAMES[cur_month]} Payroll",
        format_currency(stats["monthly_payroll"])
    )
    c4.metric("Processed This Month",  stats["processed_this_month"])

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Headcount by Department")
        dept_data = stats["dept_distribution"]
        if dept_data:
            df_dept = pd.DataFrame(dept_data)
            fig = px.pie(
                df_dept, values="cnt", names="department",
                color_discrete_sequence=[
                    "#1a237e","#283593","#3949ab","#5c6bc0",
                    "#7986cb","#9fa8da","#c5cae9","#e8eaf6"
                ],
                hole=0.5,
            )
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="v", font=dict(size=11, family="DM Sans")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=300,
                font=dict(family="DM Sans"),
            )
            fig.update_traces(textinfo="percent+label", textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No employee data yet.")

    with col_right:
        st.markdown("#### Monthly Payroll Trend")
        trend_data = stats["monthly_trend"]
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            df_trend["label"] = df_trend.apply(
                lambda r: f"{MONTH_NAMES[int(r['month'])][:3]} {int(r['year'])}", axis=1
            )
            df_trend = df_trend.iloc[::-1].reset_index(drop=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=df_trend["label"], y=df_trend["total"],
                marker_color="#3949ab", marker_line_width=0,
                name="Net Payroll",
            ))
            fig2.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#e8eaf6", tickprefix="Rs "),
                xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                showlegend=False,
                height=300,
                font=dict(family="DM Sans"),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Process payroll for multiple months to see trend.")

    st.markdown("#### Recent Payroll Records")
    recent = get_all_payroll_by_month(cur_month, cur_year)
    if recent:
        df_r = pd.DataFrame(recent)[[
            "emp_id","name","department","gross_salary","total_deductions","net_salary","status"
        ]]
        df_r.columns = ["Emp ID","Name","Department","Gross Salary","Deductions","Net Salary","Status"]
        for col in ["Gross Salary","Deductions","Net Salary"]:
            df_r[col] = df_r[col].apply(lambda x: f"Rs {x:,.2f}")
        st.dataframe(df_r, use_container_width=True, hide_index=True)
    else:
        st.info(f"No payroll processed for {MONTH_NAMES[cur_month]} {cur_year}.")


# ════════════════════════════════════════════════════════════════════
#  PAGE: EMPLOYEES
# ════════════════════════════════════════════════════════════════════

def page_employees():
    section("Employee Management")
    departments = get_departments()
    tab1, tab2, tab3 = st.tabs(["All Employees", "Add Employee", "Edit / Deactivate"])

    # ── View ─────────────────────────────────────────────
    with tab1:
        status_filter = st.selectbox("Status", ["Active","Inactive","All"], index=0)
        employees = get_all_employees(status=status_filter)
        if employees:
            df = pd.DataFrame(employees)[[
                "emp_id","name","department","designation",
                "email","phone","basic_salary","date_of_joining","status"
            ]]
            df.columns = [
                "Emp ID","Name","Department","Designation",
                "Email","Phone","Basic Salary","Joining Date","Status"
            ]
            df["Basic Salary"] = df["Basic Salary"].apply(lambda x: f"Rs {x:,.0f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"{len(employees)} record(s) found")
        else:
            st.info("No employees found.")

    # ── Add ──────────────────────────────────────────────
    with tab2:
        st.markdown("#### New Employee Record")
        next_id = get_next_emp_id()

        with st.form("add_employee_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                emp_id       = st.text_input("Employee ID",     value=next_id)
                name         = st.text_input("Full Name")
                email        = st.text_input("Email Address")
                phone        = st.text_input("Phone Number")
                dept         = st.selectbox("Department", departments)
            with c2:
                designation  = st.text_input("Designation")
                doj          = st.date_input("Date of Joining", value=date.today())
                basic_salary = st.number_input("Basic Salary (Rs)", min_value=0.0, step=500.0, value=25000.0)
                pan_number   = st.text_input("PAN Number")
                pf_applicable = st.checkbox("PF Applicable", value=True)

            st.markdown("**Bank Details**")
            b1, b2, b3 = st.columns(3)
            with b1: bank_account = st.text_input("Account Number")
            with b2: bank_name    = st.text_input("Bank Name")
            with b3: ifsc_code    = st.text_input("IFSC Code")

            submitted = st.form_submit_button("Add Employee", use_container_width=True)

            if submitted:
                errors = []
                if not emp_id.strip():       errors.append("Employee ID is required.")
                if not name.strip():         errors.append("Full name is required.")
                if not email.strip():        errors.append("Email is required.")
                if not designation.strip():  errors.append("Designation is required.")
                if basic_salary <= 0:        errors.append("Basic salary must be greater than zero.")
                if pan_number and not validate_pan(pan_number):
                    errors.append("Invalid PAN format. Expected format: ABCDE1234F")
                if ifsc_code and not validate_ifsc(ifsc_code):
                    errors.append("Invalid IFSC format. Expected format: SBIN0001234")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    ok, msg = add_employee({
                        "emp_id":         emp_id.strip().upper(),
                        "name":           name.strip(),
                        "department":     dept,
                        "designation":    designation.strip(),
                        "email":          email.strip().lower(),
                        "phone":          phone.strip(),
                        "date_of_joining":str(doj),
                        "basic_salary":   basic_salary,
                        "pan_number":     pan_number.strip().upper(),
                        "bank_account":   bank_account.strip(),
                        "bank_name":      bank_name.strip(),
                        "ifsc_code":      ifsc_code.strip().upper(),
                        "pf_applicable":  pf_applicable,
                    })
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    # ── Edit / Deactivate ─────────────────────────────────
    with tab3:
        employees_all = get_all_employees(status="All")
        if not employees_all:
            st.info("No employees found.")
            return

        emp_options = {f"{e['emp_id']} — {e['name']}": e["emp_id"] for e in employees_all}
        selected_label = st.selectbox("Select Employee", list(emp_options.keys()))
        selected_id    = emp_options[selected_label]
        emp            = get_employee_by_id(selected_id)

        if emp:
            st.markdown(f"#### Editing: {emp['name']} ({emp['emp_id']})")
            with st.form("edit_employee_form"):
                c1, c2 = st.columns(2)
                with c1:
                    name_e  = st.text_input("Full Name",   value=emp["name"])
                    email_e = st.text_input("Email",       value=emp["email"])
                    phone_e = st.text_input("Phone",       value=emp.get("phone",""))
                    dept_idx = departments.index(emp["department"]) if emp["department"] in departments else 0
                    dept_e  = st.selectbox("Department",   departments, index=dept_idx)
                with c2:
                    desig_e  = st.text_input("Designation", value=emp["designation"])
                    basic_e  = st.number_input("Basic Salary", value=float(emp["basic_salary"]), step=500.0)
                    pan_e    = st.text_input("PAN Number",  value=emp.get("pan_number",""))
                    pf_e     = st.checkbox("PF Applicable", value=bool(emp.get("pf_applicable",1)))
                    status_e = st.selectbox("Status", ["Active","Inactive"],
                                            index=0 if emp.get("status")=="Active" else 1)

                b1, b2, b3 = st.columns(3)
                with b1: bank_acc_e = st.text_input("Account Number", value=emp.get("bank_account",""))
                with b2: bank_nm_e  = st.text_input("Bank Name",      value=emp.get("bank_name",""))
                with b3: ifsc_e     = st.text_input("IFSC Code",      value=emp.get("ifsc_code",""))

                col_save, col_del = st.columns([3,1])
                with col_save: save_btn = st.form_submit_button("Save Changes",  use_container_width=True)
                with col_del:  del_btn  = st.form_submit_button("Deactivate",    use_container_width=True)

                if save_btn:
                    ok, msg = update_employee(selected_id, {
                        "name": name_e, "department": dept_e, "designation": desig_e,
                        "email": email_e, "phone": phone_e, "basic_salary": basic_e,
                        "pan_number": pan_e, "bank_account": bank_acc_e,
                        "bank_name": bank_nm_e, "ifsc_code": ifsc_e,
                        "pf_applicable": pf_e, "status": status_e,
                    })
                    st.success(msg) if ok else st.error(msg)

                if del_btn:
                    ok, msg = delete_employee(selected_id)
                    st.success(msg) if ok else st.error(msg)


# ════════════════════════════════════════════════════════════════════
#  PAGE: PROCESS PAYROLL
# ════════════════════════════════════════════════════════════════════

def page_process_payroll():
    section("Process Payroll", "Calculate and record monthly salary for an employee.")

    employees = get_all_employees()
    if not employees:
        st.warning("No active employees found. Please add employees first.")
        return

    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        emp_options    = {f"{e['emp_id']} — {e['name']}": e["emp_id"] for e in employees}
        selected_label = st.selectbox("Employee", list(emp_options.keys()))
        selected_id    = emp_options[selected_label]
    with col2:
        month     = st.selectbox("Month", list(MONTH_NAMES.values()), index=datetime.now().month - 1)
        month_num = list(MONTH_NAMES.keys())[list(MONTH_NAMES.values()).index(month)]
    with col3:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)

    emp      = get_employee_by_id(selected_id)
    existing = get_payroll_record(selected_id, month_num, int(year))

    if existing:
        st.warning(f"Payroll already processed for {month} {year}. Submitting will overwrite the existing record.")

    st.markdown("#### Attendance & Inputs")
    with st.form("payroll_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            working_days   = st.number_input("Working Days",   1,  31, 26)
            present_days   = st.number_input("Days Present",   0,  31, 26)
        with c2:
            leaves_taken   = st.number_input("Leaves Taken",   0,  31,  0)
            paid_leave_bal = st.number_input("Paid Leave Balance", 0, 30, 12)
        with c3:
            overtime_hrs   = st.number_input("Overtime Hours", 0.0, 200.0, 0.0, step=0.5)
            other_allow    = st.number_input("Other Allowances (Rs)", 0.0, step=100.0)

        other_ded = st.number_input("Other Deductions (Rs)", 0.0, step=100.0)
        calc_btn  = st.form_submit_button("Calculate Salary", use_container_width=True)

    if calc_btn or "calc_result" in st.session_state:
        if calc_btn:
            result = calculate_full_salary(
                basic             = float(emp["basic_salary"]),
                working_days      = int(working_days),
                present_days      = int(present_days),
                overtime_hours    = float(overtime_hrs),
                leaves_taken      = int(leaves_taken),
                paid_leave_balance= int(paid_leave_bal),
                other_allowances  = float(other_allow),
                other_deductions  = float(other_ded),
                pf_applicable     = bool(emp.get("pf_applicable", 1)),
            )
            st.session_state["calc_result"]  = result
            st.session_state["calc_emp_id"]  = selected_id
            st.session_state["calc_month"]   = month_num
            st.session_state["calc_year"]    = int(year)

        result = st.session_state.get("calc_result")
        if result:
            st.divider()
            st.markdown("#### Salary Breakdown")

            a1, a2, a3, a4, a5 = st.columns(5)
            a1.metric("Working Days",     result["working_days"])
            a2.metric("Present Days",     result["present_days"])
            a3.metric("Paid Leaves Used", result["paid_leaves_used"])
            a4.metric("LOP Days",         result["lop_days"])
            a5.metric("Attendance",       f"{result['attendance_percentage']:.1f}%")

            st.markdown("<br>", unsafe_allow_html=True)
            col_earn, col_ded = st.columns(2)

            with col_earn:
                st.markdown("**Earnings**")
                df_earn = pd.DataFrame({
                    "Component": [
                        "Basic Salary","HRA","Dearness Allowance",
                        "Medical Allowance","Transport Allowance",
                        "Overtime Pay","Other Allowances"
                    ],
                    "Amount (Rs)": [
                        result["basic_salary"], result["hra"], result["da"],
                        result["medical_allowance"], result["transport_allowance"],
                        result["overtime_pay"], result["other_allowances"]
                    ]
                })
                df_earn["Amount (Rs)"] = df_earn["Amount (Rs)"].apply(lambda x: f"{x:,.2f}")
                st.dataframe(df_earn, hide_index=True, use_container_width=True)
                st.markdown(f"**Gross Salary: {format_currency(result['gross_salary'])}**")

            with col_ded:
                st.markdown("**Deductions**")
                df_ded = pd.DataFrame({
                    "Component": [
                        "PF (Employee)","ESI","Professional Tax",
                        "Income Tax (TDS)","Other Deductions"
                    ],
                    "Amount (Rs)": [
                        result["pf_employee"], result["esi"], result["professional_tax"],
                        result["income_tax"], result["other_deductions"]
                    ]
                })
                df_ded["Amount (Rs)"] = df_ded["Amount (Rs)"].apply(lambda x: f"{x:,.2f}")
                st.dataframe(df_ded, hide_index=True, use_container_width=True)
                st.markdown(f"**Total Deductions: {format_currency(result['total_deductions'])}**")
                if result["pf_employer"] > 0:
                    st.caption(f"Employer PF contribution: {format_currency(result['pf_employer'])} — not deducted from salary.")

            st.markdown(f"""
            <div style='background:#1a237e; padding:20px 28px; border-radius:10px;
                        margin-top:16px; display:flex; justify-content:space-between;
                        align-items:center;'>
                <div style='color:#c5cae9; font-size:0.85rem; font-weight:600;
                            letter-spacing:1px; text-transform:uppercase;'>
                    Net Salary Payable
                </div>
                <div style='color:#ffffff; font-size:1.8rem; font-weight:700;
                            font-family:Georgia,serif;'>
                    Rs {result['net_salary']:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Confirm and Save Payroll Record", use_container_width=True, type="primary"):
                save_data = {
                    **result,
                    "emp_id": st.session_state["calc_emp_id"],
                    "month":  st.session_state["calc_month"],
                    "year":   st.session_state["calc_year"],
                }
                ok, msg = save_payroll(save_data)
                if ok:
                    st.success(msg)
                    del st.session_state["calc_result"]
                else:
                    st.error(msg)


# ════════════════════════════════════════════════════════════════════
#  PAGE: PAYSLIPS
# ════════════════════════════════════════════════════════════════════

def page_payslips():
    section("Payslips", "View and download salary slips for any processed month.")

    employees = get_all_employees()
    if not employees:
        st.warning("No active employees found.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        emp_options    = {f"{e['emp_id']} — {e['name']}": e["emp_id"] for e in employees}
        selected_label = st.selectbox("Employee", list(emp_options.keys()))
        selected_id    = emp_options[selected_label]
    with c2:
        month     = st.selectbox("Month", list(MONTH_NAMES.values()), index=datetime.now().month - 1)
        month_num = list(MONTH_NAMES.keys())[list(MONTH_NAMES.values()).index(month)]
    with c3:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)

    col_view, col_dl = st.columns(2)

    with col_view:
        if st.button("View Payslip", use_container_width=True):
            payroll = get_payroll_record(selected_id, month_num, int(year))
            emp     = get_employee_by_id(selected_id)
            if not payroll:
                st.error(f"No payroll record found for {month} {year}. Please process payroll first.")
            else:
                st.markdown(f"#### Payslip — {emp['name']} | {month} {year}")
                with st.expander("Full Details", expanded=True):
                    d1, d2, d3 = st.columns(3)
                    d1.write(f"**Employee ID:** {emp['emp_id']}")
                    d2.write(f"**Department:** {emp['department']}")
                    d3.write(f"**Designation:** {emp['designation']}")
                    st.divider()

                    ec1, ec2 = st.columns(2)
                    with ec1:
                        st.markdown("**Earnings**")
                        for label, val in [
                            ("Basic Salary",       payroll["basic_salary"]),
                            ("HRA",                payroll["hra"]),
                            ("DA",                 payroll["da"]),
                            ("Medical Allowance",  payroll["medical_allowance"]),
                            ("Transport Allowance",payroll["transport_allowance"]),
                            ("Overtime Pay",       payroll["overtime_pay"]),
                            ("Other Allowances",   payroll["other_allowances"]),
                        ]:
                            if val > 0:
                                st.write(f"{label}: **{format_currency(val)}**")
                        st.markdown(f"---\n**Gross: {format_currency(payroll['gross_salary'])}**")

                    with ec2:
                        st.markdown("**Deductions**")
                        for label, val in [
                            ("PF (Employee)",   payroll["pf_employee"]),
                            ("ESI",             payroll["esi"]),
                            ("Professional Tax",payroll["professional_tax"]),
                            ("Income Tax",      payroll["income_tax"]),
                            ("Other Deductions",payroll["other_deductions"]),
                        ]:
                            if val > 0:
                                st.write(f"{label}: **{format_currency(val)}**")
                        st.markdown(f"---\n**Total Deductions: {format_currency(payroll['total_deductions'])}**")

                    st.markdown(f"""
                    <div style='background:#1a237e; border-radius:8px; padding:14px 20px;
                                margin-top:14px; display:flex; justify-content:space-between;
                                align-items:center;'>
                        <span style='color:#c5cae9; font-size:0.8rem; letter-spacing:1px;
                                     text-transform:uppercase; font-weight:600;'>Net Salary</span>
                        <span style='color:#fff; font-size:1.4rem; font-weight:700;
                                     font-family:Georgia,serif;'>
                            Rs {payroll['net_salary']:,.2f}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

    with col_dl:
        if st.button("Download PDF", use_container_width=True):
            payroll = get_payroll_record(selected_id, month_num, int(year))
            emp     = get_employee_by_id(selected_id)
            if not payroll:
                st.error("No payroll record found. Please process payroll first.")
            else:
                try:
                    pdf_bytes = generate_payslip_pdf(emp, payroll, month_num, int(year))
                    st.download_button(
                        label     = "Click to Download PDF",
                        data      = pdf_bytes,
                        file_name = f"Payslip_{selected_id}_{month}_{year}.pdf",
                        mime      = "application/pdf",
                        use_container_width=True,
                    )
                    st.success("PDF ready. Click the button above to download.")
                except ImportError:
                    st.error("reportlab is not installed. Run: pip install reportlab")
                except Exception as e:
                    st.error(f"PDF generation failed: {e}")

    st.divider()
    st.markdown("#### Payroll History")
    history = get_employee_payroll_history(selected_id)
    if history:
        df_hist = pd.DataFrame(history)[[
            "month","year","gross_salary","total_deductions","net_salary",
            "attendance_percentage","lop_days","status"
        ]]
        df_hist["Period"] = df_hist.apply(
            lambda r: f"{MONTH_NAMES[int(r['month'])]} {int(r['year'])}", axis=1
        )
        df_hist = df_hist[[
            "Period","gross_salary","total_deductions","net_salary",
            "attendance_percentage","lop_days","status"
        ]]
        df_hist.columns = [
            "Period","Gross Salary","Deductions","Net Salary",
            "Attendance %","LOP Days","Status"
        ]
        for col in ["Gross Salary","Deductions","Net Salary"]:
            df_hist[col] = df_hist[col].apply(lambda x: f"Rs {x:,.2f}")
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
    else:
        st.info("No payroll history found for this employee.")


# ════════════════════════════════════════════════════════════════════
#  PAGE: REPORTS
# ════════════════════════════════════════════════════════════════════

def page_reports():
    section("Reports", "Analyse payroll data across months and employees.")

    tab1, tab2 = st.tabs(["Monthly Report", "Employee Report"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            rep_month = st.selectbox(
                "Month", list(MONTH_NAMES.values()),
                index=datetime.now().month - 1, key="rep_month"
            )
            rep_month_num = list(MONTH_NAMES.keys())[list(MONTH_NAMES.values()).index(rep_month)]
        with c2:
            rep_year = st.number_input(
                "Year", min_value=2020, max_value=2030,
                value=datetime.now().year, key="rep_year"
            )

        records = get_all_payroll_by_month(rep_month_num, int(rep_year))
        if records:
            df = pd.DataFrame(records)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Employees Paid",    len(df))
            k2.metric("Total Gross",       format_currency(df["gross_salary"].sum()))
            k3.metric("Total Deductions",  format_currency(df["total_deductions"].sum()))
            k4.metric("Total Net Payout",  format_currency(df["net_salary"].sum()))

            st.markdown("<br>", unsafe_allow_html=True)

            df_dept = df.groupby("department")["net_salary"].sum().reset_index()
            fig = px.bar(
                df_dept, x="department", y="net_salary",
                title=f"Net Salary by Department — {rep_month} {rep_year}",
                color_discrete_sequence=["#3949ab"],
                labels={"net_salary":"Net Salary (Rs)","department":"Department"},
            )
            fig.update_layout(
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#e8eaf6"),
                font=dict(family="DM Sans"),
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Detailed Table")
            df_display = df[[
                "emp_id","name","department","gross_salary",
                "pf_employee","income_tax","total_deductions","net_salary"
            ]].copy()
            df_display.columns = [
                "Emp ID","Name","Department","Gross Salary",
                "PF","Income Tax","Total Deductions","Net Salary"
            ]
            for col in ["Gross Salary","PF","Income Tax","Total Deductions","Net Salary"]:
                df_display[col] = df_display[col].apply(lambda x: f"Rs {x:,.2f}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            csv = df_display.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv,
                file_name=f"Payroll_Report_{rep_month}_{rep_year}.csv",
                mime="text/csv",
            )
        else:
            st.info(f"No records found for {rep_month} {rep_year}.")

    with tab2:
        employees = get_all_employees()
        if not employees:
            st.info("No employees found.")
            return

        emp_options = {f"{e['emp_id']} — {e['name']}": e["emp_id"] for e in employees}
        sel    = st.selectbox("Employee", list(emp_options.keys()), key="rep_emp")
        sel_id = emp_options[sel]
        history = get_employee_payroll_history(sel_id)

        if history:
            df_h = pd.DataFrame(history)
            df_h["Period"] = df_h.apply(
                lambda r: f"{MONTH_NAMES[int(r['month'])][:3]} {int(r['year'])}", axis=1
            )
            df_h = df_h.iloc[::-1].reset_index(drop=True)

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df_h["Period"], y=df_h["gross_salary"],
                name="Gross", line=dict(color="#3949ab", width=2),
                fill="tozeroy", fillcolor="rgba(57,73,171,0.08)",
            ))
            fig2.add_trace(go.Scatter(
                x=df_h["Period"], y=df_h["net_salary"],
                name="Net", line=dict(color="#1a237e", width=2),
                fill="tozeroy", fillcolor="rgba(26,35,126,0.08)",
            ))
            fig2.update_layout(
                title="Gross vs Net Salary — Historical",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#e8eaf6", tickprefix="Rs "),
                xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                legend=dict(orientation="h"),
                font=dict(family="DM Sans"),
                height=320,
            )
            st.plotly_chart(fig2, use_container_width=True)

            s1, s2, s3 = st.columns(3)
            s1.metric("Average Net Salary", format_currency(df_h["net_salary"].mean()))
            s2.metric("Highest Net Salary", format_currency(df_h["net_salary"].max()))
            s3.metric("Total Paid Out",     format_currency(df_h["net_salary"].sum()))
        else:
            st.info("No salary history for this employee.")


# ════════════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ════════════════════════════════════════════════════════════════════

def page_settings():
    section("Settings", "System configuration and policy reference.")

    st.markdown("#### Company Details")
    with st.expander("View / Edit", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Company Name",  value="Acme Technologies Pvt. Ltd.", disabled=True)
            st.text_input("Address",       value="123, Tech Park, Bengaluru - 560001", disabled=True)
        with c2:
            st.text_input("CIN",           value="U72900KA2020PTC123456", disabled=True)
            st.text_input("HR Email",      value="hr@acmetech.com", disabled=True)

    st.markdown("#### Salary Policy")
    with st.expander("Components and Rates", expanded=True):
        st.dataframe(pd.DataFrame({
            "Component": [
                "HRA","DA","Medical Allowance","Transport Allowance",
                "PF (Employee)","PF (Employer)","PF Ceiling","ESI (Employee)",
                "ESI Ceiling","Professional Tax","Overtime Rate",
            ],
            "Rate / Amount": [
                "40% of Basic","10% of Basic","Rs 1,250 fixed","Rs 1,600 fixed",
                "12% of Basic","12% of Basic","Rs 15,000","0.75% of Gross",
                "Rs 21,000 gross","Rs 150–200 / month","2x hourly rate",
            ],
            "Notes": [
                "Metro rate","Variable DA","Tax-exempt","Tax-exempt up to limit",
                "Deducted from salary","Borne by employer",
                "Calculated on min(basic, Rs 15,000)",
                "Applicable if gross is at or below ceiling",
                "ESI not applied above this gross",
                "As per state slabs","Double time for overtime hours",
            ]
        }), use_container_width=True, hide_index=True)

    st.markdown("#### Income Tax Slabs (New Regime FY 2024–25)")
    with st.expander("View Slabs"):
        st.dataframe(pd.DataFrame({
            "Annual Income Slab": [
                "Up to Rs 3,00,000","Rs 3,00,001 – Rs 6,00,000",
                "Rs 6,00,001 – Rs 9,00,000","Rs 9,00,001 – Rs 12,00,000",
                "Rs 12,00,001 – Rs 15,00,000","Above Rs 15,00,000",
            ],
            "Tax Rate": ["Nil","5%","10%","15%","20%","30%"],
        }), use_container_width=True, hide_index=True)
        st.caption("Section 87A rebate: zero tax if net taxable income is Rs 7,00,000 or below.")

    st.markdown("#### About")
    st.markdown("""
    **PayrollPro** v1.0  
    Stack: Python 3 · Streamlit · SQLite · ReportLab · Plotly  
    Built as a BTech Software Engineering project.
    """)


# ════════════════════════════════════════════════════════════════════
#  ROUTER
# ════════════════════════════════════════════════════════════════════

if   page == "Dashboard":       page_dashboard()
elif page == "Employees":       page_employees()
elif page == "Process Payroll": page_process_payroll()
elif page == "Payslips":        page_payslips()
elif page == "Reports":         page_reports()
elif page == "Settings":        page_settings()

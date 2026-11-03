import sqlite3
import datetime
import calendar

# Let's import the actual functions from app.py using Flask app context
import sys
from app import app, db, Teacher, Course, Enrollment, Payment, CourseTeacher, TeacherAdvance, TeacherExpense, TeacherSalaryPayout, BookSale
from app import calculate_enrollment_revenue_for_month, compute_teacher_gross_for_month, get_single_teacher_payroll_details, _calculate_period_teacher_payroll

with app.app_context():
    y = 2026
    m = 10
    req_month = f"{y:04d}-{m:02d}"
    print(f"=== COMPARING PAYROLL CALCULATIONS FOR {req_month} ===")
    
    teachers = Teacher.query.filter_by(active=True).order_by(Teacher.id).all()
    
    # 1. Run _calculate_period_teacher_payroll
    m_start = datetime.date(y, m, 1)
    _, num_days = calendar.monthrange(y, m)
    m_end = datetime.date(y, m, num_days)
    period_rows, grand_payroll_period = _calculate_period_teacher_payroll(m_start, m_end)
    period_map = {r['teacher'].id: r for r in period_rows}
    
    discrepancies = []
    
    for t in teachers:
        # compute via get_single_teacher_payroll_details
        single = get_single_teacher_payroll_details(t, y, m)
        period = period_map.get(t.id, {})
        gross_single = single['total_gross'] if single else 0.0
        earned_single = single['total_earned'] if single else 0.0
        net_single = single['net_payable'] if single else 0.0
        
        earned_period = period.get('total_earned', 0.0)
        net_period = period.get('net_payable', 0.0)
        
        # Gross computed directly
        gross_direct = compute_teacher_gross_for_month(t, y, m)
        
        diff_earned = abs(earned_single - earned_period)
        diff_gross = abs(earned_single - gross_direct)
        
        if diff_earned > 0.01 or diff_gross > 0.01:
            discrepancies.append({
                'teacher_id': t.id,
                'name': t.full_name,
                'single_earned': earned_single,
                'period_earned': earned_period,
                'gross_direct': gross_direct,
                'single_net': net_single,
                'period_net': net_period,
            })
            print(f"DISCREPANCY for {t.id} - {t.full_name}: single_earned={earned_single}, period_earned={earned_period}, gross_direct={gross_direct}")
        else:
            if earned_single > 0:
                print(f"OK: Teacher {t.id} ({t.full_name}): Earned = {earned_single:.2f} DH, Net = {net_single:.2f} DH")

    print(f"\nTotal teachers checked: {len(teachers)}")
    print(f"Total discrepancies between payroll functions: {len(discrepancies)}")

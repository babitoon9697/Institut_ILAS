import datetime
from app import app, db, Teacher, Course, Enrollment, Payment, Student, CourseTeacher, TeacherAdvance, TeacherExpense, TeacherSalaryPayout
from app import calculate_enrollment_revenue_for_month, get_single_teacher_payroll_details

with app.app_context():
    y, m = 2026, 10
    start_d = datetime.date(y, m, 1)
    end_d = datetime.date(y, m, 31)

    print("===================================================================")
    print("AUDIT: PAYMENTS IN OCTOBER 2026 AND HOW THEY MAP TO REVENUE")
    print("===================================================================")

    # 1. All payments in Oct 2026
    oct_payments = Payment.query.filter(Payment.date >= start_d, Payment.date <= end_d).all()
    print(f"Total payments made in October 2026: {len(oct_payments)}")

    unmapped_payments = []
    dropped_or_inactive_enrollment_payments = []
    
    for p in oct_payments:
        if not p.enrollment_id:
            unmapped_payments.append(p)
            continue
        en = Enrollment.query.get(p.enrollment_id)
        if not en:
            unmapped_payments.append(p)
            continue
        if en.status == 'dropped':
            dropped_or_inactive_enrollment_payments.append((p, en))

    print(f"Payments without enrollment: {len(unmapped_payments)}")
    for p in unmapped_payments:
        print(f"   Unmapped: ID {p.id}, Receipt {p.receipt}, Amount {p.amount}, Date {p.date}, Note: {p.note}")

    print(f"Payments attached to DROPPED enrollments: {len(dropped_or_inactive_enrollment_payments)}")
    for p, en in dropped_or_inactive_enrollment_payments:
        print(f"   Dropped Enroll: Payment {p.id}, Receipt {p.receipt}, Amount {p.amount}, Enroll {en.id}, Course {en.course_id}, Student {en.student_id}")

    # 2. Check all active courses and their students in Oct 2026
    print("\n===================================================================")
    print("CHECKING EACH TEACHER AND REVENUE PER STUDENT IN OCT 2026")
    print("===================================================================")
    
    active_teachers = Teacher.query.filter_by(active=True).order_by(Teacher.id).all()
    
    issues_found = []
    
    for t in active_teachers:
        details = get_single_teacher_payroll_details(t, y, m)
        if not details or details['total_earned'] == 0:
            continue
            
        print(f"\n--- Teacher {t.id}: {t.full_name} | Earned: {details['total_earned']:.2f} DH | Groups: {len(details['groups'])} ---")
        for g in details['groups']:
            c = g['course']
            # Find enrollments in this group
            all_c_enrolls = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').order_by(Enrollment.id.desc()).all()
            
            # Check students in this group
            for en in all_c_enrolls:
                st = en.student
                if not st or st.status != 'active':
                    continue
                rev = calculate_enrollment_revenue_for_month(en, y, m)
                
                # Check payments made by this student in October
                st_oct_pays = Payment.query.filter_by(student_id=st.id).filter(Payment.date >= start_d, Payment.date <= end_d).all()
                en_oct_pays = [p for p in st_oct_pays if p.enrollment_id == en.id]
                other_oct_pays = [p for p in st_oct_pays if p.enrollment_id != en.id]
                
                en_oct_paid_amt = sum(p.amount for p in en_oct_pays)
                other_oct_paid_amt = sum(p.amount for p in other_oct_pays)
                
                # Anomaly A: Student paid for THIS enrollment in October, but recognized revenue is 0
                if en_oct_paid_amt > 0 and rev == 0:
                    issues_found.append({
                        'type': 'PAID_BUT_ZERO_REV',
                        'teacher': t.full_name,
                        'course': c.name,
                        'student': f"{st.first_name} {st.last_name} (ID: {st.id})",
                        'enrollment_id': en.id,
                        'enrollment_status': en.status,
                        'enroll_date': en.enroll_date,
                        'paid_in_oct': en_oct_paid_amt,
                        'revenue_recognized': rev
                    })
                
                # Anomaly B: Student paid in October, but payment went to another enrollment while student is enrolled here with rev=0
                if rev == 0 and en.status == 'active' and other_oct_paid_amt > 0:
                    # Check if student is active in multiple courses
                    issues_found.append({
                        'type': 'MULTI_COURSE_PAYMENT_MISMATCH',
                        'teacher': t.full_name,
                        'course': c.name,
                        'student': f"{st.first_name} {st.last_name} (ID: {st.id})",
                        'enrollment_id': en.id,
                        'rev': rev,
                        'other_pays': [(p.id, p.enrollment_id, p.amount, p.note) for p in other_oct_pays]
                    })

                # Anomaly C: Revenue recognized > paid overall
                tot_paid = en.total_paid or 0.0
                if rev > tot_paid + 0.01:
                    issues_found.append({
                        'type': 'REV_EXCEEDS_TOTAL_PAID',
                        'teacher': t.full_name,
                        'course': c.name,
                        'student': f"{st.first_name} {st.last_name} (ID: {st.id})",
                        'enrollment_id': en.id,
                        'rev': rev,
                        'tot_paid': tot_paid
                    })

    print("\n===================================================================")
    print(f"ANOMALIES FOUND: {len(issues_found)}")
    print("===================================================================")
    for issue in issues_found[:30]:
        print(issue)

from app import app, db, Teacher, Course, Enrollment, Payment, Student
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    # Let's inspect each specific case from the anomalies
    cases = [
        ('MOHAMMED TARIQ', 245, 856),
        ('Saad elkarmi', 372, 743),
        ('adam aziz', 411, 851),
        ('Agmar Abdelhamid', 408, 845),
        ('Agmar Abdelhamid', 408, 852),
        ('elbaz oumaima', 320, 607),
        ('elbaz oumaima', 320, 608),
        ('SOUFIAN LMDAWZ', 173, 866),
        ('ARIAM ELHOUSSNI', 140, 233),
        ('YASMINE BOUCHIKH', 106, 354),
        ('RIHAB REGGUI', 358, 825),
        ('AZIZA DAOUDI', 37, 725),
    ]

    for name, s_id, en_id in cases:
        print(f"\n=======================================================")
        print(f"CASE: {name} (Student ID: {s_id}, Enrollment ID: {en_id})")
        print(f"=======================================================")
        st = Student.query.get(s_id)
        en = Enrollment.query.get(en_id)
        if en:
            c = en.course
            print(f"Course: {c.id} - {c.name if c else 'None'} | Teacher: {c.teacher.full_name if c and c.teacher else 'None'}")
            print(f"Enroll Details: ID={en.id}, status={en.status}, enroll_date={en.enroll_date}, end_date={getattr(en, 'end_date', None)}, custom_end_date={getattr(en, 'custom_end_date', None)}")
            print(f"Pricing: monthly={en.monthly_price}, calculated={en.calculated_price}, dur={en.duration_months}, notes={en.notes}")
            
            # calculate revenue for oct 2026
            rev_oct = calculate_enrollment_revenue_for_month(en, 2026, 10)
            rev_nov = calculate_enrollment_revenue_for_month(en, 2026, 11)
            rev_sep = calculate_enrollment_revenue_for_month(en, 2026, 9)
            print(f"Revenues: Sep 2026 = {rev_sep}, Oct 2026 = {rev_oct}, Nov 2026 = {rev_nov}")
            
            # Payments for this enrollment
            pays = Payment.query.filter_by(enrollment_id=en.id).all()
            print("Payments for this enrollment:")
            for p in pays:
                print(f"   Payment {p.id}: receipt={p.receipt}, amount={p.amount}, date={p.date}, note={p.note}")

        # All enrollments for this student
        all_ens = Enrollment.query.filter_by(student_id=s_id).all()
        print("All Enrollments for student:")
        for e in all_ens:
            c_name = e.course.name if e.course else 'None'
            t_name = e.course.teacher.full_name if e.course and e.course.teacher else 'None'
            print(f"   Enroll {e.id}: Course {e.course_id} ({c_name}) | Teacher: {t_name} | status={e.status} | enroll_date={e.enroll_date} | total_paid={e.total_paid} | Oct Rev={calculate_enrollment_revenue_for_month(e, 2026, 10)}")

        # All payments for student
        all_pays = Payment.query.filter_by(student_id=s_id).all()
        print("All Payments for student:")
        for p in all_pays:
            print(f"   Payment {p.id}: enroll_id={p.enrollment_id}, receipt={p.receipt}, amount={p.amount}, date={p.date}, note={p.note}")

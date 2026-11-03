from app import app, db, Teacher, Course, Enrollment, Payment, Student
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    st = Student.query.get(123)
    print(f"Student 123: {st.full_name}")
    for en in Enrollment.query.filter_by(student_id=123).all():
        print(f"Enroll {en.id}: course={en.course_id}, status={en.status}, enroll_date={en.enroll_date}, total_paid={en.total_paid}, monthly={en.monthly_price}, calc={en.calculated_price}, dur={en.duration_months}, notes={en.notes}")
        for p in Payment.query.filter_by(enrollment_id=en.id).all():
            print(f"   Pay {p.id}: {p.amount} DH, date={p.date}, receipt={p.receipt}, note={p.note}")
            
    en = Enrollment.query.filter_by(student_id=123).first()
    print("\nSimulating revenue by month for Enroll", en.id)
    for y, m in [(2026, 9), (2026, 10), (2026, 11), (2026, 12)]:
        rev = calculate_enrollment_revenue_for_month(en, y, m)
        print(f"   Month {y}-{m:02d}: {rev} DH")

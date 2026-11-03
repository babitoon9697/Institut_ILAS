from app import app, db, Teacher, Course, Enrollment, Payment, Student
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    st = Student.query.get(402)
    print(f"Student 402: {st.full_name}")
    for en_id in [831, 832, 833]:
        en = Enrollment.query.get(en_id)
        c = en.course
        print(f"\nEnroll {en.id}: Course {c.id} ({c.name}) | Teacher: {c.teacher.full_name if c.teacher else 'None'}")
        print(f"   monthly_price={en.monthly_price}, calculated_price={en.calculated_price}, dur={en.duration_months}")
        print(f"   enroll_date={en.enroll_date}, end_date={getattr(en, 'end_date', None)}, notes={en.notes}")
        for p in Payment.query.filter_by(enrollment_id=en.id).all():
            print(f"   Payment {p.id}: {p.amount} DH, date={p.date}, note={p.note}")
            
        rev_oct = calculate_enrollment_revenue_for_month(en, 2026, 10)
        rev_nov = calculate_enrollment_revenue_for_month(en, 2026, 11)
        print(f"   Revenue Oct 2026: {rev_oct} DH | Nov 2026: {rev_nov} DH")

from app import app, db, Teacher, Course, Enrollment, Payment, Student
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    for s_id in [274, 275, 309, 408]:
        st = Student.query.get(s_id)
        print(f"\n=======================================================")
        print(f"STUDENT {s_id}: {st.full_name}")
        print(f"=======================================================")
        for en in Enrollment.query.filter_by(student_id=s_id).all():
            c = en.course
            t = c.teacher if c else None
            print(f"Enroll {en.id}: Course {en.course_id} ({c.name if c else 'None'}) | Prof: {t.full_name if t else 'None'} | status={en.status} | total_paid={en.total_paid} | notes={en.notes}")
            print(f"   Oct Rev: {calculate_enrollment_revenue_for_month(en, 2026, 10)}")
            for p in Payment.query.filter_by(enrollment_id=en.id).all():
                print(f"      Pay {p.id}: {p.amount} DH, date={p.date}, note={p.note}")

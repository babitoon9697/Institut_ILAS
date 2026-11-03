from app import app, db, Teacher, Course, Enrollment, Payment, Student
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    print("=== AGMAR ABDELHAMID ===")
    st = Student.query.get(408)
    for en in Enrollment.query.filter_by(student_id=408).all():
        print(f"Enroll {en.id}: course={en.course_id} ({en.course.name if en.course else 'None'}), status={en.status}, enroll_date={en.enroll_date}, total_paid={en.total_paid}, notes={en.notes}")
        for p in Payment.query.filter_by(enrollment_id=en.id).all():
            print(f"   Pay {p.id}: {p.amount} DH, date={p.date}, note={p.note}")
            
    print("\n=== ELBAZ OUMAIMA ===")
    st = Student.query.get(320)
    for en in Enrollment.query.filter_by(student_id=320).all():
        print(f"Enroll {en.id}: course={en.course_id} ({en.course.name if en.course else 'None'}), status={en.status}, enroll_date={en.enroll_date}, total_paid={en.total_paid}, notes={en.notes}")
        for p in Payment.query.filter_by(enrollment_id=en.id).all():
            print(f"   Pay {p.id}: {p.amount} DH, date={p.date}, note={p.note}")

    print("\n=== ARIAM ELHOUSSNI ===")
    st = Student.query.get(140)
    for en in Enrollment.query.filter_by(student_id=140).all():
        print(f"Enroll {en.id}: course={en.course_id} ({en.course.name if en.course else 'None'}), status={en.status}, enroll_date={en.enroll_date}, total_paid={en.total_paid}, notes={en.notes}")
        for p in Payment.query.filter_by(enrollment_id=en.id).all():
            print(f"   Pay {p.id}: {p.amount} DH, date={p.date}, note={p.note}")

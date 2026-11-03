from app import app, db, Teacher, Course, Enrollment, Payment, Student
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    c = Course.query.get(39)
    print(f"Course 39: {c.name}")
    print(f"Teachers for Course 39:")
    for ct in c.teacher_assignments:
        print(f"   Teacher {ct.teacher_id} ({ct.teacher.full_name}): type={ct.compensation_type}, val={ct.compensation_value}, active={ct.is_active}")

    # Check Ariam Elhoussni (ID 140)
    en233 = Enrollment.query.get(233)
    en766 = Enrollment.query.get(766)
    rev233_sep = calculate_enrollment_revenue_for_month(en233, 2026, 9)
    rev233_oct = calculate_enrollment_revenue_for_month(en233, 2026, 10)
    rev766_oct = calculate_enrollment_revenue_for_month(en766, 2026, 10)
    print(f"\nEnroll 233 (Sept): Sep Rev = {rev233_sep}, Oct Rev (Arrears caught up) = {rev233_oct}")
    print(f"Enroll 766 (Oct): Oct Rev = {rev766_oct}")
    
    # In teachers_payroll:
    # student_enrolls_map combines both enrollments for Ariam!
    total_rev_ariam = rev233_oct + rev766_oct
    print(f"Total month rev for Ariam in Oct: {total_rev_ariam} DH")
    print(f"Primary enroll monthly_price: {en766.monthly_price} DH")
    capped_tuition = min(total_rev_ariam, en766.monthly_price or 300.0)
    print(f"Capped tuition used for teachers: {capped_tuition} DH")

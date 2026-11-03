import datetime
from app import app, db, Teacher, Course, Enrollment, Payment, Student, CourseTeacher
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    print("=== AUDIT OF ALL OCTOBER 2026 PAYMENTS (416 PAYMENTS) ===")
    
    oct_pays = Payment.query.filter(Payment.date >= '2026-10-01', Payment.date <= '2026-10-31').all()
    
    total_oct_paid = sum(p.amount for p in oct_pays)
    print(f"Total October Cash Received: {total_oct_paid:.2f} DH ({len(oct_pays)} payments)")
    
    # Categorize all October payments
    categorized = {
        'book_sales': [],
        'regular_enrollment': [],
        'no_enrollment': [],
        'dropped_enrollment': [],
        'transferred_enrollment': [],
        'future_enrollment_nov': [],
        'zero_amount': [],
        'negative_amount': []
    }
    
    for p in oct_pays:
        if p.amount == 0:
            categorized['zero_amount'].append(p)
            continue
        if p.amount < 0:
            categorized['negative_amount'].append(p)
            continue
        if not p.enrollment_id:
            if 'Vente Manuel' in (p.note or ''):
                categorized['book_sales'].append(p)
            else:
                categorized['no_enrollment'].append(p)
            continue
            
        en = Enrollment.query.get(p.enrollment_id)
        if not en:
            categorized['no_enrollment'].append(p)
            continue
            
        if en.status == 'dropped':
            categorized['dropped_enrollment'].append((p, en))
        elif en.status == 'transferred':
            categorized['transferred_enrollment'].append((p, en))
        elif en.enroll_date and en.enroll_date >= datetime.date(2026, 11, 1):
            categorized['future_enrollment_nov'].append((p, en))
        else:
            categorized['regular_enrollment'].append((p, en))

    print(f"1. Book Sales: {len(categorized['book_sales'])} payments, Total = {sum(p.amount for p in categorized['book_sales']):.2f} DH")
    print(f"2. Payments without Enrollment ID: {len(categorized['no_enrollment'])} payments, Total = {sum(p.amount for p in categorized['no_enrollment']):.2f} DH")
    print(f"3. Payments with Dropped Enrollments: {len(categorized['dropped_enrollment'])} payments, Total = {sum(p.amount for p, en in categorized['dropped_enrollment']):.2f} DH")
    print(f"4. Payments with Transferred Enrollments: {len(categorized['transferred_enrollment'])} payments, Total = {sum(p.amount for p, en in categorized['transferred_enrollment']):.2f} DH")
    print(f"5. Future (Nov) Enrollments paid in Oct: {len(categorized['future_enrollment_nov'])} payments, Total = {sum(p.amount for p, en in categorized['future_enrollment_nov']):.2f} DH")
    print(f"6. Zero Amount Payments: {len(categorized['zero_amount'])} payments")
    print(f"7. Negative (Refunds): {len(categorized['negative_amount'])} payments, Total = {sum(p.amount for p in categorized['negative_amount']):.2f} DH")
    print(f"8. Regular Active/Completed Enrollments: {len(categorized['regular_enrollment'])} payments, Total = {sum(p.amount for p, en in categorized['regular_enrollment']):.2f} DH")

    print("\n--- DETAILS OF DROPPED / TRANSFERRED PAYMENTS IN OCT ---")
    for p, en in categorized['dropped_enrollment']:
        print(f"Dropped: Pay {p.id}, {p.amount} DH, Receipt: {p.receipt}, Enroll {en.id}, Course {en.course_id}, Student {p.student_id}, Note: {p.note}")
    for p, en in categorized['transferred_enrollment']:
        print(f"Transferred: Pay {p.id}, {p.amount} DH, Receipt: {p.receipt}, Enroll {en.id}, Course {en.course_id}, Student {p.student_id}, Note: {p.note}")

    print("\n--- DETAILS OF FUTURE (NOV) ENROLLMENTS PAID IN OCT ---")
    for p, en in categorized['future_enrollment_nov']:
        c_name = en.course.name if en.course else 'None'
        t_name = en.course.teacher.full_name if en.course and en.course.teacher else 'None'
        print(f"Future: Pay {p.id}, {p.amount} DH, Date: {p.date}, Enroll {en.id} (Starts {en.enroll_date}), Course: {c_name}, Prof: {t_name}, Student {p.student_id}")

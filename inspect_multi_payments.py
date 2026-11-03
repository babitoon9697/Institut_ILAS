from app import app, db, Teacher, Course, Enrollment, Payment, Student, Invoice, InvoiceItem

with app.app_context():
    print("=== 1. FINDING RECEIPTS WITH MULTIPLE PAYMENTS (MULTI-ENROLLMENT OR MULTI-STUDENT) ===")
    
    # Receipts that appear multiple times in payments table
    from collections import defaultdict
    receipt_groups = defaultdict(list)
    for p in Payment.query.filter(Payment.receipt.isnot(None)).all():
        receipt_groups[p.receipt].append(p)
        
    multi_pay_receipts = {r: plist for r, plist in receipt_groups.items() if len(plist) > 1}
    print(f"Total receipts with multiple payments: {len(multi_pay_receipts)}")
    
    # Check which ones have different students vs same student
    diff_students = []
    same_student_diff_courses = []
    same_student_same_course = []
    
    for r, plist in multi_pay_receipts.items():
        st_ids = set(p.student_id for p in plist if p.student_id)
        en_ids = set(p.enrollment_id for p in plist if p.enrollment_id)
        
        if len(st_ids) > 1:
            diff_students.append((r, plist))
        elif len(en_ids) > 1:
            same_student_diff_courses.append((r, plist))
        else:
            same_student_same_course.append((r, plist))
            
    print(f"   -> Multi-student receipts (e.g. siblings / brothers & sisters): {len(diff_students)}")
    print(f"   -> Same student, multiple courses (e.g. Packs / multi-matières): {len(same_student_diff_courses)}")
    print(f"   -> Same student, same enrollment (e.g. installments / multiple parts): {len(same_student_same_course)}")

    print("\n--- A. SAMPLE MULTI-STUDENT RECEIPTS (SIBLINGS) ---")
    for r, plist in diff_students[:10]:
        print(f"Receipt: {r} (Date: {plist[0].date})")
        for p in plist:
            st = Student.query.get(p.student_id) if p.student_id else None
            en = Enrollment.query.get(p.enrollment_id) if p.enrollment_id else None
            c_name = en.course.name if en and en.course else 'None'
            t_name = en.course.teacher.full_name if en and en.course and en.course.teacher else 'None'
            print(f"   Payment {p.id}: Student {p.student_id} ({st.full_name if st else 'None'}) | Enroll {p.enrollment_id} | Course: {c_name} | Prof: {t_name} | Amount: {p.amount} DH | Note: {p.note}")

    print("\n--- B. SAMPLE MULTI-COURSE PACK RECEIPTS (SAME STUDENT) IN OCT 2026 ---")
    oct_packs = [item for item in same_student_diff_courses if any(p.date and p.date.strftime('%Y-%m') == '2026-10' for p in item[1])]
    print(f"Total multi-course receipts in October 2026: {len(oct_packs)}")
    for r, plist in oct_packs[:10]:
        print(f"\nReceipt: {r} (Date: {plist[0].date})")
        for p in plist:
            st = Student.query.get(p.student_id) if p.student_id else None
            en = Enrollment.query.get(p.enrollment_id) if p.enrollment_id else None
            c_name = en.course.name if en and en.course else 'None'
            t_name = en.course.teacher.full_name if en and en.course and en.course.teacher else 'None'
            print(f"   Payment {p.id}: Student {p.student_id} ({st.full_name if st else 'None'}) | Enroll {p.enrollment_id} | Course: {c_name} | Prof: {t_name} | Amount: {p.amount} DH | MonthlyPrice: {en.monthly_price if en else 'N/A'}")

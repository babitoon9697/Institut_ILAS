from app import app, db, Teacher, Course, Enrollment, Payment, Student
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    y, m = 2026, 10
    print("=== CHECKING THE MONTHLY_PRICE CAPPING EFFECT ACROSS ALL STUDENTS IN OCT 2026 ===")
    
    courses = Course.query.filter_by(active=True).all()
    capping_losses = []
    
    for c in courses:
        all_c_enrolls = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').order_by(Enrollment.id.desc()).all()
        student_enrolls_map = {}
        
        for en in all_c_enrolls:
            st = en.student
            if not st or st.status != 'active': continue
            rev = calculate_enrollment_revenue_for_month(en, y, m)
            if en.status == 'transferred':
                if rev <= 0: continue
                if not Enrollment.query.filter_by(student_id=en.student_id, status='active').first(): continue
            else:
                if not (rev > 0 or (en.enroll_date and en.enroll_date.year == y and en.enroll_date.month == m) or (en.end_date and en.end_date.year == y and en.end_date.month == m)):
                    continue
            if st.id not in student_enrolls_map:
                student_enrolls_map[st.id] = {'primary_enrollment': en, 'total_month_rev': 0.0, 'enrollments': []}
            student_enrolls_map[st.id]['total_month_rev'] += rev
            student_enrolls_map[st.id]['enrollments'].append(en)
            if en.status == 'active' or student_enrolls_map[st.id]['primary_enrollment'].status != 'active':
                student_enrolls_map[st.id]['primary_enrollment'] = en

        for s_id, s_info in student_enrolls_map.items():
            primary_en = s_info['primary_enrollment']
            std_price = primary_en.monthly_price or (c.price_per_month or c.price or 300.0)
            raw_rev = s_info['total_month_rev']
            
            # Check actual cash paid by student in October for this course's enrollments
            st_en_ids = [e.id for e in s_info['enrollments']]
            oct_cash_paid = db.session.query(db.func.sum(Payment.amount))\
                .filter(Payment.enrollment_id.in_(st_en_ids))\
                .filter(Payment.date >= '2026-10-01', Payment.date <= '2026-10-31').scalar() or 0.0
            
            if raw_rev > std_price:
                diff = raw_rev - std_price
                capping_losses.append({
                    'course_id': c.id,
                    'course_name': c.name,
                    'student_id': s_id,
                    'student_name': primary_en.student.full_name,
                    'raw_rev': raw_rev,
                    'std_price_cap': std_price,
                    'capped_loss': diff,
                    'oct_cash_paid': oct_cash_paid,
                    'num_enrollments': len(s_info['enrollments'])
                })

    print(f"Total students where revenue was capped below raw_rev: {len(capping_losses)}")
    for item in capping_losses:
        print(f"Student: {item['student_name']} (ID {item['student_id']}) in Course {item['course_id']} ({item['course_name']})")
        print(f"   -> Raw Rev: {item['raw_rev']:.2f} DH, Capped to: {item['std_price_cap']:.2f} DH (Lost: {item['capped_loss']:.2f} DH) | Oct Cash Paid: {item['oct_cash_paid']:.2f} DH | Enrollments: {item['num_enrollments']}")

from app import app, db, Teacher, Course, Enrollment, Payment, CourseTeacher
from app import calculate_enrollment_revenue_for_month

with app.app_context():
    # Let's inspect Teacher 15, 17, 18
    for t_id in [15, 17, 18]:
        teacher = Teacher.query.get(t_id)
        print(f"\n=======================================================")
        print(f"INVESTIGATING TEACHER {t_id}: {teacher.full_name}")
        print(f"=======================================================")
        
        assigned_cts = CourseTeacher.query.filter_by(teacher_id=t_id, is_active=True).all()
        assigned_courses = [ct.course for ct in assigned_cts if ct.course and ct.course.active]
        direct_courses = Course.query.filter_by(teacher_id=t_id, active=True).all()
        for c in direct_courses:
            if c not in assigned_courses:
                assigned_courses.append(c)
                
        y, m = 2026, 10
        for c in assigned_courses:
            ct = CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t_id, is_active=True).first() or \
                 CourseTeacher.query.filter_by(course_id=c.id, teacher_id=t_id).first()
            comp_type = ct.compensation_type if ct else 'percentage'
            comp_val = ct.compensation_value if ct else 50.0

            # Method A: as in get_single_teacher_payroll_details (ordered by Enrollment.id.desc())
            enrolls_A = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').order_by(Enrollment.id.desc()).all()
            # Method B: as in _calculate_period_teacher_payroll (NO ORDER BY)
            enrolls_B = Enrollment.query.filter_by(course_id=c.id).filter(Enrollment.status != 'dropped').all()

            # Let's see map A
            map_A = {}
            for en in enrolls_A:
                st = en.student
                if not st: continue
                rev = calculate_enrollment_revenue_for_month(en, y, m)
                if en.status == 'transferred':
                    if rev <= 0: continue
                    if not Enrollment.query.filter_by(student_id=en.student_id, status='active').first(): continue
                else:
                    if not (rev > 0 or (en.enroll_date and en.enroll_date.year == y and en.enroll_date.month == m) or (en.end_date and en.end_date.year == y and en.end_date.month == m)):
                        continue
                if st.id not in map_A:
                    map_A[st.id] = {'primary_enrollment': en, 'total_month_rev': 0.0, 'enrollments': []}
                map_A[st.id]['total_month_rev'] += rev
                map_A[st.id]['enrollments'].append(en)
                if en.status == 'active' or map_A[st.id]['primary_enrollment'].status != 'active':
                    map_A[st.id]['primary_enrollment'] = en

            # Let's see map B
            map_B = {}
            for en in enrolls_B:
                st = en.student
                if not st: continue
                rev = calculate_enrollment_revenue_for_month(en, y, m)
                if en.status == 'transferred':
                    if rev <= 0: continue
                    if not Enrollment.query.filter_by(student_id=en.student_id, status='active').first(): continue
                else:
                    if not (rev > 0 or (en.enroll_date and en.enroll_date.year == y and en.enroll_date.month == m) or (en.end_date and en.end_date.year == y and en.end_date.month == m)):
                        continue
                if st.id not in map_B:
                    map_B[st.id] = {'primary_enrollment': en, 'total_month_rev': 0.0}
                map_B[st.id]['total_month_rev'] += rev

            # Compare student groups
            rev_A = sum(min(s['total_month_rev'], s['primary_enrollment'].monthly_price or 300.0) for s in map_A.values() if s['total_month_rev'] > 0)
            rev_B = sum(min(s['total_month_rev'], getattr(s['primary_enrollment'], 'unit_monthly_price', None) or s['primary_enrollment'].monthly_price or (c.unit_monthly_price if hasattr(c, 'unit_monthly_price') else (c.price_per_month or c.price or 300.0))) for s in map_B.values() if s['total_month_rev'] > 0)
            
            diff = abs(rev_A - rev_B)
            if diff > 0.01:
                print(f"Course {c.id} ({c.name}): rev_A = {rev_A:.2f}, rev_B = {rev_B:.2f}, diff = {diff:.2f}")
                # Print students that differ
                for s_id in set(list(map_A.keys()) + list(map_B.keys())):
                    info_A = map_A.get(s_id)
                    info_B = map_B.get(s_id)
                    en_A = info_A['primary_enrollment'].id if info_A else None
                    en_B = info_B['primary_enrollment'].id if info_B else None
                    if en_A != en_B:
                        print(f"   Student {s_id}: primary in A is {en_A} (status={info_A['primary_enrollment'].status}, monthly={info_A['primary_enrollment'].monthly_price}), primary in B is {en_B} (status={info_B['primary_enrollment'].status}, monthly={info_B['primary_enrollment'].monthly_price})")

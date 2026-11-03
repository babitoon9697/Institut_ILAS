from app import app, db, Teacher, Course, Enrollment, Payment, Student

with app.app_context():
    print("=== CHECKING STUDENTS WITH FAMILY CODE ===")
    fam_students = Student.query.filter(Student.family_code.isnot(None), Student.family_code != '').all()
    print(f"Total students with family_code: {len(fam_students)}")
    
    from collections import defaultdict
    families = defaultdict(list)
    for s in fam_students:
        families[s.family_code].append(s)
        
    for fcode, slist in families.items():
        print(f"\nFamily Code: {fcode} ({len(slist)} members)")
        for s in slist:
            print(f"   Student {s.id}: {s.full_name} | status={s.status}")
            for en in Enrollment.query.filter_by(student_id=s.id, status='active').all():
                c = en.course
                print(f"      Active Enroll {en.id}: Course {c.id} ({c.name if c else 'None'}) | MonthlyPrice: {en.monthly_price} | TotalPaid: {en.total_paid}")
                for p in Payment.query.filter_by(enrollment_id=en.id).all():
                    print(f"         Payment {p.id}: {p.amount} DH, date={p.date}, receipt={p.receipt}, note={p.note}")

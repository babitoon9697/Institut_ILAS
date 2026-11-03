import os
from datetime import date
from app import app, db, Enrollment, Compensation, calculate_enrollment_revenue_for_month

artifact_path = r'C:\Users\Meriem\.gemini\antigravity\brain\10d23b3c-c8ad-4f8a-acee-e0b9b41d06db\production_audit.md'

with app.app_context():
    enrollments = Enrollment.query.all()
    
    with open(artifact_path, 'w', encoding='utf-8') as f:
        f.write('# 🏢 Audit Complet - Base de Données de Production\n\n')
        f.write('Ce rapport détaille chaque inscription avec les dates, la répartition financière, et la part de l\'école vs l\'enseignant.\n\n')
        f.write('| Code | Élève | Cours | Début | Fin (Calculée) | Payé (Net) | Mois | Rev. Mois | Part Prof | Part École | Reste à allouer (Futur) |\n')
        f.write('|---|---|---|---|---|---|---|---|---|---|---|\n')
        
        for e in enrollments:
            if not e.student: continue
            
            # Finances
            tot_paid = float(e.total_paid or 0.0)
            if e.calculated_price is not None and e.monthly_price is not None:
                reg_fee = max(0.0, float(e.calculated_price) - float(e.monthly_price))
            else:
                reg_fee = float(e.course.registration_fee or 0.0) if e.course else 0.0
            tuition_paid = max(0.0, tot_paid - reg_fee)
            
            # Dates
            start_dt = str(e.enroll_date) if e.enroll_date else 'N/A'
            end_dt = str(e.end_date) if e.end_date else 'N/A'
            cname = e.course.name if e.course else '-'
            
            # Teacher Comp
            prof_type = 'N/A'
            prof_val = 0.0
            if e.course and e.course.teacher:
                comp = Compensation.query.filter_by(teacher_id=e.course.teacher_id, course_id=e.course.id).first()
                if comp:
                    prof_type = comp.comp_type
                    prof_val = comp.comp_val
            
            # Timeline
            start_m = e.enroll_date.month if e.enroll_date else 8
            start_y = e.enroll_date.year if e.enroll_date else 2026
            
            # Calculate distributed revenues
            revs = []
            total_allocated = 0
            for i in range(12):
                m = start_m + i
                y = start_y
                while m > 12:
                    m -= 12
                    y += 1
                rev = calculate_enrollment_revenue_for_month(e, y, m)
                if rev > 0:
                    revs.append((y, m, rev))
                    total_allocated += rev
            
            # Format rows
            mois_str = []
            rev_str = []
            prof_str = []
            ecole_str = []
            
            rem_tuition = tuition_paid
            for (y, m, rev) in revs:
                mois_str.append(f'{m:02d}/{y}')
                rev_str.append(f'{rev:.2f}')
                
                # Calculate Teacher/School shares
                if prof_type == 'percentage':
                    t_share = round(rev * (prof_val / 100.0), 2)
                    s_share = round(rev - t_share, 2)
                    prof_str.append(f'{t_share:.2f} ({prof_val}%)')
                    ecole_str.append(f'{s_share:.2f}')
                elif prof_type == 'fixed':
                    prof_str.append('Fixe')
                    ecole_str.append(f'{rev:.2f}')
                elif prof_type == 'hourly':
                    prof_str.append('Horaire')
                    ecole_str.append(f'{rev:.2f}')
                elif prof_type == 'per_student':
                    t_share = round(prof_val, 2)
                    s_share = round(rev - t_share, 2)
                    prof_str.append(f'{t_share:.2f}')
                    ecole_str.append(f'{s_share:.2f}')
                else:
                    prof_str.append('-')
                    ecole_str.append(f'{rev:.2f}')
                    
                rem_tuition -= rev
                
            if not revs:
                mois_str = ['-']
                rev_str = ['0.00']
                prof_str = ['-']
                ecole_str = ['0.00']
                
            sep = "<br>"
            
            f.write(f'| {e.student.code} | {e.student.full_name} | {cname} | {start_dt} | {end_dt} | {tuition_paid:.2f} | ')
            f.write(f'{sep.join(mois_str)} | ')
            f.write(f'{sep.join(rev_str)} | ')
            f.write(f'{sep.join(prof_str)} | ')
            f.write(f'{sep.join(ecole_str)} | ')
            f.write(f'{max(0.0, rem_tuition):.2f} |\n')
            
print('Production Audit Created!')

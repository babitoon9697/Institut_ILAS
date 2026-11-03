import sys
import os
from datetime import datetime, date, timedelta
from app import app, db
from models import Student, Enrollment, Course, Invoice, Payment, Attendance

def audit():
    with app.app_context():
        students = Student.query.order_by(Student.id).all()
        categories = {
            'multi_month_short_duration': [],
            'frais_inscription_missing_in_calculated_price': [],
            'partial_payment_full_month': [],
            'overpaid_vs_due': [],
            'unlinked_payments': [],
            'att_after_expiry': [],
            'invoice_sum_mismatch': [],
            'active_in_august_not_renewed': []
        }

        # 1. Check Invoice sum mismatches
        for inv in Invoice.query.all():
            items_sum = sum(it.amount for it in inv.items)
            if abs(items_sum - inv.total) > 0.05 and len(inv.items) > 0:
                s = inv.student
                code = s.code if s else 'N/A'
                name = s.full_name if s else 'N/A'
                categories['invoice_sum_mismatch'].append({
                    'student': f"[{code}] {name}",
                    'inv_id': inv.id,
                    'inv_num': inv.number,
                    'total': inv.total,
                    'items_sum': items_sum,
                    'items': [(it.description, it.amount) for it in inv.items]
                })

        # 2. Check Students & Enrollments
        for s in students:
            enrs = Enrollment.query.filter_by(student_id=s.id).order_by(Enrollment.id).all()
            pays = Payment.query.filter_by(student_id=s.id).all()

            # Check unlinked payments
            unlinked = [p for p in pays if not p.enrollment_id]
            for p in unlinked:
                is_book = 'manuel' in (p.note or '').lower() or 'livre' in (p.note or '').lower()
                categories['unlinked_payments'].append({
                    'student': f"[{s.code}] {s.full_name}",
                    'pay_id': p.id,
                    'amount': p.amount,
                    'date': p.date,
                    'note': p.note,
                    'type': 'Vente Livre/Manuel' if is_book else 'Paiement sans Inscription'
                })

            for e in enrs:
                c = e.course
                if not c:
                    continue
                e_pays = [p for p in pays if p.enrollment_id == e.id]
                total_p = sum(p.amount for p in e_pays)
                monthly = float(e.monthly_price or c.price or 0.0)
                calc_p = float(e.calculated_price or 0.0)
                due = float(e.due_amount or monthly)
                start = e.enroll_date
                end = e.end_date
                custom_end = e.custom_end_date
                days_span = (end - start).days if (start and end) else 0

                # Multi-month payment but short date span
                if monthly > 0 and total_p >= (monthly * 1.7):
                    months_covered = round(total_p / monthly, 1)
                    expected_days = int(round(months_covered * 30))
                    if days_span < (expected_days - 15):
                        categories['multi_month_short_duration'].append({
                            'student': f"[{s.code}] {s.full_name}",
                            'enr_id': e.id,
                            'status': e.status,
                            'course': c.display_name,
                            'paid': total_p,
                            'monthly': monthly,
                            'months_covered': months_covered,
                            'start': start,
                            'end': end,
                            'custom_end': custom_end,
                            'days_span': days_span,
                            'notes': e.notes
                        })

                # Frais d'inscription in notes but omitted in calculated_price
                notes_lower = (e.notes or '').lower()
                if "frais d'inscription:" in notes_lower:
                    try:
                        part = notes_lower.split("frais d'inscription:")[1].split("dh")[0].strip()
                        fee = float(part)
                        if fee > 0 and calc_p > 0 and abs(calc_p - monthly) < 1.0:
                            categories['frais_inscription_missing_in_calculated_price'].append({
                                'student': f"[{s.code}] {s.full_name}",
                                'enr_id': e.id,
                                'course': c.display_name,
                                'monthly': monthly,
                                'calc_price': calc_p,
                                'frais_in_notes': fee,
                                'paid': total_p,
                                'notes': e.notes
                            })
                    except Exception:
                        pass

                # Partial payment with custom_end_date spanning full month
                if 0 < total_p < due and custom_end and start:
                    custom_span = (custom_end - start).days
                    if custom_span >= 25:
                        categories['partial_payment_full_month'].append({
                            'student': f"[{s.code}] {s.full_name}",
                            'enr_id': e.id,
                            'status': e.status,
                            'course': c.display_name,
                            'paid': total_p,
                            'due': due,
                            'balance': due - total_p,
                            'paid_sessions': e.paid_sessions,
                            'total_cycle_sessions': e.total_cycle_sessions,
                            'start': start,
                            'custom_end': custom_end,
                            'computed_end': end,
                            'custom_span': custom_span
                        })

                # Overpaid vs Due
                if due > 0 and total_p > (due + 15.0) and total_p < (monthly * 1.7):
                    categories['overpaid_vs_due'].append({
                        'student': f"[{s.code}] {s.full_name}",
                        'enr_id': e.id,
                        'course': c.display_name,
                        'paid': total_p,
                        'due': due,
                        'excess': total_p - due,
                        'notes': e.notes
                    })

                # Active subscription ended in August and never renewed in September
                if e.status == 'active' and end and end <= date(2026, 8, 31):
                    # Check if student has a renewal for this course
                    has_renewal = any(other.id != e.id and other.course_id == e.course_id and (other.enroll_date or date.min) >= date(2026, 9, 1) for other in enrs)
                    if not has_renewal:
                        categories['active_in_august_not_renewed'].append({
                            'student': f"[{s.code}] {s.full_name}",
                            'enr_id': e.id,
                            'course': c.display_name,
                            'end': end,
                            'paid': total_p,
                            'due': due
                        })

        # 3. Check Attendance after end_date
        for att in Attendance.query.all():
            enrs = Enrollment.query.filter_by(student_id=att.student_id, course_id=att.course_id).all()
            covered = False
            for e in enrs:
                if e.enroll_date and e.end_date and (e.enroll_date <= att.date <= e.end_date):
                    covered = True
                    break
            if not covered:
                latest_e = sorted(enrs, key=lambda x: x.end_date or date.min, reverse=True)
                e = latest_e[0] if latest_e else None
                s = db.session.get(Student, att.student_id)
                c = db.session.get(Course, att.course_id)
                categories['att_after_expiry'].append({
                    'student': f"[{s.code if s else '?'}] {s.full_name if s else '?'}",
                    'course': c.display_name if c else '?',
                    'att_date': att.date,
                    'status': att.status,
                    'last_end_date': e.end_date if e else None,
                    'enr_status': e.status if e else 'None'
                })

        print("="*80)
        print("RAPPORT SYNTHÉTIQUE DES ERREURS DÉTECTÉES PAR CATÉGORIE")
        print("="*80)
        print(f"1. Inscriptions multi-mois avec dates tronquées : {len(categories['multi_month_short_duration'])}")
        print(f"2. Frais d'inscription omis dans le prix dû (créant un faux excédent) : {len(categories['frais_inscription_missing_in_calculated_price'])}")
        print(f"3. Paiements partiels avec custom_end_date fixée à un mois plein : {len(categories['partial_payment_full_month'])}")
        print(f"4. Autres excédents de paiement non justifiés : {len(categories['overpaid_vs_due'])}")
        print(f"5. Paiements non liés à une inscription (manuels/livres vs scolarité) : {len(categories['unlinked_payments'])}")
        print(f"6. Factures avec doublon d'articles ou total erroné : {len(categories['invoice_sum_mismatch'])}")
        print(f"7. Inscriptions d'août restées 'active' sans renouvellement en septembre : {len(categories['active_in_august_not_renewed'])}")
        print(f"8. Séances d'assiduité enregistrées HORS période payée : {len(categories['att_after_expiry'])}")
        print("="*80)

        # Print details for each category
        for cat_name, items in categories.items():
            print(f"\n>>> DÉTAIL : {cat_name} ({len(items)} cas)")
            for it in items[:15]:
                print("   ", it)

if __name__ == '__main__':
    audit()

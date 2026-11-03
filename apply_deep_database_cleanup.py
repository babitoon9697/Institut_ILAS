import sys
import os
from datetime import datetime, date, timedelta
from app import app, db
from models import Student, Enrollment, Course, Invoice, InvoiceItem, Payment, Attendance, calculate_last_session_date

def run_cleanup():
    with app.app_context():
        print("="*75)
        print("DÉMARRAGE DU NETTOYAGE ET DE LA NORMALISATION DE LA BASE DE DONNÉES")
        print("="*75)

        # ---------------------------------------------------------
        # 1. FIX CALCULATED_PRICE FOR REGISTRATION FEE / INVOICE OMISSIONS
        # ---------------------------------------------------------
        print("\n--- 1. Harmonisation de calculated_price avec les montants payés/facturés ---")
        price_fixes = [
            (126, 240.0, "ILAS167 Aymane Jaf: calculated_price 200 -> 240 (200 scolarité + 40 frais)"),
            (213, 400.0, "ILAS196 Kawtar Fatih: calculated_price 350 -> 400 (350 scolarité + 50 frais)"),
            (214, 400.0, "ILAS197 Mohamed Fatih: calculated_price 350 -> 400 (350 scolarité + 50 frais)"),
            (131, 300.0, "ILAS033 Hajar Abassi: calculated_price 250 -> 300 (conforme facture #29)"),
            (130, 300.0, "ILAS034 Dounia El Hayati: calculated_price 250 -> 300 (conforme facture #28)"),
            (363, 260.0, "ILAS290 Ayoub Abrid: calculated_price 200 -> 260 (conforme facture #222)"),
        ]

        for eid, new_calc_price, desc in price_fixes:
            e = db.session.get(Enrollment, eid)
            if e:
                old_p = e.calculated_price
                e.calculated_price = new_calc_price
                print(f"   [OK] Enr #{eid}: {old_p} DH -> {new_calc_price} DH ({desc})")

        # ---------------------------------------------------------
        # 2. FIX CUSTOM_END_DATE FOR PARTIAL PAYMENTS
        # ---------------------------------------------------------
        print("\n--- 2. Recalcul et alignement des dates de fin pour les paiements partiels ---")
        partial_enrollments = Enrollment.query.filter(
            Enrollment.status.in_(['active', 'dropped', 'completed'])
        ).all()

        partial_fixed_count = 0
        for e in partial_enrollments:
            tot_paid = float(e.total_paid or 0.0)
            due = float(e.due_amount or 0.0)
            tot_cycle = e.total_cycle_sessions or 12

            if 0 < tot_paid < due and e.enroll_date and e.course:
                sched = e.scheduled_weekdays
                paid_sess = e.paid_sessions
                old_custom = e.custom_end_date

                if paid_sess > 0:
                    real_end = calculate_last_session_date(e.enroll_date, paid_sess, sched)
                else:
                    real_end = e.enroll_date

                if old_custom != real_end:
                    e.custom_end_date = real_end
                    s = e.student
                    code = s.code if s else '?'
                    name = s.full_name if s else '?'
                    print(f"   [OK] [{code}] {name} (Enr #{e.id} {e.course_name_display}): custom_end_date {old_custom} -> {real_end} (Payé {tot_paid}/{due} DH = {paid_sess}/{tot_cycle} séances)")
                    partial_fixed_count += 1

        print(f"   Total dates de fin partielles corrigées: {partial_fixed_count}")

        # ---------------------------------------------------------
        # 3. FIX DUPLICATE ITEMS IN INVOICE #6 (FA-0011)
        # ---------------------------------------------------------
        print("\n--- 3. Nettoyage des doublons sur la Facture #6 (FA-0011) ---")
        inv6 = db.session.get(Invoice, 6)
        if inv6:
            items = InvoiceItem.query.filter_by(invoice_id=6).order_by(InvoiceItem.id).all()
            print(f"   Facture #6 avant nettoyage: {len(items)} articles, Total={inv6.total} DH")
            # Keep first item (Item 8) and remove duplicate items 12 and 14
            for it in items[1:]:
                print(f"   [DELETE] Suppression article doublon #{it.id} ({it.description}, {it.amount} DH)")
                db.session.delete(it)

        # ---------------------------------------------------------
        # 4. MARK OLD AUGUST ENROLLMENTS AS 'COMPLETED'
        # ---------------------------------------------------------
        print("\n--- 4. Clôture des inscriptions expirées en août non renouvelées ---")
        aug_expired = Enrollment.query.filter(
            Enrollment.status == 'active',
            Enrollment.custom_end_date != None,
            Enrollment.custom_end_date <= date(2026, 8, 31)
        ).all()

        aug_closed_count = 0
        for e in aug_expired:
            e.status = 'completed'
            s = e.student
            code = s.code if s else '?'
            name = s.full_name if s else '?'
            print(f"   [COMPLETED] [{code}] {name} (Enr #{e.id} {e.course_name_display}) - Date fin: {e.custom_end_date}")
            aug_closed_count += 1

        print(f"   Total inscriptions d'août clôturées: {aug_closed_count}")

        # Commit all changes cleanly
        db.session.commit()
        print("\n" + "="*75)
        print("TOUTES LES MODIFICATIONS ONT ÉTÉ ENREGISTRÉES AVEC SUCCÈS DANS LA BASE !")
        print("="*75)

if __name__ == '__main__':
    run_cleanup()

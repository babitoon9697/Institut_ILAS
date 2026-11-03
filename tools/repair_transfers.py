# -*- coding: utf-8 -*-
"""
Script de régularisation rétroactive des transferts d'inscriptions.
Recalcule le prorata des cotisations et rééquilibre les paiements pour que les enseignants
historiques reçoivent leur part exacte sur les périodes enseignées.
"""

import os
import sys
import re
from datetime import datetime, date

# S'assurer que le répertoire racine est dans sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app, db, Enrollment, Course, Payment, calculate_transfer_split, parse_date


def repair_past_transfers(dry_run=False):
    with app.app_context():
        transferred_enrolls = Enrollment.query.filter_by(status='transferred').all()
        print(f"=== Analyse des transferts : {len(transferred_enrolls)} inscriptions 'transferred' trouvées ===")

        fixed_count = 0
        for e in transferred_enrolls:
            old_paid = float(e.total_paid or 0.0)
            print(f"\n[Dossier #{e.id}] Élève #{e.student_id} ({e.student.full_name if e.student else 'Inconnu'}) | Cours #{e.course_id} ({e.course.display_name if e.course else '-'})")
            print(f"   Payé actuel : {old_paid:.2f} DH | Tarif : {e.monthly_price or 0:.2f} DH")

            if old_paid > 0:
                print("   -> Ce dossier a déjà une part payée attribuée. Ignoré.")
                continue

            # Trouver la nouvelle inscription
            notes = e.notes or ''
            # Extraire la date de transfert depuis les notes (ex: 'le 06/09/2026')
            date_match = re.search(r'le\s+(\d{2}/\d{2}/\d{4})', notes)
            transfer_dt = None
            if date_match:
                try:
                    transfer_dt = datetime.strptime(date_match.group(1), '%d/%m/%Y').date()
                except Exception:
                    pass

            if not transfer_dt:
                transfer_dt = e.enroll_date or date.today()

            # Trouver le new_e associé
            candidate_news = Enrollment.query.filter_by(student_id=e.student_id)\
                .filter(Enrollment.id != e.id)\
                .filter(Enrollment.status == 'active')\
                .all()

            target_new_e = None
            for ne in candidate_news:
                ne_notes = ne.notes or ''
                if "Transféré depuis" in ne_notes or (ne.created_at and e.created_at and abs((ne.created_at - e.created_at).total_seconds()) < 86400 * 30):
                    target_new_e = ne
                    break

            if not target_new_e and candidate_news:
                target_new_e = candidate_news[-1]

            if not target_new_e:
                print("   -> Aucune nouvelle inscription correspondante trouvée. Ignoré.")
                continue

            target_course = target_new_e.course
            if not target_course:
                print("   -> Nouveau cours introuvable. Ignoré.")
                continue

            print(f"   -> Nouvelle inscription associée : #{target_new_e.id} | Cours : {target_course.display_name} | Date transfert : {transfer_dt.strftime('%d/%m/%Y')}")

            # Montant total à répartir
            total_tuition = float(target_new_e.monthly_price or e.monthly_price or 300.0)
            split_res = calculate_transfer_split(e, target_course, transfer_dt, custom_monthly_price=total_tuition, start_date=e.enroll_date, end_date=target_new_e.custom_end_date or target_new_e.end_date)

            old_share = split_res.get('old_share', round(total_tuition * 0.5, 2))
            new_share = split_res.get('new_share', round(total_tuition - old_share, 2))

            print(f"   -> Prorata calculé : Ancien cours (Prof {split_res.get('old_teacher_name')}) = {old_share:.2f} DH | Nouveau cours (Prof {split_res.get('new_teacher_name')}) = {new_share:.2f} DH")

            # Trouver les paiements qui sont actuellement sur target_new_e
            new_payments = Payment.query.filter_by(enrollment_id=target_new_e.id).order_by(Payment.id.asc()).all()
            tot_new_paid = sum(p.amount for p in new_payments)
            print(f"   -> Paiements actuels sur la nouvelle inscription : {tot_new_paid:.2f} DH")

            if not dry_run:
                # 1. Mettre à jour l'ancienne inscription
                e.custom_end_date = transfer_dt
                e.monthly_price = old_share
                e.calculated_price = old_share

                # 2. Mettre à jour la nouvelle inscription
                target_new_e.enroll_date = transfer_dt
                target_new_e.monthly_price = new_share
                target_new_e.calculated_price = new_share

                # 3. Rééquilibrer les paiements (rapatrier old_share vers e)
                amount_to_give_old = min(tot_new_paid, old_share)
                if amount_to_give_old > 0:
                    rem_to_give = amount_to_give_old
                    for p in reversed(new_payments):
                        if rem_to_give <= 0:
                            break
                        if p.amount <= rem_to_give + 0.001:
                            p.enrollment_id = e.id
                            p.note = (p.note or '') + f" [Régularisé vers inscription #{e.id}]"
                            rem_to_give = round(rem_to_give - p.amount, 2)
                        else:
                            # Split
                            p.amount = round(p.amount - rem_to_give, 2)
                            split_p = Payment(
                                receipt=f"{p.receipt}-RETRO" if p.receipt else "REC-RETRO",
                                enrollment_id=e.id,
                                student_id=e.student_id,
                                amount=rem_to_give,
                                method=p.method or 'cash',
                                date=p.date or transfer_dt,
                                note=f"Régularisation prorata transfert cours {e.course.display_name if e.course else ''}",
                                recorded_by=p.recorded_by,
                                invoice_id=p.invoice_id
                            )
                            db.session.add(split_p)
                            rem_to_give = 0.0
                            break

                db.session.commit()
                print(f"   [SUCCÈS] Dossier #{e.id} régularisé : Ancien prof reçoit paiement de {e.total_paid:.2f} DH, Nouveau prof garde {target_new_e.total_paid:.2f} DH")
            else:
                print(f"   [DRY-RUN] Prêt à régulariser : {old_share:.2f} DH -> #{e.id}, {new_share:.2f} DH -> #{target_new_e.id}")

            fixed_count += 1

        print(f"\n=== Fin du traitement : {fixed_count} transferts traités avec succès. ===")


if __name__ == '__main__':
    is_dry = '--dry-run' in sys.argv
    repair_past_transfers(dry_run=is_dry)

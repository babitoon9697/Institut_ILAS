import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from app import app, db
from models import Enrollment, calculate_last_session_date, timedelta

def run_fix():
    with app.app_context():
        all_ens = Enrollment.query.filter(Enrollment.status.in_(['active', 'completed', 'paused'])).all()
        updated_count = 0
        samples = []

        for e in all_ens:
            if not e.course_id or not e.enroll_date:
                continue
            sched = e.scheduled_weekdays
            if not sched:
                continue

            tot_s = e.total_sessions_month or (len(sched) * 4)
            if tot_s <= 0:
                continue

            # Calculate what the old literal last session was:
            cur = e.enroll_date
            cnt = 0
            old_last = None
            for _ in range(730):
                if cur.weekday() in sched:
                    cnt += 1
                    if cnt >= tot_s:
                        old_last = cur
                        break
                cur += timedelta(days=1)

            # Check if current custom_end_date was the old literal last session date
            if old_last and e.custom_end_date == old_last:
                new_end = calculate_last_session_date(e.enroll_date, tot_s, sched)
                if e.total_paused_days and e.total_paused_days > 0:
                    new_end += timedelta(days=e.total_paused_days)

                if new_end != e.custom_end_date:
                    old_val = e.custom_end_date
                    e.custom_end_date = new_end
                    e.clear_cache()
                    updated_count += 1
                    if len(samples) < 20:
                        s_name = e.student.full_name if e.student else f"Student #{e.student_id}"
                        samples.append((e.id, s_name, e.course_name_display, old_val, new_end))

        db.session.commit()
        print(f"[SUCCESS] Updated {updated_count} enrollments in the database.")
        print("\nSample of updated enrollments:")
        for eid, sname, cname, old_d, new_d in samples:
            print(f"  - Enr #{eid} ({sname}): {old_d} -> {new_d} [{cname}]")

if __name__ == '__main__':
    run_fix()

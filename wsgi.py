# -*- coding: utf-8 -*-
from app import app, auto_migrate_db, db, SH, seed_default_teacher_charges, User

with app.app_context():
    try:
        auto_migrate_db()
        db.create_all()
        SH.seed_defaults()
        seed_default_teacher_charges()
        if User.query.count() == 0:
            a = User(username='admin', full_name='Administrateur', role='admin', active=True)
            a.set_password('admin')
            db.session.add(a)
            db.session.commit()
            print(">>> [INIT] Admin user initialized: admin/admin")
    except Exception as e:
        print(f">>> [INIT] Startup notice: {e}")

if __name__ == '__main__':
    app.run()

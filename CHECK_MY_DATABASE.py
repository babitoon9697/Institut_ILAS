# -*- coding: utf-8 -*-
"""Diagnostic script to verify database contents and exact folder location."""

import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from app import app, db
from models import Student, Enrollment, Payment, Teacher, Course

db_path = os.path.join(BASE, 'institut.db')

print("==========================================================================")
print("  DIAGNOSTIC BASE DE DONNEES INSTITUT ILAS")
print("==========================================================================")
print(f"Dossier du projet (BASE) : {BASE}")
print(f"Fichier institut.db       : {db_path}")

if os.path.exists(db_path):
    size_kb = os.path.getsize(db_path) / 1024.0
    print(f"Taille du fichier         : {size_kb:.2f} KB")

    with app.app_context():
        st_count = Student.query.count()
        en_count = Enrollment.query.filter_by(status='active').count()
        pay_count = Payment.query.count()
        t_count = Teacher.query.filter_by(active=True).count()
        c_count = Course.query.filter_by(active=True).count()

        print(f"\n📊 CONTENU DE LA BASE DE DONNÉES ACTUELLE :")
        print(f"   * Total Élèves (Students)          : {st_count}")
        print(f"   * Inscriptions Actives (Enrollments): {en_count}")
        print(f"   * Total Paiements (Payments)       : {pay_count}")
        print(f"   * Enseignants Actifs (Teachers)    : {t_count}")
        print(f"   * Cours Actifs (Courses)           : {c_count}")

        if st_count > 0 and en_count > 0:
            print("\n✅ STATUT : LA BASE DE DONNÉES EST PARFAITEMENT REMPLIE ET VALVE !")
        else:
            print("\n❌ STATUT : LA BASE DE DONNÉES EST VIDE OU VIENT D'ETRE CREEE.")
            print("👉 Solution : Remplacez le fichier institut.db ci-dessus par le fichier institut.db de 208 KB.")
else:
    print("\n❌ ERREUR : Le fichier institut.db n'existe pas dans ce dossier.")

print("==========================================================================")

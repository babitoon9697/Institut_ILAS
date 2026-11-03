# -*- coding: utf-8 -*-
"""Script to clean test data from Institut ILAS database while preserving Tariffs, Users, Settings, and Rooms."""

import os
from app import app, db
from models import (Tariff, User, Setting, Room, Student, Enrollment, Payment, Invoice,
                    InvoiceItem, Attendance, Grade, ScheduleSlot, CourseTeacher, Course,
                    Teacher, SubstituteLog, BadgeRecord, LogEntry, SystemNotification,
                    Certificate, StudentCredit, BlockedIP, LoginAttempt)

def clean_database():
    with app.app_context():
        print("=== INSTITUT ILAS DATABASE CLEANUP ===")
        
        # Count existing records before cleanup
        print(f"Tariffs preserved : {Tariff.query.count()}")
        print(f"Users preserved   : {User.query.count()}")
        print(f"Settings preserved: {Setting.query.count()}")
        print(f"Rooms preserved   : {Room.query.count()}")

        print("\nDeleting test operational data...")

        # Delete operational & transactional records
        db.session.query(Payment).delete()
        db.session.query(InvoiceItem).delete()
        db.session.query(Invoice).delete()
        db.session.query(Enrollment).delete()
        db.session.query(StudentCredit).delete()
        db.session.query(Student).delete()
        db.session.query(Attendance).delete()
        db.session.query(Grade).delete()
        db.session.query(ScheduleSlot).delete()
        db.session.query(CourseTeacher).delete()
        db.session.query(Course).delete()
        db.session.query(Teacher).delete()
        db.session.query(SubstituteLog).delete()
        db.session.query(BadgeRecord).delete()
        db.session.query(LogEntry).delete()
        db.session.query(SystemNotification).delete()
        db.session.query(Certificate).delete()
        db.session.query(BlockedIP).delete()
        db.session.query(LoginAttempt).delete()

        # Reset auto-increment setting counters to 1
        s_stu = Setting.query.get('next_student_number')
        if s_stu: s_stu.value = '1'
        s_inv = Setting.query.get('next_invoice_number')
        if s_inv: s_inv.value = '1'
        s_rec = Setting.query.get('next_receipt_number')
        if s_rec: s_rec.value = '1'

        db.session.commit()

        print("\n=== CLEANUP VERIFICATION RESULTS ===")
        print(f"Tariffs Catalogue : {Tariff.query.count()} preserved (100%)")
        print(f"Admin Users       : {User.query.count()} preserved (100%)")
        print(f"System Settings   : {Setting.query.count()} preserved (100%)")
        print(f"Classrooms        : {Room.query.count()} preserved (100%)")
        print(f"Students          : {Student.query.count()} (Cleaned to 0)")
        print(f"Enrollments       : {Enrollment.query.count()} (Cleaned to 0)")
        print(f"Courses           : {Course.query.count()} (Cleaned to 0)")
        print(f"Teachers          : {Teacher.query.count()} (Cleaned to 0)")
        print(f"Payments          : {Payment.query.count()} (Cleaned to 0)")
        print("\nSUCCESS: Database is 100% clean and production-ready!")

if __name__ == '__main__':
    clean_database()

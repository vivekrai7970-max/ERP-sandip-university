import hashlib
import hmac
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.contrib import admin
import pyotp

from .admin import RegisterAdmin, StudentAdmin
from .models import register, Student, Payment, FacultySchedule, Attendance
from .views import _get_student_for_user


class TwoFATests(TestCase):
    def setUp(self):
        self.user = register.objects.create(
            First_name='Test',
            Last_name='User',
            Email='test@example.com',
            Date_of_birth='2000-01-01',
            course='Btech',
            contact_no='1234567890',
            Password='secret123',
            role='student',
        )

    def test_setup_2fa_works_with_session_user(self):
        session = self.client.session
        session['user_email'] = self.user.Email
        session['user_role'] = self.user.role
        session.save()

        response = self.client.get(reverse('setup_2fa'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Setup Google Authenticator')

    def test_verify_2fa_accepts_valid_code(self):
        session = self.client.session
        session['user_email'] = self.user.Email
        session['user_role'] = self.user.role
        session['two_factor_secret'] = 'JBSWY3DPEHPK3PXP'
        session.save()

        code = pyotp.TOTP(session['two_factor_secret']).now()
        response = self.client.post(reverse('verify_2fa'), {'code': code})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_get_student_for_user_uses_unique_student_id_when_taken(self):
        Student.objects.create(
            student_id='STU001',
            name='Existing Student',
            course='Btech',
            semester='Sem 1',
            attendance=0,
            pending_fee=0,
            cgpa=0.0,
        )

        student = _get_student_for_user(self.user)

        self.assertIsNotNone(student)
        self.assertEqual(student.name, 'Test User')
        self.assertNotEqual(student.student_id, 'STU001')

    def test_dashboard_includes_clickable_detail_sections(self):
        session = self.client.session
        session['user_email'] = self.user.Email
        session['user_role'] = self.user.role
        session.save()

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-bs-toggle="collapse"')
        self.assertContains(response, 'id="payment-details"')
        self.assertContains(response, 'id="results-details"')
        self.assertContains(response, 'id="schedule-details"')
        self.assertContains(response, 'id="payment-form-details"')

    def test_dashboard_sections_start_collapsed_until_expanded(self):
        session = self.client.session
        session['user_email'] = self.user.Email
        session['user_role'] = self.user.role
        session.save()

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="payment-details"')
        self.assertContains(response, 'id="results-details"')
        self.assertContains(response, 'id="schedule-details"')
        self.assertContains(response, 'id="payment-form-details"')
        self.assertContains(response, 'class="collapse"')
        self.assertNotContains(response, 'class="collapse show"')

    def test_dashboard_sidebar_links_target_sections(self):
        session = self.client.session
        session['user_email'] = self.user.Email
        session['user_role'] = self.user.role
        session.save()

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-section-target="profile-section"')
        self.assertContains(response, 'data-section-target="payment-details"')
        self.assertContains(response, 'data-section-target="results-details"')
        self.assertContains(response, 'data-section-target="schedule-details"')
        self.assertContains(response, 'data-section-target="payment-form-details"')

    def test_student_admin_form_includes_subject_assignment_field(self):
        form_class = StudentAdmin(Student, admin.site).get_form(None)
        self.assertIn('subjects', form_class.base_fields)

    def test_register_admin_form_includes_faculty_subject_assignment_field(self):
        form_class = RegisterAdmin(register, admin.site).get_form(None)
        self.assertIn('assigned_subjects', form_class.base_fields)

    def test_dashboard_shows_attendance_details_with_dates_and_status(self):
        faculty = register.objects.create(
            First_name='Faculty',
            Last_name='One',
            Email='faculty@example.com',
            Date_of_birth='1990-01-01',
            course='Faculty',
            contact_no='9876543210',
            Password='secret123',
            role='faculty',
        )
        Student.objects.create(
            student_id='STU004',
            name='Test User',
            course='Btech',
            semester='Sem 1',
            attendance=85,
            pending_fee=0,
            cgpa=8.5,
        )
        schedule = FacultySchedule.objects.create(
            faculty=faculty,
            subject='Mathematics',
            scheduled_time='10:00 AM',
        )
        Attendance.objects.create(schedule=schedule, student_name='Test User', status='present', date='2026-06-01')
        Attendance.objects.create(schedule=schedule, student_name='Test User', status='absent', date='2026-06-02')

        session = self.client.session
        session['user_email'] = self.user.Email
        session['user_role'] = self.user.role
        session.save()

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attendance Details')
        self.assertContains(response, 'Present')
        self.assertContains(response, 'Absent')
        self.assertContains(response, '2026-06-01')
        self.assertContains(response, '2026-06-02')

    @patch('erp.views.razorpay.Client')
    def test_create_razorpay_order_creates_payment_record(self, mock_client):
        student = Student.objects.create(
            student_id='STU001',
            name='Test User',
            course='Btech',
            semester='Sem 1',
            attendance=85,
            pending_fee=5000,
            cgpa=8.5,
        )
        self.user.First_name = 'Test'
        self.user.Last_name = 'User'
        self.user.save()

        mock_client.return_value.order.create.return_value = {'id': 'order_123'}

        session = self.client.session
        session['user_email'] = self.user.Email
        session['user_role'] = self.user.role
        session.save()

        response = self.client.post(reverse('create_razorpay_order'), {'amount': '500'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Payment.objects.filter(order_id='order_123', student=student).exists())

    def test_verify_payment_updates_student_balance(self):
        student = Student.objects.create(
            student_id='STU002',
            name='Test User',
            course='Btech',
            semester='Sem 1',
            attendance=90,
            pending_fee=1000,
            cgpa=9.0,
        )
        payment = Payment.objects.create(student=student, amount=500, status='Pending', order_id='order_456')

        signature = hmac.new(
            'secret'.encode(),
            f"{payment.order_id}|pay_123".encode(),
            hashlib.sha256,
        ).hexdigest()

        with patch.object(settings, 'RAZORPAY_KEY_SECRET', 'secret'):
            response = self.client.post(reverse('verify_razorpay_payment'), {
                'razorpay_payment_id': 'pay_123',
                'razorpay_order_id': payment.order_id,
                'razorpay_signature': signature,
            })

        payment.refresh_from_db()
        student.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, 'Paid')
        self.assertEqual(student.pending_fee, Decimal('500.00'))

    def test_payment_success_page_displays_confirmation(self):
        student = Student.objects.create(
            student_id='STU003',
            name='Success User',
            course='Btech',
            semester='Sem 1',
            attendance=95,
            pending_fee=1000,
            cgpa=9.2,
        )
        payment = Payment.objects.create(student=student, amount=250, status='Paid', order_id='order_789')

        response = self.client.get(reverse('payment_success', args=[payment.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Payment Successful')
        self.assertContains(response, '₹250.00')

    @patch('erp.views.razorpay.Client')
    def test_create_razorpay_order_creates_student_profile_when_missing(self, mock_client):
        mock_client.return_value.order.create.return_value = {'id': 'order_missing_profile'}
        user = register.objects.create(
            First_name='No',
            Last_name='Profile',
            Email='noprofile@example.com',
            Date_of_birth='2001-01-01',
            course='Btech',
            contact_no='9999999999',
            Password='secret123',
            role='student',
        )

        session = self.client.session
        session['user_email'] = user.Email
        session['user_role'] = user.role
        session.save()

        response = self.client.post(reverse('create_razorpay_order'), {'amount': '250'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Student.objects.filter(name='No Profile').exists())

    def test_prn_is_auto_generated_and_role_specific(self):
        student = register.objects.create(
            First_name='Student',
            Last_name='One',
            Email='student2@example.com',
            Date_of_birth='2000-01-02',
            course='BCA',
            contact_no='1111111111',
            Password='secret123',
            role='student',
        )
        faculty = register.objects.create(
            First_name='Faculty',
            Last_name='One',
            Email='faculty2@example.com',
            Date_of_birth='1990-01-02',
            course='Faculty',
            contact_no='2222222222',
            Password='secret123',
            role='faculty',
        )

        self.assertTrue(student.prn.startswith('STU'))
        self.assertTrue(faculty.prn.startswith('FAC'))
        self.assertNotEqual(student.prn, faculty.prn)

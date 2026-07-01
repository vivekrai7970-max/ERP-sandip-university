import os
import hashlib
import hmac
from datetime import datetime
from decimal import Decimal

import razorpay
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import register as Register, Student, Payment, Result, Schedule, FacultySchedule, Attendance, Subject


def _get_session_user(request):
    user_email = request.session.get('user_email')
    if not user_email:
        return None
    return Register.objects.filter(Email=user_email).first()


def register_view(request):
    if request.method == "POST":
        a = request.POST['First_name']
        b = request.POST['Last_name']
        c = request.POST['Email']
        d = request.POST['Password']
        e = request.POST['Date_of_birth']
        f = request.POST['contact_no']
        g = request.POST['course']
        h = request.POST.get('role', 'student')
        obj = Register(
            First_name=a,
            Last_name=b,
            Email=c,
            Password=d,
            Date_of_birth=e,
            contact_no=f,
            course=g,
            role=h,
        )
        obj.save()
        return redirect('login')

    return render(request, 'register.html')


def login_view(request):
    if request.method == "POST":
        email = request.POST['Email']
        password = request.POST['Password']
        role = request.POST.get('role', 'student')
        user = Register.objects.filter(Email=email, Password=password, role=role).first()
        if user:
            request.session['user_email'] = user.Email
            request.session['user_role'] = user.role
            request.session['is_2fa_verified'] = False
            return redirect('setup_2fa')
        else:
            return HttpResponse("Invalid email, password, or role")
    return render(request, 'login.html')


def _get_student_for_user(user):
    if not user:
        return None

    full_name = f"{user.First_name} {user.Last_name}".strip()
    student = Student.objects.filter(name__iexact=full_name).first()
    if student:
        return student

    if user.role == 'student':
        base_student_id = f"STU{user.id:03d}"
        student_id = base_student_id
        counter = 1
        while Student.objects.filter(student_id=student_id).exists():
            student_id = f"{base_student_id}-{counter}"
            counter += 1

        student = Student.objects.create(
            student_id=student_id,
            name=full_name or user.Email,
            course=user.course,
            semester='Sem 1',
            attendance=0,
            pending_fee=0,
            cgpa=0.0,
        )
        return student

    return None


def dashboard(request):
    user_email = request.session.get('user_email')
    user_role = request.session.get('user_role')
    if not user_email:
        return redirect('login')
    if user_role == 'faculty':
        return redirect('faculty_dashboard')

    user = Register.objects.filter(Email=user_email, role='student').first()
    student = _get_student_for_user(user)

    payments = Payment.objects.filter(student=student).order_by('-date', '-id') if student else Payment.objects.none()
    results = Result.objects.filter(student=student) if student else Result.objects.none()
    schedules = Schedule.objects.filter(student=student) if student else Schedule.objects.none()
    attendance_records = Attendance.objects.filter(student_name=student.name).order_by('-date', '-id') if student else Attendance.objects.none()
    assigned_subjects = student.subjects.all() if student else Subject.objects.none()

    context = {
        'user': user,
        'student': student,
        'payments': payments,
        'results': results,
        'schedules': schedules,
        'attendance_records': attendance_records,
        'assigned_subjects': assigned_subjects,
        'razorpay_key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }

    return render(request, 'dashboard.html', context)


def create_razorpay_order(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    user_email = request.session.get('user_email')
    if not user_email:
        return JsonResponse({'success': False, 'message': 'Please login first'}, status=401)

    user = Register.objects.filter(Email=user_email, role='student').first()
    student = _get_student_for_user(user)
    if not student:
        return JsonResponse({'success': False, 'message': 'Student profile not found'}, status=404)

    amount = int(float(request.POST.get('amount', 0)) * 100)
    if amount <= 0:
        return JsonResponse({'success': False, 'message': 'Amount must be greater than zero'}, status=400)

    client = razorpay.Client(auth=(getattr(settings, 'RAZORPAY_KEY_ID', ''), getattr(settings, 'RAZORPAY_KEY_SECRET', '')))
    order = client.order.create({
        'amount': amount,
        'currency': 'INR',
        'receipt': f"stu-{student.id}-{datetime.now().timestamp()}",
        'payment_capture': 1,
    })

    payment = Payment.objects.create(student=student, amount=amount / 100, status='Pending', order_id=order.get('id'))

    return JsonResponse({
        'success': True,
        'order_id': order.get('id'),
        'amount': amount,
        'currency': 'INR',
        'payment_id': payment.id,
    })


def verify_razorpay_payment(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    payment_id = request.POST.get('razorpay_payment_id')
    order_id = request.POST.get('razorpay_order_id')
    signature = request.POST.get('razorpay_signature')
    payment_record = Payment.objects.filter(order_id=order_id).order_by('-id').first()

    if not payment_record:
        return JsonResponse({'success': False, 'message': 'Payment record not found'}, status=404)

    generated_signature = hmac.new(
        getattr(settings, 'RAZORPAY_KEY_SECRET', '').encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(generated_signature, signature or ''):
        payment_record.razorpay_payment_id = payment_id
        payment_record.razorpay_signature = signature
        payment_record.status = 'Paid'
        payment_record.save()

        student = payment_record.student
        student.pending_fee = max(Decimal('0.00'), student.pending_fee - payment_record.amount)
        student.save(update_fields=['pending_fee'])

        return JsonResponse({'success': True, 'message': 'Payment verified successfully', 'payment_id': payment_record.id})

    return JsonResponse({'success': False, 'message': 'Payment verification failed'}, status=400)


def payment_success(request, payment_id):
    payment = Payment.objects.select_related('student').filter(id=payment_id).first()
    if not payment:
        return redirect('dashboard')
    return render(request, 'payment_success.html', {'payment': payment, 'student': payment.student})


def faculty_dashboard(request):
    user_email = request.session.get('user_email')
    if not user_email:
        return redirect('login')

    user = Register.objects.filter(Email=user_email, role='faculty').first()
    if not user:
        return redirect('dashboard')

    if request.method == "POST":
        if 'schedule_submit' in request.POST:
            subject = request.POST.get('subject', '').strip()
            scheduled_time = request.POST.get('scheduled_time', '').strip()
            if subject and scheduled_time:
                FacultySchedule.objects.create(
                    faculty=user,
                    subject=subject,
                    scheduled_time=scheduled_time,
                )
        if 'attendance_submit' in request.POST:
            schedule_id = request.POST.get('schedule')
            student_name = request.POST.get('student_name', '').strip()
            status = request.POST.get('status', 'present')
            schedule = FacultySchedule.objects.filter(id=schedule_id, faculty=user).first()
            if schedule and student_name:
                Attendance.objects.create(
                    schedule=schedule,
                    student_name=student_name,
                    status=status,
                )

    schedules = FacultySchedule.objects.filter(faculty=user)
    attendance_records = Attendance.objects.filter(schedule__faculty=user).select_related('schedule')
    students = Register.objects.filter(role='student')

    return render(request, 'faculty_dashboard.html', {
        'user': user,
        'schedules': schedules,
        'attendance_records': attendance_records,
        'students': students,
    })


def logout_view(request):
    request.session.flush()
    return redirect('login')
# --------------------SETUP 2FA-----------------------
import pyotp
import qrcode

from io import BytesIO
from base64 import b64encode


def setup_2fa(request):
    user = _get_session_user(request)
    if not user:
        return redirect('login')

    secret_key = request.session.get('two_factor_secret')
    if not secret_key:
        secret_key = pyotp.random_base32()
        request.session['two_factor_secret'] = secret_key

    totp = pyotp.TOTP(secret_key)
    uri = totp.provisioning_uri(
        name=user.Email,
        issuer_name='SandipUniversity'
    )

    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_code = b64encode(buffer.getvalue()).decode()

    return render(request, 'setup_2fa_varification.html', {'qr_code': qr_code})


#----------------verify 2FA-----------------------
def verify_2fa(request):
    user = _get_session_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        secret_key = request.session.get('two_factor_secret')

        if not secret_key:
            return redirect('setup_2fa')

        totp = pyotp.TOTP(secret_key)
        if totp.verify(code):
            request.session['is_2fa_verified'] = True
            if user.role == 'faculty':
                return redirect('faculty_dashboard')
            return redirect('dashboard')

        return render(request, 'verify_2fa.html', {'error': 'Invalid Code'})

    return render(request, 'verify_2fa.html')
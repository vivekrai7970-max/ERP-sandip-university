from django.db import models
import datetime

# Create your models here.
class Subject(models.Model):
    COURSE_CHOICES = [
        ('Btech', 'Btech'),
        ('BCA', 'BCA'),
        ('Polytechnic', 'Polytechnic'),
        ('Law', 'Law'),
    ]

    SEMESTER_CHOICES = [
        ('Sem 1', 'Sem 1'),
        ('Sem 2', 'Sem 2'),
        ('Sem 3', 'Sem 3'),
        ('Sem 4', 'Sem 4'),
        ('Sem 5', 'Sem 5'),
        ('Sem 6', 'Sem 6'),
        ('Sem 7', 'Sem 7'),
        ('Sem 8', 'Sem 8'),
    ]

    name = models.CharField(max_length=100, unique=True)
    course = models.CharField(max_length=20, choices=COURSE_CHOICES, blank=True, null=True)
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.name


class register(models.Model):
    COURSE_CHOICES = [
        ('Btech', 'Btech'),
        ('BCA', 'BCA'),
        ('Polytechnic', 'Polytechnic'),
        ('Law', 'Law'),
        ('Faculty', 'Faculty'),
    ]

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
    ]

    First_name = models.CharField(max_length=100)
    Last_name = models.CharField(max_length=100)
    Email = models.EmailField(unique=True)
    Date_of_birth = models.DateField()
    course = models.CharField(max_length=20, choices=COURSE_CHOICES)
    contact_no = models.CharField(max_length=15)
    Password = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    prn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    assigned_subjects = models.ManyToManyField(Subject, blank=True, related_name='assigned_to_register')

    def save(self, *args, **kwargs):
        if not self.prn:
            prefix = 'STU' if self.role == 'student' else 'FAC'
            year = datetime.datetime.now().strftime('%Y')
            last_user = register.objects.filter(role=self.role).order_by('-id').first()
            if last_user and last_user.prn:
                last_number = int(last_user.prn.replace(prefix, '').replace(year, '')) if last_user.prn.startswith(prefix) else 0
                number = last_number + 1
            else:
                number = 1
            self.prn = f"{prefix}{year}{number:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.First_name} {self.Last_name} ({self.role.title()})"

    class Meta:
        db_table = "register"


class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    semester = models.CharField(max_length=20)
    attendance = models.IntegerField(default=0)
    pending_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cgpa = models.FloatField(default=0)
    subjects = models.ManyToManyField(Subject, blank=True, related_name='students')

    def __str__(self):
        return self.name


class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.student.name} - {self.amount}"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    marks = models.IntegerField()

    def __str__(self):
        return f"{self.subject} - {self.marks}"


class Schedule(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    time = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.time} - {self.subject}"

class FacultySchedule(models.Model):
    faculty = models.ForeignKey(register, on_delete=models.CASCADE, limit_choices_to={'role': 'faculty'})
    subject = models.CharField(max_length=100)
    scheduled_time = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.subject} at {self.scheduled_time}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]
    schedule = models.ForeignKey(FacultySchedule, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.status.title()} on {self.date}"

from django.contrib.auth.models import User

class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    secret_key = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.user.username
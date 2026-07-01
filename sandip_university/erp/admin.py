from django.contrib import admin
from .models import (
    register,
    Student,
    Subject,
    Payment,
    Result,
    Schedule,
    FacultySchedule,
    Attendance,
    UserProfile,
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'semester', 'assigned_course', 'assigned_people')
    search_fields = ('name', 'course', 'semester')
    ordering = ('name',)
    fields = ('name', 'course', 'semester')

    def assigned_course(self, obj):
        courses = sorted({student.course for student in obj.students.all() if student.course})
        if courses:
            return ', '.join(courses)
        return '-'
    assigned_course.short_description = 'Assigned Course'

    def assigned_people(self, obj):
        people = []
        for student in obj.students.all():
            people.append(f"Student: {student.name}")
        for register_user in obj.assigned_to_register.all():
            people.append(f"Faculty: {register_user.First_name} {register_user.Last_name}".strip())
        return ', '.join(people) if people else '-'
    assigned_people.short_description = 'Assigned To'


@admin.register(register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ('First_name', 'Last_name', 'Email', 'role', 'course', 'contact_no', 'prn')
    list_filter = ('role', 'course')
    search_fields = ('First_name', 'Last_name', 'Email', 'prn')
    ordering = ('First_name', 'Last_name')
    actions = ['delete_selected']
    readonly_fields = ('prn',)
    fields = ('First_name', 'Last_name', 'Email', 'Password', 'Date_of_birth', 'contact_no', 'course', 'role', 'prn', 'assigned_subjects')


class ResultInline(admin.TabularInline):
    model = Result
    extra = 1
    fields = ('subject', 'marks')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'course', 'semester', 'attendance', 'pending_fee', 'cgpa')
    list_filter = ('course', 'semester')
    search_fields = ('student_id', 'name', 'course')
    ordering = ('name',)
    fields = ('student_id', 'name', 'course', 'semester', 'attendance', 'pending_fee', 'cgpa', 'subjects')
    inlines = [ResultInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'status', 'date', 'order_id', 'razorpay_payment_id')
    list_filter = ('status', 'date')
    search_fields = ('student__name', 'order_id', 'razorpay_payment_id')
    ordering = ('-date',)
    fields = ('student', 'amount', 'status', 'date', 'order_id', 'razorpay_payment_id', 'razorpay_signature')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'marks')
    list_filter = ('student__course',)
    search_fields = ('student__name', 'subject')
    ordering = ('student__name', 'subject')
    actions = ['delete_selected']
    fields = ('student', 'subject', 'marks')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'time')
    search_fields = ('student__name', 'subject')
    ordering = ('student__name', 'subject')
    fields = ('student', 'subject', 'time')


@admin.register(FacultySchedule)
class FacultyScheduleAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'subject', 'scheduled_time')
    search_fields = ('faculty__First_name', 'faculty__Last_name', 'subject')
    ordering = ('faculty__First_name', 'subject')
    actions = ['delete_selected']
    fields = ('faculty', 'subject', 'scheduled_time')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'schedule', 'status', 'date')
    list_filter = ('status', 'date')
    search_fields = ('student_name', 'schedule__subject')
    ordering = ('-date',)
    fields = ('student_name', 'schedule', 'status', 'date')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'secret_key')
    search_fields = ('user__username', 'user__email')
    actions = ['delete_selected']
    fields = ('user', 'secret_key')

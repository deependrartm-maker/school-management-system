from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.contrib.auth import logout
from profiles.models import ParentProfile
from audit.utils import log_activity
from django.utils import timezone
from datetime import timedelta
from audit.models import ActivityLog
from audit.utils import auto_block_ip
from .models import CustomUser, AccountLock

def login_view(request):
    context = {}

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        ip_address = request.META.get('REMOTE_ADDR')
        time_threshold = timezone.now() - timedelta(minutes=15)

        # =========================================================
        # STEP 11.6 — EXISTING IP LOCK CHECK (UNCHANGED)
        # =========================================================
        failed_attempts = ActivityLog.objects.filter(
            action_type='FAILED_LOGIN',
            ip_address=ip_address,
            timestamp__gte=time_threshold
        ).count()

        if failed_attempts >= 5:
            log_activity(
                None,
                'FAILED_LOGIN',
                f"Blocked login attempt from locked IP: {ip_address}",
                request
            )

            context['error'] = "Too many failed attempts. Try again after 15 minutes."
            return render(request, 'accounts/login.html', context)

        # =========================================================
        # 🔐 STEP 16.0 — ACCOUNT LOCK CHECK (NEW)
        # =========================================================
        try:
            user_obj = CustomUser.objects.get(email=email)
            lock_obj, created = AccountLock.objects.get_or_create(user=user_obj)

            if lock_obj.is_lock_active():
                context['error'] = "Account temporarily locked due to multiple failed login attempts."
                return render(request, 'accounts/login.html', context)

        except CustomUser.DoesNotExist:
            user_obj = None

        # =========================================================
        # NORMAL AUTHENTICATION
        # =========================================================
        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active:

            # 🔄 RESET ACCOUNT LOCK ON SUCCESS
            lock_obj, created = AccountLock.objects.get_or_create(user=user)
            lock_obj.unlock()

            login(request, user)

            log_activity(
                request.user,
                'LOGIN',
                f"{request.user.email} logged in",
                request
            )

            if user.role == 'ADMIN':
                return redirect('/dashboard/admin/')
            elif user.role == 'TEACHER':
                return redirect('/dashboard/teacher/')
            elif user.role == 'STUDENT':
                return redirect('/dashboard/student/')
            elif user.role == 'PARENT':
                return redirect('/dashboard/parent/')

        else:
            # =========================================================
            # FAILED LOGIN LOG (EXISTING)
            # =========================================================
            log_activity(
                None,
                'FAILED_LOGIN',
                f"Failed login attempt for email: {email}",
                request
            )

            # =========================================================
            # 🔐 STEP 16.0 — INCREMENT ACCOUNT ATTEMPTS (NEW)
            # =========================================================
            if user_obj:
                lock_obj, created = AccountLock.objects.get_or_create(user=user_obj)
                lock_obj.failed_attempts += 1

                if lock_obj.failed_attempts >= 5:
                    lock_obj.lock()

                    log_activity(
                        user_obj,
                        'FAILED_LOGIN',
                        "Account auto-locked after 5 failed attempts",
                        request
                    )
                else:
                    lock_obj.save(update_fields=["failed_attempts"])

            # EXISTING AUTO IP BLOCK
            auto_block_ip(ip_address)

            context['error'] = "Invalid email or password"

    return render(request, 'accounts/login.html', context)


def logout_view(request):

    # ✅ Logout logging
    if request.user.is_authenticated:
        log_activity(
            request.user,
            'LOGOUT',
            f"{request.user.email} logged out",
            request
        )

    logout(request)
    return redirect('/login/')


# -------- Dashboards (render templates from dashboard app) --------

@role_required(['ADMIN'])
def admin_dashboard(request):
    return render(request, 'dashboard/admin.html')


@role_required(['TEACHER'])
def teacher_dashboard(request):
    return render(request, 'dashboard/teacher.html')


@role_required(['STUDENT'])
def student_dashboard(request):
    return render(request, 'dashboard/student.html')


@role_required(['PARENT'])
def parent_dashboard(request):
    try:
        parent_profile = ParentProfile.objects.get(user=request.user)
        students = parent_profile.students.all()
    except ParentProfile.DoesNotExist:
        parent_profile = None
        students = []

    context = {
        "parent_profile": parent_profile,
        "students": students,
    }

    return render(request, "dashboard/parent.html", context)
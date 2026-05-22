from django.shortcuts import render, redirect
from .models import *
import random
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta


# 🔍 Get IP
def get_ip(request):
    return request.META.get('REMOTE_ADDR')


# ================= FAKE USER DETECTION =================
def detect_fake_user(user, request):
    reasons = []

    # Fake email pattern
    if "test" in user.email or user.email.count("123") > 2:
        reasons.append("Fake email pattern detected")

    # Multiple failed logins
    if user.login_attempts >= 3:
        reasons.append("Multiple failed login attempts")

    # Multiple IPs
    logs = ActivityLog.objects.filter(user=user).order_by('-created_at')[:5]
    ips = set(log.ip_address for log in logs)

    if len(ips) > 2:
        reasons.append("Multiple IP addresses detected")

    # Too many requests in 1 minute
    one_min = timezone.now() - timedelta(minutes=1)
    recent_logs = ActivityLog.objects.filter(user=user, created_at__gte=one_min)

    if recent_logs.count() > 5:
        reasons.append("Too many requests (bot activity)")

    # If any suspicious activity
    if reasons:
        user.is_suspicious = True
        user.save()

        for r in reasons:
            Alert.objects.create(
                user=user,
                message=f"FAKE USER DETECTED: {r}"
            )


# ================= REGISTER =================
def register(request):
    if request.method == "POST":
        fname = request.POST['first_name']
        lname = request.POST['last_name']
        email = request.POST['email']
        contact = request.POST['contact_no']
        password = request.POST['password']

        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'msg': 'Email already exists'})

        if "test" in email or email.count("123") > 2:
            return render(request, 'register.html', {'msg': 'Suspicious email detected'})

        otp = random.randint(1000, 9999)

        user = User.objects.create(
            first_name=fname,
            last_name=lname,
            email=email,
            contact_no=contact,
            password=password,
            otp=otp
        )

        send_mail(
            "OTP Verification",
            f"Your OTP is {otp}",
            "your_email@gmail.com",
            [email],
            fail_silently=False
        )

        request.session['email'] = email
        return redirect('otp')

    return render(request, 'register.html')


# ================= OTP =================
def otp_verify(request):
    if "email" not in request.session:
        return redirect('login')

    user = User.objects.get(email=request.session['email'])

    if request.method == "POST":
        entered_otp = int(request.POST['otp'])

        if user.otp == entered_otp:
            user.is_verified = True
            user.save()
            return redirect('login')

        else:
            # 🔥 ALERT FOR WRONG OTP
            admin_user = User.objects.filter(email="admin@gmail.com").first()

            if admin_user:
                Alert.objects.create(
                    user=admin_user,
                    message=f"Wrong OTP entered for {user.email} (IP: {get_ip(request)})"
                )

            user.delete()
            del request.session['email']

            return render(request, 'otp_verify.html', {
                'msg': 'Invalid OTP! Registration cancelled.'
            })

    return render(request, 'otp_verify.html')


# ================= LOGIN =================
def login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = User.objects.get(email=email)

            # ❌ Wrong password
            if user.password != password:
                user.login_attempts += 1
                user.save()

                ActivityLog.objects.create(
                    user=user,
                    action="Failed Login",
                    ip_address=get_ip(request)
                )

                Alert.objects.create(
                    user=user,
                    message=f"Wrong password attempt (IP: {get_ip(request)})"
                )

                detect_fake_user(user, request)

                return render(request, 'login.html', {'msg': 'Wrong password'})

            # ❌ Not verified
            if not user.is_verified:
                return render(request, 'login.html', {'msg': 'Verify OTP first'})

            # ✅ Successful login
            user.login_attempts = 0
            user.save()

            request.session['email'] = email

            ActivityLog.objects.create(
                user=user,
                action="Login",
                ip_address=get_ip(request)
            )

            check_suspicious(user)
            detect_fake_user(user, request)

            return redirect('admin_dashboard')

        except User.DoesNotExist:
            admin_user = User.objects.filter(email="admin@gmail.com").first()

            if admin_user:
                Alert.objects.create(
                    user=admin_user,
                    message=f"Fake login attempt using unregistered email: {email} (IP: {get_ip(request)})"
                )

            return render(request, 'login.html', {'msg': 'User not found'})

    return render(request, 'login.html')


# ================= SUSPICIOUS =================
def check_suspicious(user):
    logs = ActivityLog.objects.filter(user=user).order_by('-created_at')[:5]

    ips = set(log.ip_address for log in logs)

    if len(ips) > 2:
        user.is_suspicious = True
        user.save()

        Alert.objects.create(
            user=user,
            message="Multiple IP login detected"
        )


# ================= ADMIN DASHBOARD =================
def admin_dashboard(request):
    if "email" not in request.session:
        return redirect('login')

    user = User.objects.get(email=request.session['email'])

    users = User.objects.all()
    alerts = Alert.objects.all().order_by('-created_at')
    logs = ActivityLog.objects.all().order_by('-created_at')

    total_users = User.objects.count()
    total_logins = ActivityLog.objects.filter(action="Login").count()
    total_logouts = ActivityLog.objects.filter(action="Logout").count()

    five_min = timezone.now() - timedelta(minutes=5)

    active_users = ActivityLog.objects.filter(
        action="Login",
        created_at__gte=five_min
    ).values('user').distinct().count()

    context = {
        'user': user,
        'users': users,
        'alerts': alerts,
        'logs': logs,
        'total_users': total_users,
        'total_logins': total_logins,
        'total_logouts': total_logouts,
        'active_users': active_users,
    }

    return render(request, 'admin_dashboard.html', context)


# ================= LOGOUT =================
def logout(request):
    if 'email' in request.session:
        user = User.objects.get(email=request.session['email'])

        ActivityLog.objects.create(
            user=user,
            action="Logout",
            ip_address=get_ip(request)
        )

        del request.session['email']

    return redirect('login')


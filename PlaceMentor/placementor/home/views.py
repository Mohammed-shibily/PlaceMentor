from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from.models import StudentProfile, Application, Notification,Interview,HR,Job,ContactMessage
from django.contrib.auth import authenticate, login   # <-- added this
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
import re
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


def index(request):
    return render(request, 'index.html')

def studentlogin(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if a User with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email not registered!")
            return redirect("studlogin")

        # Check if this User is a Student (linked in Student model)
        if not hasattr(user, "studentprofile"):
            messages.error(request, "This account is not registered as a student.")
            return redirect("studlogin")

        # Prevent staff/admin login here
        if user.is_staff:
            messages.error(request, "Admins cannot log in here. Please use the admin portal.")
            return redirect("studlogin")

        # Authenticate using username (Django uses username internally)
        user = authenticate(request, username=user.username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("student_dashboard")
        else:
            messages.error(request, "Invalid password!")
            return redirect("studlogin")

    return render(request, "login.html")

def studentregister(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        roll_no = request.POST.get('roll_no', '').strip()
        branch = request.POST.get('branch', '').strip()
        cgpa = request.POST.get('cgpa', '').strip()
        phone = request.POST.get('phone', '').strip()
        skills = request.POST.get('skills', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()

        # 👇 Context for re-filling fields after error
        context = {
            "username": username,
            "email": email,
            "roll_no": roll_no,
            "branch": branch,
            "cgpa": cgpa,
            "phone": phone,
            "skills": skills,
        }

        # ✅ All fields required
        if not all([username, email, roll_no, branch, cgpa, phone, skills, password, password2]):
            messages.error(request, 'All fields are required')
            return render(request, 'studregister.html', context)

        # ✅ Password validations
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'studregister.html', context)

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'studregister.html', context)

        # ✅ Email validation
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format')
            return render(request, 'studregister.html', context)

        # ✅ Roll number must be numeric
        if not roll_no.isdigit():
            messages.error(request, 'Roll number must contain only numbers')
            return render(request, 'studregister.html', context)

        # ✅ Phone must be exactly 10 digits
        if not re.fullmatch(r'\d{10}', phone):
            messages.error(request, 'Phone number must be 10 digits')
            return render(request, 'studregister.html', context)

        # ✅ Duplicate checks
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'studregister.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'studregister.html', context)

        if StudentProfile.objects.filter(roll_no=roll_no).exists():
            messages.error(request, 'Roll number already registered')
            return render(request, 'studregister.html', context)

        # ✅ CGPA validation
        try:
            cgpa_value = float(cgpa)
            if cgpa_value < 0 or cgpa_value > 10:
                raise ValueError
        except ValueError:
            messages.error(request, 'Invalid CGPA. Must be between 0 and 10.')
            return render(request, 'studregister.html', context)

        # ✅ Create User
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = False
        user.is_superuser = False
        user.save()

        # ✅ Create Student Profile
        StudentProfile.objects.create(
            user=user,
            name=username,
            roll_no=roll_no,
            branch=branch,
            cgpa=cgpa_value,
            phone=phone,
            skills=skills
        )

        messages.success(request, 'Account created successfully! Please login.')
        return redirect('studlogin')

    return render(request, 'studregister.html')


@login_required
def student_dashboard(request):
    profile = get_object_or_404(StudentProfile, user=request.user)

    # Convert skills into a list
    profile.skill_list = [s.strip() for s in profile.skills.split(",")] if profile.skills else []

    applications = Application.objects.filter(student=profile).order_by("-applied_on")[:5]
    interviews = Interview.objects.filter(application__student=profile).order_by("date")[:5]
    notifications = Notification.objects.filter(student=profile).order_by("-created_at")[:3]

    total_apps = Application.objects.filter(student=profile).count()
    total_interviews = Interview.objects.filter(application__student=profile).count()
    total_offers = Application.objects.filter(student=profile, status="Selected").count()

    context = {
        "profile": profile,
        "applications": applications,
        "interviews": interviews,
        "notifications": notifications,
        "total_apps": total_apps,
        "total_interviews": total_interviews,
        "total_offers": total_offers,
    }
    return render(request, "student_dashboard.html", context)

def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("index")

def hrregister(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname", "").strip()
        company = request.POST.get("company", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()

        # 👇 context to keep data in form if validation fails
        context = {
            "fullname": fullname,
            "company": company,
            "email": email,
            "phone": phone,
            "username": username,
        }

        # ✅ All fields required
        if not all([fullname, company, email, phone, username, password, password2]):
            messages.error(request, "All fields are required")
            return render(request, "hrregister.html", context)

        # ✅ Password validations
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long")
            return render(request, "hrregister.html", context)

        if password != password2:
            messages.error(request, "Passwords do not match")
            return render(request, "hrregister.html", context)

        # ✅ Email validation
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email format")
            return render(request, "hrregister.html", context)

        # ✅ Phone must be 10 digits
        if not re.fullmatch(r"\d{10}", phone):
            messages.error(request, "Phone number must be 10 digits")
            return render(request, "hrregister.html", context)

        # ✅ Duplicate checks
        if HR.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, "hrregister.html", context)

        if HR.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return render(request, "hrregister.html", context)

        # ✅ Save HR with hashed password
        hr = HR(
            fullname=fullname,
            company=company,
            email=email,
            phone=phone,
            username=username,
            password=password,  # hash password
        )
        hr.save()

        messages.success(request, "HR registered successfully! Please login.")
        return redirect("hrlogin")

    return render(request, "hrregister.html")

def hrlogin(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        try:
            hr = HR.objects.get(username=username)

            # ✅ If you saved password as plain text (not recommended)
            if hr.password == password:
                request.session["hr_id"] = hr.id  # store session
                request.session["hr_name"] = hr.fullname
                request.session["hr_mail"] = hr.email
                messages.success(request, f"Welcome {hr.fullname}!")
                return redirect("hrdashboard")  # redirect to HR dashboard

            # ✅ If you saved hashed password (with make_password)
            # if check_password(password, hr.password):
            #     request.session["hr_id"] = hr.id
            #     request.session["hr_name"] = hr.fullname
            #     messages.success(request, f"Welcome {hr.fullname}!")
            #     return redirect("hrdashboard")

            else:
                messages.error(request, "Invalid password.")
                return redirect("hrlogin")

        except HR.DoesNotExist:
            messages.error(request, "No HR account found with that username.")
            return redirect("hrlogin")
    return render(request, "hrlogin.html")


def hrdashboard(request):
    if "hr_id" not in request.session:
        return redirect("hrlogin")

    hr_id = request.session["hr_id"]
    hr = HR.objects.get(id=hr_id)

    # Active jobs count
    active_jobs = Job.objects.filter(posted_by=hr, last_date__gte=timezone.now()).count()

    # All applications list
    applications_list = Application.objects.filter(job__posted_by=hr)

    # Count applications
    applications_count = applications_list.count()

    # Count selected applications (interviews)
    interviews_count = applications_list.filter(status="Selected").count()

    context = {
        "active_jobs": active_jobs,
        "applications": applications_list,   # ✅ iterable list for {% for %}
        "applications_count": applications_count,  # ✅ integer
        "interviews": interviews_count,
        "hr": hr,
    }
    return render(request, "hrdashboard.html", context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Job, HR

def post_job(request):
    hr_id = request.session.get("hr_id")
    if not hr_id:
        messages.warning(request, "Please log in as HR to post a job.")
        return redirect("hrlogin")

    hr = HR.objects.get(id=hr_id)

    if request.method == "POST":
        job_title = request.POST.get("title")
        description = request.POST.get("description")
        eligibility_cgpa = request.POST.get("eligibility_cgpa") or 0.0
        skills_required = request.POST.get("skills_required")
        last_date = request.POST.get("last_date")

        Job.objects.create(
            title=job_title,
            description=description,
            eligibility_cgpa=eligibility_cgpa,
            skills_required=skills_required,
            last_date=last_date,
            company=hr.company,   # ✅ save HR company
            posted_by=hr
        )

        messages.success(request, "Job posted successfully!")
        return redirect("hrdashboard")

    return render(request, "postjob.html", {"hr": hr})


def view_jobs(request):
    jobs = Job.objects.all().order_by("-created_at")  # full model objects
    return render(request, "viewjobs.html", {"jobs": jobs})


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    profile = get_object_or_404(StudentProfile, user=request.user)

    # Prevent duplicate applications
    if Application.objects.filter(student=profile, job=job).exists():
        messages.warning(request, "You have already applied for this job!")
    else:
        Application.objects.create(
            student=profile,
            job=job,
            position=job.title,  # ✅ only valid field
        )

        # Create notification and save to DB
        note = Notification.objects.create(
            student=profile,
            message=f"You successfully applied for {job.title} at {job.company}"
        )

        # Send email notification
        if profile.user.email:
            send_mail(
                subject="📢 Job Application Submitted",
                message=note.message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[profile.user.email],
                fail_silently=False,
            )

        messages.success(request, "Applied successfully!")

    return redirect("student_dashboard")






@login_required
def my_applications(request):
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    applications = Application.objects.filter(student=student_profile).select_related("job").order_by("-applied_on")

    return render(request, "my_applications.html", {"applications": applications})

def hr_applications(request):
    if "hr_id" not in request.session:
        return redirect("hrlogin")

    hr = HR.objects.get(id=request.session["hr_id"])
    applications = Application.objects.filter(job__posted_by=hr).select_related("student", "job")

    return render(request, "hr_applications.html", {"applications": applications})

def update_application_status(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        app.status = new_status
        app.save()

        # Create notification
        note = Notification.objects.create(
            student=app.student,
            message=f"Your application for {app.job.title} at {app.job.company} was {new_status}."
        )

        # Send email
        if app.student.user.email:
            send_mail(
                subject="📢 Application Status Update",
                message=note.message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[app.student.user.email],
                fail_silently=False,
            )

        messages.success(request, f"Status updated to {new_status} for {app.student.user.username}")
    return redirect("hr_applications")



def create_interview(request, app_id):
    if "hr_id" not in request.session:
        return redirect("hrlogin")

    application = get_object_or_404(Application, id=app_id)

    # Prevent duplicate interview
    if hasattr(application, "interview"):
        messages.error(request, "Interview already scheduled for this application.")
        return redirect("hrdashboard")

    if request.method == "POST":
        date = request.POST.get("date")
        location = request.POST.get("location")

        # Create interview
        interview = Interview.objects.create(
            application=application,
            date=date,
            location=location,
        )

        # Create notification
        note = Notification.objects.create(
            student=application.student,
            message=f"Interview scheduled for {application.job.title} at {application.job.company} on {date} at {location}."
        )

        # Send email
        if application.student.user.email:
            send_mail(
                subject="📅 Interview Scheduled",
                message=note.message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[application.student.user.email],
                fail_silently=False,
            )

        messages.success(request, "Interview scheduled successfully!")
        return redirect("hrdashboard")

    return render(request, "create_interview.html", {"application": application})


def about(request):
    return render(request, "about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                message=message
            )
            messages.success(request, "Your message has been sent successfully!")
            return redirect("contact")   # reloads the page
        else:
            messages.error(request, "All fields are required.")
            
    return render(request, "contact.html")

@login_required
def notifications(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    notifications = Notification.objects.filter(student=profile).order_by('-created_at')
    return render(request, "notifications.html", {"notifications": notifications})
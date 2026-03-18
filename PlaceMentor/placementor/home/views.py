from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from .models import StudentProfile, Application, Notification, Interview, HR, Job, ContactMessage, BookmarkedJob
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


def compute_profile_completion(profile):
    """Compute profile completion percentage based on filled fields."""
    fields = [
        bool(profile.name),
        bool(profile.college_name),
        bool(profile.branch),
        bool(profile.phone),
        profile.cgpa is not None and float(profile.cgpa) > 0,
        bool(profile.skills),
    ]
    return int((sum(fields) / len(fields)) * 100)


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
        college_name = request.POST.get('college_name', '').strip()
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
            "college_name": college_name,
            "branch": branch,
            "cgpa": cgpa,
            "phone": phone,
            "skills": skills,
        }

        # ✅ All fields required
        if not all([username, email, college_name, branch, cgpa, phone, skills, password, password2]):
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
            college_name=college_name,
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

    # Compute and save profile completion
    profile.profile_completion = compute_profile_completion(profile)
    profile.save(update_fields=['profile_completion'])

    # Convert skills into a list
    profile.skill_list = [s.strip() for s in profile.skills.split(",")] if profile.skills else []

    applications = Application.objects.filter(student=profile).order_by("-applied_on")[:5]
    interviews = Interview.objects.filter(application__student=profile).order_by("date")[:5]
    notifications = Notification.objects.filter(student=profile).order_by("-created_at")[:3]

    # 🔔 Unread "new job" alerts for popup
    job_alerts = Notification.objects.filter(
        student=profile, is_read=False, message__contains="🚀 New Job Alert"
    ).order_by("-created_at")[:5]

    total_apps = Application.objects.filter(student=profile).count()
    total_interviews = Interview.objects.filter(application__student=profile).count()
    total_offers = Application.objects.filter(student=profile, status="Selected").count()

    context = {
        "profile": profile,
        "applications": applications,
        "interviews": interviews,
        "notifications": notifications,
        "job_alerts": job_alerts,
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
            password=make_password(password),
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

            # ✅ Verify hashed password
            if check_password(password, hr.password):
                request.session["hr_id"] = hr.id
                request.session["hr_name"] = hr.fullname
                request.session["hr_mail"] = hr.email
                messages.success(request, f"Welcome {hr.fullname}!")
                return redirect("hrdashboard")



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

    # Only active (non-expired) jobs for the main list
    jobs_list = Job.objects.filter(posted_by=hr, last_date__gte=timezone.now()).order_by("-created_at")

    context = {
        "active_jobs": active_jobs,
        "applications": applications_list,
        "applications_count": applications_count,
        "interviews": interviews_count,
        "hr": hr,
        "jobs_list": jobs_list,
        "now": timezone.now(),
    }
    return render(request, "hrdashboard.html", context)



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

        new_job = Job.objects.create(
            title=job_title,
            description=description,
            eligibility_cgpa=eligibility_cgpa,
            skills_required=skills_required,
            last_date=last_date,
            company=hr.company,   # ✅ save HR company
            posted_by=hr
        )

        # 🔔 Notify ALL students about the new job posting
        all_students = StudentProfile.objects.all()
        notifications_to_create = []
        for student in all_students:
            notifications_to_create.append(
                Notification(
                    student=student,
                    message=(
                        f"🚀 New Job Alert! '{new_job.title}' at {new_job.company} "
                        f"is now open for applications. Apply before it's too late!"
                    ),
                )
            )
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

        messages.success(request, "Job posted successfully!")
        return redirect("hrdashboard")

    return render(request, "postjob.html", {"hr": hr})


def edit_job(request, job_id):
    if "hr_id" not in request.session:
        return redirect("hrlogin")

    job = get_object_or_404(Job, id=job_id, posted_by_id=request.session["hr_id"])

    if request.method == "POST":
        job.title = request.POST.get("title")
        job.description = request.POST.get("description")
        job.eligibility_cgpa = request.POST.get("eligibility_cgpa") or 0.0
        job.skills_required = request.POST.get("skills_required")
        job.last_date = request.POST.get("last_date")
        job.save()

        messages.success(request, "Job updated successfully!")
        return redirect("hrdashboard")

    return render(request, "edit_job.html", {"job": job})


def delete_job(request, job_id):
    if "hr_id" not in request.session:
        return redirect("hrlogin")

    job = get_object_or_404(Job, id=job_id, posted_by_id=request.session["hr_id"])
    job.delete()
    messages.success(request, "Job deleted successfully!")
    return redirect("hrdashboard")


def view_jobs(request):
    from datetime import timedelta
    today = timezone.now()
    closing_soon_date = today + timedelta(days=3)
    
    # Filter out expired jobs
    jobs_list = Job.objects.filter(last_date__gte=today).order_by("-created_at")
    
    # Annotate jobs with priority status
    for job in jobs_list:
        job.is_closing_soon = job.last_date <= closing_soon_date.date()
        
    return render(request, "viewjobs.html", {"jobs": jobs_list, "today": today})


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    profile = get_object_or_404(StudentProfile, user=request.user)

    # --- Eligibility Check: CGPA ---
    cgpa_req = float(job.eligibility_cgpa or 0)
    stud_cgpa = float(profile.cgpa or 0)
    if stud_cgpa < cgpa_req:
        messages.error(request, f"Sorry, this job requires a minimum CGPA of {cgpa_req}. Your current CGPA is {stud_cgpa}.")
        return redirect("view_jobs")

    # Prevent duplicate applications
    if Application.objects.filter(student=profile, job=job).exists():
        messages.warning(request, "You have already applied for this job!")
    else:
        Application.objects.create(
            student=profile,
            job=job,
            position=job.title,
        )

        # --- Smart Notification Engine ---
        # Robust parsing for accurate notification content
        import re
        import difflib
        def parse_skills_local(s):
            if not s: return []
            s = re.sub(r'[\r\n;]+', ',', s)
            return [item.strip().lower() for item in s.split(',') if item.strip()]

        job_skills_raw = parse_skills_local(job.skills_required)
        stud_skills_raw = parse_skills_local(profile.skills)
        matched = [s for s in job_skills_raw if any(difflib.get_close_matches(s, stud_skills_raw, n=1, cutoff=0.75))]
        match_pct = round((len(matched) / len(job_skills_raw)) * 100) if job_skills_raw else 75
        cgpa_ok = True # Already checked above

        if match_pct >= 80 and cgpa_ok:
            note_msg = (f"🚀 Great news, {profile.user.username}! You applied for '{job.title}' at {job.company}. "
                        f"You match {match_pct}% of the required skills — you're a strong candidate!")
        elif match_pct >= 50:
            note_msg = (f"✅ Application submitted for '{job.title}' at {job.company}. "
                        f"You match {match_pct}% of required skills. Tip: brush up on the remaining skills to stand out!")
        else:
            note_msg = (f"📋 You applied for '{job.title}' at {job.company}. "
                        f"Consider visiting Skill Gap Advisor to boost your profile before the deadline.")

        note = Notification.objects.create(student=profile, message=note_msg)

        # Send email notification
        if profile.user.email:
            send_mail(
                subject="📢 Job Application Submitted — PlaceMentor",
                message=note_msg.replace('**', ''),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[profile.user.email],
                fail_silently=True,
            )

        messages.success(request, "Applied successfully!")

    return redirect("student_dashboard")






@login_required
def my_applications(request):
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    applications = Application.objects.filter(student=student_profile).select_related("job").order_by("-applied_on")

    context = {
        "applications": applications,
        "total_count": applications.count(),
        "selected_count": applications.filter(status="Selected").count(),
        "shortlisted_count": applications.filter(status="Shortlisted").count(),
        "pending_count": applications.filter(status="Applied").count(),
        "rejected_count": applications.filter(status="Rejected").count(),
    }
    return render(request, "my_applications.html", context)

def _rank_candidate(app):
    """AI Candidate Ranker: compute a composite fit score (0-100) for each applicant."""
    import difflib
    score = 0
    breakdown = {}

    # 1. Skill Match (50 pts)
    job_skills = [s.strip().lower() for s in (app.job.skills_required or '').replace(',', ' ').split() if s.strip()]
    stud_skills = [s.strip().lower() for s in (app.student.skills or '').replace(',', ' ').split() if s.strip()]
    if job_skills:
        matches = [s for s in job_skills if any(difflib.get_close_matches(s, stud_skills, n=1, cutoff=0.8))]
        skill_score = round((len(matches) / len(job_skills)) * 50)
    else:
        skill_score = 25  # neutral
        matches = []
    score += skill_score
    breakdown['skills'] = skill_score

    # 2. CGPA Eligibility (25 pts)
    cgpa_req = float(app.job.eligibility_cgpa or 0)
    stud_cgpa = float(app.student.cgpa or 0)
    if stud_cgpa >= cgpa_req:
        cgpa_score = 25
    else:
        gap = cgpa_req - stud_cgpa
        cgpa_score = max(0, 25 - int(gap * 20))
    score += cgpa_score
    breakdown['cgpa'] = cgpa_score

    # 3. Profile Completion (15 pts)
    pc = float(app.student.profile_completion or 0)
    pc_score = round(pc * 0.15)
    score += pc_score
    breakdown['profile'] = pc_score

    # 4. Branch Relevance (10 pts)
    branch = (app.student.branch or '').lower()
    job_title = (app.job.title or '').lower() + ' ' + (app.job.description or '').lower()
    branch_map = {
        'cs': ['software', 'developer', 'web', 'python', 'java', 'frontend', 'backend', 'data', 'ai', 'ml'],
        'it': ['software', 'developer', 'web', 'network', 'cloud', 'devops'],
        'ece': ['hardware', 'embedded', 'electronics', 'iot', 'vlsi'],
        'me': ['mechanical', 'design', 'cad', 'production', 'automation'],
    }
    branch_score = 0
    for key, kws in branch_map.items():
        if key in branch and any(k in job_title for k in kws):
            branch_score = 10
            break
    score += branch_score
    breakdown['branch'] = branch_score

    total = min(100, score)
    if total >= 80:   tier, tier_color = 'Excellent', '#10b981'
    elif total >= 60: tier, tier_color = 'Good',      '#14b8a6'
    elif total >= 40: tier, tier_color = 'Fair',      '#d4af37'
    else:             tier, tier_color = 'Weak',      '#ef4444'

    # AI Summary Generation
    user_name = app.student.name or app.student.user.username
    top_skills = ', '.join(matches[:2]) if matches else (app.student.branch or "general skills")
    meets_cgpa = "exceeds" if stud_cgpa > cgpa_req else ("meets" if stud_cgpa == cgpa_req else "is below")
    
    if total >= 80:
        summary = f"{user_name} is a highly recommended candidate ({total}% match) with a strong background in {top_skills}. Their CGPA of {stud_cgpa} {meets_cgpa} the {cgpa_req} requirement. Excellent technical fit."
    elif total >= 60:
        summary = f"{user_name} is a strong candidate ({total}% match) demonstrating proficiency in {top_skills}. Their profile is solid, and their CGPA {meets_cgpa} the requirement. Worth interviewing."
    elif total >= 40:
        summary = f"{user_name} is a potential candidate ({total}% match). They have some relevant background in {top_skills}, but might need upskilling. Their CGPA {meets_cgpa} the requirement."
    else:
        summary = f"{user_name} has a lower match score ({total}%) for this specific role. They lack key skills compared to the job description. CGPA {meets_cgpa} the requirement."

    return {
        'score': total,
        'tier': tier,
        'tier_color': tier_color,
        'breakdown': breakdown,
        'matched_skills': matches,
        'ai_summary': summary,
    }


def hr_applications(request):
    if "hr_id" not in request.session:
        return redirect("hrlogin")

    hr = HR.objects.get(id=request.session["hr_id"])
    raw_apps = Application.objects.filter(job__posted_by=hr).select_related("student", "job")

    # Attach ranking data to each application
    applications = []
    for app in raw_apps:
        rank_data = _rank_candidate(app)
        app.rank_score = rank_data['score']
        app.rank_tier = rank_data['tier']
        app.rank_tier_color = rank_data['tier_color']
        app.rank_breakdown = rank_data['breakdown']
        app.rank_tier_color = rank_data['tier_color']
        app.rank_breakdown = rank_data['breakdown']
        app.matched_skills = rank_data['matched_skills']
        app.ai_summary = rank_data['ai_summary']
        app.has_interview = hasattr(app, 'interview')
        applications.append(app)

    # Sort by rank score descending
    applications.sort(key=lambda a: a.rank_score, reverse=True)

    # Counts for stats bar
    shortlisted_count = sum(1 for a in applications if a.status == 'Shortlisted')
    selected_count    = sum(1 for a in applications if a.status == 'Selected')
    rejected_count    = sum(1 for a in applications if a.status == 'Rejected')

    return render(request, "hr_applications.html", {
        "applications": applications,
        "shortlisted_count": shortlisted_count,
        "selected_count": selected_count,
        "rejected_count": rejected_count,
    })

def update_application_status(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        app.status = new_status
        app.save()

        # --- Smart Notification Engine: status-aware message ---
        status_messages = {
            'Shortlisted': (
                f"🎉 Congratulations, {app.student.user.username}! You've been shortlisted for "
                f"'{app.job.title}' at {app.job.company}. Get ready — an interview may be coming soon!"
            ),
            'Selected': (
                f"🏆 Amazing! You've been Selected for '{app.job.title}' at {app.job.company}. "
                f"The HR team will reach out with the next steps. Best of luck!"
            ),
            'Rejected': (
                f"📋 Your application for '{app.job.title}' at {app.job.company} was not selected this time. "
                f"Don't be discouraged — visit the Skill Gap Advisor for personalised improvement tips!"
            ),
            'In Review': (
                f"🔍 Your application for '{app.job.title}' at {app.job.company} is currently under review. "
                f"Hang tight — the HR team is evaluating your profile!"
            ),
        }
        note_msg = status_messages.get(
            new_status,
            f"Your application for '{app.job.title}' at {app.job.company} has been updated to: {new_status}."
        )
        note = Notification.objects.create(student=app.student, message=note_msg)

        # Send email
        if app.student.user.email:
            send_mail(
                subject=f"📢 Application Update — {new_status} | PlaceMentor",
                message=note_msg,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[app.student.user.email],
                fail_silently=True,
            )

        messages.success(request, f"Status updated to {new_status} for {app.student.user.username}")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'status': new_status})

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})

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
    unread_count = notifications.filter(is_read=False).count()
    return render(request, "notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })


@login_required
def mark_notifications_read(request):
    """Mark all notifications as read."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    Notification.objects.filter(student=profile, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications")


@login_required
def toggle_bookmark(request, job_id):
    """Toggle bookmark on a job."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    job = get_object_or_404(Job, id=job_id)
    bookmark, created = BookmarkedJob.objects.get_or_create(student=profile, job=job)
    if not created:
        bookmark.delete()
        messages.success(request, f"Removed '{job.title}' from saved jobs.")
    else:
        messages.success(request, f"Saved '{job.title}' to your bookmarks.")
    return redirect(request.META.get('HTTP_REFERER', 'view_jobs'))


@login_required
def saved_jobs(request):
    """Show all bookmarked jobs."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    bookmarks = BookmarkedJob.objects.filter(student=profile).select_related('job').order_by('-bookmarked_at')
    return render(request, "saved_jobs.html", {"bookmarks": bookmarks})


# Free learning resource mapping for common skills
_SKILL_RESOURCES = {
    'python':     {'url': 'https://www.learnpython.org/',         'platform': 'LearnPython.org',  'icon': 'fa-brands fa-python'},
    'django':     {'url': 'https://docs.djangoproject.com/',      'platform': 'Django Docs',      'icon': 'fa-solid fa-globe'},
    'javascript': {'url': 'https://javascript.info/',             'platform': 'javascript.info',  'icon': 'fa-brands fa-js'},
    'react':      {'url': 'https://react.dev/learn',              'platform': 'React Docs',       'icon': 'fa-brands fa-react'},
    'sql':        {'url': 'https://sqlbolt.com/',                 'platform': 'SQLBolt',           'icon': 'fa-solid fa-database'},
    'java':       {'url': 'https://www.learnjavaonline.org/',     'platform': 'LearnJava',        'icon': 'fa-brands fa-java'},
    'c++':        {'url': 'https://www.learncpp.com/',            'platform': 'LearnCpp',         'icon': 'fa-solid fa-code'},
    'machine learning': {'url': 'https://www.coursera.org/learn/machine-learning', 'platform': 'Coursera (Andrew Ng)', 'icon': 'fa-solid fa-brain'},
    'data science': {'url': 'https://www.kaggle.com/learn',      'platform': 'Kaggle Learn',     'icon': 'fa-solid fa-chart-line'},
    'html':       {'url': 'https://www.w3schools.com/html/',      'platform': 'W3Schools',        'icon': 'fa-brands fa-html5'},
    'css':        {'url': 'https://www.w3schools.com/css/',       'platform': 'W3Schools',        'icon': 'fa-brands fa-css3-alt'},
    'node':       {'url': 'https://nodejs.dev/en/learn/',         'platform': 'Node.js Docs',     'icon': 'fa-brands fa-node-js'},
    'docker':     {'url': 'https://docs.docker.com/get-started/', 'platform': 'Docker Docs',      'icon': 'fa-brands fa-docker'},
    'git':        {'url': 'https://learngitbranching.js.org/',    'platform': 'Learn Git Branching','icon': 'fa-brands fa-git-alt'},
    'linux':      {'url': 'https://linuxjourney.com/',            'platform': 'Linux Journey',    'icon': 'fa-brands fa-linux'},
    'flutter':    {'url': 'https://flutter.dev/docs',             'platform': 'Flutter Docs',     'icon': 'fa-solid fa-mobile-screen'},
    'kotlin':     {'url': 'https://kotlinlang.org/docs/home.html','platform': 'Kotlin Docs',      'icon': 'fa-solid fa-code'},
    'aws':        {'url': 'https://aws.amazon.com/training/',     'platform': 'AWS Training',     'icon': 'fa-brands fa-aws'},
    'networking': {'url': 'https://www.netacad.com/',             'platform': 'Cisco NetAcad',    'icon': 'fa-solid fa-network-wired'},
}


@login_required
def skill_gap_advisor(request):
    """Smart Skill Gap Advisor — shows missing skills per job and learning resources."""
    import difflib
    profile = get_object_or_404(StudentProfile, user=request.user)
    today = timezone.now()

    import re
    # More robust parsing: split by comma, semicolon, newline, or multiple spaces
    def parse_skills(s):
        if not s: return []
        # Replace common separators with commas, then split
        s = re.sub(r'[\r\n;]+', ',', s)
        return [item.strip().lower() for item in s.split(',') if item.strip()]

    stud_skills = parse_skills(profile.skills)
    all_jobs = Job.objects.filter(last_date__gte=today)

    gap_data = []           
    already_applied_ids = set(
        Application.objects.filter(student=profile).values_list('job_id', flat=True)
    )

    for job in all_jobs:
        job_skills = parse_skills(job.skills_required)
        if not job_skills:
            continue

        matched = [s for s in job_skills if any(difflib.get_close_matches(s, stud_skills, n=1, cutoff=0.7))]
        missing = [s for s in job_skills if s not in matched]
        match_pct = round((len(matched) / len(job_skills)) * 100)

        # Show even high matches (0 missing) if requested, or at least one matched
        # But user said "show all ai match job in this list"
        # So we show everything that has at least some relevance or missing skills
        resources = []
        for skill in missing[:4]:  # top 4 missing skills
            res = None
            for key, val in _SKILL_RESOURCES.items():
                if key in skill or skill in key:
                    res = {'skill': skill, **val}
                    break
            if not res:
                res = {
                    'skill': skill,
                    'url': f'https://www.youtube.com/results?search_query={skill}+tutorial',
                    'platform': 'YouTube Tutorial',
                    'icon': 'fa-brands fa-youtube',
                }
            resources.append(res)

        job_title_lower = job.title.lower()
        job_skills_lower = ' '.join(job_skills)
        
        # Smart mapping using both title and required skills
        if any(x in job_title_lower or x in job_skills_lower for x in ['frontend', 'ui', 'ux', 'react', 'angular', 'vue', 'html', 'css']):
            roadmap = {'name': 'Frontend Developer', 'url': 'https://roadmap.sh/frontend'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['backend', 'django', 'node', 'spring', 'api', 'server', 'express', 'flask']):
            roadmap = {'name': 'Backend Developer', 'url': 'https://roadmap.sh/backend'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['data', 'machine', 'ai', 'analytics', 'python', 'sql', 'scientist', 'model']):
            roadmap = {'name': 'AI & Data Scientist', 'url': 'https://roadmap.sh/ai-data-scientist'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['full', 'stack', 'mern', 'mean']):
            roadmap = {'name': 'Full Stack Developer', 'url': 'https://roadmap.sh/full-stack'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['devops', 'cloud', 'aws', 'azure', 'docker', 'kubernetes', 'ci', 'cd', 'linux']):
            roadmap = {'name': 'DevOps Engineer', 'url': 'https://roadmap.sh/devops'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['android', 'ios', 'mobile', 'flutter', 'react native', 'swift', 'kotlin']):
            roadmap = {'name': 'Mobile Developer', 'url': 'https://roadmap.sh/android'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['security', 'cyber', 'pentest', 'ethical']):
            roadmap = {'name': 'Cyber Security', 'url': 'https://roadmap.sh/cyber-security'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['qa', 'test', 'automation', 'selenium']):
            roadmap = {'name': 'QA Engineer', 'url': 'https://roadmap.sh/qa'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['blockchain', 'web3', 'solidity', 'crypto', 'smart contract']):
            roadmap = {'name': 'Blockchain Developer', 'url': 'https://roadmap.sh/blockchain'}
        elif any(x in job_title_lower or x in job_skills_lower for x in ['game', 'unity', 'unreal', 'godot']):
            roadmap = {'name': 'Game Developer', 'url': 'https://roadmap.sh/game-developer'}
        else:
            roadmap = {'name': 'Software Developer', 'url': 'https://roadmap.sh/software-architect'}

        gap_data.append({
            'job': job,
            'match_pct': match_pct,
            'matched': matched,
            'missing': missing,
            'total_skills_count': len(job_skills),
            'resources': resources,
            'roadmap': roadmap,
            'applied': job.id in already_applied_ids,
        })

    # Sort: highest match % first
    gap_data.sort(key=lambda x: x['match_pct'], reverse=True)

    return render(request, 'skill_gap_advisor.html', {
        'profile': profile,
        'gap_data': gap_data,
        'stud_skills': sorted(stud_skills),
    })

@login_required
def job_recommendations(request):
    import difflib
    from datetime import timedelta
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # 1. Advanced Skill Parsing & Normalization
    def get_normalized_skills(skills_str):
        import re
        if not skills_str: return []
        # Split by comma, semicolon, newline, or multiple spaces
        raw_list = re.split(r'[,\n\r;]+', skills_str)
        return [s.strip().lower() for s in raw_list if s.strip()]

    student_skills = get_normalized_skills(profile.skills)
    student_branch = (profile.branch or "").lower()
    
    # 2. Filtering & Preparation
    today = timezone.now()
    closing_soon_date = today + timedelta(days=3)
    all_jobs = Job.objects.filter(last_date__gte=today)
    recommended_jobs = []
    
    # Profile Completion Score (Static component)
    profile_score = (profile.profile_completion or 0) * 0.1 # Max 10%
    
    for job in all_jobs:
        job_skills = get_normalized_skills(job.skills_required)
        job_title = (job.title or "").lower()
        job_desc = (job.description or "").lower()
        
        # --- PHASE A: Skill Fit (Max 50%) ---
        if not job_skills:
            skill_score = 25 # Neutral if not specified
            matched_skills = []
            missing_skills = []
        else:
            matches = [s for s in job_skills if any(difflib.get_close_matches(s, student_skills, n=1, cutoff=0.8))]
            skill_match_ratio = len(matches) / len(job_skills)
            skill_score = skill_match_ratio * 50
            matched_skills = matches
            missing_skills = [s for s in job_skills if s not in matches]

        # --- PHASE B: Contextual Fit (Max 20%) ---
        # Look for student skills in Title/Description
        context_matches = 0
        for s in student_skills:
            if s in job_title or s in job_desc:
                context_matches += 1
        
        context_score = min(20, (context_matches * 5)) if student_skills else 10

        # --- PHASE C: Academic & Branch Fit (Max 20%) ---
        academic_score = 0
        
        # Branch Relevance (Manual mapping for common patterns)
        branch_keywords = {
            'cs': ['software', 'developer', 'web', 'python', 'java', 'frontend', 'backend', 'data'],
            'it': ['software', 'developer', 'web', 'network', 'cloud'],
            'ece': ['hardware', 'embedded', 'electronics', 'iot', 'vlsih'],
            'me': ['mechanical', 'design', 'cad', 'production', 'automation'],
        }
        
        is_branch_match = False
        for key, keywords in branch_keywords.items():
            if key in student_branch:
                if any(k in job_title for k in keywords):
                    is_branch_match = True
                    break
        
        if is_branch_match: academic_score += 10
        
        # CGPA Factor
        cgpa_req = float(job.eligibility_cgpa or 0)
        stud_cgpa = float(profile.cgpa or 0)
        if stud_cgpa >= cgpa_req:
            academic_score += 10
        else:
            # Penalize slightly but don't zero out if gap is small
            gap = cgpa_req - stud_cgpa
            academic_score += max(0, 10 - (gap * 20))

        # --- FINAL AGGREGATION ---
        final_score = skill_score + context_score + academic_score + profile_score
        final_score = round(max(0.0, min(100.0, float(final_score))), 1)
        
        if True: # Show all jobs to give students a comprehensive view
            recommended_jobs.append({
                'job': job,
                'score': final_score,
                'breakdown': {
                    'skills': round(skill_score, 1),
                    'context': round(context_score, 1),
                    'academic': round(academic_score, 1),
                    'profile': round(profile_score, 1),
                },
                'matched_skills': matched_skills,
                'missing_skills': missing_skills,
                'is_closing_soon': job.last_date <= closing_soon_date.date(),
                'insights': [
                    "Strong branch alignment" if is_branch_match else None,
                    "Academic requirement met" if stud_cgpa >= cgpa_req else None,
                    f"Matched {len(matched_skills)} key skills" if matched_skills else None,
                ]
            })

    # Filter out None insights
    for item in recommended_jobs:
        item['insights'] = [i for i in item['insights'] if i]
            
    recommended_jobs.sort(key=lambda x: x['score'], reverse=True)
    # Return all jobs, not just top 12
    # recommended_jobs = recommended_jobs[:12]

    # Post-process Tiers
    for item in recommended_jobs:
        s = item['score']
        if s >= 85: item['tier'] = 'excellent'
        elif s >= 65: item['tier'] = 'good'
        elif s >= 40: item['tier'] = 'fair'
        else: item['tier'] = 'low'

    context = {
        "recommended_jobs": recommended_jobs,
        "profile": profile,
        "student_skills": sorted(student_skills),
        "excellent_count": sum(1 for i in recommended_jobs if i['tier'] == 'excellent'),
        "top_score": recommended_jobs[0]['score'] if recommended_jobs else 0,
    }
    return render(request, "job_recommendations.html", context)

@login_required
def edit_profile(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == "POST":
        profile.phone = request.POST.get("phone", profile.phone)
        profile.college_name = request.POST.get("college_name", profile.college_name)
        profile.branch = request.POST.get("branch", profile.branch)
        profile.cgpa = request.POST.get("cgpa", profile.cgpa)
        profile.skills = request.POST.get("skills", profile.skills)
        profile.profile_completion = compute_profile_completion(profile)
        profile.save()
        messages.success(request, "Profile updated successfully!")
    return redirect("student_dashboard")


@login_required
def withdraw_application(request, app_id):
    """Allow students to withdraw a pending application."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    application = get_object_or_404(Application, id=app_id, student=profile)

    if application.status != "Applied":
        messages.error(request, "You can only withdraw applications that are still pending.")
    else:
        job_title = application.job.title
        company = application.job.company
        application.delete()

        Notification.objects.create(
            student=profile,
            message=f"You withdrew your application for {job_title} at {company}."
        )
        messages.success(request, "Application withdrawn successfully.")

    return redirect("my_applications")


@login_required
def notifications(request):
    """Show all notifications for the logged-in student."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    notifications = Notification.objects.filter(student=profile).order_by("-created_at")
    unread_count = notifications.filter(is_read=False).count()
    return render(request, "notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })


@login_required
def mark_notifications_read(request):
    """Mark all notifications as read for the logged-in student."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    Notification.objects.filter(student=profile, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications")


@login_required
def dismiss_job_alerts(request):
    """Mark new-job alert notifications as read (called via AJAX from dashboard popup)."""
    if request.method == "POST":
        profile = get_object_or_404(StudentProfile, user=request.user)
        Notification.objects.filter(
            student=profile, is_read=False, message__contains="🚀 New Job Alert"
        ).update(is_read=True)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def change_password(request):
    """Allow students to change their password."""
    if request.method == "POST":
        current_password = request.POST.get("current_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif len(new_password) < 8:
            messages.error(request, "New password must be at least 8 characters.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            # Re-login to prevent session invalidation
            login(request, request.user)
            messages.success(request, "Password changed successfully!")

    return redirect("student_dashboard")

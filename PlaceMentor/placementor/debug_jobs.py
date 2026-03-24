import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'placementor.settings')
django.setup()

from home.models import Job, Notification, StudentProfile
from django.utils import timezone

def check():
    now = timezone.now()
    active_jobs = Job.objects.filter(last_date__gte=now)
    active_job_titles = [j.title for j in active_jobs]
    active_job_companies = [j.company for j in active_jobs]
    
    print("--- Active Jobs ---")
    for j in active_jobs:
        print(f"ID: {j.id}, Title: '{j.title}' at {j.company}, Last Date: {j.last_date}")

    print("\n--- Unread New Job Alerts ---")
    alerts = Notification.objects.filter(message__contains="🚀 New Job Alert", is_read=False)
    for a in alerts:
        print(f"ID: {a.id}, Student: {a.student.user.username}, Message: {a.message}")

if __name__ == "__main__":
    check()

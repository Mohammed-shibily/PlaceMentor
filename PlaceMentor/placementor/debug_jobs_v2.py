import os
import django
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'placementor.settings')
django.setup()

from home.models import Job, Notification
from django.utils import timezone

try:
    now = timezone.now()
    active_jobs = Job.objects.filter(last_date__gte=now)
    
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        f.write("--- Active Jobs ---\n")
        for j in active_jobs:
            f.write(f"ID: {j.id}, Title: {j.title} at {j.company}, Last Date: {j.last_date}\n")
            
        f.write("\n--- Unread New Job Alerts ---\n")
        alerts = Notification.objects.filter(message__contains="🚀 New Job Alert", is_read=False)
        for a in alerts:
            f.write(f"ID: {a.id}, Student: {a.student.user.username}, Message: {a.message}\n")
    print("Debug script completed. Check debug_output.txt")
except Exception as e:
    with open('debug_error.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    print("Debug script failed. Check debug_error.txt")

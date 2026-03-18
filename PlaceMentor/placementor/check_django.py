import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "placementor.settings")
django.setup()

import sys
import traceback

from home.models import StudentProfile

try:
    list(StudentProfile.objects.all())
    print("Success")
except Exception as e:
    with open('error.txt', 'w') as f:
        traceback.print_exc(file=f)

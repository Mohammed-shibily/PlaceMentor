from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)  
    college_name = models.CharField(max_length=200, blank=True)
    branch = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True) 
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    skills = models.TextField(help_text="Comma separated skills", blank=True)
    profile_completion = models.IntegerField(default=0)

    def __str__(self):
        
        return self.user.username
    

    
class Interview(models.Model):
        application = models.OneToOneField("Application", on_delete=models.CASCADE)
        date = models.DateTimeField()
        location = models.CharField(max_length=200, blank=True)

        def __str__(self):
            return f"{self.application.student.user.username} - {self.application.company} ({self.application.position})"
        
class Notification(models.Model):
        student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
        message = models.CharField(max_length=255)
        is_read = models.BooleanField(default=False)
        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{self.student.user.username} - {self.message}"
        

class HR(models.Model):
    fullname = models.CharField(max_length=100)
    company = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=200)  # store hashed password later

    def __str__(self):
        return f"{self.fullname} ({self.company})"
    
class Job(models.Model):
    posted_by = models.ForeignKey(
        "HR",
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,  # HR.jobs.all() → all jobs posted by HR
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    eligibility_cgpa = models.FloatField(default=0.0)
    company = models.CharField(max_length=200, default="Unknown")
    skills_required = models.CharField(max_length=255, null=True, blank=True)
    last_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('In Review', 'In Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Selected', 'Selected'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    job = models.ForeignKey("Job", on_delete=models.CASCADE)
    position = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Applied')
    applied_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.job.company} ({self.position})"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"


class BookmarkedJob(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='bookmarks')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='bookmarked_by')
    bookmarked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'job')

    def __str__(self):
        return f"{self.student.user.username} bookmarked {self.job.title}"
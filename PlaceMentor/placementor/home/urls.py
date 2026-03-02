from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Common
    path("", views.index, name="index"),
    path("logout/", views.custom_logout, name="logout"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    # 🎓 Student Routes
    path("studregister/", views.studentregister, name="studregister"),
    path("studlogin/", views.studentlogin, name="studlogin"),
    path("dashboard/", views.student_dashboard, name="student_dashboard"),
    path("jobs/", views.view_jobs, name="view_jobs"),
    path("apply-job/<int:job_id>/", views.apply_job, name="apply_job"),
    path("notifications/", views.notifications, name="notifications"),
    # 👔 HR Routes
    path("hrregister/", views.hrregister, name="hrregister"),
    path("hrlogin/", views.hrlogin, name="hrlogin"),
    path("hrdashboard/", views.hrdashboard, name="hrdashboard"),
    path("post-job/", views.post_job, name="post_job"),
    path("hrlogout/", views.custom_logout, name="hr_logout"),
    path("hr/applications/", views.hr_applications, name="hr_applications"),
    path("hr/update-status/<int:app_id>/", views.update_application_status, name="update_application_status"),
    path("hr/interview/create/<int:app_id>/", views.create_interview, name="create_interview"),

]

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
    path("my-applications/", views.my_applications, name="my_applications"),
    path("recommendations/", views.job_recommendations, name="job_recommendations"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("withdraw-application/<int:app_id>/", views.withdraw_application, name="withdraw_application"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/mark-read/", views.mark_notifications_read, name="mark_notifications_read"),
    path("bookmark/<int:job_id>/", views.toggle_bookmark, name="toggle_bookmark"),
    path("saved-jobs/", views.saved_jobs, name="saved_jobs"),
    path("skill-gap/", views.skill_gap_advisor, name="skill_gap_advisor"),
    path("dismiss-job-alerts/", views.dismiss_job_alerts, name="dismiss_job_alerts"),
    # 👔 HR Routes
    path("hrregister/", views.hrregister, name="hrregister"),
    path("hrlogin/", views.hrlogin, name="hrlogin"),
    path("hrdashboard/", views.hrdashboard, name="hrdashboard"),
    path("post-job/", views.post_job, name="post_job"),
    path("hrlogout/", views.custom_logout, name="hr_logout"),
    path("hr/applications/", views.hr_applications, name="hr_applications"),
    path("hr/update-status/<int:app_id>/", views.update_application_status, name="update_application_status"),
    path("hr/interview/create/<int:app_id>/", views.create_interview, name="create_interview"),
    path("hr/job/edit/<int:job_id>/", views.edit_job, name="edit_job"),
    path("hr/job/delete/<int:job_id>/", views.delete_job, name="delete_job"),

]

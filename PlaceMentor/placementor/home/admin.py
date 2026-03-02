from django.contrib import admin
from .models import StudentProfile, Application, Job,ContactMessage,HR

admin.site.register(HR)
admin.site.register(ContactMessage)
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'company', 'posted_by', 'eligibility_cgpa', 'last_date', 'created_at'
    )
    fields = (
        'posted_by',
        'title',
        'description',
        'eligibility_cgpa',
        'company',
        'skills_required',
        'last_date',
    )
    search_fields = ('title', 'company', 'skills_required')
    list_filter = ('company', 'last_date', 'eligibility_cgpa')


# Register other models normally
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_no', 'branch', 'cgpa')
    search_fields = ('user__username', 'roll_no', 'branch')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'status', 'applied_on')
    list_filter = ('status', 'applied_on')
    search_fields = ('student__user__username', 'job__title')
class ApplicationInline(admin.TabularInline):
    model = Application
    extra = 0
    fields = ('student', 'status', 'applied_on')
    readonly_fields = ('applied_on',)

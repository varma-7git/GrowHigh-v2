from django.contrib import admin

from .models import CompanyProfile, FacultyProfile, StudentProfile, User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("login_id", "full_name", "email", "role", "is_active", "created_at")
    search_fields = ("login_id", "full_name", "email")
    list_filter = ("role", "is_active")
    # The password is stored as a hash. Typing a plain password into this box saves it unhashed and locks the person out,
    # so it is read-only here. Set passwords with:  python manage.py changepassword LOGIN_ID
    readonly_fields = ("password",)

    def save_model(self, request, obj, form, change):
        if not change and not obj.password:  # created here without a password: make it unusable instead of blank
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)
admin.site.register(StudentProfile, list_display=("user", "branch", "year_of_study"))
admin.site.register(FacultyProfile, list_display=("user", "department", "status"), list_filter=("status",))
admin.site.register(CompanyProfile, list_display=("company_name", "user", "status"), list_filter=("status",))

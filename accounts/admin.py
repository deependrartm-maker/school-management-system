from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin
from .models import AccountLock

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active')

    ordering = ('email',)
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active'),
        }),
    )

    USERNAME_FIELD = 'email'

    
@admin.register(AccountLock)
class AccountLockAdmin(admin.ModelAdmin):
    list_display = ("user", "failed_attempts", "is_locked", "locked_at")
    readonly_fields = ("locked_at",)
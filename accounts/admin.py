from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class ProfileUserAdmin(UserAdmin):
    inlines = (ProfileInline, )
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_superuser', 'date_joined', )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(ProfileUserAdmin, self).get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, ProfileUserAdmin)

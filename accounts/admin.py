from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import PasswordResetForm
from django.utils.crypto import get_random_string
from simple_history.admin import SimpleHistoryAdmin

from .forms import UserCreationForm
from .models import HistoryUser, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class ProfileUserAdmin(SimpleHistoryAdmin, UserAdmin):
    """Allow admins to create users with only a username & email"""
    inlines = (ProfileInline, )
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_superuser', 'date_joined', )
    change_form_template = 'admin/user_change_form.html'
    add_form_template = 'admin/user_add_form.html'

    add_form = UserCreationForm
    add_fieldsets = (
        (None, {
            'fields': ('email', 'username',),
        }),
        ('Password', {
            'description': "Optionally, you may set the user's password here.",
            'fields': ('password1', 'password2'),
            'classes': ('collapse', 'collapse-closed'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            # Creating user, send a password reset email
            if not form.cleaned_data['password1'] or not obj.has_usable_password():
                # Django's PasswordResetForm won't let us reset an unusable
                # password. We set it above super() so we don't have to save twice.
                obj.set_password(get_random_string())
            reset_password = True
        else:
            reset_password = False

        super().save_model(request, obj, form, change)

        # Generate reset password key and send email to new user
        if reset_password:
            reset_form = PasswordResetForm({'email': obj.email})
            # Not checking results of form validation here as
            # the incoming email is validated by the User ModelForm
            reset_form.is_valid()
            reset_form.save(
                request=request,
                use_https=request.is_secure(),
                subject_template_name='registration/account_creation_subject.txt',
                email_template_name='registration/account_creation_email.html',
            )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(ProfileUserAdmin, self).get_inline_instances(request, obj)


admin.site.unregister(get_user_model())
admin.site.register(HistoryUser, ProfileUserAdmin)

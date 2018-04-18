from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm

from .models import Profile

User = get_user_model()


class ProfilePasswordChangeForm(PasswordChangeForm):
    """
    PasswordChange form which is only processed if a change is attempted
    by the user
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.empty_permitted = True
        self.fields['old_password'].required = False
        self.fields['new_password1'].required = False
        self.fields['new_password2'].required = False
        # auth.forms.PasswordChangeForm.old_password sets autofocus to True,
        # not desired here since this is part of a larger form on the page
        del self.fields['old_password'].widget.attrs['autofocus']
        self.fields['old_password'].widget.attrs['autocomplete'] = 'off'
        self.fields['new_password1'].widget.attrs['autocomplete'] = 'off'
        self.fields['new_password2'].widget.attrs['autocomplete'] = 'off'

    def _get_field_data(self):
        old = self.data.get('old_password')
        new = self.data.get('new_password1')
        confirm = self.data.get('new_password2')
        return (old, new, confirm)

    def attempted_change(self):
        """
        True if user has populated at least one field,
        attempting to change their password.
        """
        return any(self._get_field_data())

    def partial_change(self):
        """True if user attempted a change but did not provide all fields"""
        return self.attempted_change() and not all(self._get_field_data())

    def clean(self):
        super().clean()
        if self.partial_change():
            raise forms.ValidationError("All password fields are required to change your credentials.")


class ProfileForm(forms.ModelForm):
    """User editable profile fields"""
    class Meta:
        model = Profile
        fields = ['phone_number', ]


class UserForm(forms.ModelForm):
    """User editable fields"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', ]


class UserCreationForm(UserCreationForm):
    """
    A UserCreationForm with optional password inputs.
    """

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        # If one field gets autocompleted but not the other, our 'neither
        # password or both password' validation will be triggered.
        self.fields['password1'].widget.attrs['autocomplete'] = 'off'
        self.fields['password2'].widget.attrs['autocomplete'] = 'off'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = super().clean_password2()
        if bool(password1) ^ bool(password2):
            raise forms.ValidationError("Fill out both fields")
        return password2

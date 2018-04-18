from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView

from .forms import ProfileForm, ProfilePasswordChangeForm, UserForm


class UserProfileView(LoginRequiredMixin, TemplateView):
    """
        Handle three forms for user profile page
        User model form
        Profile model form
        Modified Django password change form
    """
    success_url = reverse_lazy('profile')
    template_name = "profile.html"

    NO_CHANGES_MESSAGE = "The submitted data was identical to the existing data. No changes were made."
    PASSWORD_CHANGED_MESSAGE = "Your password has been updated, please login again."
    PROFILE_CHANGED_MESSAGE = "Your profile has successfully been updated!"

    def get_context_data(self, *args, **kwargs):
        """Add all forms to context"""
        data = super().get_context_data(*args, **kwargs)
        data['userform'] = self.get_form(UserForm, 'user')
        data['userprofileform'] = self.get_form(ProfileForm, 'userprofile')
        data['passwordchangeform'] = self.get_form(ProfilePasswordChangeForm, 'passwordchangeform')
        return data

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """Check validity of all our forms"""
        forms = {
            'userform': self.get_form(UserForm, 'user'),
            'userprofileform': self.get_form(ProfileForm, 'userprofile'),
            'passwordchangeform': self.get_form(ProfilePasswordChangeForm, 'passwordchangeform')
        }
        if all(f.is_valid() for f in forms.values()):
            return self.form_valid(forms)
        else:
            return self.form_invalid(forms)

    def get_form(self, form_class=None, prefix=None):
        if form_class and prefix:
            return form_class(**self.get_form_kwargs(prefix))

    def get_form_kwargs(self, prefix):
        """Add additional kwargs to individual forms"""
        kwargs = {}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({'data': self.request.POST})
        if prefix == 'passwordchangeform':
            kwargs.update({'user': self.request.user})
        else:
            # Give the modelForms an instance
            instance = self.request.user.profile if prefix == 'userprofile' else self.request.user
            kwargs.update({'instance': instance, 'prefix': prefix})
        return kwargs

    def form_valid(self, forms):
        """Save the forms that have changed and let the user know what happened"""
        passwordchangeform = forms['passwordchangeform']
        userform = forms['userform']
        profileform = forms['userprofileform']
        user_data_changed = False
        password_changed = False

        if userform.has_changed():
            userform.save()
            user_data_changed = True
        if profileform.has_changed():
            profileform.save()
            user_data_changed = True
        if passwordchangeform.has_changed():
            passwordchangeform.save()
            password_changed = True
            messages.success(self.request, self.PASSWORD_CHANGED_MESSAGE)

        if user_data_changed:
            messages.success(self.request, self.PROFILE_CHANGED_MESSAGE)
        elif not user_data_changed and not password_changed:
            messages.warning(self.request, self.NO_CHANGES_MESSAGE)

        return HttpResponseRedirect(self.success_url)

    def form_invalid(self, forms):
        return self.render_to_response(self.get_context_data(form=forms))

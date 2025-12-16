from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    # Make email required (it's optional by default in Django)
    email = forms.EmailField(required=True, help_text='Required. We use this for password resets.')

    class Meta:
        model = User
        # These are the fields that will appear in the HTML
        fields = ('username', 'email')
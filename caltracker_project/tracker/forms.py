from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    # Make email required 
    email = forms.EmailField(required=True, help_text='Required. We use this for password resets.')

    class Meta:
        model = User
        fields = ('username', 'email')
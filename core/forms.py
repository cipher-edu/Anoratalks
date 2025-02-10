from django import forms
from .models import *
from django.contrib.auth.models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'middle_name', 'birth_date', 'address', 'phone_number']
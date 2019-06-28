'''
Created on Nov 22, 2017

@author: LongQuan
'''
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import AppUser

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    address = forms.CharField(max_length=40, required=False, help_text='Optional.')
    
    class Meta:
        model = AppUser
        fields = ('username', 'first_name', 'last_name', 'email', 'address','password1', 'password2', )
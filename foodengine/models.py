'''
Created on Nov 23, 2017

@author: LongQuan
'''
from django.db import models
from django.contrib.auth.models import AbstractUser

class AppUser(AbstractUser):
    # additional attributes to User
    member = models.CharField(max_length=1, default='N', blank=False)
    # member by default is 'N'. Update to 'Y' after becoming a member
    address = models.CharField(max_length=40, blank=False)

    def isMember(self):
        return self.member != 'N'
    
    def __str__(self):
        return self.username
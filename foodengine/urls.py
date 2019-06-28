'''
Created on Oct 9, 2017

@author: LongQuan
'''
from django.conf.urls import include, url
from foodengine import views

urlpatterns = [
    url(r'^signout', views.signout, name='signout'),
    url(r'^$', views.home, name='index'),
    url(r'^(?P<uid>\d+)$', views.userHome, name='userhome'),
    url(r'^home', views.home, name='home'),
    url(r'^search', views.search, name='search'), 
    url(r'^refineSearch', views.refineSearch, name='refineSearch'), 
    url(r'^changeLocation', views.changeLocation, name='changeLocation'),  
    url(r'^sort', views.sort, name='sort'),
    url(r'^signup', views.signup, name='signup'),
    url(r'^signin', views.signin, name='signin'),
    url(r'^myprofile/(?P<uid>\d+)/$', views.userProfile, name='myprofile'),
    url(r'^member', views.member, name='member'),
    url(r'^favorites', views.saveFavorites, name='savefavorites'),
    url(r'^about', views.about, name='about'),
]
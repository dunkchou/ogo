from django.conf.urls import patterns, url

from evernote import views

urlpatterns = patterns('',
    url(r'^list_evernote$', views.list_evernote, name='list_evernote'),
)

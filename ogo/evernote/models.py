from django.db import models
from django.contrib.auth.models import User

# Create a Note model and a Notebook model
class Notebook(models.Model):
    user_id = models.ForeignKey(User)

    title = models.CharField(max_length=1000, default='Untitled')
    guid = models.CharField(max_length=100)
    stack = models.CharField(max_length=1000, blank=True, null=True)
    last_modified = models.DateTimeField('date last modified')

    def __unicode__(self):
        return self.title


class Note(models.Model):
    user_id = models.ForeignKey(User)
    
    title = models.CharField(max_length=1000, default='Untitled')
    guid = models.CharField(max_length=100)
    notebook = models.ForeignKey(Notebook, blank=True, null=True)
    last_modified = models.DateTimeField('date last modified')
    create_date = models.DateTimeField('date created')

    def __unicode__(self):
        return self.title


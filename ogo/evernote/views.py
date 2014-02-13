from django.shortcuts import render, render_to_response, redirect
from django.core.urlresolvers import reverse
from binder.models import Note, Notebook, Stack
from django.http import HttpResponse

# Create your views here.
from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec

EN_CONSUMER_KEY = 'dunkchou'
EN_CONSUMER_SECRET = '76b12406fc9ca473'
ACCESS_TOKEN = 'S=s1:U=8dbb0:E=14b62418c4c:C=1440a906050:P=185:A=dunkchou:V=2:H=3e0f3c725ae9c725896ed67df9e7a449'

# Forms
from django import forms

def get_evernote_client(token=None):
    global EN_CONSUMER_KEY
    global EN_CONSUMER_SECRET
    if token:
        return EvernoteClient(token=token, sandbox=True)
    else:
        return EvernoteClient(
            consumer_key=EN_CONSUMER_KEY,
            consumer_secret=EN_CONSUMER_SECRET,
            sandbox=True
        )


def create_notebook(notebook, user):
    # create a new notebook
    if notebook.stack:
        notebook_db = Notebook(title=notebook.name, user_id=user, stack=notebook.stack, guid=notebook.guid, last_modified = notebook.serviceUpdated)
        notebook_db.save()
    else:
        notebook_db = Notebook(title=notebook.name, user_id=user, guid=notebook.guid, last_modified = notebook.serviceUpdated)
        notebook_db.save()
        
    notefiler = NoteFilter(notebookGuid=notebook.guid)
    result_spec = NotesMetadataResultSpec(includeTitle=True)

    result_list = note_store.findNotesMetadata(ACCESS_TOKEN, notefiler, 0, 10000, result_spec)
    for note in result_list.notes:
        if Note.objects.get(guid=note.guid):
            note_db = Note.objects.get(guid=note.guid)
            if note_db.last_modified != note.updated:
                note_db.title = note.title
                note_db.notebook = notebook_db
                note_db.last_modified = note.updated
                note_db.save()
        else:
            note_db = Note(title=note.title, guid=note.guid, user_id=request.user, notebook=notebook_db, last_modified = note.updated, create_date=note.created)
            note_db.save()
        
    return(notebook_db)
    
def update_notebook(notebook, user):
    # update the notebook
    notebook_db = Notebook.objects.get(guid=notebook.guid)
    if notebook_db.last_modified != notebook.serviceUpdated:
        notebook_db.title = notebook.name
        notebook_db.last_modified = notebook.serviceUpdated
        notebook_db.stack = notebook.stack
        notebook_db.save()
        
        # update the note
        notefiler = NoteFilter(notebookGuid=notebook.guid)
        result_spec = NotesMetadataResultSpec(includeTitle=True)

        result_list = note_store.findNotesMetadata(ACCESS_TOKEN, notefiler, 0, 10000, result_spec)
        for note in result_list.notes:
            if Note.objects.get(guid=note.guid):
                note_db = Note.objects.get(guid=note.guid)
                if note_db.last_modified != note.updated:
                    note_db.title = note.title
                    note_db.notebook = notebook_db
                    note_db.last_modified = note.updated
            else:
                note_db = Note(title=note.title, guid=note.guid, user_id=request.user, notebook=notebook_db, last_modified = note.updated, create_date=note.created)
                note_db.save()
    
    
class BinderForm(forms.Form):
    title = forms.CharField(max_length=1000)

def index(request):
    if request.method == 'POST': # If the form has been submitted...
        form = BinderForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            binder = Binder(title=form.cleaned_data['title'], is_main_binder=True, user_id=request.user)
            binder.save()
    else:
        form = BinderForm() # An unbound form        
        

def init_evernote(request):
    # initialize the notebook database
    if (len(Note.objects.all()) == 0) and (len(Notebook.objects.all()) == 0):
        return redirect('refresh_evernote')
        
    global ACCESS_TOKEN
    client = get_evernote_client(ACCESS_TOKEN)
    
    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()

    for notebook in notebooks:
        # Get notebook
        notebook_db = create_notebook(notebook, request.user)
            
        notefiler = NoteFilter(notebookGuid=notebook.guid)
        result_spec = NotesMetadataResultSpec(includeTitle=True)

        note_list = []
        result_list = note_store.findNotesMetadata(ACCESS_TOKEN, notefiler, 0, 10000, result_spec)
        for note in result_list.notes:
            note_tmp = Note(title=note.title, guid=note.guid, user_id=request.user, notebook=notebook_db, last_modified = note.updated, create_date=note.created)
            note_tmp.save()
         
    return redirect('list_evernote')
    
    
def list_evernote(request):
    notebooks = []

    for notebook in Notebook.objects.all():
        notebook_info = {}
        notebook_info['title'] = notebook.title
        notebook_info['id'] = notebook.id
        notebook_info['notes'] = []
        for note in notebook.note_set.all():
            notebook_info['notes'].append({'title':note.title, 'guid':note.guid}) 

    return render(request, 'evernote/notebook_list.html', {'notebooks': notebooks})

    
def refresh_evernote(request):
    global ACCESS_TOKEN
    client = get_evernote_client(ACCESS_TOKEN)
    
    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()

    for notebook in notebooks:
        # Get notebook
        if Notebook.objects.get(guid=notebook.guid):
            update_notebook(notebook)
        else:
            create_notebook(notebook)
         
    return redirect('list_evernote')

'''
def binder_detail(request, binder_id):
    cur_binder = Binder.objects.get(pk=binder_id)
    
    if request.method == 'POST': # If the form has been submitted...
        form = BinderForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            binder = Binder(title=form.cleaned_data['title'], is_main_binder=False, user_id=request.user, p_binder=cur_binder)
            binder.save()
    else:
        form = BinderForm() # An unbound form

    binders = []
    for binder in cur_binder.binder_set.all():
        binder_info = {}
        binder_info['title'] = binder.title
        binder_info['notes'] = []
        for note in binder.subnote.all():
            binder_info['notes'].append({'title':note.title, 'guid':note.guid}) 

        binder_info['subbinders'] = []
        for subbinder in binder.binder_set.all():
            binder_info['subbinders'].append({'title':subbinder.title, 'id':subbinder.id}) 

        binders.append(binder_info)

    note_list = []
    if cur_binder.subnote.all():
        for note in cur_binder.subnote.all():
            note_list.append({'title':note.title, 'guid':note.guid}) 

    return render(request, 'binder/binder_detail.html', {'binders': binders, 'note_list':note_list, 'form':form, 'binder_id':binder_id})

def note_detail(request, note_guid):    
    global ACCESS_TOKEN
    print ACCESS_TOKEN
    try:
        client = get_evernote_client(ACCESS_TOKEN)
    except KeyError:
        return redirect('oauth/index.html')

    note_store = client.get_note_store()
    notedetail = note_store.getNote(ACCESS_TOKEN, note_guid, True, True, True, True)
    
    return(HttpResponse(notedetail.content))
'''


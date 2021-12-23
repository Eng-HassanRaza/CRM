import uuid

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template import loader
from .models import agent_clients
from .forms import AgentClientForm,UploadFileForm
from django.contrib import messages
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
import pandas as pd
from django.conf import settings
from sqlalchemy import create_engine

from ..home.models import InitiateCalls


@login_required(login_url="/login/")
def agent_client(request):
    if not request.user.profile.profile_active:
        return redirect('updateprofile')
    msg=""
    if request.method == "POST":
        df=pd.read_excel(request.FILES['file'])
        df.columns=["appointment_scheduled", "product", "name","surname", "gender", "phone_number","age"]
        df["id"] = [uuid.uuid4() for _ in range(len(df.index))]
        df["source"] = ["manually added" for _ in range(len(df.index))]
        df.set_index("id", inplace=True)
        user = settings.DATABASES['default']['USER']
        password = settings.DATABASES['default']['PASSWORD']
        database_name = settings.DATABASES['default']['NAME']
        database_port = settings.DATABASES['default']['PORT']
        database_host = settings.DATABASES['default']['HOST']
        # database_url = settings.CORE_DIR+"/db.sqlite3"
        database_url = 'postgresql://{user}:{password}@{host}:{port}/{database_name}'.format(
            user=user,
            password=password,
            host=database_host,
            port=database_port,
            database_name=database_name,
        )
        try:
            engine = create_engine(database_url, echo=False)
        except:
            msg = "database not connected"
        df.to_sql('crm_agent_clients', con=engine,  if_exists='append')
    agent_client_data = agent_clients.objects.all()
    context = {'segment': 'agent_client','agent_data':agent_client_data,'message':msg}
    html_template = loader.get_template('crm/agent_client.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def agent_client_add(request):
    if not request.user.profile.profile_active:
        return redirect('updateprofile')

    if request.method == 'POST':
        agent_client_form = AgentClientForm(request.POST)
        if agent_client_form.is_valid():
            agent_client_form.save()

            messages.success(request, _('Your profile was successfully updated!'))
            return redirect('/crm/agent_client')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        agent_client_form = AgentClientForm()
    return render(request, 'crm/agent_client_add.html', {
        'agent_client_form': agent_client_form,
    })


@login_required(login_url="/login/")
def start_calls(request):
    if not request.user.profile.profile_active:
        return redirect('updateprofile')
    if request.method == 'POST':
        if request.FILES:
            df = pd.read_excel(request.FILES['file'])
            bulk_phones=[]
            for index, row in df.iterrows():
                obj = InitiateCalls(user=request.user,phone_number=row['phone_number'])
                bulk_phones.append(obj)
            InitiateCalls.objects.bulk_create(bulk_phones)
        else:
            InitiateCalls.objects.filter(call_status__isnull=True).update(call_status="waiting_to_call")

    initiate_calls = InitiateCalls.objects.filter(call_status__isnull=True)
    waiting_to_call = InitiateCalls.objects.filter(call_status="waiting_to_call")
    completed_calls = InitiateCalls.objects.exclude(Q(call_status__isnull=True) | Q(call_status="waiting_to_call"))
    return render(request, 'crm/start_calls.html', {
        'initiate_calls': initiate_calls,
        'waiting_to_call': waiting_to_call,
        'completed_calls': completed_calls,
    })


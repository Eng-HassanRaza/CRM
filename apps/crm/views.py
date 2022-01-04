import uuid
import datetime
import xlwt as xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader
from .models import agent_clients,AgentClientTags,AgentClientRemarks
from .forms import AgentClientForm,UploadFileForm
from django.contrib import messages
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
import pandas as pd
from ics import Calendar, Event
from ics.parse import Container,ContentLine
from django.conf import settings
from sqlalchemy import create_engine

from ..home.models import InitiateCalls
from apps.authentication.midllewares.auth import auth_middleware


@login_required(login_url="/login/")
@auth_middleware
def agent_client(request):
    agent_tags = ["new lead","reschedule a callback", "appointment set", "follow up", "burst deal", "win deal"]
    msg=""
    if request.is_ajax():
        agent_client_req = agent_clients.objects.filter(id=request.GET['client_id']).first()
        if "tag_change_fn" in request.GET:
            agent_client_req.tag = request.GET['selected_tag']
            agent_client_req.save()
            agent_client_tag = AgentClientTags(client_id=request.GET['client_id'],client_tag=request.GET['selected_tag'])
            agent_client_tag.save()
        else:
            agent_client_req.remarks = request.GET['client_remarks']
            agent_client_req.save()
            agent_client_tag = AgentClientRemarks(client_id=request.GET['client_id'],
                                                  client_remarks=request.GET['client_remarks'])
            agent_client_tag.save()
        return JsonResponse({'success': True})
    if request.method == "POST":
        df=pd.read_excel(request.FILES['file'])
        df.columns=["appointment_scheduled", "product", "name","surname", "gender", "phone_number","age"]
        df["id"] = [uuid.uuid4() for _ in range(len(df.index))]
        df["source"] = ["manually added" for _ in range(len(df.index))]
        df["agent_id"] = [request.user.id for _ in range(len(df.index))]
        df["created_at"] = [datetime.datetime.now() for _ in range(len(df.index))]
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
    agent_client_data = agent_clients.objects.filter(agent=request.user).order_by("-created_at")
    context = {'segment': 'agent_client','agent_data':agent_client_data,'message':msg, "agent_tags":agent_tags}
    html_template = loader.get_template('crm/agent_client.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
@auth_middleware
def agent_client_add(request):
    if request.method == 'POST':
        agent_client_form = AgentClientForm(request.POST)
        if agent_client_form.is_valid():
            instance = agent_client_form.save(commit=False)
            instance.agent = request.user
            instance.save()

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
@auth_middleware
def start_calls(request):
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


@login_required(login_url="/login/")
def create_icsfile(request,id):
    ICS_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    first_agent = agent_clients.objects.filter(id=id).first()
    calendar = Calendar()
    event = Event()
    event.name = _(first_agent.name)
    event.extra == [
        ContentLine(name="product", value=first_agent.product),
        ContentLine(name="surname", value=first_agent.surname),
        ContentLine(name="gender", value=first_agent.gender),
        ContentLine(name="phone_number", value=first_agent.phone_number),
        ContentLine(name="tag", value=first_agent.tag),
        ContentLine(name="remarks", value=first_agent.remarks),
        ContentLine(name="age", value=first_agent.age),
    ]
    event.begin = first_agent.appointment_scheduled.strftime(ICS_DATETIME_FORMAT)
    event.description = (f"Product: {first_agent.product}, Surname: {first_agent.surname}, Gender: {first_agent.gender}, Phone Number: {first_agent.phone_number}, Tag: {first_agent.tag }, Remarks: {first_agent.remarks }, Age: {first_agent.age }.")
    # event.end = agent_clients.end_time.strftime(ICS_DATETIME_FORMAT)
    # event.organizer = settings.DEFAULT_FROM_EMAIL
    calendar.events.add(event)
    filename_event = 'invite-%d.ics' % first_agent.id
    with open(filename_event, 'w') as ics_file:
        ics_file.writelines(calendar)
    response = HttpResponse(open(filename_event, 'rb').read())
    response['Content-Type'] = 'text/plain'
    response['Content-Disposition'] = 'attachment; filename=Event.ics'
    return response

@login_required(login_url="/login/")
def download_excelfile(request):
        # content-type of response
        response = HttpResponse(content_type='application/ms-excel')

        # decide file name
        response['Content-Disposition'] = 'attachment; filename="add_clients_template.xls"'

        # creating workbook
        wb = xlwt.Workbook(encoding='utf-8')

        # adding sheet
        ws = wb.add_sheet("sheet1")

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        # headers are bold
        font_style.font.bold = True

        # column header names, you can use your own headers here
        columns = ['appointment_secehdule', 'product', 'name', 'surname','phone_number','age' ]

        # write column headers in sheet
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

       # get your data, from database or from a text file...
      #  data = get_data()  # dummy method to fetch data.
        #for my_row in data:
        for i in range(0,1):
            row_num = row_num + 1
            ws.write(row_num, 0, "2021/12/15 10:00", font_style)
            ws.write(row_num, 1, "life insurance", font_style)
            ws.write(row_num, 2, "tan", font_style)
            ws.write(row_num, 3, "m", font_style)
            ws.write(row_num, 4, "6512341234", font_style)
            ws.write(row_num, 5, "12", font_style)

        wb.save(response)
        return response

@login_required(login_url="/login/")
def download_startcall(request):
    # content-type of response
    response = HttpResponse(content_type='application/ms-excel')

    # decide file name
    response['Content-Disposition'] = 'attachment; filename="add_phonenumber_template.xls"'

    # creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

    # adding sheet
    ws = wb.add_sheet("sheet1")

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    # headers are bold
    font_style.font.bold = True

    # column header names, you can use your own headers here
    columns = ['phone_number']

    # write column headers in sheet
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    # get your data, from database or from a text file...
    #  data = get_data()  # dummy method to fetch data.
    # for my_row in data:
    for i in range(0, 3):
        row_num = row_num + 1
        ws.write(row_num, 0, "6512341234", font_style)


    wb.save(response)
    return response

@login_required(login_url="/login/")
def ajax_date(request):
    data = dict()
    if request.is_ajax and request.method == "POST":
        client_id = request.POST.get("client_id", None)
        agent_date = request.POST.get("client_date", None)

        date_time = datetime.datetime.strptime(agent_date, '%Y-%m-%dT%H:%M')


        query=agent_clients.objects.filter(id=client_id).first()
        query.appointment_scheduled = date_time
        query.save()
        data['html_table'] = True
    return JsonResponse(data)



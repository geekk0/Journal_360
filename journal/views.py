import itertools
import datetime
import json
import smtplib
import ssl
from email.header import Header
from email.utils import formataddr

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import DetailView, View
from django.views.generic import TemplateView, ListView
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django import forms
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import MO, TU, WE, TH, FR, SA, SU
from django.contrib import messages
from django.core.mail import send_mail
from email.message import EmailMessage
from itertools import *
from operator import *


from .models import Notes, Record, Images, Comments, Department, Objectives, ObjectivesDone, ObjectivesStatus, \
    ScheduledTasks, RecordTags
from .forms import LoginForm, RegistrationForm, AddNote, AddComment, ResetPassword, AddScheduledTaskForm
from django_python3_ldap.utils import format_search_filters


class LoginView(View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        context = {'form': form}
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)

            if user:
                login(request, user)

                return HttpResponseRedirect('/')
            else:
                print('no user')
                print(username, password)
        return render(request, 'login.html', {'form': form})


class ResetPasswordView(View):

    def get(self, request, *args, **kwargs):
        form = ResetPassword(request.POST or None)
        form.initial['username'] = request.user.username
        context = {'form': form}
        return render(request, 'password_reset.html', context)

    def post(self, request, *args, **kwargs):
        current_user = request.user
        form = ResetPassword(request.POST or None)
        uid = request.user.username

        if form.is_valid():
            current_user.set_password(form.cleaned_data['new_password'])
            current_user.save()
            return HttpResponseRedirect('/')
        return render(request, 'password_reset.html', {'form': form})


class RegistrationView(View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        context = {'form': form}

        return render(request, 'registration.html', context)

    def post(self, request, *args, **kwargs):

        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)

            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.phone = form.cleaned_data['phone']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()

            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            login(request, user)
            return HttpResponseRedirect('/')
        context = {'form': form}
        return render(request, 'registration.html', context)


class AddNoteView(View):

    def get(self, request, *args, **kwargs):

        user = request.user.id

        if Notes.objects.filter(author=user).exists():
            return HttpResponseRedirect('/')

        else:

            form = AddNote(request.POST or None)
            context = {'form': form}

            return render(request, 'add_note.html', context)

    def post(self, request, *args, **kwargs):

        form = AddNote(request.POST or None)

        if form.is_valid():
            report = form.save(commit=False)

            report.author = request.user
            report.created_date = timezone.now()
            report.save()

            return HttpResponseRedirect('/')


class AddCommentView(View):

    def get(self, request, *args, **kwargs):

        form = AddComment(request.POST or None)
        context = {'form': form}

        return render(request, 'add_comment.html', context)

    def post(self, request, record_id, *args, **kwargs):

        form = AddComment(request.POST or None)

        if form.is_valid():
            comment = form.save(commit=False)

            comment.record_id = Record.objects.get(id=record_id)
            comment.author = request.user
            comment.created = timezone.now()
            comment.save()

            comments_count(request, record_id)

            return HttpResponseRedirect('/')


class AddScheduledTask(View):

    def get(self, request, *args, **kwargs):


        form = AddScheduledTaskForm(request.POST or None)
        form.initial['start_date'] = timezone.now()
        context = {'form': form}

        return render(request, 'add_scheduled_task.html', context)

    def post(self, request, *args, **kwargs):

        form = AddScheduledTaskForm(request.POST or None)

        if form.is_valid():
            new_scheduled_task = form.save(commit=False)

            new_scheduled_task.start_date = form.cleaned_data['start_date']
            new_scheduled_task.regularity = form.cleaned_data['regularity']
            new_scheduled_task.name = form.cleaned_data['name']
            new_scheduled_task.text = form.cleaned_data['text']
            new_scheduled_task.created = timezone.now()
            new_scheduled_task.author = request.user

            """department_to_create = form.cleaned_data['departments'][0]"""
            departments = form.cleaned_data['departments']

            week_days = form.cleaned_data['week_days']

            dates = get_task_dates(form.cleaned_data['start_date'], form.cleaned_data['regularity'], week_days)

            new_scheduled_task.date_list = dates

            new_scheduled_task.save()

            for dep in departments:

                new_scheduled_task.departments.add(dep)

            new_scheduled_task.save()

            return HttpResponseRedirect('/')
        else:
            print(form.errors)


def get_task_dates(start_date, regularity, week_days):


    task_dates = []

    delta = None

    end_date = datetime.date(2030, 6, 15)

    if week_days:
        for date in week_days:
            date = int(date)
            cycle_start_date = start_date + relativedelta(weekday=date)
            delta = relativedelta(weeks=1)
            while cycle_start_date <= end_date:
                task_dates.append(str(cycle_start_date))
                cycle_start_date += delta
        return task_dates

    if regularity == 'week':

        delta = relativedelta(weeks=1)

    if regularity == 'month':

        delta = relativedelta(months=1)

    if regularity == 'on weekends':

        satuday = start_date+relativedelta(weekday=5)
        sunday = start_date+relativedelta(weekday=6)
        delta = relativedelta(weeks=1)

        while (satuday <= end_date) & (sunday <= end_date):
            satuday_str = str(satuday)
            task_dates.append(satuday_str)
            satuday += delta
            sunday_str = str(sunday)
            task_dates.append(sunday_str)
            sunday += delta

        return task_dates

    if regularity == 'None':

        task_dates.append(str(start_date))

        return task_dates

    while start_date <= end_date:
        date = str(start_date)
        task_dates.append(date)
        start_date += delta

    return task_dates


def add_comment(request, record_id):

    record = Record.objects.get(id=record_id)

    input_text = request.GET.get('input_text')

    comment = Comments.objects.create(author_id=request.user.id, record_id=record)

    comment.text = input_text
    comment.created = timezone.now()
    comment.save()

    return HttpResponseRedirect('/')


def get_role(request):

    if request.user.is_authenticated:
        roles = []
        role = ''
        records_list = None
        notes = None

        for g in request.user.groups.all():
            roles.append(g.name)

        if not roles:
            records_list = None
            return render(request, 'not_in_group.html')

        else:

            role = roles[0]
        return role
    else:
        render(request, 'login.html')


def get_roles(request):
    if request.user.is_authenticated:
        roles = []
        role = ''
        records_list = None
        notes = None

        for g in request.user.groups.all():
            roles.append(g.name)

        if not roles:
            records_list = None
            return render(request, 'not_in_group.html')
        else:
            return roles
    else:
        render(request, 'login.html')


def send_report(request): # Преобразует заметки в записи

    full_text = ''
    author = request.user
    created_date = timezone.now()

    for note in Notes.objects.all():
        full_text = note.message

    Record.objects.create(author=author, created_date=created_date, text=full_text)

    Notes.objects.all().delete()

    return HttpResponseRedirect('/')


def edit_note(request, note_id):

    note = Notes.objects.get(id=note_id)

    if request.method != 'POST':
        form = AddNote(instance=note, initial={'message': note.message})
        context = {'form': form}

        return render(request, 'edit_note.html', context)

    else:
        form = AddNote(instance=note, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')

    context = {'note': note, 'index': index, 'form': form}
    return render(request, 'record.html', context)


def detect_admin_groups():
    all_users = User.objects.all()

    group_names = []


    for user in all_users:
        if user.has_perm('journal.change_record'):
            group_name = Group.objects.get(user=user.id)
            group_names.append(group_name)
    return group_names


@login_required
def rec_list(request, *device):

    admin_groups = detect_admin_groups()

    multirole = False

    roles = str(get_roles(request))
    user_groups = request.user.groups.all()

    user_departments_list = []


    for group in user_groups:

        deps = Department.objects.filter(groups=group)

        for dep_objects in deps:
            user_departments_list.append(dep_objects.name)


    if len(user_departments_list) > 1:
        multirole = True
    current_user = request.user
    match_authors_list = []

    user_departments = Department.objects.filter(groups__in=user_groups)

    for dep in user_departments:
        for group in Group.objects.filter(department=dep):
            for author in User.objects.filter(groups__name=group):
                match_authors_list.append(author)

    records = Record.objects.filter(author__in=match_authors_list).order_by('-created_date')

    notes = prepare_note(request)

    comments = Comments.objects.all().order_by('-created')

    groups_authors_list = Group.objects.filter(department__in=user_departments).distinct().\
        exclude(name__in=admin_groups).order_by('id')

    shifts_dates = shifts_match()

    scheduled_dates_query = ScheduledTasks.objects.filter(departments__in=user_departments).distinct()

    scheduled_dates_dict = create_scheduled_tasks_dict(scheduled_dates_query)

    task_date = str(datetime.date.today())

    tags = RecordTags.objects.filter(departments__in=user_departments).distinct()

    user_agent = request.META['HTTP_USER_AGENT']

    if 'Mobile' in user_agent:
        device = 'mobile'
    else:
        device = 'pc'

    objectives = Objectives.objects.filter(departments__in=user_departments).distinct().order_by('-created_date')

    objectives_sliced = objectives[:5]

    objectives_full = False

    if len(objectives) > 5:
        objectives_full = True

    if request.user.has_perm('journal.change_record'):
        user_is_admin = True
    else:
        user_is_admin = False

    context = {'records': records, 'comments': comments, 'roles': roles, 'current_user': current_user, 'notes': notes,
               'multirole': multirole, 'group_list': user_groups, 'author_list': match_authors_list,
               'user_departments': user_departments, 'groups_authors_list': groups_authors_list,
               'user_departments_list': user_departments_list, 'shifts_dates': json.dumps(shifts_dates),
               'scheduled_dates_dict': json.dumps(scheduled_dates_dict), 'device': device, 'objectives': objectives,
               'user_is_admin': user_is_admin, 'task_date': task_date, 'tags': tags, 'objectives_full': objectives_full,
               'objectives_sliced': objectives_sliced}

    return render(request, 'rec_list.html', context)


def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


def delete_note(request):

    user = request.user.id

    Notes.objects.filter(author=user).delete()
    return HttpResponseRedirect('/')


def comments_count(request, record_id):

    record = Record.objects.get(id=record_id)
    correct_count = len(Comments.objects.filter(record_id=record_id))
    record.comments_count = correct_count
    record.save()


def convert_date(date):


    set_year = date[:4]
    month = int(date[5:7])
    set_month = str(month - 1)
    set_day = date[8:10]

    set_date = set_year+', '+set_month+', '+set_day

    return set_date


def find_by_date(request):

    date = request.GET.get('date')

    multirole = False

    if request.user.groups.all().count() > 1:
        multirole = True

    admin_groups = detect_admin_groups()

    multirole = False

    roles = str(get_roles(request))
    user_groups = request.user.groups.all()

    user_departments_list = []

    for group in user_groups:

        deps = Department.objects.filter(groups=group)

        for dep_objects in deps:
            user_departments_list.append(dep_objects.name)

    if len(user_departments_list) > 1:
        multirole = True
    current_user = request.user.username
    match_authors_list = []

    user_departments = Department.objects.filter(groups__in=user_groups)

    for dep in user_departments:
        for group in Group.objects.filter(department=dep):
            for author in User.objects.filter(groups__name=group):
                match_authors_list.append(author)

    records = Record.objects.filter(author__in=match_authors_list).order_by('-created_date')

    groups_authors_list = Group.objects.filter(department__in=user_departments).distinct(). \
        exclude(name__in=admin_groups).order_by('id')

    if date:
        date = datetime.datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")

    else:
        return HttpResponseRedirect('/')

    for group in user_groups:
            for author in User.objects.filter(groups__name=group):
                match_authors_list.append(author)

    set_date = convert_date(date)

    task_date = date

    all_records = Record.objects.filter(author__in=match_authors_list).order_by('-created_date')

    search_query = records.filter(report_date=date)

    notes = Notes.objects.order_by('-created_date')
    comments = Comments.objects.all()

    shifts_dates = shifts_match()

    selected_department = request.GET.get('d')

    if selected_department:
        multirole = False
        try:
            groups_authors_list = Group.objects.filter(department__exact=selected_department).distinct(). \
            exclude(name__in=admin_groups).order_by('id')
        except:
            multirole = True


    user_agent = request.META['HTTP_USER_AGENT']

    if 'Mobile' in user_agent:
        device = 'mobile'
    else:
        device = 'pc'

    scheduled_dates_query = ScheduledTasks.objects.filter(departments__in=user_departments).distinct()

    scheduled_dates_dict = create_scheduled_tasks_dict(scheduled_dates_query)

    objectives = Objectives.objects.filter(departments__in=user_departments).distinct().order_by('-created_date')

    objectives_sliced = objectives[:5]

    objectives_full = False

    if len(objectives) > 5:
        objectives_full = True

    if request.user.has_perm('journal.change_record'):
        user_is_admin = True
    else:
        user_is_admin = False



    context = {'search_query': search_query, 'comments': comments, 'roles': roles, 'current_user': current_user, 'notes': notes,
               'multirole': multirole, 'group_list': user_groups, 'author_list': match_authors_list,
               'set_date': set_date, 'user_departments': user_departments, 'groups_authors_list': groups_authors_list,
               'user_departments_list': user_departments_list, 'all_records': all_records,
               'shifts_dates': json.dumps(shifts_dates), 'device': device, 'selected_department': selected_department,
               'scheduled_dates_dict': json.dumps(scheduled_dates_dict), 'task_date': task_date,
               'objectives_full': objectives_full, 'objectives': objectives, 'objectives_sliced': objectives_sliced,
               'user_is_admin': user_is_admin}

    user_agent = request.META['HTTP_USER_AGENT']

    if 'Mobile' in user_agent:
        return render(request, 'search_result.html', context)

    return render(request, 'search_result.html', context)


def sort_by_group(request, group_id):

    shifts_dates = shifts_match()


    admin_groups = detect_admin_groups()

    multirole = False

    roles = str(get_roles(request))
    user_groups = request.user.groups.all()

    selected_group = Group.objects.get(id=group_id)

    user_departments_list = []

    for group in user_groups:

        deps = Department.objects.filter(groups=group)

        for dep_objects in deps:
            user_departments_list.append(dep_objects.name)

    current_user = request.user.username
    match_authors_list = []

    user_departments = Department.objects.filter(groups=selected_group)

    for dep in user_departments:
        for group in Group.objects.filter(department=dep):
            for author in User.objects.filter(groups__name=group):
                match_authors_list.append(author)


    records = Record.objects.filter(author__in=match_authors_list).order_by('-created_date')

    notes = Notes.objects.filter(author__in=match_authors_list)

    comments = Comments.objects.all().order_by('-created')

    groups_authors_list = Group.objects.filter(department__in=user_departments).distinct(). \
        exclude(name__in=admin_groups).order_by('id')


    all_records = Record.objects.filter(author__in=match_authors_list).order_by('-created_date')

    single_group = Group.objects.get(id=group_id)
    single_group_authors = User.objects.filter(groups__name=single_group)
    search_query = records.filter(author__in=single_group_authors).order_by('-created_date')

    comments = Comments.objects.all()

    user_agent = request.META['HTTP_USER_AGENT']

    if 'Mobile' in user_agent:
        device = 'mobile'
    else:
        device = 'pc'

    if request.user.has_perm('journal.change_record'):
        user_is_admin = True
    else:
        user_is_admin = False

    task_date = str(datetime.date.today())

    scheduled_dates_query = ScheduledTasks.objects.filter(departments__in=user_departments).distinct()

    scheduled_dates_dict = create_scheduled_tasks_dict(scheduled_dates_query)

    objectives = Objectives.objects.filter(departments__in=user_departments).order_by('-created_date')


    context = {'search_query': search_query, 'comments': comments, 'roles': roles, 'current_user': current_user, 'notes': notes,
               'multirole': multirole, 'group_list': user_groups, 'author_list': match_authors_list,
               'user_departments': user_departments, 'groups_authors_list': groups_authors_list,
               'user_departments_list': user_departments_list, 'all_records': all_records,
               'shifts_dates': json.dumps(shifts_dates), 'device': device, 'task_date': task_date,
               'scheduled_dates_dict': json.dumps(scheduled_dates_dict), 'objectives':objectives,
               'user_is_admin': user_is_admin}

    return render(request, 'search_result.html', context)


def find_by_author(request, author_id):

    multirole = False

    if request.user.groups.all().count() > 1:
        multirole = True

    group_list = Group.objects.all()

    current_group = request.GET.get('group')

    current_group_name = 'Отдел:'

    role = get_role(request)

    roles = str(get_roles(request))

    date = request.GET.get('date')

    author = request.GET.get('author')

    tag = request.GET.get('tag')

    user_groups = request.user.groups.all()

    author_list = User.objects.filter(groups__name=role)

    match_authors_list = []
    for group in user_groups:
        for author in User.objects.filter(groups__name=group):
            match_authors_list.append(author)

    all_records = Record.objects.filter(author__in=match_authors_list).order_by('-created_date')

    search_query = Record.objects.filter(author_id=author_id).order_by('-created_date')

    comments = Comments.objects.all()

    user_agent = request.META['HTTP_USER_AGENT']

    if 'Mobile' in user_agent:
        device = 'mobile'
    else:
        device = 'pc'



    context = {'search_query': search_query,  'role': role, "author_list": author_list,
               "author": author, "all_records": all_records, 'multirole': multirole, 'roles': roles,
               'current_group': current_group, 'group_list': group_list, 'current_group_name': current_group_name,
               'comments': comments, 'device': device}

    return render(request, 'search_result.html', context)


def find_by_text(request, *args, **kwargs):

    admin_groups = detect_admin_groups()

    multirole = False

    user_groups = request.user.groups.all()

    input_text = request.GET.get('q')

    user_departments_list = []

    for group in user_groups:

        deps = Department.objects.filter(groups=group)

        for dep_objects in deps:
            user_departments_list.append(dep_objects.name)

    if len(user_departments_list) > 1:
        multirole = True
    current_user = request.user.username
    match_authors_list = []

    user_departments = Department.objects.filter(groups__in=user_groups)

    for dep in user_departments:
        for group in Group.objects.filter(department=dep):
            for author in User.objects.filter(groups__name=group):
                match_authors_list.append(author)

    records = Record.objects.filter(author__in=match_authors_list).order_by('-created_date')

    search_query = records.filter(text__icontains=input_text).order_by('-created_date')

    all_records = records

    comments = Comments.objects.all().order_by('-created')

    groups_authors_list = Group.objects.filter(department__in=user_departments).distinct(). \
        exclude(name__in=admin_groups).order_by('id')

    shifts_dates = shifts_match()

    user_departments = Department.objects.filter(groups__in=user_groups)

    user_agent = request.META['HTTP_USER_AGENT']

    if 'Mobile' in user_agent:
        device = 'mobile'
    else:
        device = 'pc'

    selected_department = request.GET.get('d')

    if selected_department:
        multirole = False
        try:
            groups_authors_list = Group.objects.filter(department__exact=selected_department).distinct(). \
                exclude(name__in=admin_groups).order_by('id')
        except:
            multirole = True

    task_date = str(datetime.date.today())

    scheduled_dates_query = ScheduledTasks.objects.filter(departments__in=user_departments).distinct()

    scheduled_dates_dict = create_scheduled_tasks_dict(scheduled_dates_query)

    objectives = Objectives.objects.filter(departments__in=user_departments).distinct().order_by('-created_date')

    objectives_sliced = objectives[:5]

    objectives_full = False

    if len(objectives) > 5:
        objectives_full = True

    if request.user.has_perm('journal.change_record'):
        user_is_admin = True
    else:
        user_is_admin = False

    context = {'comments': comments, 'current_user': current_user, 'multirole': multirole,
               'group_list': user_groups, 'author_list': match_authors_list, 'search_query': search_query,
               'all_records': all_records, 'shifts_dates': json.dumps(shifts_dates), 'task_date': task_date,
               'groups_authors_list': groups_authors_list, 'device': device, 'user_departments': user_departments,
               'selected_department': selected_department, 'scheduled_dates_dict': json.dumps(scheduled_dates_dict),
               'objectives': objectives, 'objectives_full': objectives_full, 'objectives_sliced': objectives_sliced,
               'user_is_admin': user_is_admin }

    return render(request, 'search_result.html', context)


def sort_by_department(request, department_id):

    shifts_dates = shifts_match()

    admin_groups = detect_admin_groups()

    author_groups_list = Group.objects.filter(department=department_id)

    selected_department = department_id

    selected_dep = Department.objects.get(id=selected_department)

    authors_list = User.objects.filter(groups__in=author_groups_list)

    records = Record.objects.filter(author__in=authors_list)

    user_groups = request.user.groups.all()

    current_user = request.user.username

    roles = str(get_roles(request))

    user_departments_list = []

    match_authors_list = []

    multirole = False

    if len(user_departments_list) > 1:
        multirole = True

    user_departments = Department.objects.filter(groups__in=user_groups)

    for dep in user_departments:
        for group in Group.objects.filter(department=dep):
            for author in User.objects.filter(groups__name=group):
                match_authors_list.append(author)

    for group in user_groups:

        deps = Department.objects.filter(groups=group)

        for dep_objects in deps:
            user_departments_list.append(dep_objects.name)

    groups_authors_list = Group.objects.filter(department=selected_department).distinct(). \
        exclude(name__in=admin_groups)

    comments = Comments.objects.all().order_by('-created')

    user_agent = request.META['HTTP_USER_AGENT']

    if 'Mobile' in user_agent:
        device = 'mobile'
    else:
        device = 'pc'

    task_date = str(datetime.date.today())

    scheduled_dates_query = ScheduledTasks.objects.filter(departments__in=user_departments).distinct()

    scheduled_dates_dict = create_scheduled_tasks_dict(scheduled_dates_query)

    objectives = Objectives.objects.filter(departments=selected_dep).distinct().order_by('-created_date')

    if request.user.has_perm('journal.change_record'):
        user_is_admin = True
    else:
        user_is_admin = False

    context = {'all_records': records, 'comments': comments, 'groups_authors_list': groups_authors_list,
               'current_user': current_user, 'roles': roles, 'user_departments': user_departments,
               'user_departments_list': user_departments_list, 'shifts_dates': json.dumps(shifts_dates),
               'device': device, 'selected_department': selected_department, 'multirole': multirole,
               'scheduled_dates_dict': json.dumps(scheduled_dates_dict), 'objectives': objectives,
               'task_date': task_date, 'user_is_admin': user_is_admin}

    return render(request, 'search_result.html', context)


def by_date_view(request):

    shifts_dates = shifts_match()

    context = {'shifts_dates': shifts_dates}

    return render(request, 'mobile_by_date.html', context)


def by_group_view(request):
    admin_groups = detect_admin_groups()

    multirole = False

    roles = str(get_roles(request))
    user_groups = request.user.groups.all()

    user_departments_list = []

    for group in user_groups:

        deps = Department.objects.filter(groups=group)

        for dep_objects in deps:
            user_departments_list.append(dep_objects.name)

    if len(user_departments_list) > 1:
        multirole = True
    current_user = request.user
    match_authors_list = []

    user_departments = Department.objects.filter(groups__in=user_groups)

    for dep in user_departments:
        for group in Group.objects.filter(department=dep):
            for author in User.objects.filter(groups__name=group):
                match_authors_list.append(author)
    groups_authors_list = Group.objects.filter(department__in=user_departments).distinct(). \
        exclude(name__in=admin_groups)

    user_agent = request.META['HTTP_USER_AGENT']


    context = {'groups_authors_list': groups_authors_list, 'current_user': current_user, 'multirole': multirole,
               'roles': roles, 'user_departments': user_departments}

    return render(request, 'mobile_by_group.html', context)


def create_shift_dates(start_date):

    shift_dates = []

    end_date = datetime.date(2024, 6, 15)

    delta = datetime.timedelta(days=4)

    while start_date <= end_date:
        shift_dates.append(str(start_date))

        start_date += delta
    return shift_dates


def check_dates_in_shifts(shift_dates, shift_name):

    start_check_date = datetime.date(2020, 6, 15)

    end_check_date = datetime.date(2024, 6, 15)

    shift_dates_dict = {}

    delta = datetime.timedelta(days=1)

    counter = 0

    while start_check_date <= end_check_date:

        if str(start_check_date) in shift_dates:
            shift_dates_dict.update({str(start_check_date): shift_name})
        start_check_date += delta
        counter += 1

    return shift_dates_dict


def shifts_match():
    shift_1_dates = create_shift_dates(datetime.date(2020, 6, 6))
    shift_2_dates = create_shift_dates(datetime.date(2020, 6, 7))
    shift_3_dates = create_shift_dates(datetime.date(2020, 6, 8))
    shift_4_dates = create_shift_dates(datetime.date(2020, 6, 9))

    match_dates_shift1 = check_dates_in_shifts(shift_1_dates, 'shift_1_dates')
    match_dates_shift2 = check_dates_in_shifts(shift_2_dates, 'shift_2_dates')
    match_dates_shift3 = check_dates_in_shifts(shift_3_dates, 'shift_3_dates')
    match_dates_shift4 = check_dates_in_shifts(shift_4_dates, 'shift_4_dates')

    match_dates_shift1.update(match_dates_shift2)
    match_dates_shift1.update(match_dates_shift3)
    match_dates_shift1.update(match_dates_shift4)

    all_shifts_match = match_dates_shift1

    return all_shifts_match


def add_objective(request):

    objective_name = request.GET.get('new_objective_name')

    departments_id_list = request.GET.getlist('department')

    if len(departments_id_list) == 0:

        user_groups = Group.objects.filter(user=request.user)

        departments = Department.objects.filter(groups__in=user_groups)

    else:
        departments = Department.objects.filter(id__in=departments_id_list)

    """department_to_create = Department.objects.get(id=departments_id_list[0])"""

    author = request.user

    created_date = timezone.now()

    for dep in departments:

        if Objectives.objects.filter(departments=dep).count() < 5:
            new_objective = Objectives.objects.create(author=author, created_date=created_date, name=objective_name)

            if Objectives.objects.filter(name=objective_name).count() > 1:

                new_objective.delete()
                created_objective = Objectives.objects.get(name=objective_name)
                created_objective.departments.add(dep)
            else:

                new_objective.departments.add(dep)
                new_objective.save()
        else:
            messages.warning(request, "Задание не было создано - превышено количество заданий для отдела: "+str(dep))
            return HttpResponseRedirect('/')

    return HttpResponseRedirect('/')


def add_status(request, objective_id):

    objective = Objectives.objects.get(id=objective_id)

    status_text = request.GET.get('input_text')

    status = ObjectivesStatus.objects.create(author_id=request.user.id, objective_id=objective)
    status.created = timezone.now()
    status.status = status_text
    status.save()

    return HttpResponseRedirect('/')


def finalize_objective(request, objective_id):

    objective = Objectives.objects.get(id=objective_id)

    objective_done = ObjectivesDone.objects.create(author_id=request.user.id)
    objective_done.name = str(objective.name)
    objective_done.created = timezone.now()
    objective_done_reports = ''

    departments = Department.objects.filter(objectives=objective)

    all_objective_reports = ObjectivesStatus.objects.filter(objective_id=objective_id)

    for report in all_objective_reports:
        objective_done_reports = objective_done_reports+'\n'+(str(report.created))[:19]+' '+str(report.author) + \
                                 ':''     ' + str(report.status)

    objective_done.reports = objective_done_reports

    objective_done.departments.set(departments)

    objective_done.save()

    Objectives.objects.get(id=objective_id).delete()

    return HttpResponseRedirect('/')


def create_scheduled_tasks_dict(queryset):

    all_tasks_dictionary = {}

    for task in queryset:
        task_dict = clean_task_format(task)
        for key, value in task_dict.items():
            if key in all_tasks_dictionary:
                all_tasks_dictionary[key] = f'- {all_tasks_dictionary.get(key)}\n - {task_dict.get(key)}'
            else:
                all_tasks_dictionary[key] = task_dict.get(key)

    return all_tasks_dictionary


def scheduled_tasks_dict(queryset):
    dictionary = {}


def clean_task_format(task):

    task_dict = {}

    for date in task.date_list.split(','):
        date = date.replace('[', '')
        date = date.replace(']', '')
        date = date.replace("'", "")
        date = date.replace(" ", "")
        task_dict[date] = task.text

    return task_dict


def prepare_note(request):
    try:
        note = Notes.objects.get(author_id=request.user.id)


    except:
        note = Notes.objects.create(author=request.user)

        note.created_date = timezone.now()
        note.save()



    return note


def new_edit_note(request):

    note = Notes.objects.get(author_id=request.user.id)

    text = request.GET.get("new_report")

    note.message = text

    note.save()

    return HttpResponse(status=204)


def publish_notes_to_records():
    all_notes = Notes.objects.all()
    for note in all_notes:
        if (len(note.message) > 5) and (note.status == 'initial'):
            author = note.author
            created_date = note.created_date
            full_text = note.message
            record = Record.objects.create(author=author, created_date=created_date, text=full_text)
            note.status = 'published'
            note.to_record = record
            note.save()


def update_record_from_note():
    published_notes = Notes.objects.filter(status='published')
    for note in published_notes:
        record = Record.objects.get(notes=note)
        record.text = note.message
        note.status = 'updated'
        record.save()
        note.save()



def finalize_note():
    updated_notes = Notes.objects.filter(status='updated')
    for note in updated_notes:
        note.to_record = None
    updated_notes.delete()


def send_email(*args, **kwargs):

    """send_mail('Тема тестового письма', 'Текст тестового письма', from_email='gekk0dw@gmail.com',
              recipient_list=['e.epov@360tv.ru'], fail_silently=False, auth_user='gekk0dw@gmail.com',
              auth_password='Frq93AdfsJVjHjTA')"""

    updated_notes = Notes.objects.filter(status='updated')
    for note in updated_notes:
        record = Record.objects.create(notes=note, author=note.author)
        record.text = note.message

        date = (datetime.datetime.strptime(str(record.created_date.date()), "%Y-%m-%d").strftime("%d.%m.%Y"))

        department = Department.objects.filter(groups__in=Group.objects.filter(user=record.author))

        group = Group.objects.get(user=record.author)

        print('connect to smtp...')

        send_mail(subject='Отчет за '+date, message=record.text+'\n'+'\n'+'\n'+'С уважением,'+'\n'+
                    record.author.first_name+'\n'+record.author.last_name+'\n'+'Отдел: '+str(department[0].name)+'\n'+
                    'Смена: '+str(group),
                  from_email='Journal360@mosobltv.ru', recipient_list=['litvinenkostudy@gmail.com', 'o.litvinenko@360tv.ru'],
                  fail_silently=False, auth_user='Journal360', auth_password='Ju123456')

    return HttpResponseRedirect('/')


def send_email_with_smptlib(*args, **kwargs):
    updated_notes = Notes.objects.filter(status='updated')
    for note in updated_notes:

        record = Record.objects.create(notes=note, author=note.author)

        record.text = note.message

        date = (datetime.datetime.strptime(str(record.created_date.date()), "%Y-%m-%d").strftime("%d.%m.%Y"))

        department = Department.objects.filter(groups__in=Group.objects.filter(user=record.author))

        group = Group.objects.get(user=record.author)

        """hostname = "smtp.office365.com"
        username = "journal360@outlook.com"
        password = "3P4cnprkBzWxB9zK"""""

        hostname = "email.mosobltv.ru"
        username = "Journal360"
        password = "Ju123456"

        msg = EmailMessage()
        msg.set_content(record.text+'\n'+'\n'+'\n'+'С уважением,'+'\n'+record.author.first_name+'\n'+
                        record.author.last_name+'\n'+'Отдел: '+str(department[0].name)+'\n'+'Смена: '+str(group))

        msg['Subject'] = 'Отчет за '+date
        msg['From'] = ('Journal360@360tv.ru')
        msg['To'] = ["o.litvinenko@360tv.ru", 'i.akhtyrskiy@360tv.ru']

        server = smtplib.SMTP(hostname, 25)
        print('smtp port match')
        server.ehlo()  # Secure the connection
        print('starttls connected')
        server.login(username, password)
        print('authorization succeed')
        server.send_message(msg)
        print('message sent')
        server.quit()
        print('quit connection')

    return HttpResponseRedirect('/')


def custom_format_search_filters(ldap_fields):
    # Add in simple filters.
    ldap_fields["memberOf"] = "ou=mathematicians,dc=example,dc=com"
    # Call the base format callable.
    search_filters = format_search_filters(ldap_fields)
    # Advanced: apply custom LDAP filter logic.
    search_filters.append("(|(memberOf=GroupA)(memberOf=GroupB))")
    # All done!
    return search_filters
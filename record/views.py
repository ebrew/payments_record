from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout as logout_check, login as login_checks
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from payment_record.settings import EMAIL_HOST_USER
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from record.emails import send_pending_feedback_email
from django.contrib.auth.signals import user_logged_in, user_logged_out
import socket, os, random, string
from django.core.files.base import File
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from wsgiref.util import FileWrapper
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q
import math
# import numpy as np
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from reportlab.lib.pagesizes import A4, letter, A6
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Table, TableStyle, Paragraph, Frame, Spacer, Image, \
    SimpleDocTemplate
from reportlab.lib.enums import TA_RIGHT, TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas
from io import StringIO, BytesIO
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from django.core.files.base import File
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

User = get_user_model()


def get_path():
    cdir = os.path.expanduser("~")
    path = os.path.join(cdir, "Downloads/")
    return path.replace(os.sep, '/')


internet_issues = (OSError, socket.gaierror)


def is_connected():
    try:
        socket.create_connection(("1.1.1.1", 53))
        return True
    except internet_issues:
        return False


# inactive when so many access rights, hard coding is required
def record_user_logged_in(sender, user, request, **kwargs):
    Event.objects.create(user_id=user.pk, action='Logged in to Payment Records')


def record_user_logged_out(sender, user, request, **kwargs):
    Event.objects.create(user_id=user.pk, action='Logged out from Payment Records')


user_logged_in.connect(record_user_logged_in)
user_logged_out.connect(record_user_logged_out)


def home(request):
    if request.user.is_authenticated:
        return render(request, 'home.html')
    return render(request, 'users/login.html')


def about(request):
    return render(request, 'about.html')


@login_required(login_url='login')
def logout(request):
    u = request.user
    logout_check(request)
    messages.success(request, 'Logged out successfully {}! '
                              'Thanks for spending some quality time with the Web site today.'.format(u))
    return render(request, 'users/login.html')


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid:
            email = request.POST['email']
            password = request.POST['password']

            try:
                existing_user = User.objects.get(email=email)
                inactive_user = User.objects.filter(email=email, is_active=False)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                existing_user = None
            if existing_user is None:
                print(existing_user)
                messages.warning(request, 'Your account does not exist! Fill the below form to register.')
                return render(request, 'users/register.html')
            elif inactive_user:
                current_site = get_current_site(request)
                subject = "USER ACCOUNT ACTIVATION - PAYMENT RECORD MANAGEMENT SYSTEM"
                recipients = [email]
                message = render_to_string('users/account_activation_email.html', {
                    'user': inactive_user.first(),
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(inactive_user.first().pk)),
                    'token': account_activation_token.make_token(inactive_user.first()),
                })
                if is_connected():
                    send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)
                    messages.success(request, f'Your account already exist! Check your mail and verify your email '
                                              f'provided for login')
                    return render(request, 'users/login.html')
                messages.success(request, f'Your account already exist! Check your internet connection and login')
                return render(request, 'users/login.html')
            elif existing_user:
                user = authenticate(email=email, password=password)
                if user is not None:
                    if user.is_active:
                        login_checks(request, user)
                        # record_user_logged_in()
                        # inactive when so many access rights, hard coding is required
                        return redirect('home')
                else:
                    messages.warning(request, 'Invalid credentials')
                    return render(request, 'users/login.html')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid:
            pn = request.POST['phone_number']
            p1 = request.POST['password1']
            p2 = request.POST['password2']
            email = request.POST['email']
            fn = request.POST['first_name']
            mn = request.POST['middle_name']
            ln = request.POST['last_name']
            inactive_user = User.objects.filter(email=email, is_active=False)
            phone_chosen = User.objects.filter(phone_number='+233' + pn[-9:])

            try:
                valid_phone = (len(pn) == 10) or (len(pn) == 13)
                valid_password = (p1 == p2)
                existing_user = User.objects.get(email=email, is_active=True)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                existing_user = None

            if (not valid_phone) and (not valid_password):
                messages.warning(request, 'Invalid Phone Number and Password mismatch!')
                return render(request, 'users/register.html')
            elif not valid_phone:
                messages.warning(request, 'Invalid Phone Number!')
                return render(request, 'users/register.html')
            elif not valid_password:
                messages.warning(request, 'Password mismatch!')
                return render(request, 'users/register.html')
            elif inactive_user:
                current_site = get_current_site(request)
                subject = "USER ACCOUNT ACTIVATION - PAYMENT RECORD MANAGEMENT SYSTEM"
                recipients = [email]
                message = render_to_string('users/account_activation_email.html', {
                    'user': inactive_user.first(),
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(inactive_user.first().pk)),
                    'token': account_activation_token.make_token(inactive_user.first()),
                })
                if is_connected():
                    send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)
                    messages.success(request, f'Your account already exist! Check your mail and verify your email '
                                              f'provided for login')
                    return render(request, 'users/login.html')
                messages.success(request, f'Your account already exist! Check your internet connection and login')
                return render(request, 'users/login.html')
            elif existing_user:
                messages.warning(request, 'Your account already exist! Login here.')
                return render(request, 'users/login.html')
            elif phone_chosen:
                messages.warning(request, 'Phone number provided has already been chosen!')
                return render(request, 'users/register.html')
            else:
                phone = '+233' + pn[-9:]
                user = User.objects.create_user(email=email, first_name=fn, middle_name=mn, last_name=ln,
                                                phone_number=phone, password=p1)
                user.is_active = False
                user.save()
                Event.objects.create(user_id=user.pk, action='Created an account, awaiting activation')
                current_site = get_current_site(request)
                subject = "USER ACCOUNT ACTIVATION - PAYMENT RECORD MANAGEMENT SYSTEM"
                recipients = [email]
                message = render_to_string('users/account_activation_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                if is_connected():
                    send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)
                    messages.success(request, f'Your account has been created! Check your mail and verify your email '
                                              f'provided for login')
                    return render(request, 'users/login.html')
                messages.success(request, f'Your account has been created! Check your internet connection and login')
                return render(request, 'users/login.html')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


# User being activated via email
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_confirmed = True
        user.save()
        current_site = get_current_site(request)
        subject = "Account Activation"
        message = render_to_string('users/account_activated_email.html', {
            'user': user,
            # 'current_user': request.user,
            'domain': current_site.domain,
        })
        recipient = [user.email]

        Event.objects.create(user=request.user, action='Activated his/her account')
        if is_connected():
            send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False)
            messages.info(request, "Account activated successfully! Kindly login here")
            return redirect('login')
        else:
            messages.warning(request, f'Failed to activate; Connect to internet and use the link to activate')
            return redirect('login')

    else:
        messages.warning(request, f'Sorry, Invalid token! The link has expired')
        return render(request, 'users/login.html')


# User account
@login_required(login_url='login')
def user_account_options(request):
    return render(request, "users/user_account.html")


# Update profile image
@login_required
def update_profile_image(request):
    user = User.objects.get(id=request.user.pk)
    if request.method == 'POST':
        form = ImageProfileForm(request.POST, request.FILES)
        if form.is_valid():
            image = request.FILES['image']
            if user.image:
                user.image.delete()
                user.image.save(f'{image.name[:3]}-{user.first_name}-{user.pk}', image)
                Event.objects.create(user_id=request.user.pk, action='Updated profile picture')
            else:
                user.image.save(f'{user.first_name}-{user.pk}', image)
                Event.objects.create(user_id=request.user.pk, action='Updated profile picture')
            return redirect('user_profile')
    else:
        form = ImageProfileForm()
    return render(request, 'users/update_profile_image.html', {'form': form})


# Update profile
@login_required
def update_user_profile(request):
    current_user = request.user
    user = User.objects.get(id=current_user.pk)
    form = UpdateProfileForm(instance=user)

    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            Event.objects.create(user_id=current_user.pk, action='Updated profile')
            # messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
    return render(request, 'users/update_profile.html', {'form': form})


@login_required
def user_profile(request):
    current_user = request.user
    return render(request, 'users/user_profile.html', {'user': current_user})


# History
@login_required(login_url='login')
def event(request):
    history = Event.objects.filter(user=request.user.pk).order_by('-created_at')
    title, start_date, end_date = '', '', ''
    if request.method == 'POST':
        start_date = request.POST['date']
        end_date = request.POST["date2"]
        title = f'From {start_date} to {end_date}'
        history = Event.objects.filter(user=request.user.pk, created_at__date__range=(start_date, end_date)).order_by(
            '-created_at')
    return render(request, "users/event.html",
                  {'events': history, 'title': title, 'date2': end_date, 'date': start_date})


# # User accounts that have been activated
# @login_required(login_url='login')
# def activate_user(request, pk):
#     current_user = request.user
#     user = User.objects.get(id=pk)
#
#     if request.method == 'POST':
#         privilege = request.POST['privilege'].upper()
#
#         current_site = get_current_site(request)
#         subject = "MARGINS ID SYSTEM"
#         message = render_to_string('users/account_activated_email.html', {
#             'user': user,
#             'privilege': privilege,
#             'current_user': current_user,
#             'domain': current_site.domain,
#         })
#         recipient = [user.email]
#
#         if privilege == 'NONE':
#             messages.warning(request,
#                              "{}'s user account was not activated since no privilege level was selected!".format(user))
#             return redirect('inactive_users')
#         elif privilege == 'ADMIN':
#             user.is_active = True
#             user.is_staff = True
#             user.profile.email_confirmed = True
#             user.save()
#             Event.objects.create(user_id=current_user.pk,
#                                  action="Activated {}'s user account as {} user".format(user, privilege))
#             if is_connected():
#                 send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False)
#                 messages.success(request, "{}'s user account has been activated as {} successfully! {} will be "
#                                           "notified by mail.".format(user, privilege, user))
#                 return redirect('inactive_users')
#             else:
#                 messages.success(request,
#                                  "{}'s user account has been activated as {} successfully!".format(user, privilege))
#                 messages.warning(request, f'Email notification failed; You are not connected to internet!')
#                 return redirect('inactive_users')
#
#         elif privilege == 'TECHNICIAN':
#             user.is_active = True
#             user.profile.email_confirmed = True
#             user.save()
#             Event.objects.create(user_id=current_user.pk,
#                                  action="Activated {}'s user account as {} user".format(user, privilege))
#             if is_connected():
#                 send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False)
#                 messages.success(request, "{}'s user account has been activated as {} successfully! {} will be "
#                                           "notified by mail.".format(user, privilege, user))
#                 return redirect('inactive_users')
#             else:
#                 messages.success(request,
#                                  "{}'s user account has been activated as {} successfully!".format(user, privilege))
#                 messages.warning(request, f'Email notification failed; You are not connected to internet!')
#                 return redirect('inactive_users')
#         elif privilege == 'ACCOUNTANT':
#             user.is_active = True
#             user.is_accountant = True
#             user.profile.email_confirmed = True
#             user.save()
#             Event.objects.create(user_id=current_user.pk,
#                                  action="Activated {}'s user account as {} user".format(user, privilege))
#             if is_connected():
#                 send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False)
#                 messages.success(request, "{}'s user account has been activated as {} successfully! {} will be "
#                                           "notified by mail.".format(user, privilege, user))
#                 return redirect('inactive_users')
#             else:
#                 messages.success(request,
#                                  "{}'s user account has been activated as {} successfully!".format(user, privilege))
#                 messages.warning(request, f'Email notification failed; You are not connected to internet!')
#                 return redirect('inactive_users')
#
#         else:
#             user.is_active = True
#             user.is_pro = True
#             user.profile.email_confirmed = True
#             user.save()
#             Event.objects.create(user_id=current_user.pk,
#                                  action="Activated {}'s user account as {} user".format(user, privilege))
#             if is_connected():
#                 send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False)
#                 messages.success(request, "{}'s user account has been activated as {} successfully! {} will be "
#                                           "notified by mail.".format(user, privilege, user))
#                 return redirect('inactive_users')
#             else:
#                 messages.success(request,
#                                  "{}'s user account has been activated as {} successfully!".format(user, privilege))
#                 messages.warning(request, f'Email notification failed; You are not connected to internet!')
#                 return redirect('inactive_users')
#     return render(request, 'users/activate_prompt.html', {'item': user})
#
#
# # Give user privilege levels to a user or activate user's account
# # User accounts that require admin activation
# @login_required(login_url='login')
# def inactive_users(request):
#     users = User.objects.filter(is_active=False).order_by('-created_at')
#     return render(request, "users/inactive_users.html", {'users': users})
#
#
# # Remove admin access from a user
# @login_required(login_url='login')
# def deactivate_user(request, pk):
#     current_user = request.user
#     user = User.objects.get(id=pk)
#
#     if request.method == 'POST':
#         user.is_active = False
#         user.is_staff = False
#         user.is_accountant = False
#         user.is_pro = False
#         user.profile.email_confirmed = False
#         user.save()
#         Event.objects.create(user_id=current_user.pk, action="Deactivated {}'s user account".format(user))
#         current_site = get_current_site(request)
#         subject = "MARGINS ID SYSTEM"
#         message = render_to_string('users/account_deactivated_email.html', {
#             'user': user,
#             'current_user': current_user,
#             'domain': current_site.domain,
#         })
#         recipient = [user.email]
#
#         if is_connected():
#             send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False)
#             messages.success(request, '{} user account has been deactivated successfully! {} will be notified by mail.'
#                              .format(user, user))
#             return redirect('active_users')
#         else:
#             messages.success(request, "{}'s user account has been deactivated successfully!".format(user))
#             messages.warning(request, f'Email notification failed; You are not connected to internet!')
#             return redirect('active_users')
#
#     return render(request, 'users/delete_prompt.html', {'item': user})
#
#
# # User being activated via admin email
# def admin_activate(request, uidb64, token):
#     try:
#         uid = force_text(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         user = None
#
#     if user is not None and account_activation_token.check_token(user, token):
#         user.is_active = True
#         user.profile.email_confirmed = True
#         # user.save()
#         current_site = get_current_site(request)
#         subject = "MARGINS ID SYSTEM"
#         message = render_to_string('users/account_activated_email.html', {
#             'user': user,
#             'current_user': request.user,
#             'domain': current_site.domain,
#         })
#         recipient = [user.email]
#
#         if is_connected():
#             send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False)
#             messages.info(request, "{}'s Activation failed!; Link blocked by developer but {} will be notified by mail."
#                           .format(user, user))
#             return redirect('login')
#         else:
#             messages.warning(request, f'Failed to activate; Connect to internet and use the link to activate the user '
#                                       f'or log in to the system and to activate the user!')
#             return redirect('login')
#
#     else:
#         messages.warning(request, f'Sorry, Invalid token! The link has already been used by different Admin')
#         return render(request, 'users/login.html')
#
#
# # User report
# @login_required(login_url='login')
# def user_report(request):
#     plist, title = [], 'All Technicians Report'
#     qrst = User.objects.filter(is_active=True).order_by('first_name')
#     for name in qrst:
#         if not (name.is_pro or name.is_accountant):
#             plist.append(name)
#
#     for i in plist:
#         r = 0
#         schedules = Schedule.objects.filter(user=i.id, cancelled=False).all()
#         cancel = Schedule.objects.filter(cancelled=True, requested_by=i.email).all()
#         fixed = Schedule.objects.filter(cancelled=False, fixed_by__icontains=str(i.id)).all()
#         part_reqs = PartStock.objects.filter(user=f'{i.first_name} {i.middle_name} {i.last_name}',
#                                              action_status='Approved')
#         for k in part_reqs:
#             r += k.request
#         i.username = len(schedules)  # total scheduled
#         i.email = len(fixed)  # total fixed
#         i.password = len(cancel)  # total cancelled
#         i.is_active = r  # total parts requested
#     start_date = 'All'
#     end_date = 'All'
#     if request.method == 'POST':
#         start_date = request.POST['date']
#         end_date = request.POST["date2"]
#         title = f'Technicians Report from {start_date} to {end_date}'
#
#         for i in plist:
#             r = 0
#             schedules = Schedule.objects.filter(cancelled=False, user=i.id, created_at__gte=start_date,
#                                                 created_at__lte=end_date)
#             cancel = Schedule.objects.filter(date_cancelled__gte=start_date, date_cancelled__lte=end_date,
#                                              cancelled=True, requested_by=i.email)
#             fixed = Schedule.objects.filter(cancelled=False, date_repaired__gte=start_date,
#                                             date_repaired__lte=end_date, fixed_by__icontains=str(i.id))
#             part_reqs = PartStock.objects.filter(user=f'{i.first_name} {i.middle_name} {i.last_name}',
#                                                  action_status='Approved', created_at__gte=start_date,
#                                                  created_at__lte=end_date)
#             for k in part_reqs:
#                 r += k.request
#             i.username = len(schedules)  # total scheduled
#             i.email = len(fixed)  # total fixed
#             i.password = len(cancel)  # total cancelled
#             i.is_active = r  # total parts requested
#     return render(request, "users/user_report.html",
#                   {'parts': plist, 'title': title, 'date2': end_date, 'date': start_date})
#
#
# # User report breakdown
# @login_required(login_url='login')
# def user_report_details(request, pk, type, period, date, date2):
#     user = User.objects.get(pk=pk)
#     r = 0
#     schedules = Schedule.objects.filter(user=pk, cancelled=False).all()
#     cancel = Schedule.objects.filter(cancelled=True, requested_by=user.email).all()
#     fixed = Schedule.objects.filter(cancelled=False, fixed_by__icontains=str(user.id)).all()
#     part_reqs = PartStock.objects.filter(user=f'{user.first_name} {user.middle_name} {user.last_name}',
#                                          action_status='Approved').exclude(request=0)
#     title = f'Printers {type} by {user}'
#
#     if type == 'scheduled' and period[0] == 'A':
#         data = schedules
#     elif type == 'scheduled':
#         data = Schedule.objects.filter(cancelled=False, user=user.id, created_at__gte=date, created_at__lte=date2)
#     elif type == 'fixed' and period[0] == 'A':
#         data = fixed
#     elif type == 'fixed':
#         data = Schedule.objects.filter(cancelled=False, fixed_by__icontains=str(user.id), date_repaired__gte=date,
#                                        date_repaired__lte=date2)
#     elif type == 'cancelled' and period[0] == 'A':
#         data = cancel
#     elif type == 'cancelled':
#         title = f'Approved {type} contribution by {user}'
#         data = Schedule.objects.filter(cancelled=True, requested_by=user.email, date_cancelled__gte=date,
#                                        date_cancelled__lte=date2)
#     else:
#         title = f'Part requested by {user}'
#         data = part_reqs
#     json_data = {'schedules': data, 'period': period, 'pk': pk, 'type': type, 'title': title, 'date': date,
#                  'date2': date2}
#     return render(request, 'member/user_report_details.html', json_data)
#
#
# # Part report breakdown
# @login_required(login_url='login')
# def user_part_report_details(request, pk, name, period, date, date2):
#     user = User.objects.get(pk=pk)
#     title = f'All {name} serial numbers used by {user}'
#     schedules, board, ph, others = [], [], [], []
#     if period[0] == 'A':
#         fixed = Schedule.objects.filter(cancelled=False, repair_status='Fixed', fixed_by__icontains=str(pk)). \
#             order_by('-date_repaired')
#         for i in fixed:
#             if name == 'Print head' and i.new_head_barcode:
#                 ph.append(i)
#             elif name == 'Board' and i.new_board:
#                 board.append(i)
#         if name == 'Board':
#             schedules = board
#         elif name == 'Print head':
#             schedules = ph
#         else:
#             schedules = others
#     else:
#         title = f'{name} serial numbers used by {user} from {date} to {date2}'
#         fixed = Schedule.objects.filter(cancelled=False, fixed_by__icontains=str(pk), date_repaired__gte=date,
#                                         date_repaired__lte=date2)
#         for i in fixed:
#             if name == 'Print head' and i.new_head_barcode:
#                 ph.append(i)
#             elif name == 'Board' and i.new_board:
#                 board.append(i)
#         if name == 'Board':
#             schedules = board
#         elif name == 'Print head':
#             schedules = ph
#         else:
#             schedules = others
#
#     json_data = {'schedules': schedules, 'name': name, 'title': title}
#     return render(request, 'member/user_part_report_details.html', json_data)


# Contribution managements options
@login_required(login_url='login')
def contribution_options(request):
    return render(request, "contribution/contribution_options.html")


# Add a new contribution organisation to our list of contribution
@login_required(login_url='login')
def add_contribution(request):
    if request.method == 'POST':

        form = AddContributionForm(request.POST, request.FILES)
        if form.is_valid():
            current_user = request.user
            image = request.FILES['image']
            name = request.POST['name']
            desc = request.POST['description']

            new = Organisation.objects.create(user=current_user, name=name, type='Contribution', description=desc)
            if image:
                new.image.save(f'{image.name[:5]}-{name[:5]}-{new.pk}', image)
            user = User.objects.get(id=current_user.pk)
            user.profile.organisation_count += 1
            user.save()
            Event.objects.create(user=current_user, action='Added {} as a new contribution organisation'.format(name))
            messages.success(request, 'Organisation {} added successfully!'.format(name))
            return redirect('add_contribution_organisation')
    else:
        form = AddContributionForm()
    return render(request, 'contribution/add_contribution_org.html', {'form': form})


# user organisations under contribution group
@login_required(login_url='login')
def user_contribution_organisations(request):
    more = False
    orgs = Organisation.objects.filter(user=request.user).order_by('-created_at')
    size = len(orgs)
    if size > 6:
        more = True
    return render(request, 'contribution/user_contribution_organisations.html', {'orgs': orgs, 'more': more})


# Update profile
def update_user_contribution_organisations(request, pk):
    current_user = request.user
    org = Organisation.objects.get(id=pk)
    form = UpdateOrganisationForm(instance=org)

    if request.method == 'POST':
        form = UpdateOrganisationForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            Event.objects.create(user=current_user, action='Updated {} Organisation'.format(org.name))
            if not Organisation.objects.get(id=pk).image:
                messages.warning(request, f'Image is required for Organisation {org.name}!')
                return redirect('update_user_contribution_organisations', pk=pk)
            return redirect('user_contribution_organisations')
    return render(request, 'contribution/update_organisation.html', {'form': form})


# View organisational members with their total contributions
@login_required(login_url='login')
def organisational_members(request, pk):
    org = Organisation.objects.get(id=pk)
    members = Member.objects.filter(user=request.user, organisation=org).order_by('first_name')
    title, start_date, end_date = 'Contribution updates to date', '', ''
    for i in members:
        i.image = 0
        i.created_at = i.created_at.strftime('%d %b, %Y')
        pays = Payment.objects.filter(user=request.user, organisation=org, member=i)
        for j in pays:
            i.image += j.amount

    if request.method == 'POST':
        start_date = request.POST['date']
        end_date = request.POST["date2"]
        title = f'Contribution updates from {start_date} to {end_date}'
        for i in members:
            i.image = 0
            pays = Payment.objects.filter(user=request.user, organisation=org, member=i,
                                          created_at__date__range=(start_date, end_date))
            for j in pays:
                i.image += j.amount
    data = {
        'org': org,
        'members': members,
        'title': title,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, "contribution/organisational_members.html", data)


# View org members WILL EDIT
@login_required(login_url='login')
def organisational_members1(request, pk):
    org = Organisation.objects.get(id=pk)
    members = Member.objects.filter(user=request.user, organisation=org).order_by('-updated_at')
    title, start_date, end_date = '', '', ''
    if request.method == 'POST':
        start_date = request.POST['date']
        end_date = request.POST["date2"]
        title = f'Contribution updates from {start_date} to {end_date}'
        members = Member.objects.filter(user=request.user, organisation=org,
                                        created_at__date__range=(start_date, end_date)).order_by('-updated_at')
    data = {
        'org': org,
        'members': members,
        'title': title,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, "contribution/organisational_members.html", data)


# Organizational options
@login_required(login_url='login')
def organisational_menu(request, pk):
    org = Organisation.objects.get(id=pk)
    return render(request, "contribution/organisational_menu.html", {'org': org})


# Add a new member to a contribution organisation
def add_organisational_member(request, pk):
    if request.method == 'POST':
        form = AddOrganisationalMemberForm(request.POST)
        if form.is_valid:
            pn = request.POST['phone_number']
            email = request.POST['email']
            fn = request.POST['first_name']
            mn = request.POST['middle_name']
            ln = request.POST['last_name']

            phone_chosen = Member.objects.filter(phone_number='+233' + pn[-9:])
            org = Organisation.objects.get(id=pk)

            try:
                valid_phone = (len(pn) == 10) or (len(pn) == 13)
                existing_user = Member.objects.get(email=email, organisation=org)
            except (TypeError, ValueError, OverflowError, Member.DoesNotExist):
                existing_user = None

            if not valid_phone:
                messages.warning(request, 'Invalid Phone Number!')
                return redirect('add_organisational_member', pk)
            elif existing_user:
                messages.warning(request, 'Member already added!')
                return redirect('add_organisational_member', pk)
            elif phone_chosen:
                messages.warning(request, 'Phone number provided has already been chosen!')
                return redirect('add_organisational_member', pk)
            else:
                current_user = User.objects.get(id=request.user.pk)
                phone = '+233' + pn[-9:]
                member = Member.objects.create(user=request.user, organisation=org, email=email, first_name=fn,
                                               middle_name=mn, last_name=ln, phone_number=phone)

                Event.objects.create(user_id=current_user.pk, action=f'Added {fn} {mn} {ln} as a new member to {org}')
                current_site = get_current_site(request)
                subject = f"MEMBER ACCOUNT CREATION - {str(org).upper()}"
                recipients = [email]
                message = render_to_string('contribution/add_member_email_prompt.html', {
                    'user': current_user,
                    'member': member,
                    'domain': current_site.domain,
                })
                send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)
                messages.success(request, f'Member added successfully! Email notification sent to {member}')
                # return redirect('organisational_menu', pk)
                return redirect('add_organisational_member', pk)
    else:
        form = AddOrganisationalMemberForm()
    return render(request, 'contribution/add_organisational_member.html', {'form': form, 'org': pk})


# # Add a new member to a contribution organisation
# def add_contribution_member(request):
#     def get_form_kwargs(self):
#         """ Passes the request object to the form class.
#          This is necessary to only display organisations that belong to a given user"""
#
#         kwargs = super(add_contribution_member(get_form_kwargs(self)), self)
#         # kwargs = super(add_contribution_member(get_form_kwargs(self)))
#         kwargs['request'] = self.request
#         return kwargs
#
#     if request.method == 'POST':
#
#         form = AddContributionMemberForm(request.POST, request.FILES)
#         if form.is_valid():
#             org = request.POST['org']
#             pn = request.POST['phone_number']
#             email = request.POST['email']
#             fn = request.POST['first_name']
#             mn = request.POST['middle_name']
#             ln = request.POST['last_name']
#             phone_chosen = User.objects.filter(phone_number='+233' + pn[-9:])
#             current_user = request.user
#             image = request.FILES['image']
#             desc = request.POST['description']
#
#             # new = Organisation.objects.create(user=current_user, name=name, type='Contribution', description=desc)
#             # if image:
#             #     new.image.save(f'{image.name[:5]}-{name[:5]}-{new.pk}', image)
#             # user = User.objects.get(id=current_user.pk)
#             # user.profile.organisation_count += 1
#             # user.save()
#             # Event.objects.create(user=current_user, action='Added {} as a new contribution organisation'.format(name))
#             # messages.success(request, 'Organisation {} added successfully!'.format(name))
#             return redirect('add_contribution_organisation')
#     else:
#         form = AddContributionMemberForm()
#     return render(request, 'contribution/add_contribution_org.html', {'form': form})

# From list of user organisations
class AddContributionMember(CreateView):
    model = Member
    form_class = AddContributionMemberForm
    template_name = 'contribution/add_contribution_org.html'
    success_url = reverse_lazy('contribution_options')
    success_message = "Check your inbox for the verification email"

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display organisations that belong to a given user"""

        kwargs = super(AddContributionMember, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class SubdomainDetailView(FormView):
    form_class = SubdomainForm
    template_name = 'contribution/add_contribution_org.html'
    success_url = reverse_lazy('contribution_options')
    success_message = "Good, will get back to you."

    def get_form_kwargs(self, form_class=SubdomainForm):
        s = dict(slug=self.kwargs['slug'])
        print(s)
        return s

    # roll


# delete member from member list
@login_required(login_url='login')
def delete_member(request, pk):
    item = Member.objects.get(id=pk)
    old_member = item
    current_user = request.user

    if request.method == 'POST':
        item.delete()
        Event.objects.create(user=current_user, action=f"Deleted {old_member.user} from {old_member.organisation}")
        subject = "ACCOUNT DELETED/REMOVAL FROM ORGANISATION"
        message = render_to_string('member/member_removal_email.html', {
            'user': current_user,
            'member': old_member,
        })
        recipient = [old_member.email]
        send_mail(subject, message, EMAIL_HOST_USER, recipient, fail_silently=False)
        messages.success(request, f'{old_member.user} from {old_member.organisation} deleted successfully!')
        return redirect('organisational_members', old_member.organisation.pk)

    return render(request, 'member/delete_prompt.html', {'item': item})


# Update member details from member list
@login_required(login_url='login')
def update_member(request, pk):
    item = Member.objects.get(id=pk)
    form = UpdateMemberForm(instance=item)
    current_user = request.user

    if request.method == 'POST':
        form = UpdateMemberForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            Event.objects.create(user=current_user, action=f'Updated {item.user} from {item.organisation}')
            messages.success(request, f'{item.user} from {item.organisation} details updated successfully!')
            return redirect('organisational_members', item.organisation.pk)
    return render(request, 'contribution/update_org_member.html', {'form': form, 'org': item.organisation.pk})


# contributional receipt
def receipt(current_user, member, org, payment, current_site):
    date = payment.created_at.strftime('%d %b, %Y')
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.translate(inch, inch)

    # Temp Data for the invoice
    my_prod = {1: ['Hard Disk', 80], 2: ['RAM', 90], 3: ['Monitor', 70],
               4: ['CPU', 55], 5: ['Keyboard', 20], 6: ['Mouse', 10],
               7: ['Mother Board', 50], 8: ['Power Supply', 20],
               9: ['Speaker', 50], 10: ['Microphone', 45]}
    my_sale = {1: 2, 3: 2, 7: 1, 4: 3, 6: 5, 5: 3, 2: 1, 9: 1, 10: 3}
    discount_rate = 10  # 10% discount
    tax_rate = 12  # 12% tax rate
    # logo = ImageReader(org.image)

    # pdf template
    p.setFont('Helvetica', 14)
    p.setStrokeColorRGB(0.1, 0.8, 0.1)
    p.setFillColorRGB(0, 0, 1)

    p.drawImage(ImageReader(org.image), 0.1 * inch, 9.2 * inch, 0.8 * inch, 0.8 * inch)
    # p.drawImage('static/images/default.jpg', 0.1 * inch, 1 * inch, 0.8 * inch, 0.8 * inch)

    p.drawString(0, 9 * inch, f"Contributor : {str(member)}")
    p.drawString(0, 8.7 * inch, f"Account : {str(member.email)}")
    p.setFillColorRGB(0, 0, 0)
    p.line(0, 8.6 * inch, 6.8 * inch, 8.6 * inch)
    p.drawString(5.6 * inch, 9.3 * inch, date)
    p.setFillColorRGB(1, 0, 0)
    p.setFont('Times-Bold', 40)
    p.drawString(3 * inch, 9.6 * inch, str(org))
    p.setFillColorRGB(1, 0, 0)
    p.setFont('Times-Bold', 30)
    p.drawString(4.3 * inch, 8.7 * inch, 'RECEIPT')
    # p.rotate(45)  # rotate by 45 degrees
    p.setFillColorCMYK(0, 0, 0, 0, 0.08)  # font colour CYAN, MAGENTA, YELLOW and BLACK
    p.setFont('Helvetica', 140)
    # p.rotate(-45)
    p.setFillColorRGB(0, 0, 0)
    p.setFont('Times-Roman', 15)
    p.drawString(0.5 * inch, 8.3 * inch, 'MEMBER NAME')
    p.drawString(4 * inch, 8.3 * inch, 'AMOUNT')
    p.drawString(5 * inch, 8.3 * inch, 'DATE ')
    p.drawString(6.1 * inch, 8.3 * inch, 'TOTAL')
    p.setStrokeColorCMYK(0, 0, 0, 1)  # vertical line colour
    p.line(0, 8.2 * inch, 6.8 * inch, 8.2 * inch)
    p.line(3.9 * inch, 8.2 * inch, 3.9 * inch, 2.7 * inch)  # first vertical line
    p.line(4.9 * inch, 8.2 * inch, 4.9 * inch, 2.7 * inch)  # second vertical line
    p.line(6.1 * inch, 8.2 * inch, 6.1 * inch, 2.7 * inch)  # third vertical line
    p.line(0.01 * inch, 2.7 * inch, 6.8 * inch, 2.7 * inch)  # horizontal line total

    p.drawString(1 * inch, 1.8 * inch, "Discount: N/A")
    p.drawString(1 * inch, 1.2 * inch, "Tax: N/A")
    p.setFont("Times-Roman", 22)
    p.drawString(2 * inch, 0.8 * inch, f"Total: GHS {str(payment.amount)}")
    p.setFont("Times-Roman", 22)
    # p.drawString(5.6 * inch, -0.1 * inch, str(current_site))
    p.setStrokeColorRGB(0.1, 0.8, 0.1)  # Bottom line colour
    p.line(0, -0.7 * inch, 6.8 * inch, -0.7 * inch)
    p.setFont("Helvetica", 13)
    p.setFillColorRGB(1, 0, 0)  # font colour
    p.drawString(6.5, -0.1 * inch, f' Website: {str(current_site)}')

    # Populate temp data
    p.setFillColorRGB(0, 0, 1)
    p.setFont("Helvetica", 15)
    row_gap = 0.6
    line_y = 7.9

    # first data
    p.drawString(0.1 * inch, line_y * inch, str(member))  # product name
    p.drawRightString(4.45 * inch, line_y * inch, str(payment.amount))  # product price
    p.drawString(4.9 * inch, line_y * inch, str(payment.created_at.strftime("%d/%m/%Y")))  # date
    p.drawRightString(6.7 * inch, line_y * inch, str(payment.amount))  # sub total

    # Total contributions
    line_y -= 2 * row_gap  # vertical line
    p.drawString(0.1 * inch, line_y * inch, 'Total No. of contributions')  # product name
    p.drawRightString(4.45 * inch, line_y * inch, '')  # product price
    p.drawString(4.9 * inch, line_y * inch, '')  # date
    p.drawRightString(6.7 * inch, line_y * inch, 'N/A')  # sub total

    p.showPage()
    p.save()
    receipt_pdf = buffer.getvalue()
    buffer.close()

    subject = f"MEMBER CONTRIBUTIONAL UPDATE - {str(org).upper()}"
    recipients = [member.email]
    message = render_to_string('payments/contributional_receipt_email.html', {
        'user': current_user,
        'member': member,
        'domain': current_site,
    })
    email = EmailMessage(subject, message, EMAIL_HOST_USER, recipients)
    email.attach('contribution_receipt.pdf', receipt_pdf, 'application/pdf')
    email.send()


# Make payment to a contribution organisation from member list
def direct_payment(request, orgpk, mempk):
    current_user = User.objects.get(id=request.user.pk)
    org = Organisation.objects.get(id=orgpk)
    current_site = get_current_site(request)
    member = Member.objects.get(id=mempk)
    if request.method == 'POST':
        form = DirectContributionalPaymentsForm(request.POST)
        if form.is_valid:
            amount = request.POST['amount']

            payment = Payment.objects.create(user=current_user, organisation=org, member=member, amount=amount)
            # Receipt design here
            receipt(current_user, member, org, payment, current_site.domain)
            Event.objects.create(user=current_user, action=f'Updated {member}"s contribution of GHS {amount} to {org}')
            subject = f"MEMBER CONTRIBUTION - {str(org).upper()}"
            recipients = [member.email]
            message = render_to_string('payments/payment_receipt_email.html', {
                'user': current_user,
                'member': member,
                'domain': current_site.domain,
            })
            # send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)
            messages.success(request, f'Payment of GHS {amount} made successfully to {member}"s account')
            return redirect('organisational_members', orgpk)
    else:
        form = DirectContributionalPaymentsForm()
    return render(request, 'payments/direct_payment.html', {'form': form, 'org': orgpk, 'mem': member})


# Make payment to a contribution organisation
def make_contributional_payment(request, pk):
    current_user = User.objects.get(id=request.user.pk)
    org = Organisation.objects.get(id=pk)
    if request.method == 'POST':
        form = MakeContributionalPaymentsForm(request.POST)
        if form.is_valid:
            member = Member.objects.get(id=request.POST['member'])
            amount = request.POST['amount']

            # Receipt design here

            # payment = Payment.objects.create(user=current_user, organisation=org, member=member, amount=amount)
            # Event.objects.create(user=current_user, action=f'Updated {member}"s contribution of GHS {amount} to {org}')
            subject = f"MEMBER CONTRIBUTION - {str(org).upper()}"
            recipients = [member.email]
            current_site = get_current_site(request)
            message = render_to_string('payments/payment_receipt_email.html', {
                'user': current_user,
                'member': member,
                'domain': current_site.domain,
            })
            # send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)
            # messages.success(request, f'Payment of GHS {amount} made successfully to {member}"s account')
            messages.warning(request, "Pls this functionality is under development, kindly use the Organisational "
                                      "members option to make payment.")
            return redirect('make_contributional_payment', pk)
    else:
        form = MakeContributionalPaymentsForm()
    return render(request, 'payments/make_payments.html', {'form': form, 'org': pk})

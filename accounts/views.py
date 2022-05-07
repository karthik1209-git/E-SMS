from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from .forms import NewUSerForm
from django.core.mail import EmailMessage
from django.conf import settings

def sendmail(request):
    subject="Y19 PFSD Django Sessions"
    email="papatlakarthikchaithanya@gmail.com" #to whom you want to send
    email=EmailMessage(subject,"All The Best",to=[email])  #to will take list of email IDs
    email.send()
    return HttpResponse("Success")

def signup_view(request):
    if request.method == 'POST':
        form = NewUSerForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main:home')
    else:
        form = NewUSerForm()
    return render(request, 'accounts/signup.html', { 'form': form })

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return redirect('main:home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', { 'form': form })

def logout_view(request):
    if request.method == 'POST':
            logout(request)
            return redirect('/')
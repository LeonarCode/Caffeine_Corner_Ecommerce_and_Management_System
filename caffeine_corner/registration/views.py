from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth import logout
from django.contrib import messages

# Create your views here.
def signin(request):
    return render(request, 'authentication/signin.html',)

def signup(request):
    return render(request, 'authentication/signup.html',)

def email_signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created successfully. You can now log in.')
            return redirect('/authentication/signin/')
        else:
            messages.error(request, 'Something went wrong. Please try again.')
    else:
        form = RegistrationForm()
    

    return render(request, 'authentication/emailSignup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('/shop/home/',)



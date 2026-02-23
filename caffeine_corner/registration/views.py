from django.shortcuts import render

# Create your views here.
def signin(request):
    return render(request, 'authentication/signin.html')

def signup(request):
    return render(request, 'authentication/signup.html')

def email_signup(request):
    return render(request, 'authentication/emailSignup.html')

def email_signin(request):
    return render(request, 'authentication/emailSignin.html')
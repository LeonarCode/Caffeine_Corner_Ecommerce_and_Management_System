from django.shortcuts import render
from .forms import RegistrationForm

# Create your views here.
def signin(request):
    return render(request, 'authentication/signin.html')

def signup(request):
    return render(request, 'authentication/signup.html')

def email_signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            print("SUCCESS ✅")
        else:
            print(form.errors)
    else:
        form = RegistrationForm()

    return render(request, 'authentication/emailSignup.html', {'form': form})



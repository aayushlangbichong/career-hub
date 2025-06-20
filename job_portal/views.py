from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as lg, logout as lgout
from django.contrib.auth.models import User

def index(request):
    return render(request,"index.html")


def login(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    ctx = {}

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")


        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "auth/login.html", ctx)

        ctx = {
            "username": username,
            "password": password
        }

        user = authenticate(request, username=username, password=password)
        if user is not None:
            lg(request, user)
            return redirect('index')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "auth/login.html", ctx)

    return render(request, "auth/login.html", ctx)



def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    ctx = {}

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Field validation
        if not all([first_name, last_name, username , password, confirm_password]):
            messages.error(request, "All fields are required.")
            return render(request, "auth/register.html", ctx)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "auth/register.html", ctx)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "auth/register.html", ctx)

     
        # Create the user
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.save()

        messages.success(request, "Account created successfully! Please login.")
        return redirect("login")

    return render(request, "auth/register.html", ctx)

def logout(request):
    lgout(request)
    return redirect('index')
    


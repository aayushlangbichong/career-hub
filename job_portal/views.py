from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as lg, logout as lgout
from django.contrib.auth.models import User
from .models import JobSeekerProfile, CompanyProfile,JobPost

def get_role(user):
    try:
        profile = JobSeekerProfile.objects.get(user=user)
        return "job_seeker"
    except JobSeekerProfile.DoesNotExist:
        try:
            profile = CompanyProfile.objects.get(user=user)
            return "employer"
        except CompanyProfile.DoesNotExist:
            return None

def index(request):
    jobs= JobPost.objects.all()
    ctx = {
        "jobs": jobs
    }

    return render(request,"index.html",ctx)

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

        user = authenticate(request, username=username, password=password)
        if user is not None:
            lg(request, user)
            role = get_role(user)

            if role == "job_seeker":
                profile, created = JobSeekerProfile.objects.get_or_create(user=user)
                if profile.resume and profile.skills:
                    return redirect('index')
                else:
                    return redirect('/onboarding/?role=job_seeker')

            elif role == "employer":
                profile, created = CompanyProfile.objects.get_or_create(user=user)
                if profile.company_name and profile.company_description:
                    return redirect('dashboard')
                else:
                    return redirect('/onboarding/?role=employer')

            return redirect('index')  
        else:
            messages.error(request, "Invalid username or password.")
            ctx = {"username": username}
            return render(request, "auth/login.html", ctx)

    return render(request, "auth/login.html", ctx)


def onboarding(request):
    role = request.GET.get('role')
    ctx = {
        "role": role
    }
    if role not in ["job_seeker", "employer"]:
        messages.error(request, "Invalid role specified.")
        return redirect('index')
    
    if request.method == "POST":
        if role == "job_seeker":
            profile = JobSeekerProfile.objects.get(user=request.user)
            profile.resume = request.FILES.get("resume")
            profile.skills = request.POST.get("skills")
            profile.save()
            messages.success(request, "Job Seeker profile updated successfully!")
            return redirect('index')
        elif role == "employer":
            profile = CompanyProfile.objects.get(user=request.user)
            profile.company_name = request.POST.get("company_name")
            profile.company_description = request.POST.get("company_description")
            profile.logo = request.FILES.get("logo")
            profile.save()
            messages.success(request, "Company profile updated successfully!")
            return redirect('index')
    return render(request, "auth/onboarding.html",ctx)

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    role = get_role(request.user)
    if role != "employer":
        messages.error(request, "Access denied.")
        return redirect('index')

    company_profile = CompanyProfile.objects.get(user=request.user)
    job_posts = JobPost.objects.filter(company=company_profile)

    ctx = {
        "company_profile": company_profile,
        "job_posts": job_posts,
        "role": role
    }
    return render(request, "company/dashboard.html", ctx)

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
        role=request.POST.get("user_type")

        if not all([first_name, last_name, username , password, confirm_password,role]):
            messages.error(request, "All fields are required.")
            return render(request, "auth/register.html", ctx)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "auth/register.html", ctx)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "auth/register.html", ctx)

     
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        if role == "job_seeker":
            profile = JobSeekerProfile(user=user)
            profile.save()
        else:
            profile = CompanyProfile(user=user)
            profile.save()
        user.save()

        messages.success(request, "Account created successfully! Please login.")
        return redirect("login")

    return render(request, "auth/register.html", ctx)

def logout(request):
    lgout(request)
    return redirect('index')

def applied(request):
    return render(request, "applied.html")

def jobs(request):
    return render(request, "jobs.html")

def post_jobs(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        location = request.POST.get("location")
        salary = request.POST.get("salary")
        working_hours = request.POST.get("working_hours")

        if not all([title, description, location, salary, working_hours]):
            messages.error(request, "All fields are required.")
            return render(request, "post_jobs.html")

        company_profile = CompanyProfile.objects.get(user=request.user)
        job_post = JobPost(
            company=company_profile,
            title=title,
            description=description,
            location=location,
            salary=salary,
            working_hours=working_hours
        )
        job_post.save()
        messages.success(request, "Job posted successfully!")

    return render(request, "post_jobs.html")
    
def user_profile(request):
    if not request.user.is_authenticated:
        return redirect("login")

    user = request.user
    ctx = {}

    if request.method == "POST":
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.save()

        try:
            profile = JobSeekerProfile.objects.get(user=user)
            profile.skills = request.POST.get("skills")
            if request.FILES.get("resume"):
                profile.resume = request.FILES["resume"]
            profile.save()
            ctx["role"] = "job_seeker"
        except JobSeekerProfile.DoesNotExist:
            try:
                profile = CompanyProfile.objects.get(user=user)
                profile.company_name = request.POST.get("company_name")
                profile.company_description = request.POST.get("company_description")
                profile.save()
                ctx["role"] = "employer"
            except CompanyProfile.DoesNotExist:
                messages.error(request, "Profile not found.")
                return redirect("index")

        messages.success(request, "Profile updated successfully!")
        return redirect("user_profile")

    try:
        profile = JobSeekerProfile.objects.get(user=user)
        ctx = {"profile": profile, "role": "job_seeker"}
    except JobSeekerProfile.DoesNotExist:
        try:
            profile = CompanyProfile.objects.get(user=user)
            ctx = {"profile": profile, "role": "employer"}
        except CompanyProfile.DoesNotExist:
            ctx = {"profile": None, "role": None}

    return render(request, "user_profile.html", ctx)
 


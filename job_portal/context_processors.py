from .models import JobSeekerProfile, CompanyProfile

def user_role(request):
    role = None

    if request.user.is_authenticated:
        if JobSeekerProfile.objects.filter(user=request.user).exists():
            role = 'jobseeker'
        elif CompanyProfile.objects.filter(user=request.user).exists():
            role = 'employer'
        else:
            role = 'user'  

    return {
        'user_role': role
    }

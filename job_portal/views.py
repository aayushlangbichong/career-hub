from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as lg, logout as lgout
from django.contrib.auth.models import User
from .models import JobSeekerProfile, CompanyProfile,JobPost
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from .models import Application
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, IntegerField
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .utils.resume_parser import extract_text_from_resume



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
    jobs= JobPost.objects.all()[:4]
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
            return redirect('dashboard')
    return render(request, "auth/onboarding.html",ctx)

def dashboard(request):
    company_profile = request.user.company_profile  
    employer_jobs = JobPost.objects.filter(company=company_profile)
    recent_applications = Application.objects.filter(
        job__in=employer_jobs
    ).select_related("applicant__user", "job").order_by("-applied_at")[:10]

    return render(request, "company/dashboard.html", {
        "recent_applications": recent_applications
    })

def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    ctx = {}

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email","").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        role = request.POST.get("user_type", "")

       
        if not all([first_name, last_name,email, username, password, confirm_password, role]):
            messages.error(request, "All fields are required.")
            return render(request, "auth/register.html", ctx)

        
        if len(username) < 4 or len(username) > 20:
            messages.error(request, "Username must be between 4 and 20 characters.")
            return render(request, "auth/register.html", ctx)

       
        if len(password) < 8 or len(password) > 20:
            messages.error(request, "Password must be between 8 and 20 characters.")
            return render(request, "auth/register.html", ctx)

       
        if not re.search(r"[A-Z]", password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return render(request, "auth/register.html", ctx)
        if not re.search(r"[a-z]", password):
            messages.error(request, "Password must contain at least one lowercase letter.")
            return render(request, "auth/register.html", ctx)
        if not re.search(r"\d", password):
            messages.error(request, "Password must contain at least one number.")
            return render(request, "auth/register.html", ctx)
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            messages.error(request, "Password must contain at least one special character (!@#$%^&* etc.).")
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
            JobSeekerProfile.objects.create(user=user)
        else:
            CompanyProfile.objects.create(user=user)

        messages.success(request, "Account created successfully! Please login.")
        return redirect("login")

    return render(request, "auth/register.html", ctx)

def logout(request):
    lgout(request)
    return redirect('index')

def applied(request):
    return render(request, "applied.html")

def jobs(request):
    jobs= JobPost.objects.all()
    ctx = {
        "jobs": jobs
    }
    return render(request, "jobs.html",ctx)

def post_jobs(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        work_type = request.POST.get("work_type")
        salary = request.POST.get("salary")
        working_hours = request.POST.get("working_hours")

        if not all([title, description, work_type, salary, working_hours]):
            messages.error(request, "All fields are required.")
            return render(request, "company/post_jobs.html")

        company_profile = CompanyProfile.objects.get(user=request.user)
        job_post = JobPost(
            company=company_profile,
            title=title,
            description=description,
            work_type=work_type,
            salary=salary,
            working_hours=working_hours
        )
        job_post.save()
        messages.success(request, "Job posted successfully!")

    return render(request, "company/post_jobs.html")
    
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


def view_user_profile(request, user_id, job_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, "company/view_user_profile.html", {
        "user": user,
        "job_id": job_id,
    })  
 
def company_profile(request):
    if not request.user.is_authenticated:
        return redirect("login")

    user = request.user
    try:
        company_profile = CompanyProfile.objects.get(user=user)
    except CompanyProfile.DoesNotExist:
        messages.error(request, "Company profile not found.")
        return redirect("dashboard")

    if request.method == "POST":
        company_profile.company_name = request.POST.get("company_name")
        company_profile.company_description = request.POST.get("company_description")
        company_profile.company_location=request.POST.get("company_location")
        if request.FILES.get("logo"):
            company_profile.logo = request.FILES["logo"]
        company_profile.save()
        messages.success(request, "Company profile updated successfully!")
        return redirect("company_profile")

    ctx = {
        "company_profile": company_profile
    }
    return render(request, "company/company_profile.html", ctx)

def job_details(request, job_id):
    job = get_object_or_404(JobPost, id=job_id)
    has_applied = False

    if request.user.is_authenticated:
        try:
            profile = JobSeekerProfile.objects.get(user=request.user)
            has_applied = Application.objects.filter(job=job, applicant=profile).exists()
        except JobSeekerProfile.DoesNotExist:
            pass

    return render(request, 'job_details.html', {
        'job': job,
        'has_applied': has_applied
    })
    

def search_jobs(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', '')

    # Base Query
    jobs = JobPost.objects.all()

    # Apply search
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company__company_name__icontains=query)
        )

    # Apply Sorting
    if sort == "salary":
        jobs = jobs.order_by("-salary")  # Highest → Lowest

    elif sort == "work_type":
        jobs = jobs.order_by(
            Case(
                When(work_type="Remote", then=0),
                When(work_type="On-site", then=1),
                default=2,
                output_field=IntegerField()
            )
        )

    # Return partial HTML
    html = render_to_string('partials/search_results.html', {'jobs': jobs})
    return HttpResponse(html)

def manage_jobs(request):
    if not request.user.is_authenticated:
        return redirect('login')

    company_profile = CompanyProfile.objects.get(user=request.user)
    job_posts = JobPost.objects.filter(company=company_profile)
    role = get_role(request.user)
   

    ctx = {
        "company_profile": company_profile,
        "job_posts": job_posts,
        "role": role
    }
    return render(request, "company/manage_jobs.html", ctx)

def apply_job(request, job_id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to apply.")
        return redirect('login')

  
    job = get_object_or_404(JobPost, id=job_id)

    try:
        
        profile = JobSeekerProfile.objects.get(user=request.user)
    except JobSeekerProfile.DoesNotExist:
        messages.error(request, "You must complete your job seeker profile to apply.")
        return redirect('job_details', job_id=job_id)

    
    if Application.objects.filter(job=job, applicant=profile).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect('job_details', job_id=job_id)

    if request.method == "POST":
        message = request.POST.get("message")

        
        Application.objects.create(
            job=job,
            applicant=profile,
            message=message
        )

        messages.success(request, "Application submitted successfully.")
        return redirect('applied')

    return redirect('job_details', job_id=job_id)


def applied(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = JobSeekerProfile.objects.get(user=request.user)
    except JobSeekerProfile.DoesNotExist:
        messages.error(request, "Job seeker profile not found.")
        return redirect('index')

    applications = Application.objects.filter(applicant=profile).select_related('job', 'job__company')

    return render(request, "applied.html", {"applications": applications})


def job_list(request):
    if not request.user.is_authenticated:
        return redirect("login")

    role = get_role(request.user)
    if role != "employer":
        messages.error(request, "Access denied.")
        return redirect("index")

    company = CompanyProfile.objects.get(user=request.user)
    jobs = JobPost.objects.filter(company=company)

    context = {
        "role": role,
        "jobs": jobs,
        
    }
    return render(request, "company/job_list.html", context)

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, company__user=request.user)

    if request.method == "POST":
        job.title = request.POST.get("title")
        job.description = request.POST.get("description")
        job.work_type = request.POST.get("work_type")
        job.salary = request.POST.get("salary")
        job.working_hours = request.POST.get("working_hours")
        job.save()
        messages.success(request, "Job updated successfully!")
        return redirect("manage_jobs")

    return render(request, "company/edit_job.html", {"job": job})


def delete_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, company__user=request.user)
    job.delete()
    messages.success(request, "Job deleted successfully!")
    return redirect('manage_jobs')

def update_application_status(request, app_id, new_status):
    if not request.user.is_authenticated:
        return redirect('login')

    application = get_object_or_404(Application, id=app_id, job__company__user=request.user)
    if new_status in ['approved', 'rejected']:
        application.status = new_status
        application.save()
        messages.success(request, f"Application marked as {new_status.capitalize()}.")
    return redirect('view_job_applicants', job_id=application.job.id)

def clean_text(text):
    if not text:
        return ""
    text = text.lower()  # lowercase
    text = re.sub(r'\d+', '', text)  # remove numbers
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # remove extra spaces
    return text


# Enhanced aggressive matching algorithm for higher scores

def enhanced_text_preprocessing(text):
    """Enhanced text preprocessing with better cleaning and normalization"""
    if not text:
        return ""
    
    text = text.lower()
    
    # More comprehensive technology normalization
    tech_mappings = {
        # JavaScript variations
        r'\bjs\b': 'javascript',
        r'\breactjs\b': 'react',
        r'\bnodejs\b': 'node javascript',
        r'\bnode\.js\b': 'node javascript',
        r'\bvuejs\b': 'vue javascript',
        r'\bangularjs\b': 'angular javascript',
        
        # Database variations
        r'\bmongodb\b': 'mongo database nosql',
        r'\bmysql\b': 'sql database relational',
        r'\bpostgresql\b': 'postgres sql database relational',
        r'\bpostgres\b': 'postgresql sql database',
        
        # Programming languages
        r'\bc\+\+': 'cpp programming',
        r'\bc#': 'csharp dotnet programming',
        r'\b\.net\b': 'dotnet csharp microsoft',
        
        # Cloud and DevOps
        r'\baws\b': 'amazon web services cloud',
        r'\bgcp\b': 'google cloud platform',
        r'\bazure\b': 'microsoft cloud',
        r'\bdevops\b': 'development operations deployment',
        
        # Web technologies
        r'\bhtml5\b': 'html web markup',
        r'\bcss3\b': 'css styling web',
        r'\brestful\b': 'rest api web services',
        r'\bgraphql\b': 'graph query language api',
        
        # Frameworks and tools
        r'\bbootstrap\b': 'css framework responsive',
        r'\btailwind\b': 'css framework utility',
        r'\bwebpack\b': 'bundler build tool',
        r'\bvite\b': 'build tool bundler',
        
        # Methodologies
        r'\bai/ml\b': 'artificial intelligence machine learning',
        r'\bui/ux\b': 'user interface user experience design',
        r'\bfull.?stack\b': 'fullstack frontend backend',
        r'\bfront.?end\b': 'frontend user interface',
        r'\bback.?end\b': 'backend server side',
        
        # Testing
        r'\btdd\b': 'test driven development testing',
        r'\bbdd\b': 'behavior driven development testing',
    }
    
    for pattern, replacement in tech_mappings.items():
        text = re.sub(pattern, replacement, text)
    
    # Remove punctuation but preserve important technical characters
    text = re.sub(r'[^\w\s+#.-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_comprehensive_skills(text):
    """Extract skills with weighted importance"""
    if not text:
        return {}
    
    # Define skill categories with importance weights
    skill_categories = {
        'core_programming': {
            'weight': 3.0,
            'pattern': r'\b(react|javascript|typescript|python|java|node|angular|vue)\b'
        },
        'web_technologies': {
            'weight': 2.5,
            'pattern': r'\b(html|css|sass|less|bootstrap|tailwind|responsive)\b'
        },
        'databases': {
            'weight': 2.0,
            'pattern': r'\b(mysql|postgresql|mongodb|redis|elasticsearch|sql|database|nosql)\b'
        },
        'tools_frameworks': {
            'weight': 2.0,
            'pattern': r'\b(webpack|vite|jest|cypress|docker|git|github|gitlab)\b'
        },
        'cloud_devops': {
            'weight': 2.0,
            'pattern': r'\b(aws|azure|gcp|docker|kubernetes|jenkins|devops|ci/cd)\b'
        },
        'api_architecture': {
            'weight': 2.5,
            'pattern': r'\b(rest|restful|graphql|api|microservices|json)\b'
        },
        'state_management': {
            'weight': 2.5,
            'pattern': r'\b(redux|context|state|vuex|mobx)\b'
        },
        'testing': {
            'weight': 1.8,
            'pattern': r'\b(jest|cypress|testing|unit|integration|tdd|test)\b'
        },
        'methodologies': {
            'weight': 1.5,
            'pattern': r'\b(agile|scrum|kanban|waterfall|methodology)\b'
        },
        'soft_skills': {
            'weight': 1.0,
            'pattern': r'\b(leadership|communication|teamwork|problem.solving|analytical|management)\b'
        }
        
    }
    
    extracted_skills = {}
    text_lower = text.lower()
    
    for category, config in skill_categories.items():
        matches = re.findall(config['pattern'], text_lower)
        if matches:
            extracted_skills[category] = {
                'skills': list(set(matches)),
                'weight': config['weight']
            }
    
    return extracted_skills

def calculate_weighted_skill_match(job_text, resume_text):
    """Calculate skill matching with category weights"""
    job_skills = extract_comprehensive_skills(job_text)
    resume_skills = extract_comprehensive_skills(resume_text)
    
    if not job_skills:
        return 0.0
    
    total_job_weight = 0
    matched_weight = 0
    
    for category, job_data in job_skills.items():
        category_weight = job_data['weight']
        job_category_skills = set(job_data['skills'])
        total_job_weight += category_weight
        
        if category in resume_skills:
            resume_category_skills = set(resume_skills[category]['skills'])
            overlap = job_category_skills.intersection(resume_category_skills)
            
            if overlap:
                match_ratio = len(overlap) / len(job_category_skills)
                matched_weight += category_weight * match_ratio
    
    return matched_weight / total_job_weight if total_job_weight > 0 else 0.0

def calculate_enhanced_similarity(job_text, resume_text):
    """Enhanced similarity calculation with aggressive scoring"""
    
    # Preprocess texts
    job_clean = enhanced_text_preprocessing(job_text)
    resume_clean = enhanced_text_preprocessing(resume_text)
    
    if not job_clean or not resume_clean:
        return 0.0
    
    # 1. TF-IDF Cosine Similarity
    try:
        tfidf = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),  
            max_features=8000,
            sublinear_tf=True,
            min_df=1,
            max_df=0.95
        )
        
        tfidf_matrix = tfidf.fit_transform([job_clean, resume_clean])
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except Exception as e:
        print(f"TF-IDF error: {e}")
        cosine_sim = 0.0
    
    weighted_skill_score = calculate_weighted_skill_match(job_text, resume_text)
    
    job_words = set(job_clean.split())
    resume_words = set(resume_clean.split())
    
    if len(job_words) > 0:
        word_overlap = len(job_words.intersection(resume_words)) / len(job_words)
    else:
        word_overlap = 0.0
    
    base_score = (cosine_sim * 0.3) + (weighted_skill_score * 0.7)
    
    # Apply moderate boosts (toned down from aggressive version)
    if weighted_skill_score >= 0.7:
        final_score = min(base_score * 1.35, 0.95) 
    elif weighted_skill_score >= 0.5:
        final_score = min(base_score * 1.25, 0.90) 
    elif weighted_skill_score >= 0.3:
        final_score = min(base_score * 1.15, 0.85) 
    elif weighted_skill_score >= 0.1:
        final_score = min(base_score * 1.05, 0.75) 
    else:
        final_score = base_score
    
    # Additional boost for high word overlap (reduced)
    if word_overlap >= 0.3:
        final_score = min(final_score * 1.08, 0.95)  # Smaller boost, cap at 95%
    
    # Minimum score boost for any technical content
    if cosine_sim > 0.1 and weighted_skill_score > 0.1:
        final_score = max(final_score, 0.25)  
    
    print(f"Cosine similarity: {cosine_sim:.3f}")
    print(f"Weighted skill score: {weighted_skill_score:.3f}")
    print(f"Word overlap: {word_overlap:.3f}")
    print(f"Base score: {base_score:.3f}")
    print(f"Final score: {final_score:.3f}")
    
    return final_score

@login_required
def view_job_applicants(request, job_id):
    if not request.user.is_authenticated:
        return redirect("login")

    job = get_object_or_404(JobPost, id=job_id, company__user=request.user)
    applications = Application.objects.filter(job=job).select_related("applicant__user")

    scored_apps = []
    for app in applications:
        resume_text = ""

        # Extract resume text
        if app.applicant.resume:
            resume_text = extract_text_from_resume(app.applicant.resume)

        # Append skills field if available
        if app.applicant.skills:
            resume_text += " " + app.applicant.skills

        print(f"\n--- Processing application for {app.applicant.user.username} ---")
        print(f"Job description length: {len(job.description)}")
        print(f"Resume text length: {len(resume_text)}")
        
        # Calculate enhanced similarity
        similarity_score = calculate_enhanced_similarity(job.description, resume_text)
        
        final_percentage = round(similarity_score * 100, 1)
        print(f"Final similarity score: {final_percentage}%")

        scored_apps.append({
            "app": app,
            "score": final_percentage
        })

    # Sort highest to lowest score
    scored_apps.sort(key=lambda x: x["score"], reverse=True)

    return render(request, "company/job_applicant.html", {
        "job": job,
        "applications": scored_apps
    })

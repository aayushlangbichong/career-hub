from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='job_seeker_profile')
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - Job Seeker Profile"

class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True,related_name='company_profile')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)
    company_location=models.TextField(max_length=255,blank=True,null=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    def __str__(self):
        return f"{self.company_name}"
    
class JobPost(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    work_type = models.CharField(max_length=255, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    working_hours=models.CharField(max_length=100, blank=True, null=True)
    posted = models.DateTimeField(auto_now_add=True)
     
    def __str__(self):
        return f"{self.title} at {self.company.company_name}"

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey('JobPost', on_delete=models.CASCADE)
    applicant = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

def __str__(self):
        return f"{self.applicant.user.username} - {self.job.title}"




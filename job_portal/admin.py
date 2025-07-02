from django.contrib import admin
from .models import CompanyProfile,JobSeekerProfile,JobPost

admin.site.register(CompanyProfile)
admin.site.register(JobSeekerProfile)
admin.site.register(JobPost)


from django.contrib import admin
from django.urls import path
from .import views as v
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Auth
    path('login/',v.login,name="login" ),
    path('register/',v.register,name="register" ),
    path('logout/',v.logout,name="logout" ),
    path('onboarding/',v.onboarding,name="onboarding" ),
    
    # Job seeker pages
    path('',v.index,name="index" ),
    path('jobs/', v.jobs, name="jobs"),
    path('applied/', v.applied, name="applied"),
    path('user_profile/', v.user_profile, name="user_profile"),
    path('job_details/<int:job_id>/', v.job_details, name="job_details"),
    path('search/', v.search_jobs, name='search_jobs'),
    path('apply/<int:job_id>/', v.apply_job, name='apply_job'),
    path("applied/", v.applied, name="applied"),


    # Company pages
    path('dashboard/', v.dashboard, name="dashboard"),
    path('post_jobs/', v.post_jobs, name="post_jobs"),
    path('company_profile/', v.company_profile, name="company_profile"),
    path('manage_jobs/', v.manage_jobs, name="manage_jobs"),
    path('job_list/', v.job_list, name="job_list"),
    path('jobs/<int:job_id>/edit/', v.edit_job, name='edit_job'),
    path('jobs/<int:job_id>/delete/', v.delete_job, name='delete_job'),
    path('application/<int:app_id>/status/<str:new_status>/', v.update_application_status, name='update_application_status'),
    path('jobs/<int:job_id>/applicants/', v.view_job_applicants, name="view_job_applicants"),
    path("company/<int:user_id>/<int:job_id>/",v.view_user_profile,name="view_user_profile"),
    

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])



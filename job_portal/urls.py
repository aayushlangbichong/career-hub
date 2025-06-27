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

    # Company pages
    path('dashboard/', v.dashboard, name="dashboard"),
    path('post_jobs/', v.post_jobs, name="post_jobs"),
    path('company_profile/', v.company_profile, name="company_profile"),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])



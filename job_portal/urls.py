from django.contrib import admin
from django.urls import path
from .import views as v
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',v.index,name="index" ),
    path('login/',v.login,name="login" ),
    path('register/',v.register,name="register" ),
    path('logout/',v.logout,name="logout" ),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])



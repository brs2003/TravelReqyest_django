from django.urls import path,include

urlpatterns = [
    path('travel/',include('Travel_App.urls')),
]
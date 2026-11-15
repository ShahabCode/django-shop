
from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/<int:address_id>/default/', views.set_default_address, name='set_default_address'),
    path('otp/', views.otp_request, name='otp_request'),
    path('otp/verify/', views.otp_verify, name='otp_verify'),
]

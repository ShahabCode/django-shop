from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('products/', views.ProductListAPIView.as_view(), name='product_list_api'),
    path('product/<int:pk>/', views.ProductDetailAPIView.as_view(), name='product_detail_api'),
    path('users/', views.UserListAPIView.as_view(), name='user_list_api'),
]
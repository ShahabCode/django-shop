from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    # path('products/', views.ProductListAPIView.as_view(), name='product_list_api'),
    # path('product/<int:pk>/', views.ProductDetailAPIView.as_view(), name='product_detail_api'),
    path('', include(router.urls)),
    path('users/', views.UserListAPIView.as_view(), name='user_list_api'),
    path('register/', views.UserRegistrationAPIView.as_view(), name='register_api'),
]
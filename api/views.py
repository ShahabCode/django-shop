from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from account.models import ShopUser
from shop.models import Product
from .serializers import ProductSerializer, ShopUserSerializer
from rest_framework import generics, permissions
from rest_framework import views

class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class UserListAPIView(views.APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAdminUser]
    def get(self, request, *args, **kwargs):
        users = ShopUser.objects.all()
        serializer = ShopUserSerializer(users, many=True)
        return Response(serializer.data)
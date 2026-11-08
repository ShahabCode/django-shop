from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from account.models import ShopUser
from shop.models import Product
from .serializers import ProductSerializer, ShopUserSerializer, UserRegistrationSerializer
from rest_framework import generics, permissions, viewsets, status
from rest_framework import views
from rest_framework.decorators import action

# class ProductListAPIView(generics.ListAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#
#
# class ProductDetailAPIView(generics.RetrieveAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=False, methods=['GET'])
    def discount_products(self, request):
        min_discount = request.query_params.get('min_discount', 0)
        try:
            min_discount = int(min_discount)
        except ValueError:
            return Response({'error': 'Invalid Value For min_discount'}, status=status.HTTP_400_BAD_REQUEST)
        products = self.queryset.filter(off__gt=min_discount)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class UserListAPIView(views.APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAdminUser]
    def get(self, request, *args, **kwargs):
        users = ShopUser.objects.all()
        serializer = ShopUserSerializer(users, many=True)
        return Response(serializer.data)


class UserRegistrationAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = ShopUser.objects.all()
    serializer_class = UserRegistrationSerializer
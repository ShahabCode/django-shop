from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.http import require_POST
from .models import Category, Product, FavoriteProduct

PRODUCTS_PER_PAGE = 12

@vary_on_headers('X-Requested-With')
def product_list(request, category_slug=None):
    category = None
    products = Product.objects.select_related('category').prefetch_related('images')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(name__icontains=q)

    in_stock = request.GET.get('in_stock', '')
    if in_stock == '1':
        products = products.filter(inventory__gt=0)

    min_price = request.GET.get('min_price', '')
    if min_price.isdigit():
        products = products.filter(new_price__gte=int(min_price))

    max_price = request.GET.get('max_price', '')
    if max_price.isdigit():
        products = products.filter(new_price__lte=int(max_price))


    sort = request.GET.get('sort', 'newest')
    if sort == 'cheapest':
        products = products.order_by('new_price', '-created')
    elif sort == 'expensive':
        products = products.order_by('-new_price', '-created')
    else:
        sort = 'newest'
        products = products.order_by('-created')

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page = paginator.get_page(request.GET.get('page'))

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(request.user.favorites.all().values_list('product_id', flat=True))

    context = {
        'category': category,
        'products': page,
        'sort': sort,
        'q': q,
        'in_stock': in_stock,
        'min_price': min_price,
        'max_price': max_price,
        'favorite_ids': favorite_ids,
    }

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        template = 'shop/_product_results.html'
    else:
        template = 'shop/list.html'

    return render(request, template, context)

def product_detail(request, id, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'features'),
        id=id,
        slug=slug,
    )

    related_products = (
        Product.objects.filter(category=product.category)
        .exclude(id=product.id)
        .select_related('category')
        .prefetch_related('images')[:4]
    )

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(request.user.favorites.all().values_list('product_id', flat=True))

    context = {
        'product': product,
        'related_products': related_products,
        'favorite_ids': favorite_ids,
    }
    return render(request, 'shop/detail.html', context)


@require_POST
def toggle_favorite(request, product_id):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {'success': False, 'error': 'login_required', 'login_url': reverse('account:login')},
            status=401
        )

    product = get_object_or_404(Product, id=product_id)
    favorite, created = FavoriteProduct.objects.get_or_create(product=product, user=user)

    if not created:
        favorite.delete()

    return JsonResponse({
        'success': True,
        'is_favorite': created,
        'count': user.favorites.count(),
    })


@login_required
def favorite_list(request):
    favorites = (
        FavoriteProduct.objects
        .filter(user=request.user)
        .select_related('product__category')
        .prefetch_related('product__images')
    )
    return render(request, 'shop/favorite_list.html', {'favorites': favorites})
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Category, Product

PRODUCTS_PER_PAGE = 12


def product_list(request, category_slug=None):
    category = None
    products = Product.objects.select_related('category').prefetch_related('images')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(name__icontains=q)

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

    context = {
        'category': category,
        'products': page,
        'sort': sort,
        'q': q,
    }
    return render(request, 'shop/list.html', context)


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

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'shop/detail.html', context)

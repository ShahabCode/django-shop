from django.shortcuts import render, get_object_or_404
from .models import Category, Product
from django.core.paginator import Paginator

# Create your views here.
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.all()
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    sort = request.GET.get('sort', 'newest')

    if sort == 'cheapest':
        products = products.order_by('new_price')
    elif sort == 'expensive':
        products = products.order_by('-new_price')
    else:
        sort = 'newest'
        products = products.order_by('-created')

    paginator = Paginator(products, 2)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'category': category,
        'categories': categories,
        'products': products
    }
    return render(request, 'shop/list.html', context)


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug)
    context = {
        'product': product
    }
    return render(request, 'shop/detail.html', context)

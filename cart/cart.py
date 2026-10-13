from django.template.context_processors import request

from shop.models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart


    def add(self, product):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 1, 'price': product.new_price, 'weight': product.weight}
        else:
            if self.cart[product_id]['quantity'] < product.inventory:
                self.cart[product_id]['quantity'] += 1
        self.save()


    def decrease(self, product):
        product_id = str(product.id)
        if self.cart[product_id]['quantity'] > 1:
            self.cart[product_id]['quantity'] -= 1
        self.save()


    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
        self.save()


    def clear(self):
        self.cart = {}
        self.save()


    def get_total_price(self):
        products = Product.objects.filter(id__in=self.cart.keys())

        return sum(
            product.new_price * self.cart[str(product.id)]['quantity']
            for product in products
        )


    def get_post_price(self):
        products = Product.objects.filter(id__in=self.cart.keys())

        weight = sum(
            product.weight * self.cart[str(product.id)]['quantity']
            for product in products
        )
        if weight < 1000:
            return 20000
        elif weight < 2000:
            return 30000
        return 50000


    def get_final_price(self):
        return self.get_total_price() + self.get_post_price()


    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())


    def __iter__(self):
        products = Product.objects.filter(id__in=self.cart.keys())

        for product in products:
            product_id = str(product.id)
            item = self.cart[product_id].copy()

            item['price'] = product.new_price
            item['weight'] = product.weight
            item['product'] = product
            item['total'] = item['price'] * item['quantity']

            yield item


    def save(self):
        self.session.modified = True








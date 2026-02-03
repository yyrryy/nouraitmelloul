from django import template
from pis_product.models import Product, Category
from django.db.models import Count, F



register = template.Library()

@register.filter
def split_word(v):
    return v.split()

@register.simple_tag
def product_notifications(retailer_id):
    p=Product.objects.filter(retailer__id=retailer_id)
    return len([i for i in p if i.stock==0])

@register.simple_tag
def lenproducts():
    return Product.objects.all().count

@register.simple_tag
def products():
    return Product.objects.all()

@register.simple_tag
def command():
    return Product.objects.filter(command=True).count

# @register.simple_tag
# def ensemble():
#     ids=[54, 70, 58, 86, 90, 75, 51, 76, 83, 156, 59, 57]
#     #ids=[5, 17]
#     categories=[Category.objects.get(pk=i) for i in ids]
#     products = Product.objects.filter(stock__lt=1, category__in=categories).annotate(num_products=Count('id'))
#     return products.count()


@register.simple_tag
def arr():
    ids=[77, 132, 144, 106]
    categories=[Category.objects.get(pk=i) for i in ids]
    products = Product.objects.filter(stock__lt=4, category__in=categories).annotate(num_products=Count('id'))
    return products.count()

@register.simple_tag
def urgentpdcts():
    return Product.objects.filter(urgent=True).count

@register.filter
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.simple_tag
def minpdcts():
    print(Product.objects.filter(minstock__gte=0, stock__lte=F('minstock')).count())
    return Product.objects.filter(minstock__gt=0, stock__lte=F('minstock')).count
    #return Product.objects.filter(minstock__gte=0, stock__lte=F('minstock')).count


@register.simple_tag
def categorynames():
    return Category.objects.all()


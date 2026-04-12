from __future__ import unicode_literals
from django.db import models
from django.db.models import Sum, Q
import random
from django.db.models.signals import post_save
import json
from pis_com.models import DatedModel
from django.utils import timezone
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    isactive=models.BooleanField(default=True)
    detals = models.TextField(null=True)
    def __str__(self) -> str:
        return self.name
class Itemsbysupplier(models.Model):
    supplier= models.ForeignKey(Supplier, related_name='supplier',on_delete=models.CASCADE, default=None)
    date = models.DateTimeField(auto_now_add=True)
    items = models.TextField(blank=True, null=True, help_text='Quantity and Product name would save in JSON format')
    total = models.DecimalField(max_digits=65, decimal_places=2, default=0.00)
    nbon = models.CharField(max_length=100, blank=True, null=True)
    rest= models.DecimalField(max_digits=65, decimal_places=2, default=0.00)


class Avancesbon(models.Model):
    bon = models.ForeignKey(Itemsbysupplier, related_name='supplier_avance',on_delete=models.CASCADE, default=None)
    date = models.DateTimeField(auto_now_add=True)
    avance = models.DecimalField(max_digits=65, decimal_places=2, default=0.00)
    details = models.CharField(max_length=100, blank=True, null=True)

class Category(models.Model):
    parent = models.ForeignKey('self', related_name='children', on_delete=models.CASCADE, blank = 
    True, null=True)
    name = models.CharField(max_length=100)
    def __str__(self) -> str:
        return self.name
        
class SubCategory(models.Model):
    category = models.ForeignKey(
        Category, related_name='category_subcategory',on_delete=models.CASCADE, default=None
    )
    name = models.CharField(max_length=100)
    def __str__(self) -> str:
        return self.name

class Mark(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self) -> str:
        return self.name

class Product(models.Model):
    #panier indicates if product is in panier
    date_command = models.DateTimeField(default=None, null=True, blank=True)
    barcode=models.CharField(default='-', null=True, blank=True, max_length=120, unique=True)
    panier=models.BooleanField(default=False)
    # already
    already=models.BooleanField(default=False)
    category=models.ForeignKey(Category, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=5000, default=None, null=True, blank=True)
    ref = models.CharField(max_length=5000, default=None, null=True, blank=True)
    entry = models.CharField(max_length=5000, default=None, null=True, blank=True)
    brand_name = models.CharField(max_length=200, blank=True, null=True)
    retailer = models.ForeignKey(
        'pis_retailer.Retailer',
        related_name='retailer_product',on_delete=models.CASCADE, default=None
    )
    price=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pr_achat=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    prices = models.TextField(default='[]')
    # used to indicate if the product is commanded
    command=models.BooleanField(default=False)
    urgent=models.BooleanField(default=False)
    # used to indicate if the product is ready to be commanded
    rcommand=models.BooleanField(default=False)
    commanded=models.BooleanField(default=False)
    qtycommand=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    disponibleinother=models.BooleanField(default=False)
    supplier=models.ForeignKey(Supplier, on_delete=models.CASCADE, default=None, null=True, blank=True, related_name="command_supplier")
    originsupp=models.ForeignKey(Supplier, on_delete=models.CASCADE, default=None, null=True, blank=True, related_name="original_supplier")
    mark=models.ForeignKey(Mark, on_delete=models.CASCADE, default=None, null=True, blank=True, related_name="product_mark")
    stock=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    car = models.CharField(max_length=5000, blank=True, null=True, default=None)
    bar_code = models.CharField(max_length=13, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    minstock=models.IntegerField(default=0, blank=True, null=True)
    supplierprices=models.TextField(default='[]')
    # marks of refs saisie
    marks=models.TextField(default='', null=True, blank=True)
    expensive=models.BooleanField(default=False)
    def getsimillars(self):
        try:
            originref=self.ref.split()[0]
        except:
            originref=self.ref
        return Product.objects.exclude(id=self.id).filter(category=self.category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref), stock__gt=0)
    
    def getprices(self):
        #return []
        prices=json.loads(self.prices)
        filtered_prices = [item for item in prices if float(item[1]) != 0]
        return filtered_prices
    

    def total_items(self):
        try:
            obj_stock_in = self.stockin_product.aggregate(Sum('quantity'))
            stock_in = float(obj_stock_in.get('quantity__sum'))
        except:
            stock_in = 0

        return stock_in

    def product_available_items(self):
        try:
            obj_stock_in = self.stockin_product.aggregate(Sum('quantity'))
            stock_in = float(obj_stock_in.get('quantity__sum'))
        except:
            stock_in = 0

        try:
            obj_stock_out = self.purchased_product.aggregate(Sum('quantity'))
            stock_out = float(obj_stock_out.get('quantity__sum'))
        except:
            stock_out = 0
        dif= stock_in - stock_out
        return dif
    
    def product_purchased_items(self):
        try:
            obj_stock_out = self.stockout_product.aggregate(
                Sum('stock_out_quantity'))
            stock_out = float(obj_stock_out.get('stock_out_quantity__sum'))
        except:
            stock_out = 0
        return  stock_out

    def total_num_of_claimed_items(self):
        obj = self.claimed_product.aggregate(Sum('claimed_items'))
        return obj.get('claimed_items__sum')
    

def generate_unique_7_digit_barcode():
    while True:
        # Generate a random 7-digit number
        barcode = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        
        # Check for uniqueness
        if not Product.objects.filter(barcode=barcode).exists():
            return barcode

# def create_save_bar_code(sender, instance, created, **kwargs):

#     if created and (not instance.barcode or instance.barcode == '-'):
#         # Use the unique 7-digit barcode
#         instance.barcode = generate_unique_7_digit_barcode()
#         instance.save()
#post_save.connect(create_save_bar_code, sender=Product)

class Productscommand(models.Model):
    product = models.ForeignKey(
        Product, related_name='productcommande',on_delete=models.CASCADE, default=None
    )
    qty=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


def int_to_bin(value):
        return bin(value)[2:]


def bin_to_int(value):
        return int(value, base=2)


# Signals Function for bar code
# def create_save_bar_code(sender, instance, created, **kwargs):

#     if not instance.bar_code:
#         import time
#         from pis_com import ean13

#         code = None

#         r = random.Random(time.time())
#         m = int_to_bin(instance.pk % 4)
#         if len(m) == 1:
#             m = '0' + m
#         elif not len(m):
#             m = '00'

#         while not code:
#             g = ''.join([str(r.randint(0, 1)) for i in range(32)])
#             chk = int_to_bin(bin_to_int(g) % 16)

#             if len(chk) < 4:
#                 chk = '0' * (4 - len(chk)) + chk

#             chk = ''.join(['1' if x == '0' else '0' for x in chk])

#             if m == '11':
#                 code = ''.join(['1', m, g[:16], chk, g[16:32]])
#             elif m == '10':
#                 code = ''.join(['1', m, g[:11], chk, g[11:32]])
#             elif m == '01':
#                 code = ''.join(['1', m, g[:19], chk, g[19:32]])
#             else:
#                 code = ''.join(
#                     ['1', m, g[:9], chk[:2], g[9:23], chk[2:4], g[23:32]])

#             code = '%d' % bin_to_int(code)
#             code += '%d' % ean13.get_checksum(code)

#         instance.bar_code = code
#         instance.save()


# Signal Calls bar code
#post_save.connect(create_save_bar_code, sender=Product)


class StockIn(models.Model):
    product = models.ForeignKey(
        Product, related_name='stockin_product',on_delete=models.CASCADE, default=None
    )
    quantity = models.FloatField(
        default=0.0, blank=True, null=True
    )
    price = models.FloatField(
        default=0.0, blank=True, null=True
    )
    dated_order = models.DateTimeField(auto_now_add=True)
    reciept=models.ForeignKey(Itemsbysupplier, related_name='supplier_product',on_delete=models.CASCADE, default=None, null=True, blank=True)

    def __unicode__(self):
        return self.product.ref


class ProductDetail(DatedModel):
    product = models.ForeignKey(
        Product, related_name='product_detail',on_delete=models.CASCADE, default=None
    )
    retail_price = models.DecimalField(
        max_digits=65, decimal_places=2, default=0
    )
    consumer_price = models.DecimalField(
        max_digits=65, decimal_places=2, default=0
    )
    available_item = models.IntegerField(default=1)
    purchased_item = models.IntegerField(default=0)

    def __unicode__(self):
        return self.product.name


class PurchasedProduct(DatedModel):
    #add article, since products will be entered manually
    article=models.CharField(max_length=5000, blank=True, null=True, default=None)
    product = models.ForeignKey(
        Product, related_name='purchased_product',on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    invoice = models.ForeignKey(
        'pis_sales.SalesHistory', related_name='purchased_invoice',
        blank=True, null=True,on_delete=models.CASCADE
    )
    quantity = models.DecimalField(
        max_digits=65, decimal_places=2, default=1, blank=True, null=True
    )
    price = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )
    discount_percentage = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )
    purchase_amount = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )




class ExtraItems(DatedModel):
    retailer = models.ForeignKey(
        'pis_retailer.Retailer', related_name='retailer_extra_items',on_delete=models.CASCADE, default=None
    )
    item_name = models.CharField(
        max_length=100, blank=True, null=True)
    quantity = models.CharField(
        max_length=100, blank=True, null=True)
    price = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True)
    discount_percentage = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True)
    total = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True)

    def __unicode__(self):
        return self.item_name or ''


class ClaimedProduct(DatedModel):
    product = models.ForeignKey(Product, related_name='claimed_product',on_delete=models.CASCADE, default=None)
    customer = models.ForeignKey(
        'pis_com.Customer', related_name='customer_claimed_items',
        null=True, blank=True,on_delete=models.CASCADE
    )
    claimed_items = models.IntegerField(
        default=1, verbose_name='No. of Claimed Items')
    claimed_amount = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True)

    def __unicode__(self):
        return self.product.name


class StockOut(models.Model):
    product = models.ForeignKey(
        Product, related_name='stockout_product',on_delete=models.CASCADE, default=None
    )
    invoice = models.ForeignKey(
        'pis_sales.SalesHistory', related_name='out_invoice',
        blank=True, null=True,on_delete=models.CASCADE
    )
    purchased_item = models.ForeignKey(
        PurchasedProduct, related_name='out_purchased',
        blank=True, null=True,on_delete=models.CASCADE
    )
    stock_out_quantity=models.CharField(max_length=100, blank=True, null=True)
    selling_price = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )
    buying_price = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )
    dated=models.DateField(blank=True, null=True)

    def __unicode__(self):
        return self.product.name


# Signals
def purchase_product(sender, instance, created, **kwargs):
    
    product_items = (
        instance.product.product_detail.filter(
            available_item__gt=0).order_by('created_at')
    )

    if product_items:
        item = product_items[0]
        item.available_item - 1
        item.save()

class Avoir(models.Model):
    supplier= models.ForeignKey(Supplier, related_name='suppavoir',on_delete=models.CASCADE, default=None)
    avoir=models.TextField(default=None)


class Reforigin(models.Model):
    category=models.ForeignKey(Category, on_delete=models.CASCADE, default=None)
    reforigin=models.CharField(max_length=9200, default=None, null=True, blank=True)
class Facture(models.Model):
    client=models.ForeignKey(
        'pis_com.Customer', related_name='clientfacture',
        null=True, blank=True,on_delete=models.SET_NULL
    )
    date=models.DateField()
    total=models.FloatField(default=0.00, null=True)
    avance=models.FloatField(default=0.00, null=True, blank=True)
    facture_no=models.CharField(max_length=100)
    ispaid=models.BooleanField(default=False)
    # is ,anual ,eans is entreprise
    ismanual=models.BooleanField(default=False)
    note=models.TextField(default='', null=True, blank=True)

class Factureitems(models.Model):
    facture=models.ForeignKey(Facture, on_delete=models.CASCADE, null=True, default=None, related_name='factureitems')
    article=models.CharField(max_length=500, default=None, null=True)
    bl=models.CharField(max_length=500, default=None, null=True)
    bc=models.CharField(max_length=500, default=None, null=True)
    mtrc=models.CharField(max_length=500, default=None, null=True)
    qty=models.CharField(max_length=500, default=None, null=True)
    price=models.CharField(max_length=500, default=None, null=True)
    total=models.CharField(max_length=500, default=None, null=True)


class Releve(models.Model):
    client=models.ForeignKey(
        'pis_com.Customer', related_name='clientofreleve',
        null=True, blank=True,on_delete=models.SET_NULL
    )
    datefrom=models.DateField(null=True, blank=True, default=None)
    dateto=models.DateField(null=True, blank=True, default=None)
    total=models.FloatField(default=0.00, null=True)
    facture_no=models.CharField(max_length=100, null=True, blank=True, default=None)
    ispaid=models.BooleanField(default=False)

class Releveitems(models.Model):
    releve=models.ForeignKey(Releve, on_delete=models.CASCADE, null=True, default=None)
    date=models.DateField(default=None, null=True, blank=True)
    facture=models.CharField(max_length=500, default=None, null=True, blank=True)
    total=models.CharField(max_length=500, default=None, null=True, blank=True)


class Devise(models.Model):
    client=models.ForeignKey(
        'pis_com.Customer', related_name='clientdevise',
        null=True, blank=True,on_delete=models.SET_NULL
    )
    date=models.DateField()
    total=models.FloatField(default=0.00, null=True)
    Devise_no=models.CharField(max_length=100)
    note=models.CharField(max_length=100, default=None, null=True)

class Deviseitems(models.Model):
    devise=models.ForeignKey(Devise, on_delete=models.SET_NULL, null=True)
    article=models.CharField(max_length=500)
    qty=models.CharField(max_length=500)
    price=models.CharField(max_length=500)
    total=models.CharField(max_length=500)

def create_save_fc(sender, instance, created, **kwargs):
    if created and not instance.facture_no:
        year_month = timezone.now().strftime("%y")
        latest_receipt = Facture.objects.filter(
            facture_no__startswith=f"FC{year_month}"
        ).last()
        if latest_receipt:
            facture_no = int(latest_receipt.facture_no[-6:])
            facture_no = f"FC{year_month}{facture_no + 1:06}"
        else:
            facture_no = f"FC{year_month}000001"
        instance.facture_no = facture_no
        instance.save()


# Signal Calls
#post_save.connect(create_save_fc, sender=Facture)

def create_save_dv(sender, instance, created, **kwargs):
    if created and not instance.Devise_no:
        year_month = timezone.now().strftime("%y")
        latest_receipt = Devise.objects.filter(
            Devise_no__startswith=f"DV{year_month}"
        ).last()
        if latest_receipt:
            latest_Devise_no = int(latest_receipt.Devise_no[-6:])
            Devise_no = f"DV{year_month}{latest_Devise_no + 1:06}"
        else:
            Devise_no = f"DV{year_month}000001"
        instance.Devise_no = Devise_no
        instance.save()


# Signal Calls
post_save.connect(create_save_dv, sender=Devise)

class Todo(models.Model):
    name=models.TextField()
    isdon=models.BooleanField(default=False)
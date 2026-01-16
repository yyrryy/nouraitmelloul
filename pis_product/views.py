from __future__ import unicode_literals
from django.shortcuts import render, redirect, get_object_or_404
import json
import qrcode
from django.views.generic import TemplateView, UpdateView
from django.views.generic import FormView, ListView
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from django.db.models.functions import Coalesce
from pis_product.models import PurchasedProduct, ExtraItems, ClaimedProduct,StockOut, StockIn, Product, ProductDetail, Category, SubCategory, Supplier, Itemsbysupplier, Avancesbon, Mark, Avoir, Reforigin, Facture, Factureitems, Devise, Deviseitems, Releve, Releveitems
from pis_product.forms import (
    ProductForm, ProductDetailsForm, ClaimedProductForm,StockDetailsForm,StockOutForm)
from django.utils import timezone
import pandas as pd
from django.views.decorators.csrf import csrf_exempt
from pis_retailer.models import Retailer
from django.db.models import Count
from django.db import transaction
from datetime import datetime
from pis_sales.models import SalesHistory
from pis_com.models import Customer
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
this_year = datetime.now().year
this_month = datetime.now().month
today=timezone.now().date()

def number_to_letters(num):
    result = ''
    alphabet = 'uqslfarch'  # Mapping for digits 1 to 9

    # Convert each digit to a letter, ignore decimals and handle 0s
    for digit in str(num):
        if digit == '.':
            result += '.'  # Preserve the decimal point
        elif digit == '0':
            result += 'x'  # Use 'x' to represent '0'; you can change this if needed
        else:
            index = int(digit) - 1  # Convert to 0-based index
            if 0 <= index < len(alphabet):
                result += alphabet[index]  # Append the corresponding letter

    return result


def letters_to_number(letters):
    result = ''
    alphabet = 'uqslfarch'  # Mapping for digits 1 to 9

    # Convert each letter back to a digit
    for char in letters:
        if char == '.':
            result += '.'  # Preserve the decimal point
        elif char == 'x':
            result += '0'  # Convert 'x' back to '0'
        else:
            index = alphabet.index(char)  # Get index of the letter
            if index != -1:
                result += str(index + 1)  # Convert back to number (1-based)

    return result


def printbarcodes(request):
    productid = request.GET.get('productid')
    # if the request is comming from achat
    achat = request.GET.get('achat')=='1'
    # qty = int(request.GET.get('qty', 1))  # Default to 1 if not provided
    price = request.GET.get('price')
    supplier = request.GET.get('supplier')

    # Retrieve the product from the database
    product = Product.objects.get(pk=productid)
    print('>>', product.barcode)

    # Use the barcode directly as a string
    code = product.barcode
    # code_class = barcode.get_barcode_class('ean8')

    # # List to hold the barcodes in base64 format
    # barcodes = []
    # target_width_mm = 25
    # mm_to_inches = 25.4
    # barcode_width_inches = target_width_mm / mm_to_inches
    # # Generate barcodes for the specified quantity
    # #for _ in range(1):
    # buffer = BytesIO()
    # barcode_instance = code_class(code, writer=ImageWriter())
    # options = {
    #     'write_text': False,
    #     'dpi': 300,           # Adjust module width for precision
    #     'module_width': 6 / len(code),
    #     'module_height':80/len(code)
    # }
    # barcode_instance.write(buffer, options)

    # # Convert the image to base64 and append it to the list
    # barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    # barcodes.append(barcode_base64)
    # buffer.close()
    # lastachat=StockIn.objects.filter(product=product).last()
    # print(">> ss", lastachat, achat)
    # # if achat means the request is coming from bon achat, date will be today
    # if achat:
    #     print('>>>> todat')
    #     date=datetime.today().strftime('%m%y')
    # else:
    #     if lastachat and lastachat.reciept:
    #         date=lastachat.reciept.date.strftime('%m%y')
    #     else:
    #         date='-'
    # # Pass the barcodes and quantity to the template for rendering
    # text=f'{product.category.name.upper()} {product.ref.split()[0].upper()}{product.mark.name.upper()}{price}/{date} {product.car}'
    # return render(request, 'products/barcode.html', {
    #     'barcodes': barcodes,
    #     'text': text,
    #     'product':product,
    #     'date':date,
    #     'price':price
    # })
    

    # Encode data as a string
    qr_text = (
        f"{code}A{price}"
    )

    # Generate the QR Code
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=0,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    # Save QR Code to a BytesIO buffer
    buffer = BytesIO()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(buffer, format="PNG")

    # Convert image to Base64
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    # Determine date
    lastachat = StockIn.objects.filter(product=product).last()
    if achat:
        date = datetime.today().strftime('%m%y')
    else:
        date = lastachat.reciept.date.strftime('%m%y') if lastachat and lastachat.reciept else '-'

    # Dynamic text for display
    text = (
        f"{product.category.name.upper()} {product.ref.split()[0].upper()} "
        f"{product.mark.name.upper()} P{price}/D{date} -{supplier}- {product.car}"
    )

    # Render the template with the QR code and additional data
    return render(request, 'products/barcode.html', {
        'barcodes': qr_code_base64,
        'text': text,
        'product': product,
        'date': date,
        'price': price,
    })

def barcodescan(request):
    return render(request, 'products/barcodescan.html')

def geturgentbycategory(request):
    category_id = request.POST.get('category')
    products = Product.objects.filter(category_id=category_id, urgent=True).order_by('ref')
    products = sorted(products, key=lambda p: len(p.getsimillars()))

    suppliers=Supplier.objects.all()

    ctx={
        'products':products,
        'suppliers':suppliers,
        'urgent':True
    }
    return JsonResponse({
        'data':render(request, 'products/low_stock.html', ctx).content.decode('utf-8')
    })

def facturedetailsprint(request, id):
    order=Facture.objects.get(pk=id)
    orderitems=Factureitems.objects.filter(facture=order).order_by('-id')
    # split the orderitems into chunks of 10 items
    orderitems=list(orderitems)
    orderitems=[orderitems[i:i+30] for i in range(0, len(orderitems), 30)]

    ctx={
        'title':f'Facture {order.facture_no}',
        'facture':order,
        'orderitems':orderitems,
        'tva':order.tva,
        'ttc':order.total,
        'ht':round(order.total-order.tva, 2),
    }
    return render(request, 'facturedetailsprint.html', ctx)

def makeurgent(request):
    id=request.POST.get('id')
    product=Product.objects.get(pk=id)
    product.urgent=True
    product.save()
    return JsonResponse({
        'valid':True
    })
def urgent(request):
    products=Product.objects.filter(urgent=True)
    cc = Category.objects.filter(
    product__in=products
    ).distinct()
    targets = Category.objects.filter(parent__isnull=False, product__urgent=True).annotate(
    total_products=Count('product')
    )
    return render(request, 'products/urgent.html', {'title':'Urgent Stock', 'categories':targets, 'ids':cc.values_list('id', flat=True),
    'suppliers':Supplier.objects.all()})

def duplicate(request):
    pp=Product.objects.get(id=request.POST.get('id'))
    rr=request.POST.get('ref')
    marksofref=request.POST.get('marks')
    categoryid=request.POST.get('categoryid')
    mark=request.POST.get('mark')
    supplier=request.POST.get('supplier')
    saisie=request.POST.get('saisie')
    #stt=request.POST.get('stock')
    pr=request.POST.get('price')
    originref=pp.ref.split()[0]
    print('>> mrks', marksofref)
    simillar = Product.objects.filter(category=categoryid).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
    print(simillar)
    marks=[]
    for i in simillar:
        marks.append(i.mark_id)
    print(mark, marks)
    if int(mark) in marks:
        return JsonResponse({
            'success':False,
            'error':'mark deja exist'
        })

    # priceslist=[]
    # if float(pr) > 0:
    #     suppname=Supplier.objects.get(id=supplier).name
    #     # priceslist=[[prachat, stock, suppname]]
    #     priceslist=[[pr, stt, suppname]]
    barcode=''
    while True:
        # Generate a random 7-digit number
        barcode = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        
        # Check for uniqueness
        if not Product.objects.filter(barcode=barcode).exists():
            break
    print('>>>>> bar',barcode)
    product=Product.objects.create(
        retailer_id=1,
        price=pr,
        pr_achat=pr,
        category_id=categoryid,
        stock=0,
        car=pp.car,
        ref=f'{pp.ref} {rr}',
        mark_id=mark,
        originsupp_id=supplier,
        image=pp.image,
        entry=saisie,
        marks=marksofref,
        barcode=barcode
    )
    # if float(stt)>0:
    #     StockIn.objects.create(
    #         product=product,
    #         quantity=stt,
    #     )
    originref=product.ref.split(' ')[0]
    simillar = Product.objects.filter(category=categoryid).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
    sim=any([i.stock>0 for i in simillar])
    print('stock in others',sim)
    if sim:
        simillar.update(disponibleinother=True)
        simillar.update(rcommand=False)
        simillar.update(command=False)
        simillar.update(commanded=False)
        simillar.update(supplier=None)
    else:
        simillar.update(disponibleinother=False)
        simillar.update(rcommand=True)
    return JsonResponse({
        'success':True
    })
    #return redirect('product:producthistory', product.id)

def refreshitemssupplier(request):
    supplier=request.POST.get('supplier')
    products=Product.objects.filter(supplier_id=supplier)
    return JsonResponse({
        'data':render(request, 'products/refreshsupplierproducts.html', {'products':products}).content.decode('utf-8'),
        'len':len(products)
    })


def searchrefinstock(request):
    ref=request.POST.get('ref').strip()
    products=Product.objects.filter(ref__icontains=ref)
    ctx={
        'products':products,
        'home':False,
        'marks':Mark.objects.all(),
        'suppliers':Supplier.objects.all()
    }
    return JsonResponse({
        'data':render(request, 'products/product_search.html', ctx).content.decode('utf-8')
    })

def refreshmark(request):
    marks=Mark.objects.all()
    options=''
    for mark in marks:
        options+=f'<option value="{mark.id}">{mark.name}</option>'
    return JsonResponse({
        'data':options
    })

def refexeption(request):
    ref=request.POST.get('ref')
    #categoryid=request.POST.get('categoryid')
    # products=Product.objects.filter(category_id=categoryid, ref__icontains=ref)
    products=Product.objects.filter(ref__icontains=ref)
    print(products)
    return JsonResponse({
        'data':render(request, 'products/refexeption.html', {'products':products}).content.decode('utf-8'),
    })


def filtercommandesupp(request):
    suppid=request.POST.get('supplierid')
    products=Product.objects.filter(supplier_id=suppid, command=True, commanded=True).order_by('category__name')
    pdctnotcmnd=Product.objects.filter(supplier_id=suppid, command=True, commanded=False).order_by('category__name')
    print('>>> Getting products of supplier', suppid)
    print('>>> not commanded', pdctnotcmnd.count())
    print('>>> not commanded', products.count())
    suppliers=Supplier.objects.all()
    panier=Product.objects.filter(panier=True, supplier_id=suppid)
    print(">> panier", panier)
    datapanier=[]
    for i in panier:
        p={
            'ref':str(i.ref).upper(),
            'category':str(i.category.name).upper(),
            'car':str(i.car).upper(),
            'mark':str(i.mark).upper(),
            'supplier':str(i.supplier.name).upper(),
            'qtycommand':i.qtycommand,
            'pdctid':i.id,
            'ctgid':i.category.id,
            'suppid':i.supplier.id,
            'commanded':i.commanded
        }
        datapanier.append(p)
    return JsonResponse({
        'data':render(request, 'products/commandefilter.html', {'products':products, 'pdctnotcmnd':pdctnotcmnd, 'suppliers':suppliers}).content.decode('utf-8'),
        'len':len(products),
        'avoirs':list(Avoir.objects.filter(supplier_id=request.POST.get('supplierid')).values()),
        'panier':datapanier,
        'panierlen':panier.count()
    })

# add new ledger from modal
@csrf_exempt
def addclient(request):
    name=request.POST.get('name')
    phone=request.POST.get('phone') or 0000000000
    ice=request.POST.get('ice') or None
    adress=request.POST.get('address') or None
    print(name, phone, adress, ice)
    Customer.objects.create(customer_name=name,customer_phone=phone,address=adress, ice=ice, retailer=Retailer.objects.get(id=request.user.retailer_user.retailer.id))
    return JsonResponse({'status':True})


def productslistbycategory(request):

    categories = Category.objects.filter(parent=None).order_by('name')
    cc = Category.objects.filter(children__isnull=True).order_by('name')
    parents = Category.objects.all()
    first=0
    if cc:
        first=cc[0].id

    ctx={
        'parents':parents,
        'categories':categories,
        'title':'Liste Articles par categorie',
        'children':cc,
        #first id to put it in the form of adding bulk
        'firstid':first,
        'suppliers':Supplier.objects.all(),
        'marks':Mark.objects.all()
    }
    return render(request, 'products/productslistbycategory.html', ctx)




def retour(request):
    purchase=PurchasedProduct.objects.get(pk=request.POST.get('purchaseid'))
    qty=request.POST.get('qtyinp')
    productid=request.POST.get('productid')
    if float(qty)==float(purchase.quantity):
        purchase.delete()
        # purchase.save()
    else:
        purchase.quantity=float(purchase.quantity)-float(qty)
        purchase.save()
    product=Product.objects.get(pk=productid)
    product.stock=product.product_available_items()
    product.save()
    originref=product.ref.split(' ')[0]
    simillar = Product.objects.filter(category=product.category.id).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
    simillar.update(disponibleinother=True)
    simillar.update(rcommand=False)
    return redirect('product:producthistory', productid)

def lowstock(request):
    products=Product.objects.filter(stock=0)
    cc = Category.objects.filter(
    product__in=products
    ).distinct()
    targets = Category.objects.filter(parent__isnull=False, product__stock=0).annotate(
    total_products=Count('product')
    )
    return render(request, 'products/lowstock.html', {'title':'Rupture Stock', 'categories':targets, 'ids':cc.values_list('id', flat=True),
    'suppliers':Supplier.objects.all()})


def lowintwins(request):
    #ids are the category ids that we want to display in low twins
    ids=[54, 70, 58, 86, 90, 75, 51, 76, 83, 156, 59, 57]
    products=Product.objects.filter(category_id__in=ids, stock__lte=1)
    print(products.count())
    #ids=[5, 17]
    categories=Category.objects.filter(pk__in=ids, product__stock__lte=1).annotate(total_products=Count('product'))
    ctx={
        'title':'Stock alert twins',
        'categories':categories,
        'suppliers':Supplier.objects.all()
    }
    return render(request, 'products/twinstock.html', ctx)



def lowinarr(request):
    ids=[77, 132, 144]
    categories=Category.objects.filter(pk__in=ids, product__stock__lte=4).annotate(total_products=Count('product'))
    ctx={
        'title':'Stock alert twins',
        'categories':categories,
        'suppliers':Supplier.objects.all()
    }
    return render(request, 'products/lowarr.html', ctx)


def getlowintwins(request):
    category=request.POST.get('category')
    # get rpoducts by catgoory and having stock not devided by 2
    products = Product.objects.filter(category=Category.objects.get(pk=category), stock__lte=1).order_by('ref')
    products = sorted(products, key=lambda p: len(p.getsimillars()))

    ctx={
        'products':products,
        'suppliers':Supplier.objects.all(),
        'noturgent':True
    }
    return JsonResponse({
        'data':render(request, 'products/low_stock.html', ctx).content.decode('utf-8')
    })

def getlowinarr(request):
    category=request.POST.get('category')
    # get rpoducts by catgoory and having stock not devided by 2
    products = Product.objects.filter(category=Category.objects.get(pk=category), stock__lt=4).order_by('ref')
    products = sorted(products, key=lambda p: len(p.getsimillars()))

    ctx={
        'products':products,
        'suppliers':Supplier.objects.all(),
        'noturgent':True
    }
    return JsonResponse({
        'data':render(request, 'products/low_stock.html', ctx).content.decode('utf-8')
    })


def searchrefinlow(request):
    ref=request.POST.get('ref').lower()
    # get products that starts with ref and stock = 0
    products=Product.objects.filter(ref__icontains=ref, stock=0).order_by('disponibleinother')
    #products=Product.objects.filter(ref__istarts=ref, stock=0)
    print(products)
    if products:
        products=products
    else:
        products=[]
    ctx={
        'products':products,
        'suppliers':Supplier.objects.all(),
        'noturgent':True
    }
    return JsonResponse({
        'data':render(request, 'products/low_stock.html', ctx).content.decode('utf-8')
    })

def categories(request):
    categories = Category.objects.all()
    ctx={
        'cc':categories,
        'title':'Liste Categories'
    }
    return render(request, 'products/categories.html', ctx)

def getproductsbycategory(request):
    # category = Category.objects.get(pk=request.POST.get('category'))
    # products = category.product.filter(category=category)[:10]
    # get ten products from the category
    if request.POST.get('category')=='C3':
        products = Product.objects.all()[:3000]
    elif request.POST.get('category')=='C4':
        products = Product.objects.all()[3000:4000]
    elif request.POST.get('category')=='C5':
        products = Product.objects.all()[4000:5000]
    elif request.POST.get('category')=='C6':
        products = Product.objects.all()[5000:6000]
    elif request.POST.get('category')=='C7':
        products = Product.objects.all()[6000:7000]
    elif request.POST.get('category')=='C8':
        products = Product.objects.all()[7000:8000]
    elif request.POST.get('category')=='C9':
        products = Product.objects.all()[8000:9000]
    elif request.POST.get('category')=='C10':
        products = Product.objects.all()[9000:10000]
    elif request.POST.get('category')=='C11':
        products = Product.objects.all()[10000:11000]
    elif request.POST.get('category')=='C12':
        products = Product.objects.all()[11000:12000]
    elif request.POST.get('category')=='C13':
        products = Product.objects.all()[12000:13000]
    elif request.POST.get('category')=='C14':
        products = Product.objects.all()[13000:14000]
    elif request.POST.get('category')=='C15':
        products = Product.objects.all()[14000:15000]
    elif request.POST.get('category')=='C16':
        products = Product.objects.all()[15000:16000]
    elif request.POST.get('category')=='C17':
        products = Product.objects.all()[16000:17000]
    
    else:
        products = Product.objects.filter(category__pk=request.POST.get('category'))[:50]
    ctx={
        'products':products,
        'home':False,
        'marks':Mark.objects.all(),
        'suppliers':Supplier.objects.all()
    }
    return JsonResponse({
        'data':render(request, 'products/product_search.html', ctx).content.decode('utf-8')
    })


def productscommande(request):
    #products=Product.objects.filter(command=True)
    return render(request, 'products/productscommande.html', {
        'title': 'commande',
        #'products':products,
        'suppliers':Supplier.objects.all(),
    })

#low stok by category
def getlowbycategory(request):
    # category = Category.objects.get(pk=request.POST.get('category'))
    # products = category.product.filter(category=category)[:10]
    # get ten products from the category
    category_id = request.POST.get('category')
    # products = Product.objects.filter(category_id=category_id, stock=0).order_by('disponibleinother')
    products = Product.objects.filter(category_id=category_id, stock=0).order_by('ref')

    # Calculate the length of getsimillars for each product and sort the list
    products = sorted(products, key=lambda p: len(p.getsimillars()))
    suppliers=Supplier.objects.all()

    ctx={
        'products':products,
        'suppliers':suppliers,
        'noturgent':True
    }
    return JsonResponse({
        'data':render(request, 'products/low_stock.html', ctx).content.decode('utf-8')
})

# not in use
def searchproductsincategory(request):
    # Category=Category.objects.get(pk=request.POST.get('category'))
    # products = Category.product.filter(name__icontains=request.POST.get('item'))
    # earch products in category given
    products = Product.objects.filter(category__pk=request.POST.get('category'), name__icontains=request.POST.get('name'))
    ctx={
        'products':products,
        'home':False
    }
    return JsonResponse({
        'data':render(request, 'products/product_search.html', ctx).content.decode('utf-8')
    })


@csrf_exempt
def addbulkcategory(request, id):
    sub=Category.objects.get(pk=id)
    myfile=request.FILES["excel_file"]
    retailer=Retailer.objects.get(id=request.user.retailer_user.retailer.id)
    df = pd.read_excel(myfile)
    df = df.fillna('-')
    for d in df.itertuples():

        product = Product.objects.create(
            retailer=retailer,
            name=d.article,
            price=d.prix,
            pr_achat=d.prachat,
            category=sub,
            car=d.car,
            stock=d.qty,
            ref=d.ref
        )
        StockIn.objects.create(
            product=product,
            quantity=d.qty,
        )
    #return a json response
    return redirect('product:productslistbycategory')


@csrf_exempt
def addcategory(request):
    category=request.POST.get('category')
    parent=None if request.POST.get('parent')=='0' else Category.objects.get(pk=request.POST.get('parent'))
    Category.objects.create(name=category, parent=parent)
    return redirect('product:productslistbycategory')

def deletecategory(request, id):
    category=Category.objects.get(pk=id)
    category.delete()
    return redirect('product:categories')


def updatebonline(request, id):
    itemid=request.POST.get('itemid')
    qty=request.POST.get('qty')
    product=Product.objects.get(pk=itemid)
    bon=Itemsbysupplier.objects.get(pk=id)
    stockin=StockIn.objects.get(reciept_id=id, product_id=itemid)
    avance = Avancesbon.objects.filter(bon_id=id)
    items=json.loads(bon.items)
    sumavances=sum([i.avance for i in avance])
    itemtoupdate = next((item for item in items if item['item_id'] == itemid), None)
    items = [item for item in items if item['item_id'] != itemid]


    if float(qty)==0:
        stockin.delete()
        product.stock=product.product_available_items()
        product.save()
        newstock=product.stock
        if newstock==0:
            originref=product.ref.split(' ')[0]
            simillar = Product.objects.filter(category=product.category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
            sim=any([int(i.stock) for i in simillar])
            if sim:
                simillar.update(disponibleinother=True)
                simillar.update(rcommand=False)
            else:
                simillar.update(disponibleinother=False)
                simillar.update(rcommand=True)
        total = itemtoupdate['total']
        if items:
            # items not empty
            newtotal=float(bon.total)-float(total)
            newrest=float(newtotal)-float(sumavances)
            bon.total=newtotal
            bon.rest=newrest
            bon.items=json.dumps(items)
            bon.save()
            return redirect('product:bonentree', id)
        else:
            # items empty
            bon.delete()
            avance.delete()
            return redirect('product:bonsentrees')

    else:
        price=request.POST.get('price')
        remise=request.POST.get('remise')
        total=request.POST.get('total')
        # update stockin
        stockin.quantity=qty
        stockin.save()
        #update item in bon
        # old total to compare
        oldtotal=itemtoupdate['total']
        itemtoupdate['total']=total
        itemtoupdate['remise']=remise
        itemtoupdate['qty']=qty
        itemtoupdate['price']=price
        newtotal=float(bon.total)-float(oldtotal)+float(total)
        newrest=float(newtotal)-float(sumavances)
        items.insert(0, itemtoupdate)
        bon.items=json.dumps(items)
        bon.total=newtotal
        bon.rest=newrest
        bon.save()
        # uppdate stock
        product.stock=product.product_available_items()
        product.save()
        originref=product.ref.split(' ')[0]
        simillar = Product.objects.filter(category=product.category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
        sim=any([int(i.stock) for i in simillar])
        if sim:
            simillar.update(disponibleinother=True)
            simillar.update(rcommand=False)
        else:
            simillar.update(disponibleinother=False)
            simillar.update(rcommand=True)
    return redirect('product:bonentree', id)

@csrf_exempt
def product_search(request):
    ref=request.POST.get('ref').strip()
    car=request.POST.get('car').strip()
    category=request.POST.get('category')
    print(ref, car, category)
    query = Q()
    if ref:
        query &= Q(ref__icontains=ref)
    if car:
        query &= Q(car__icontains=car)
    if category:
        query &= Q(category= category)
    products = request.user.retailer_user.retailer.retailer_product.filter(query).order_by('-stock')[:20]
    return JsonResponse({
        'data': render(request, 'products/product_search.html', {'products': products, 'home':True, 'suppliers':Supplier.objects.all(),
            'marks':Mark.objects.all()}).content.decode('utf-8')
    })


@csrf_exempt
def getproducts(request):
    products = Product.objects.filter(name__icontains=request.POST.get('item'))
    return JsonResponse({
        'data':render(request, 'products.html', {'products': products}).content.decode('utf-8')
    })


@csrf_exempt
def addbulk(request):
    # get the uploaded file

    myfile=request.FILES[next(iter(request.FILES))]
    retailer=Retailer.objects.get(id=request.user.retailer_user.retailer.id)

    df = pd.read_excel(myfile)
    df = df.fillna('-')
    for d in df.itertuples():
        product = Product.objects.create(
            retailer=retailer,
            name=d.article,
            brand_name=d.marque,
            price=d.prix,
            pr_achat=d.prachat
        )
        StockIn.objects.create(
            product=product,
            quantity=d.qty,
        )
    #return a json response
    return redirect('index')


def updatestock(request):
    qty=float(request.POST.get('sortieqty'))
    id=request.POST.get('productid')
    product=Product.objects.get(pk=id)
    refinput=request.POST.get('ref')
    
    print('>> refglobal', refinput)
    carinput=request.POST.get('car')
    categoryinput=request.POST.get('category')
    query = Q()
    if refinput:
        query &= Q(ref__icontains=refinput)
    if carinput:
        query &= Q(car__icontains=carinput)
    if categoryinput:
        query &= Q(category= categoryinput)
    products = request.user.retailer_user.retailer.retailer_product.filter(query).order_by('-stock')[:20]
    print('is zero',product.stock==0)
    if float(product.stock)==0 or float(qty)>float(product.stock):
        # 
        print('stock is null')
        return JsonResponse({
            'data': render(request, 'products/product_search.html', {'home':True}).content.decode('utf-8'),
            'zerostock':False,
            'error':'Quantity superieur au stock'
        })
    else:
        print('>>1')
        prices=json.loads(product.prices)
        # price=product.pr_achat
        print('>>2')
        price=float(request.POST.get('price'))
        # from here
        #amount=float(qty)*float(price)
        print('>>3')
        amount=float(price)
        for b, p in enumerate(prices):
            if float(p[0])==price and float(p[1])>0:
                news=float(prices[b][1])-float(qty)
                # if news==0:
                #     prices.pop(b)
                #     product.prices=json.dumps(prices)
                # else:
                #     prices[b][1] =float(prices[b][1])-float(qty)
                #     product.prices=json.dumps(prices)
                #     break
                # if float(prices[b][1])!=0:
                prices[b][1] =float(prices[b][1])-float(qty)
                product.prices=json.dumps(prices)
                break
            
        print('>>3')
        category=Category.objects.get(pk=request.POST.get('categoryid'))
        t=PurchasedProduct.objects.create(product_id=product.id, quantity=qty, purchase_amount=amount, price=amount)
        StockOut.objects.create(stock_out_quantity=qty, product_id=product.id)
        product.stock=float(product.stock)-float(qty)
        print('>>4')
        product.save()
        newstock=product.stock
        print('>>>>>>>>> minstock',product.minstock, newstock <= product.minstock, newstock==0 or newstock <= product.minstock, product.originsupp.name)
        if newstock==0 or newstock <= product.minstock:
            # supplier=product.originsupp
            # if supplier.id in [52, 91, 96]:
            #     product.supplier=supplier
            #     product.save()
            originref=product.ref.split(' ')[0]
            simillar = Product.objects.filter(category=product.category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref)).exclude(pk=product.id)
            print(simillar)
            sim=any([int(i.stock) for i in simillar])
            if sim:
                print('>>>>>>disinother')
                simillar.update(disponibleinother=True)
                simillar.update(rcommand=False)
            else:
                print('>>>>>>>not disinother')
                simillar.update(disponibleinother=False)
                simillar.update(rcommand=True)
                product.command=True
                product.commanded=False
                product.supplier=product.originsupp
                product.save()


        #ids=[54, 70, 58, 86, 90, 75, 51, 76, 83, 156, 59]
        # if newstock<=product.minstock:
        #     if product.category_id in ids:
        #         originref=product.ref.split(' ')[0]
        #         simillar = Product.objects.filter(category_id=product.category_id).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
        #         sim=any([int(i.stock) for i in simillar])
        #         if sim:
        #             simillar.update(disponibleinother=True)
        #             simillar.update(rcommand=False)
        #         else:
        #             simillar.update(disponibleinother=False)
        #             simillar.update(rcommand=True)
        #             product.command=True
        #             product.supplier=product.originsupp
        #             product.commanded=False
        #             product.save()
    return JsonResponse({
        'data': render(request, 'products/product_search.html', {'home':True, 'products':products}).content.decode('utf-8'),
        'zerostock':newstock==0,
    })

#cancel commande in 0 stock
def cancelcommande(request):
    product=Product.objects.get(pk=request.POST.get('id'))
    product.command=False
    product.supplier=None
    product.commanded=False
    product.already=True
    product.save()
    category=Category.objects.get(pk=request.POST.get('categoryid'))
    originref=product.ref.split(' ')[0]
    simillar = Product.objects.filter(category=category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
    anycomanded=any([i.command for i in simillar])
    print('one commanded',simillar, anycomanded, [i for i in simillar], [i.command for i in simillar])
    if anycomanded:
        simillar.update(rcommand=False)
    else:
        simillar.update(rcommand=True)
    
    return JsonResponse({
        'valid':True,
        # return html
        'getsimillarscommand':render(request, 'products/simillarcommand.html', {'item':product}).content.decode('utf-8')
    })

#cancel the green lign
def cancelcommanded(request):
    product=Product.objects.get(pk=request.POST.get('id'))
    product.commanded=False
    product.already=True
    product.save()
    return JsonResponse({
        'valid':True
    })

#cancel commande supp
def cancelcommandesupp(request):
    product=Product.objects.get(pk=request.POST.get('id'))
    print('cance')
    category=Category.objects.get(pk=request.POST.get('categoryid'))
    originref=product.ref.split(' ')[0]
    simillar = Product.objects.filter(category=category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
    simillar.update(rcommand=True)
    product.command=False
    product.supplier=None
    product.commanded=False
    product.save()
    return JsonResponse({
        'valid':True
    })

def deletemark(request):
    markid=request.POST.get('markid')
    mark = Mark.objects.get(pk=markid)
    if mark.product_mark.exists():
        return JsonResponse({
            'valid':False
        })
    else:
        mark.delete()
        return JsonResponse({
            'valid':True
        })


# marks view
def marks(request):
    return render(request, 'products/marks.html', {'title':'les marques', 'marks':Mark.objects.all()})

@csrf_exempt
def addmark(request):
    Mark.objects.create(name=request.POST.get('name'))
    return redirect('product:marks')

@csrf_exempt
def addoneproduct(request):
    # get data from formData sent from the ajax request
    # name = request.POST.get('name').strip()
    print('>> mrk', request.POST.get('mark'))
    print('>> mrkS', request.POST.get('marks'))
    marks=request.POST.get('marks')
    mark = Mark.objects.get(pk=request.POST.get('mark'))
    entry = request.POST.get('entry')
    expensive = True if request.POST.get('expensive')=='oui' else False
    supplier =request.POST.get('originsupp') or None
    car=request.POST.get('car').strip()
    #price = request.POST.get('price')
    stock=request.POST.get('stock') or 0
    prachat = request.POST.get('prachat') or 0
    priceslist=[]
    if float(prachat) > 0:
        if supplier:
            suppname=Supplier.objects.get(pk=supplier).name
            priceslist=[[prachat, stock, suppname]]

        # supplierprices=[[]]
    ref=request.POST.get('ref').strip().lower()
    category=request.POST.get('pcategory')
    minstock=request.POST.get('minstock') or 0
    image = request.FILES.get('image')
    print('>>>>>>>> expensive', expensive, 'rre', request.POST.get('expensive'))
    barcode=''
    while True:
        # Generate a random 7-digit number
        barcode = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        
        # Check for uniqueness
        if not Product.objects.filter(barcode=barcode).exists():
            break
    print('>> bar', barcode)
    try:
        product=Product.objects.create(
            retailer=request.user.retailer_user.retailer,
            # name=name.strip(),
            price=0,
            pr_achat=prachat,
            category=Category.objects.get(pk=category),
            stock=stock,
            car=car,
            minstock=minstock,
            ref=ref,
            originsupp_id=supplier,
            mark=mark,
            entry=entry,
            image=image,
            prices=json.dumps(priceslist),
            supplier_id=supplier,
            expensive=expensive,
            marks=marks,
            barcode=barcode
        )
        if float(prachat) > 0:
            StockIn.objects.create(
                product=product,
                quantity=stock,
            )
        originref=product.ref.split(' ')[0]
        simillar = Product.objects.filter(category=category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
        sim=any([i.stock for i in simillar])
        if sim:
            simillar.update(disponibleinother=True)
            simillar.update(rcommand=False)
        else:
            if int(stock)==0:
                product.command=True
                product.save()
            simillar.update(disponibleinother=False)
            simillar.update(rcommand=True)


        return redirect('product:producthistory', product.id)
    except Exception as e:
        print('>>>', e)
        return redirect('product:addproduct')
    #return a json response without serialaize error data as product is not json serializable
    # return JsonResponse({
    #     'data':{
    #         'name':product.name,
    #         'price':product.price,
    #         'prachat':product.pr_achat,
    #         'brand':product.brand_name,
    #         'stock':product.stock,
    #         'id':product.id
    #     }
    # })

def checkrefupdate(request):
    ref=request.POST.get('ref').lower().split()[0]
    mark=request.POST.get('mark')
    productid=request.POST.get('productid')
    print('product id', productid)
    categoryid=request.POST.get('categoryid')
    product=Product.objects.filter(mark=mark, category=categoryid).exclude(pk=productid).filter(Q(ref__startswith=ref+' ') | Q(ref=ref)).first()

    if product:
        return JsonResponse({
            'status':True,
        })
    else:
        return JsonResponse({
            'status':False,
        })

def checkrefsaisi(request):
    ref=request.POST.get('ref').lower().split()[0]
    categoryid=request.POST.get('categoryid')
    product=Product.objects.filter(category=categoryid).filter(Q(ref__startswith=ref+' ') | Q(ref=ref)).first()

    if product:
        return JsonResponse({
            'status':True,
        })
    else:
        return JsonResponse({
            'status':False,
        })

@csrf_exempt
def updatecategory(request, id):
    name=request.POST.get('categoryname')
    category=Category.objects.get(pk=id)
    category.name=name
    category.save()
    return redirect('product:productslistbycategory')


def validcommande(request):
    product=Product.objects.get(pk=request.POST.get('itemid'))
    originref=product.ref.split()[0]
    simillar = Product.objects.filter(category=product.category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref)).exclude(id=request.POST.get('itemid'))
    print('simm', simillar)

    simillar.update(rcommand=False)
    simillar.update(command=False)
    simillar.update(supplier=None)
    # else:
    #     simillar.update(disponibleinother=False)
    #     simillar.update(rcommand=True)
    product.commanded=True
    product.date_command=timezone.now()
    product.save()
    return JsonResponse({
        'valid':True
    })


# new view to update product from the modals
def updateproduct(request, id):
    # get data from formData sent from the ajax request
    try:
        image = request.FILES.get('updateimage')
        ref = request.POST.get('updateref').strip().lower()
        # name = request.POST.get('name')
        car = request.POST.get('updatecar')
        marks = request.POST.get('updatemarks')
        
        minstock = request.POST.get('updateminimum').strip()
        #price = request.POST.get('updateprice')
        expensive=True if request.POST.get('updateexpensive') == 'oui' else False
        print('>>>>>>>', expensive)
        prachat = request.POST.get('updatepr_achat')
        category=Category.objects.get(pk=request.POST.get('updatecategory'))
        mark = Mark.objects.get(pk=request.POST.get('updatemark'))
        originsupp =Supplier.objects.get(pk=request.POST.get('updateoriginsupp'))
        product=Product.objects.get(pk=id)
        print('pr acha', prachat)
        #product.name=name
        product.ref=ref
        # product.price=price
        product.car=car
        product.mark=mark
        product.marks=marks
        product.expensive=expensive
        product.minstock=minstock
        product.category=category
        product.originsupp=originsupp
        #product.supplier=originsupp
        product.pr_achat=prachat
        if image:
            product.image=image
        product.save()
        originref=product.ref.split(' ')[0]
        simillar = Product.objects.filter(category=product.category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
        sim=any([int(i.stock) for i in simillar])
        print(">>>>sim",originref, sim)
        if sim:
            product.disponibleinother=True
            simillar.update(disponibleinother=True)
            simillar.update(rcommand=False)
            simillar.update(command=False)
        else:
            product.disponibleinother=False
            simillar.update(disponibleinother=False)
            simillar.update(rcommand=True)
        # see if any item in simmilar is alraey in commande, if any commanded the product will not be ready to be commanded
        anycomanded=any([i.command for i in simillar])
        if anycomanded:
            product.rcommand=False
        else:
            product.rcommand=True
        product.save()
        # #return a json response without serialaize error data as product is not json serializable
        return JsonResponse({
            'status': True,
        })
    except Exception as e:
        return JsonResponse({
            'status': False,
            'error': e
        })

# get products based on supplier in commande
def getsupplierproducts(request):
    supplier=Supplier.objects.get(pk=request.POST.get('supplier'))

    products=Product.objects.filter(supplier=supplier)
    return JsonResponse({
        'data':render(request, 'products/setecttagsupply.html', {'products':products, 'len':len(products), 'categories':Category.objects.filter(children__isnull=True), 'id':supplier.id}).content.decode('utf-8')
    })
# new view to add stock from modal
def addstock(request, id):
    try:
        stock = float(request.POST.get('stock'))
        product=Product.objects.get(pk=id)
        StockIn.objects.create(
            product=product,
            quantity=stock,
        )
        #return a json response without serialaize error data as product is not json serializable
        return JsonResponse({
            'status': True,
        })
    except Exception as e:
        return JsonResponse({
            'status': False,
            'error': e
        })

def updatecommande(request):
    product=Product.objects.get(pk=request.POST.get('itemid'))
    supplier=Supplier.objects.get(pk=request.POST.get('supplier'))
    product.supplier=supplier
    product.save()
    print(product, supplier)
    return JsonResponse({
        'success':True
    })
    # return redirect('product:productscommande')


# this to command a product
def commandproduct(request):
    supplier=Supplier.objects.get(pk=request.POST.get('supplier'))
    qty=float(request.POST.get('qty'))
    product=Product.objects.get(pk=request.POST.get('itemid'))
    category=Category.objects.get(pk=request.POST.get('categoryid'))
    product.command=True
    product.supplier=supplier
    product.qtycommand=qty
    product.save()
    originref=product.ref.split(' ')[0]
    simillar = Product.objects.filter(category=category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
    # make all simillare not ready to commande
    simillar.update(rcommand=False)
    sim=any([int(i.stock) for i in simillar])
    if sim:
        simillar.update(disponibleinother=True)
    else:
        simillar.update(disponibleinother=False)

    return JsonResponse({
        'valid':True
    })


# new view for product history
def producthistory(request, id):
    product=Product.objects.get(pk=id)
    pr=StockIn.objects.filter(product=product).order_by('-dated_order')
    stockout=PurchasedProduct.objects.filter(product=product).order_by('-created_at')
    totalin=pr.aggregate(Sum('quantity'))['quantity__sum'] or 0
    totalcost=round(float(totalin)*float(product.pr_achat), 2)
    ctx={ 'title':'Historique Article', 'stockin':pr, 'product':product,  'totalin':totalin, 'totalcost':totalcost, 'netprofit':0}
    if stockout:
        totalamountout=stockout.aggregate(Sum('purchase_amount')).get('purchase_amount__sum')
        ctx.update({
            'stockout':stockout,
            'totalamountout':round(totalamountout, 2),
            'totalout':stockout.aggregate(Sum('quantity')).get('quantity__sum'),
            'netprofit':round(float(totalamountout)-float(totalcost), 2),
            'rest':float(totalin)-float(stockout.aggregate(Sum('quantity')).get('quantity__sum')),
            #'percentage':round(float(stockout.aggregate(Sum('quantity')).get('quantity__sum'))*100/float(totalin)),
        })
    else:
        ctx.update({
            'netprofit':-float(totalcost)
        })
    return render(request, 'products/producthistory.html', ctx)



def reports(request):
    return render(request, 'products/reports.html', {'title':'Rapports'})


def reportnetprofit(request):
    year=this_year if request.POST.get('year')=='0' else request.POST.get('year')
    month=False if request.POST.get('month')=='0' else request.POST.get('month')
    if month:
        totalprofit=round(SalesHistory.objects.filter(
            created_at__year=year, created_at__month=month
            ).aggregate(
            total_revenue=Sum('paid_amount')
        )['total_revenue'] or 0, 2)

        totalcost=round(Product.objects.filter(
            stockin_product__dated_order__year=year, stockin_product__dated_order__month=month
            ).annotate(
                total_items=Sum('stockin_product__quantity')
            ).aggregate(
                total_cost=ExpressionWrapper(Sum(F('pr_achat') * F('total_items'), output_field=DecimalField()), output_field=DecimalField())
            )['total_cost'] or 0, 2)
    else:
        totalprofit=round(SalesHistory.objects.filter(
            created_at__year=year
            ).aggregate(
            total_revenue=Sum('paid_amount')
        )['total_revenue'] or 0, 2)
        totalcost=round(Product.objects.filter(
            stockin_product__dated_order__year=year
            ).annotate(
                total_items=Sum('stockin_product__quantity')
            ).aggregate(
                total_cost=ExpressionWrapper(Sum(F('pr_achat') * F('total_items'), output_field=DecimalField()), output_field=DecimalField())
            )['total_cost'] or 0, 2)




    #for i in products:
        #totalcost+=round(float(i.stock)*float(i.pr_achat), 2)
        # stockout=PurchasedProduct.objects.filter(product=i)
        # if stockout:
        #     for i in stockout:
        #         totalprofit+=i.purchase_amount



    return JsonResponse({
        'totalprofit':totalprofit,
        'totalcost':totalcost,
        'netprofit':round(float(totalprofit)-float(totalcost), 2)
    })


def productsranking(request):
    year=this_year if request.POST.get('year')=='0' else request.POST.get('year')
    month=False if request.POST.get('month')=='0' else request.POST.get('month')
    if month:products = (
    PurchasedProduct.objects.filter(
        created_at__year=year, created_at__month=month
        ).values('product')
    .annotate(
        total_quantity=Sum('quantity'),
        total_purchase_amount=Sum('purchase_amount')
    )
    .order_by('-total_quantity')
    .values('product__ref', 'total_quantity', 'total_purchase_amount')[:10]
    )
    else:
        products = (
    PurchasedProduct.objects.filter(
        created_at__year=year
        ).values('product')
    .annotate(
        total_quantity=Sum('quantity'),
        total_purchase_amount=Sum('purchase_amount')
    )
    .order_by('-total_quantity')
    .values('product__ref', 'product__category__name', 'total_quantity', 'total_purchase_amount')[:10]
    )
    return JsonResponse({
        'data':render(request, 'products/productsranking.html', {'products':products}).content.decode('utf-8')
    })


def downranking(request):
    year=this_year if request.POST.get('year')=='0' else request.POST.get('year')
    month=False if request.POST.get('month')=='0' else request.POST.get('month')
    if month:products = (
    PurchasedProduct.objects.filter(
        created_at__year=year, created_at__month=month
        ).values('product')
    .annotate(
        total_quantity=Sum('quantity'),
        total_purchase_amount=Sum('purchase_amount')
    )
    .order_by('total_quantity')
    .values('product__name', 'total_quantity', 'total_purchase_amount')[:10]
    )

    else:
        products = (
    PurchasedProduct.objects.filter(
        created_at__year=year
        ).values('product')
    .annotate(
        total_quantity=Sum('quantity'),
        total_purchase_amount=Sum('purchase_amount')
    )
    .order_by('total_quantity')
    .values('product__name', 'total_quantity', 'total_purchase_amount')[:10]
    )

    return JsonResponse({
        'data':render(request, 'products/productsranking.html', {'products':products}).content.decode('utf-8')
    })

def relve(request):
    products=request.user.retailer_user.retailer.retailer_product.all()
    return render(request, 'products/relve.html', {'title': 'bilan Stock', 'products':products})


def statsofrelve(request):
    year=this_year if request.POST.get('year')=='0' else request.POST.get('year')
    month=False if request.POST.get('month')=='0' else request.POST.get('month')
    product_data = []
    products=request.user.retailer_user.retailer.retailer_product.all()
    # Loop through each product
    for product in products:
        if month:
        # Get the available and sold items for the product
            totalitems=StockIn.objects.filter(
                product=product, dated_order__year=year, dated_order__month=month
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0
            available_items = product.stock
            sold_items = PurchasedProduct.objects.filter(
                product=product, created_at__year=year, created_at__month=month
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0

            # Calculate the total cost and total profit for the product
            total_cost = round(float(product.pr_achat) * float(totalitems), 2)
            total_profit = PurchasedProduct.objects.filter(
                product=product, created_at__year=year, created_at__month=month
            ).aggregate(Sum('purchase_amount'))['purchase_amount__sum'] or 0

            # Calculate the net profit for the product
            net_profit = round(float(total_profit) - float(total_cost), 2)

            # Add the product data to the list
            product_data.append({
                'id': product.id,
                'name': f'{product.ref} {product.category}',
                'available_items': available_items,
                'sold_items': sold_items,
                'total_profit': total_profit,
                'total_cost': total_cost,
                'net_profit': net_profit,
            })
        else:
            totalitems=StockIn.objects.filter(
                product=product, dated_order__year=year
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0
            available_items = product.stock
            sold_items = PurchasedProduct.objects.filter(
                product=product, created_at__year=year
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0

            # Calculate the total cost and total profit for the product
            total_cost = round(float(product.pr_achat) * float(totalitems), 2)
            total_profit = PurchasedProduct.objects.filter(
                product=product, created_at__year=year
            ).aggregate(Sum('purchase_amount'))['purchase_amount__sum'] or 0

            # Calculate the net profit for the product
            net_profit = round(float(total_profit) - float(total_cost), 2)

            # Add the product data to the list
            product_data.append({
                'id': product.id,
                'name': f'{product.ref} {product.category}',
                'available_items': available_items,
                'sold_items': sold_items,
                'total_profit': total_profit,
                'total_cost': total_cost,
                'net_profit': net_profit,
            })
    sorted_list = sorted(product_data, key=lambda k: k['total_profit'], reverse=True)

    return JsonResponse({
        'data':render(request, 'products/relvestats.html', {"products":sorted_list}).content.decode('utf-8')
    })


def dailystatsstock(request):
    date=request.POST.get('date')
    product_data = []
    products=request.user.retailer_user.retailer.retailer_product.all()
    # Loop through each product
    for product in products:
        # Get the available and sold items for the product
        totalitems=StockIn.objects.filter(
            product=product, dated_order__date=date
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
        available_items = product.stock
        sold_items = PurchasedProduct.objects.filter(
            product=product, created_at__date=date
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0

        # Calculate the total cost and total profit for the product
        total_cost = round(float(product.pr_achat) * float(totalitems), 2)
        total_profit = PurchasedProduct.objects.filter(
            product=product, created_at__date=date
        ).aggregate(Sum('purchase_amount'))['purchase_amount__sum'] or 0

        # Calculate the net profit for the product
        net_profit = round(float(total_profit) - float(total_cost), 2)

        # Add the product data to the list
        product_data.append({
            'id': product.id,
            'name': f'{product.ref} {product.category}',
            'available_items': available_items,
            'sold_items': sold_items,
            'total_profit': total_profit,
            'total_cost': total_cost,
            'net_profit': net_profit,
        })
    sorted_list = sorted(product_data, key=lambda k: k['total_profit'], reverse=True)

    return JsonResponse({
        'data':render(request, 'products/relvestats.html', {"products":sorted_list}).content.decode('utf-8')
    })

def supply(request):
    suppliers=Supplier.objects.all()

    return render(request, 'products/supply.html', {'title':'Recevoir des peoduits', 'suppliers':suppliers})

def addproduct(request):
    cc = Category.objects.filter(children__isnull=True).order_by('name')


    ctx={
        'title':'Ajouter les produits',
        'children':cc,
        'suppliers':Supplier.objects.all(),
        'marks':Mark.objects.all(),
        'reforigin':Reforigin.objects.all()
    }
    return render(request, 'products/add_product.html', ctx)

def addsupply(request):
    print('>>>> test')
    nbon=request.POST.get('nbon')
    items = json.loads(request.POST.get('items'))
    supplier=Supplier.objects.get(pk=request.POST.get('supplier'))
    reciept=Itemsbysupplier.objects.create(supplier=supplier, items=request.POST.get('items'), total=float(request.POST.get('total')), nbon=nbon, rest=float(request.POST.get('total')))
    with transaction.atomic():
        for i in items:
            item=i.get('item_id')
            try:
                product = Product.objects.get(pk=item)
                product.pr_achat=float(i['price'])
                prices=json.loads(product.prices)
                pricefound=False
                for b, p in enumerate(prices):
                    print('>> price, qty supp in addsupply', float(p[0]), float(p[1]),p[2].lower(), supplier.name.lower())
                    if int(float(prices[b][0])) == int(float(i['price'])) and float(prices[b][1])>=0 and prices[b][2].lower()==supplier.name.lower():
                        prices[b][1]=float(prices[b][1])+float(i['qty'])
                        # if qty of this price=0 remove it
                        pricefound=True
                        break
                if not pricefound:
                    prices.append([float(i['price']), float(i['qty']), supplier.name])
                product.prices=json.dumps(prices)
                # if len(prices)==0:
                # else:
                #     found=False
                #     for price in prices:
                #         if float(price[0]) == float(i['price']):
                #             found=True
                #             price[1] =float(price[1])+float(i['qty'])
                #             product.prices=json.dumps(prices)
                #     if found==False:
                #         print('price not found')
                #         prices.append([float(i['price']), float(i['qty']), supplier.name])
                #         product.prices=json.dumps(prices)

                # product.prices=json.dumps(prices)
                product.urgent=False
                product.command=False
                product.panier=False
                if supplier.id != 87:
                    product.originsupp=supplier
                product.supplier=None
                StockIn.objects.create(
                    product=product,
                    quantity=float(i['qty']),
                    price=float(i['price']),
                    reciept=reciept
                )
                product.stock=float(product.stock)+float(i['qty'])
                originref=product.ref.split()[0]
                simillar = Product.objects.filter(category=product.category.id).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
                simillar.update(disponibleinother=True)
                simillar.update(rcommand=False)
                simillar.update(command=False)
                simillar.update(supplier=None)
                # CANCEL COMMAND FOR OTHERS
                simillar.update(commanded=False)
                product.save()
            except Exception as e:
                print(e)
                prices.append([float(i['price']), float(i['qty']), supplier.name])
                product.prices=json.dumps(prices)
                # if len(prices)==0:
                # else:
                #     found=False
                #     for price in prices:
                #         if float(price[0]) == float(i['price']):
                #             found=True
                #             price[1] =float(price[1])+float(i['qty'])
                #             product.prices=json.dumps(prices)
                #     if found==False:
                #         print('price not found')
                #         prices.append([float(i['price']), float(i['qty']), supplier.name])
                #         product.prices=json.dumps(prices)

                # product.prices=json.dumps(prices)
                product.urgent=False
                product.command=False
                product.panier=False
                if supplier.id != 87:
                    product.originsupp=supplier
                product.supplier=None
                StockIn.objects.create(
                    product=product,
                    quantity=float(i['qty']),
                    price=float(i['price']),
                    reciept=reciept
                )
                product.stock=float(product.stock)+float(i['qty'])
                originref=product.ref.split()[0]
                simillar = Product.objects.filter(category=product.category.id).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
                simillar.update(disponibleinother=True)
                simillar.update(rcommand=False)
                simillar.update(command=False)
                simillar.update(supplier=None)
                # CANCEL COMMAND FOR OTHERS
                simillar.update(commanded=False)
                product.save()

    return JsonResponse({
        'status': True,
    })

def bonentree(request, id):
    itemsbysupplier = json.loads(Itemsbysupplier.objects.get(id=id).items)

    return render(request, 'products/bonentree.html', {
        'suppliers':Supplier.objects.all(),
        'items':itemsbysupplier,
        'title':'Details bon entree',
        'bon':Itemsbysupplier.objects.get(id=id),
        'avances':Avancesbon.objects.filter(bon=id)
    })

def bonsentrees(request):
    bb=Itemsbysupplier.objects.all().order_by('-date')
    return render(request, 'products/supplierslist.html', {
        'title':'Liste Bons Fournisseurs',
        'bonslist':bb,
        # bons is true to add condition in template to only use one teplate for suppliers list and bons list
        'bons':True
    })

def supplierslist(request):

    suppliers=Supplier.objects.all()
    supplier_data = []
    for supplier in suppliers:
        rest = Itemsbysupplier.objects.filter(supplier=supplier).aggregate(rest=Sum('rest'))['rest'] or 0
        supplier_data.append({'id':supplier.id, 'name':supplier.name, 'details':supplier.detals, 'rest':rest})
    # order suppliers_data descending by rest
    supplier_data = sorted(supplier_data, key=lambda k: k['rest'], reverse=True)
    return render(request, 'products/supplierslist.html', {
        'title':'Liste Fournisseurs',
        'suppliers':supplier_data
    })

def supplierinfo(request, id):


    supplier=Supplier.objects.get(pk=id)
    bons=Itemsbysupplier.objects.filter(supplier=supplier).order_by('-date')
    return render (request, 'products/supplierinfo.html', {
        'title':supplier.name+' Bons',
        'bons':bons,
        'supplier':supplier
    })

def addpaymentsupplier(request, id):
    amount=request.POST.get('amount')
    details=request.POST.get('details')
    bon=Itemsbysupplier.objects.get(pk=id)
    avances=Avancesbon.objects.filter(bon=bon).aggregate(Sum('avance'))['avance__sum']
    if avances:
        avances=float(avances)+float(amount)
    else:avances=amount
    bon.rest=float(bon.total)-float(avances)
    bon.save()
    Avancesbon.objects.create(
        bon=bon,
        avance=amount,
        details=details,
    )
    #return reverse('product:bonentree', kwargs={'id':bon.id})
    return JsonResponse({
        'rr':'rest'
    })

def addsupplier(request):
    name=request.POST.get('name')
    details=request.POST.get('details')
    Supplier.objects.create(name=name, detals=details)
    return redirect('product:supplierslist')

def editsupp(request):
    supp=Supplier.objects.get(pk=request.POST.get('pid'))

    supp.name=request.POST.get('pname')
    supp.detals=request.POST.get('pdetals')
    supp.save()
    return redirect('product:supplierslist')

def dailystats(request):
    date=request.POST.get('date')
    totalprofit=round(SalesHistory.objects.filter(
            created_at__date=date
            ).aggregate(
            total_revenue=Sum('paid_amount')
        )['total_revenue'] or 0, 2)
    totalcost=round(Product.objects.filter(
            stockin_product__dated_order__date=date
            ).annotate(
                total_items=Sum('stockin_product__quantity')
            ).aggregate(
                total_cost=ExpressionWrapper(Sum(F('pr_achat') * F('total_items'), output_field=DecimalField()), output_field=DecimalField())
            )['total_cost'] or 0, 2)
    return JsonResponse({
        'totalprofit':totalprofit,
        'totalcost':totalcost,
        'netprofit':totalprofit-totalcost
    })

def dailyproductsranking(request):
    date=request.POST.get('date')
    products = (
    PurchasedProduct.objects.filter(
        created_at__date=date
        ).values('product')
    .annotate(
        total_quantity=Sum('quantity'),
        total_purchase_amount=Sum('purchase_amount')
    )
    .order_by('-total_quantity')
    .values('product__ref', 'product__category__name', 'total_quantity', 'total_purchase_amount')
    )
    return JsonResponse({
        'data':render(request, 'products/productsranking.html', {'products':products}).content.decode('utf-8')
    })


def dailyproductsrankingdown(request):
    date=request.POST.get('date')
    products = (
    PurchasedProduct.objects.filter(
        created_at__date=date
        ).values('product')
    .annotate(
        total_quantity=Sum('quantity'),
        total_purchase_amount=Sum('purchase_amount')
    )
    .order_by('-total_quantity')
    .values('product__name', 'total_quantity', 'total_purchase_amount')
    )
    return JsonResponse({
        'data':render(request, 'products/productsranking.html', {'products':products}).content.decode('utf-8')
    })





class ProductItemList(TemplateView):
    template_name = 'products/product_list.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return

        return super(
            ProductItemList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProductItemList, self).get_context_data(**kwargs)
        products = (
            self.request.user.retailer_user.retailer.retailer_product.all()
        )
        context.update({
            'products': products
        })
        return context


class ProductDetailList(TemplateView):
    template_name = 'products/item_details.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))

        return super(
            ProductDetailList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProductDetailList, self).get_context_data(**kwargs)
        try:
            product = (
                self.request.user.retailer_user.retailer.
                retailer_product.get(id=self.kwargs.get('pk'))
            )
        except ObjectDoesNotExist:
            raise Http404('Product not found with concerned User')

        context.update({
            'items_details': product.product_detail.all().order_by(
                '-created_at'),
            'product': product,
        })

        return context


class AddNewProduct(FormView):
    form_class = ProductForm
    template_name = 'products/add_product.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            AddNewProduct, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        product = form.save()

        return HttpResponseRedirect(reverse('product:stock_items_list'))

    def form_invalid(self, form):
        return super(AddNewProduct, self).form_invalid(form)


class AddProductItems(FormView):
    template_name = 'products/add_product_items.html'
    form_class = ProductDetailsForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(AddProductItems, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        product_item_detail = form.save()
        return HttpResponseRedirect(
            reverse('product:item_details', kwargs={
                'pk': product_item_detail.product.id
            })
        )

    def form_invalid(self, form):
        return super(AddProductItems, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(AddProductItems, self).get_context_data(**kwargs)
        try:
            product = (
                self.request.user.retailer_user.retailer.
                retailer_product.get(id=self.kwargs.get('product_id'))
            )
        except ObjectDoesNotExist:
            raise Http404('Product not found with concerned User')

        context.update({
            'product': product
        })
        return context


class PurchasedItems(TemplateView):
    template_name = 'products/purchased_items.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(PurchasedItems, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PurchasedItems, self).get_context_data(**kwargs)
        purchased_product = PurchasedProduct.objects.filter(
            product__retailer=self.request.user.retailer_user.retailer
        ).order_by('-created_at')

        context.update({
            'purchased_products': purchased_product
        })

        return context


class ExtraItemsView(TemplateView):
    template_name = 'products/purchased_extraitems.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(ExtraItemsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ExtraItemsView, self).get_context_data(**kwargs)
        extra_products = ExtraItems.objects.filter(
            retailer=self.request.user.retailer_user.retailer
        )

        context.update({
            'purchased_extra_items': extra_products
        })

        return context


class ClaimedProductFormView(FormView):
    template_name = 'products/claimed_product.html'
    form_class = ClaimedProductForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            ClaimedProductFormView, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def purchased_items_update(claimed_item, claimed_number):
        product = (
            claimed_item.product.product_detail.filter(
                available_item__gte=claimed_number
            ).first()
        )
        product.purchased_item = (
            product.purchased_item - claimed_number
        )
        product.save()

    # def claimed_items_payment(self, claimed_item, amount):
    #     payment_form_kwargs = {
    #         'customer': claimed_item.customer.id,
    #         'retailer': self.request.user.retailer_user.retailer.id,
    #         'amount': amount,
    #         'description': 'Amount Refunded from Claimed'
    #                        ' Item ID (%s)' % claimed_item.id
    #     }
    #     payment_form = PaymentForm(payment_form_kwargs)
    #     if payment_form.is_valid():
    #         payment_form.save()

    def form_valid(self, form):
        claimed_item = form.save()

        # update the purchased product accordingly
        self.purchased_items_update(
            claimed_item=claimed_item,
            claimed_number=int(form.cleaned_data.get('claimed_items'))
        )

        # Doing a payment of claimed amount
        # self.claimed_items_payment(
        #     claimed_item=claimed_item,
        #     amount=form.cleaned_data.get('claimed_amount')
        # )

        return HttpResponseRedirect(reverse('product:items_list'))

    def form_invalid(self, form):
        return super(ClaimedProductFormView, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(
            ClaimedProductFormView, self).get_context_data(**kwargs)

        products = (
            self.request.user.retailer_user.retailer.
            retailer_product.all().order_by('name')
        )
        customers = (
            self.request.user.retailer_user.retailer.
            retailer_customer.all().order_by('customer_name')
        )
        context.update({
            'products': products,
            'customers': customers,
        })

        return context


class ClaimedItemsListView(TemplateView):
    template_name = 'products/claimed_product_list.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            ClaimedItemsListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(
            ClaimedItemsListView, self).get_context_data(**kwargs)
        context.update({
            'claimed_items': ClaimedProduct.objects.all().order_by(
                '-created_at')
        })
        return context


class StockItemList(ListView):
    template_name = 'products/stock_list.html'


    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))

        return super(
            StockItemList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.queryset


    def get_context_data(self, **kwargs):

        context = super(StockItemList, self).get_context_data(**kwargs)
        context.update({
            'search_value_name': self.request.GET.get('name'),
            'title':"Liste des produits",


        })
        return context


class AddStockItems(FormView):
    template_name = 'products/add_stock_item.html'
    form_class = StockDetailsForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(AddStockItems, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        product_item_detail = form.save()
        return HttpResponseRedirect(
             reverse('product:stockin_list', kwargs={'product_id': self.kwargs.get('product_id')})
            # used to reverse to entréé list
            #reverse('index')
        )

    def form_invalid(self, form):
        return super(AddStockItems, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(AddStockItems, self).get_context_data(**kwargs)
        try:
            product = (
                self.request.user.retailer_user.retailer.
                retailer_product.get(id=self.kwargs.get('product_id'))
            )
        except ObjectDoesNotExist:
            raise Http404('Product not found with concerned User')

        context.update({
            'product': product,
            'title':'Ajouter Entrée'
        })
        return context


class StockOutItems(FormView):
    form_class = StockOutForm
    template_name = 'products/stock_out.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(StockOutItems, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        product_item_detail = form.save()
        return HttpResponseRedirect(
            reverse('product:stock_items_list')
        )

    def form_invalid(self, form):
        return super(StockOutItems, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(StockOutItems, self).get_context_data(**kwargs)
        try:
            product = (
                self.request.user.retailer_user.retailer.
                    retailer_product.get(id=self.kwargs.get('product_id'))
            )
        except ObjectDoesNotExist:
            raise Http404('Product not found with concerned User')

        context.update({
            'product': product,
            'title':"Sorties"
        })
        return context


class StockDetailView(TemplateView):
    template_name = 'products/stock_detail.html'

    def get_context_data(self, **kwargs):
        context = super(
            StockDetailView, self).get_context_data(**kwargs)

        try:
            item = Product.objects.get(id=self.kwargs.get('product_id'))
        except StockIn.DoesNotExist:
            return Http404('Item does not exists in database')

        item_stocks_in = item.stockin_product.all()
        item_stocks_out = item.stockout_product.all()

        context.update({
            'item': item,
            'item_stock_in': item_stocks_in.order_by('-dated_order'),
            'item_stock_out': item_stocks_out.order_by('-dated'),
        })

        return context


class StockInListView(ListView):
    template_name = 'products/stockin_list.html'
    paginate_by = 100
    model = StockIn
    ordering = '-id'

    def get_queryset(self):
        queryset = self.queryset
        if not queryset:
            queryset = StockIn.objects.all()

        queryset = queryset.filter(product=self.kwargs.get('product_id'))
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super(StockInListView, self).get_context_data(**kwargs)
        context.update({
            'product': Product.objects.get(id=self.kwargs.get('product_id')),
            'title':'Entrée'
        })
        return context


class StockOutListView(ListView):
    template_name = 'products/stockout_list.html'
    paginate_by = 100
    model = StockOut
    ordering = '-id'

    def get_queryset(self, **kwargs):
        queryset = self.queryset
        if not queryset:
            queryset = StockOut.objects.all()

        queryset = queryset.filter(product=self.kwargs.get('product_id'))
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super(StockOutListView, self).get_context_data(**kwargs)
        context.update({
            'product': Product.objects.get(id=self.kwargs.get('product_id'))
        })
        return context

#this update products
class ProductUpdateView(UpdateView):
    template_name = 'products/update_product.html'
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('index')


class StockInUpdateView(UpdateView):
    template_name = 'products/update_stockin.html'
    model = StockIn
    form_class = StockDetailsForm

    def form_valid(self, form):
        obj = form.save()
        return HttpResponseRedirect(
            reverse('product:stockin_list',
                    kwargs={'product_id': obj.product.id})
        )

    def form_invalid(self, form):
        return super(StockInUpdateView, self).form_invalid(form)


def deleteproduct(request):
    product_id = request.POST.get('id')
    password=request.POST.get('password')
    product = Product.objects.get(id=product_id)
    if password=='803230':
        product.delete()
    return redirect('product:productslistbycategory')

def minimumstock(request):
    products=Product.objects.filter(minstock__gt=0, stock__lte=F('minstock'))
    cc = Category.objects.filter(
    product__in=products
    ).distinct().annotate(
    total_products=Count('product')
    )
    # categories=Category.objects.annotate(product_count=Count('product', filter(product__stock__lte=F('minstock'))).filter(parent__isnull=False))
    return render(request, 'products/minstock.html', {'title':'Minimum Stock', 'categories':cc, 'ids':cc.values_list('id', flat=True),
    'suppliers':Supplier.objects.all()})

def getminbycategory(request):
    category_id = request.POST.get('category')
    #products = Product.objects.filter(category_id=category_id, minstock__gt=0, stock__lte=F('minstock')).order_by('disponibleinother')
    products = Product.objects.filter(
    category_id=category_id, minstock__gt=0, stock__lte=F('minstock')
    ).order_by('ref')

    # Calculate the length of getsimillars for each product and sort the list
    sorted_products = sorted(products, key=lambda p: len(p.getsimillars()))
    suppliers=Supplier.objects.all()
    ctx={
        'products':sorted_products,
        'suppliers':suppliers,
    }
    return JsonResponse({
        'data':render(request, 'products/low_stock.html', ctx).content.decode('utf-8')
    })


def updatemark(request):
    markid=request.POST.get('markid')
    markname=request.POST.get('markname')
    print(markid, markname)
    mark=Mark.objects.get(pk=markid)
    mark.name=markname
    mark.save()
    return redirect('product:marks')

def avoirsupp(request):
    supplierid=request.POST.get('supplierid')
    avoir=request.POST.get('avoir')
    Avoir.objects.create(supplier_id=supplierid, avoir=avoir)
    return JsonResponse({
        'success':True
    })


def deleteavoir(request):
    id=request.GET.get('id')
    Avoir.objects.get(pk=id).delete()
    return JsonResponse({
        'success':True
    })


def addreforigin(request):
    cat=request.GET.get('cat')
    ref=request.GET.get('ref')
    Reforigin.objects.create(category_id=cat, reforigin=ref)
    return JsonResponse({
        'success':True
    })

def removereforigin(request):
    refid=request.GET.get('refid')
    Reforigin.objects.get(pk=refid).delete()
    return JsonResponse({
        'success':True
    })



@csrf_exempt
def searchglobal(request):
    term = request.POST.get('global')

    # Split the term into individual words separated by '*'
    search_terms = term.split('+')
    print(search_terms)
    # Create a list of Q objects for each search term and combine them with &
    q_objects = Q()
    for term in search_terms:
        if term:
            q_objects &= (Q(ref__iregex=term) | Q(category__name__iregex=term) | Q(car__iregex=term) | Q(mark__name__iregex=term)| Q(supplier__name__iregex=term))

    products = Product.objects.filter(q_objects).order_by('-stock')

    return JsonResponse({
        'data': render(request, 'products/product_search.html', 
                       {'products': products,
                        'marks':Mark.objects.all(),
                        'suppliers':Supplier.objects.all(),
                        'home': True}).content.decode('utf-8')
    })

def searchproduct(request):
    term = request.GET.get('term').strip()
    print(term)
    # regex_search_term = term.replace('*', '.*')

    # Split the term into individual words separated by '*'
    search_terms = term.split('+')

    # Create a list of Q objects for each search term and combine them with &
    q_objects = Q()
    for term in search_terms:
        if term:
            q_objects &= (Q(ref__iregex=term) | Q(car__iregex=term))

    products = Product.objects.filter(q_objects)
    results=[]
    for i in products:
        results.append({
            'id':f'{i.ref},{i.car},{i.pr_achat},{i.stock},{i.id}',
            'text':f'{i.ref} - {i.car}'
        })
    return JsonResponse({'results': results})
def createbon(request):
    datebon=request.POST.get('date')
    print('>>>>>', datebon)
    datebon=datetime.strptime(datebon, '%Y-%m-%d')
    total=request.POST.get('total')
    customer=request.POST.get('customer')
    items=json.loads(request.POST.get('items'))
    retailer=request.user.retailer_user.retailer
    print('>>>>>', datebon)
    #create invoice
    invoice=SalesHistory.objects.create(retailer=retailer, grand_total=total, date=datebon, customer_id=customer)
    # add total to caisse
    #create outproducts
    # todo: when contoir, we dont need to reduse qty from stock, it(s already done)
    purchased_items_id = []
    with transaction.atomic():
        for item in items:
            
            purchased=PurchasedProduct.objects.create(
                quantity=item.get('qty'),
                article=item.get('article'),
                price=item.get('price'),
                purchase_amount=item.get('total'),
                invoice=invoice
            )
            purchased_items_id.append(purchased.id)
    invoice.purchased_items.set(purchased_items_id)
    return JsonResponse({
        'success':True
    })
def factureview(request):
    ctx={
        'title':'+Facture',
        'today':today,
        'customers':Customer.objects.all()
    }
    return render(request, 'products/createfacture.html', ctx)
# def getcategoryname(request):
#     termlower=request.GET.get('term').lower()
#     termupper=request.GET.get('term').upper()
#     pass


def deviseview(request):
    ctx={
        'title':'+Devise',
        'today':today,
        'customers':Customer.objects.all()
    }
    return render(request, 'products/createdevise.html', ctx)
def createfacture(request):
    number=''
    year_month = timezone.now().strftime("%y")
    latest_receipt = Facture.objects.filter(
        facture_no__startswith=f"FC{year_month}"
    ).last()
    if latest_receipt:
        facture_no = int(latest_receipt.facture_no[-6:])
        number = f"FC{year_month}{facture_no + 1:06}"
    else:
        number = f"FC{year_month}000001"
    print('>>>number', number)
    datebon=request.POST.get('date')
    print('>>>>>', datebon)
    datebon=datetime.strptime(datebon, '%Y-%m-%d')
    total=request.POST.get('total')
    manualswitch=request.POST.get('manualswitch')=='true'
    customer=request.POST.get('customer')
    items=json.loads(request.POST.get('items'))
    print('>>>>>', datebon)
    #create invoice
    facture=Facture.objects.create(total=total, date=datebon, client_id=customer, facture_no=number, ismanual=manualswitch)
    # add total to caisse
    #create outproducts
    # todo: when contoir, we dont need to reduse qty from stock, it(s already done)
    with transaction.atomic():
        for item in items:
            Factureitems.objects.create(
                qty=item.get('qty'),
                article=item.get('article'),
                price=item.get('price'),
                total=item.get('total'),
                mtrc=item.get('mtrc'),
                bc=item.get('bc'),
                bl=item.get('bl'),
                facture=facture
            )
    return JsonResponse({
        'success':True
    })

def createreleve(request):
    datefrom=request.POST.get('datefrom')
    dateto=request.POST.get('dateto')
    datefrom=datetime.strptime(datefrom, '%Y-%m-%d')
    dateto=datetime.strptime(dateto, '%Y-%m-%d')
    total=request.POST.get('total')
    customer=request.POST.get('customer')
    items=json.loads(request.POST.get('items'))
    #create invoice
    releve=Releve.objects.create(total=total, datefrom=datefrom, dateto=dateto, client_id=customer)
    releve.facture_no=f'RLV00{releve.id}'
    releve.save()
    # add total to caisse
    #create outproducts
    # todo: when contoir, we dont need to reduse qty from stock, it(s already done)
    print('>> items', items)
    with transaction.atomic():
        for item in items:
            Releveitems.objects.create(
                date=item.get('datefacture'),
                facture=item.get('article'),
                total=item.get('totalfacture'),
                releve=releve
            )
    return JsonResponse({
        'success':True
    })


def updatereleve(request):
    datefrom=request.POST.get('datefrom')
    id=request.POST.get('id')
    dateto=request.POST.get('dateto')
    datefrom=datetime.strptime(datefrom, '%Y-%m-%d')
    dateto=datetime.strptime(dateto, '%Y-%m-%d')
    total=request.POST.get('total')
    customer=request.POST.get('customer')
    items=json.loads(request.POST.get('items'))
    print('>>id', id)
    releve=Releve.objects.get(pk=id)
    releveitems=Releveitems.objects.filter(releve=releve)
    releveitems.delete()
    releve.total=total
    releve.datefrom=datefrom
    releve.dateto=dateto
    releve.client_id=customer
    releve.save()
    # add total to caisse
    #create outproducts
    # todo: when contoir, we dont need to reduse qty from stock, it(s already done)
    print('>> items', items)
    with transaction.atomic():
        for item in items:
            Releveitems.objects.create(
                date=item.get('datefacture'),
                facture=item.get('article'),
                total=item.get('totalfacture'),
                releve=releve
            )
    return JsonResponse({
        'success':True
    })
def reglefacture(request):
    id=request.GET.get('id')
    note=request.GET.get('note')
    facture=Facture.objects.get(pk=id)
    facture.note=note
    facture.ispaid=True
    facture.save()
    return JsonResponse({
        'success':True
    })
def modifierdevi(request):
    devi=Devise.objects.get(pk=request.GET.get('id'))
    items=Deviseitems.objects.filter(devise=devi)
    ctx={
        'devi':devi,
        'items':items,
        'customers':Customer.objects.all(),
        'title':f'Modifier Devi N° {devi.Devise_no}'
    }
    return render(request, 'products/modifierdevi.html', ctx)

def deletedevi(request):
    devi=Devise.objects.get(pk=request.GET.get('id'))
    items=Deviseitems.objects.filter(devise=devi)
    devi.delete()
    items.delete()
    return redirect('product:listdevises')

def updatefacture(request):
    datebon=request.POST.get('date')
    datebon=datetime.strptime(datebon, '%Y-%m-%d')
    total=request.POST.get('total')
    note=request.POST.get('note')
    factureid=request.POST.get('factureid')
    manualswitch=request.POST.get('manualswitch')=='true'
    facture=Facture.objects.get(pk=factureid)
    customer=request.POST.get('customer')
    items=json.loads(request.POST.get('items'))
    print('>>>>>', datebon)
    #create invoice
    facture.total=total
    facture.note=note
    facture.ismanual=manualswitch
    facture.date=datebon
    facture.client_id=customer
    facture.save()
    print(facture, facture.id)
    #delete old items
    olditems=Factureitems.objects.filter(facture=facture)
    olditems.delete()
    # add total to caisse
    #create outproducts
    # todo: when contoir, we dont need to reduse qty from stock, it(s already done)
    with transaction.atomic():
        for item in items:
            Factureitems.objects.create(
                qty=item.get('qty'),
                article=item.get('article'),
                price=item.get('price'),
                total=item.get('total'),
                mtrc=item.get('mtrc'),
                bc=item.get('bc'),
                bl=item.get('bl'),
                facture=facture
            )
    return JsonResponse({
        'success':True
    })

def updatedevi(request):
    datebon=request.POST.get('date')
    datebon=datetime.strptime(datebon, '%Y-%m-%d')
    total=request.POST.get('total')
    deviid=request.POST.get('deviid')
    devi=Devise.objects.get(pk=deviid)
    customer=request.POST.get('customer')
    items=json.loads(request.POST.get('items'))
    print('>>>>>', datebon)
    #create invoice
    devi.total=total
    devi.date=datebon
    devi.client_id=customer
    devi.save()
    print(devi, devi.id)
    #delete old items
    olditems=Deviseitems.objects.filter(devise=devi)
    olditems.delete()
    # add total to caisse
    #create outproducts
    # todo: when contoir, we dont need to reduse qty from stock, it(s already done)
    with transaction.atomic():
        for item in items:
            Deviseitems.objects.create(
                qty=item.get('qty'),
                article=item.get('article'),
                price=item.get('price'),
                total=item.get('total'),
                devise=devi
            )
    return JsonResponse({
        'success':True
    })



def modifierfacture(request):
    id=request.GET.get('id')
    facture=Facture.objects.get(pk=id)
    items=Factureitems.objects.filter(facture=facture).order_by('id')
    ctx={
        'facture':facture,
        'items':items,
        'customers':Customer.objects.all(),
        'title':f'Modifier facture N° {facture.facture_no}'
    }
    return render(request, 'products/modifierfacture.html', ctx)

def modifierreleve(request):
    id=request.GET.get('id')
    releve=Releve.objects.get(pk=id)
    items=Releveitems.objects.filter(releve=releve)
    ctx={
        'releve':releve,
        'items':items,
        'customers':Customer.objects.all(),
        'title':f'Modifier relve client {releve.client.customer_name}'
    }
    return render(request, 'products/modifierreleve.html', ctx)

def createdevise(request):
    datebon=request.POST.get('date')
    print('>>>>>', datebon)
    datebon=datetime.strptime(datebon, '%Y-%m-%d')
    total=request.POST.get('total')
    customer=request.POST.get('customer')
    items=json.loads(request.POST.get('items'))
    print('>>>>>', datebon)
    #create invoice
    devise=Devise.objects.create(total=total, date=datebon, client_id=customer)
    # add total to caisse
    #create outproducts
    # todo: when contoir, we dont need to reduse qty from stock, it(s already done)
    with transaction.atomic():
        for item in items:
            
            Deviseitems.objects.create(
                qty=item.get('qty'),
                article=item.get('article'),
                price=item.get('price'),
                total=item.get('total'),
                devise=devise
            )
    return JsonResponse({
        'success':True
    })

def facturedetails(request, id):
    facture=Facture.objects.get(pk=id)
    items=Factureitems.objects.filter(facture=facture).order_by('-id')
    ctx={
        'facture':facture,
        'items':items
    }
    return render(request, 'products/facturedetails.html', ctx)
def facturedetails1(request, id):
    facture=Facture.objects.get(pk=id)
    items=Factureitems.objects.filter(facture=facture).order_by('id')
    ctx={
        'facture':facture,
        'items':items,
        'bl':True,
    }
    return render(request, 'products/facturedetails.html', ctx)
def facturedetails2(request, id):
    facture=Facture.objects.get(pk=id)
    items=Factureitems.objects.filter(facture=facture).order_by('id')
    ctx={
        'facture':facture,
        'items':items,
        'bl':True,
        'bc':True,
    }
    return render(request, 'products/facturedetails.html', ctx)
def facturedetails3(request, id):
    facture=Facture.objects.get(pk=id)
    items=Factureitems.objects.filter(facture=facture).order_by('id')
    ctx={
        'facture':facture,
        'items':items,
        'bl':True,
        'bc':True,
        'mtrc':True
    }
    return render(request, 'products/facturedetails.html', ctx)

def devisedetails(request, id):
    devise=Devise.objects.get(pk=id)
    items=Deviseitems.objects.filter(devise=devise)
    ctx={
        'devise':devise,
        'items':items
    }
    return render(request, 'products/devisedetails.html', ctx)

def listfacturesnonpaye(request):
    factures=Facture.objects.filter(ispaid=False, ismanual=False).order_by('-facture_no')
    return render(request, 'products/listfactures.html', {'factures':factures, 'title':'list facture non reglé'})
def listfacturespaye(request):
    factures=Facture.objects.filter(ispaid=True, ismanual=False).order_by('-facture_no')
    return render(request, 'products/listfactures.html', {'factures':factures, 'title':'list facture reglé'})
def listfacturesmanual(request):
    factures=Facture.objects.filter(ismanual=True).order_by('-facture_no')
    return render(request, 'products/listfactures.html', {'factures':factures, 'title':'list facture Entreprise'})
def listdevises(request):
    devises=Devise.objects.order_by('-Devise_no')
    return render(request, 'products/listdevises.html', {'devises':devises})

def editfacture(request, id):
    facture=Facture.objects.get(pk=id)
    return JsonResponse({
        'success':True
    })

def addfactureitem(request):
    factureid=request.GET.get('factureid')
    qty=request.GET.get('qty')
    price=request.GET.get('price')
    total=request.GET.get('total')
    bl=request.GET.get('bl')
    bc=request.GET.get('bc')
    mtrc=request.GET.get('mtrc')
    article=request.GET.get('article')
    facture=Facture.objects.get(pk=factureid)
    facture.total=float(facture.total)+float(total)
    facture.save()
    Factureitems.objects.create(facture=facture, qty=qty, article=article, bl=bl, bc=bc, mtrc=mtrc, total=total, price=price)
    print(factureid, qty, price, total, bl, bc, mtrc, article)
    return JsonResponse({
        'success':True
    })

def loadpdctsinstock(request):
    page=int(request.GET.get('page', 1))
    categoryid=request.GET.get('categoryid')
    perpage=50
    start=perpage*(page-1)
    end=perpage*page
    print('>>>>>>>>',page, start, end, categoryid=='0')
    if categoryid=='0':
        perpage=10000
        start=perpage*(page-1)
        end=perpage*page
        products=Product.objects.all()[start:end]  
    else:
        products=Product.objects.filter(category_id=categoryid)[start:end]   
    ctx={
        'products':products,
        'home':False,
        'marks':Mark.objects.all()
    }
    return JsonResponse({
        'trs':render(request, 'products/product_search.html', ctx).content.decode('utf-8'),
        'has_more':len(products)==perpage
    })

def panier(request):
    itemid=request.GET.get('itemid')
    print('>>> itemid', itemid)
    product=Product.objects.get(pk=itemid)
    if product.panier:
        return JsonResponse({
        'success':False
    })
    product.panier=True
    product.save()
    print('>> product', product.panier)
    return JsonResponse({
        'success':True
    })

import random
def generate_unique_7_digit_barcode():
    while True:
        # Generate a random 7-digit number
        barcode = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        
        # Check for uniqueness
        if not Product.objects.filter(barcode=barcode).exists():
            return barcode



def assignbarcode(request):
    # products=Product.objects.filter(barcode='-')
    # print('>>>>', products.count())
    # for i in products:
    #     i.barcode=generate_unique_7_digit_barcode()
    #     i.save()
    return JsonResponse({
        'ee':'ee'
    })


def generate_barcode(request, code):
    # Ensure the code parameter is valid (for example, non-empty and within allowed characters)
    if not code:
        return HttpResponse("Invalid code", status=400)
    
    # # Example: Generate a Code128 barcode
    # code_class = barcode.get_barcode_class('ean8')
    # barcode_instance = code_class(code, writer=ImageWriter())
    
    # # Create a BytesIO buffer
    # buffer = BytesIO()
    
    # # Write the barcode to the buffer
    # barcode_instance.write(buffer)
    
    # # Create an HttpResponse object with image content type
    # response = HttpResponse(buffer.getvalue(), content_type='image/png')
    # response['Content-Disposition'] = f'inline; filename="barcode_{code}.png"'
    
    # return response
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR Code (1 = smallest)
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,  # Size of each box in the QR code grid
        border=4,  # Minimum border size
    )
    qr.add_data(code)  # Add the code data
    qr.make(fit=True)

    # Create an image from the QR Code
    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image to a BytesIO buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    # Return the image in the response
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="qr_code_{code}.png"'
    
    return response
def sorticontoir(request):
    
    ctx={
        'title':'Bon Sortie comptoir',
        'present_date': timezone.now().date(),
        'children':Category.objects.filter(children__isnull=True).order_by('name'),
        'marks':Mark.objects.all()
    }
    return render(request, 'products/sorticontoir.html', ctx)

def updatestockcontoir(request):
    productid=request.GET.get('productid')
    outid=request.GET.get('outid')
    price=request.GET.get('price')
    print('>>price', price)
    product=Product.objects.get(pk=productid)
    increase=True if request.GET.get('increase')=='true' else False
    print(increase)
    if increase:
        
        
        prices=json.loads(product.prices)
        for b, p in enumerate(prices):
            if int(float(p[0])) == int(float(price)):
                print('>>price', p[0])
                news=float(prices[b][1])+1
                # if news==0:
                #     prices.pop(b)
                #     product.prices=json.dumps(prices)
                # else:
                #     prices[b][1] =float(prices[b][1])-float(qty)
                #     product.prices=json.dumps(prices)
                #     break
                # if float(prices[b][1])!=0:
                prices[b][1] =float(prices[b][1])+1
                product.prices=json.dumps(prices)
                break
        product.stock+=1
        product.save()
        print('>> delet', PurchasedProduct.objects.get(pk=outid))
        PurchasedProduct.objects.get(pk=outid).delete()
        return JsonResponse({
            'success':True
        })
    product.stock-=1
    product.save()
    
    return JsonResponse({
        'success':True
    })
        
# thuis is the scanner
def scanproductdata(request):
    # barcode=request.GET.get('barcode')[:7]
    barcode=request.GET.get('barcode').lower().replace('shift', '')
    print('>> barcode', barcode)
    code=barcode.split('q')[0]
    price=barcode.split('q')[1]
    print('<>>code', code, price)
    product=Product.objects.get(barcode=code)
    print('<<>>', product.stock, float(product.stock)==0.00)
    # STOP IF THERE IS NO STOCK
    if float(product.stock)==0.00:
        return JsonResponse({
            'success':False,
            'message':'Zero stock'
        })
    
    # if float(product.stock)==0:
    #     # 
    #     print('stock is null')
    #     return JsonResponse({
    #         'success':False,
    #         'ref':product.ref,
    #         'car':product.car,
    #         'image':product.image.url if product.image else '',
    #         'mark':product.mark.name if product.mark else '',
    #         'total':product.pr_achat,
    #         'price':price,
    #         'stock':product.stock,
    #         'id':product.id,
    #     })
    #else:
    prices=json.loads(product.prices)
    new_prices = []
    found=False
    for b, p in enumerate(prices):
        if int(float(p[0])) == int(float(price)) and float(prices[b][1])>0:
            prices[b][1] =float(prices[b][1])-1
            found=True
            break
            print('>>price', p[0])
            news=float(prices[b][1])-1
            # if news<=0:
            #     return JsonResponse({
            #         'success':False,
            #         'message':'Prix zero stock'
            #     })
            # else:
            #     prices[b][1] =float(prices[b][1])-float(qty)
            #     product.prices=json.dumps(prices)
            #     break
            # if float(prices[b][1])!=0:
    if not found:
        return JsonResponse({
            'success':False,
            'message':'Zero stock prix'
        })
    product.prices=json.dumps(prices)       
    product.stock-=1
    product.save()
    out=PurchasedProduct.objects.create(product=product, quantity=1, price=price)
    newstock=product.stock
    if newstock==0 or newstock <= product.minstock:
        # supplier=product.originsupp
        # if supplier.id in [52, 91, 96]:
        #     product.supplier=supplier
        #     product.save()
        originref=product.ref.split(' ')[0]
        simillar = Product.objects.filter(category=product.category).filter(Q(ref__startswith=originref+' ') | Q(ref=originref)).exclude(pk=product.id)
        print(simillar)
        sim=any([int(i.stock) for i in simillar])
        if sim:
            print('>>>>>>disinother')

            simillar.update(disponibleinother=True)
            simillar.update(rcommand=False)
            product.command=False
            product.commanded=False
            product.supplier=product.originsupp
            product.save()
        else:
            print('>>>>>>>not disinother')
            simillar.update(disponibleinother=False)
            simillar.update(rcommand=True)
            product.command=True
            product.commanded=False
            product.supplier=product.originsupp
            product.save()
    return JsonResponse({
        'success':True,
        'ref':product.ref,
        'car':product.car,
        'image':product.image.url if product.image else '',
        'mark':product.mark.name if product.mark else '',
        'total':product.pr_achat,
        'price':price,
        'stock':product.stock,
        'id':product.id,
        'out_id':out.id
    })
@csrf_exempt
def sortiecomptoir(request):
    datebon=request.POST.get('datebon')
    datebon=datetime.strptime(datebon, '%Y-%m-%d')
    total=request.POST.get('total')
    items=json.loads(request.POST.get('items'))
    print(datebon, total, items)
    retailer=request.user.retailer_user.retailer
    #create invoice
    invoice=SalesHistory.objects.create(retailer=retailer, grand_total=total)
    # add total to caisse
    
    #create outproducts
    # todo: when contoir, we dont need to reduse qty from stock, it(s already done)
    purchased_items_id = []
    with transaction.atomic():
        for item in items:
            try:
                product = Product.objects.get(
                    pk=item.get('item_id'),
                )
                purchased=PurchasedProduct.objects.create(
                    product=product,
                    quantity=item.get('qty'),
                    price=item.get('pr_achat'),
                    purchase_amount=item.get('total'),
                    invoice=invoice


                )
                #purchased_items_id.append(purchased.id)
            except:
                pass
    #invoice.purchased_items.set(purchased_items_id)
    return JsonResponse({
        'success':True
    })
def deleteinfacture(request):
    id=request.GET.get('id')
    print('>> id', id)
    invoice=Facture.objects.get(pk=id)
    # if float(invoice.total_quantity)>0:
    #     return redirect('sales:invoice_update', invoice.id)
    # else:
    # pp=PurchasedProduct.objects.filter(
    #     invoice__id=invoice.id)
    # for i in pp:
    #     product=Product.objects.get(id=i.product.id)
    #     product.stock=float(product.stock)+float(i.quantity)
    #     product.save()
    # StockOut.objects.filter(
    #     invoice__id=invoice.id).delete()
    # Ledger.objects.filter(
    #     invoice__id=invoice.id).delete()
    invoice.delete()
    return HttpResponseRedirect(reverse('product:listfactures'))


def updateclientname(request):
    name=request.GET.get('name')
    clientid=request.GET.get('clientid')
    client=Customer.objects.get(pk=clientid)
    client.customer_name=name
    client.save()
    return JsonResponse({
        'success':True
    })

def updateclientice(request):
    ice=request.GET.get('ice')
    clientid=request.GET.get('clientid')
    client=Customer.objects.get(pk=clientid)
    client.ice=ice
    client.save()
    return JsonResponse({
        'success':True
    })

def updateclientphone(request):
    phone=request.GET.get('phone')
    clientid=request.GET.get('clientid')
    client=Customer.objects.get(pk=clientid)
    client.customer_phone=phone
    client.save()
    return JsonResponse({
        'success':True
    })


def relveview(request):
    ctx={
        'title':'+releve',
        'today':today,
        'customers':Customer.objects.all()
    }
    return render(request, 'products/createreleve.html', ctx)

def listreleve(request):
    releve=Releve.objects.all().order_by('-id')
    return render(request, 'products/listreleve.html', {'releve':releve})

def releveprint(request):
    id=request.GET.get('id')
    releve=Releve.objects.get(pk=id)
    releveitems=Releveitems.objects.filter(releve=releve).order_by('-id')
    # releve=Releve.objects.get()
    return render(request, 'products/releveprint.html', {'releve':releve, 'items':releveitems})

def addpdct(request):
    with open('pdcts.json', "r") as json_file:
        factureitems_data = json.load(json_file)
    factureitems = []
    for item_data in factureitems_data:
        facture_item = Factureitems(
            id=item_data["id"],  # Explicitly set the ID
            article=item_data.get("article", ""),
            qty=item_data.get("qty", 0),
            price=item_data.get("price", 0.0),
            total=item_data.get("total", 0.0),
            bc=item_data.get("bc", ""),
            bl=item_data.get("bl", ""),
            mtrc=item_data.get("mtrc", ""),
            facture_id=item_data.get("facture_id", None),  # Ensure this matches your foreign key structure
        )
        factureitems.append(facture_item)

    # Bulk insert facture items

    # Bulk insert products
    print('>>> creating bulk')
    Factureitems.objects.bulk_create(factureitems, ignore_conflicts=True)

    print(f"Imported {len(factureitems)} products.")
    return JsonResponse({
        'success':True
    })

def removefromcart(request):
    id=request.GET.get('id')
    product=Product.objects.get(pk=id)
    product.panier=False
    product.save()
    return JsonResponse({
        'success':True
    })



def pp(request):
    products = Product.objects.select_related('category', 'mark').all()

    data = []
    count=1
    for product in products:
        print(">> count", count)
        data.append({
            "id": product.id,
            "ref": product.ref,
            "name": product.name,
            "price": float(product.price) if product.price is not None else None,
            "car": product.car,
            "category": product.category.name if product.category else None,
            "mark": product.mark.name if product.mark else None,
            "image": product.image.name if product.image else None,
        })
        count+=1

    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="products.json"'
    return response

import json, ast
def zz(request):
    data=[]
    [["99.00", 2.0, "COPIMA"], ["99.00", 8, "izejze"]]
    for item in Product.objects.all():
        prices=json.loads(item.prices)

        qties = 0
        for i in prices:
            if item.stock == 0:
                item.prices=[]
                item.save()
            if float(i[1]) < 0:
                data.append([item.id, qties, item.stock])
            qties+=float(i[1])
        if qties != item.stock:
            data.append([item.id, qties, item.stock])
                
    return JsonResponse({
        'data':data
    })

def printeffet(request):
    amount=request.GET.get('amount')
    return render(request, 'products/printeffet.html', {'amount':amount})

def getfacturedate(request):
    facturenumber=request.GET.get('facturenumber')
    facture=Facture.objects.get(facture_no=facturenumber)
    return JsonResponse({
        'date':facture.date,
        'total':facture.total,
    })


def reglerelve(request):
    id=request.GET.get('id')
    relve=Releve.objects.get(pk=id)
    relve.ispaid=True
    relve.save()
    return redirect('product:listreleve')

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def searchfacture(request):
    word = request.GET.get('word', '').strip()
    target = request.GET.get('target', '').strip()
    print('>> type', type(word))

    filters = (
        Q(client__customer_name__icontains=word) |
        Q(facture_no__icontains=word) |
        Q(note__icontains=word) |
        Q(factureitems__article__icontains=word) |
        Q(factureitems__bl__icontains=word) |
        Q(factureitems__bc__icontains=word) |
        Q(factureitems__mtrc__icontains=word)
    )
    print('taraget === ', target)
    
    # Only add numeric fields if word is a number
    if is_number(word):
        filters |= (
            Q(total=word) 
        )
    print('filters>>', filters)
    factures = Facture.objects.filter(filters)
    if target == 'listfacturesnonpaye':
        factures = factures.filter(ismanual=False,ispaid=False).distinct()
    elif target == 'listfacturespaye':
        factures = factures.filter(ispaid=True).distinct()
    else:
        factures = factures.filter(ismanual=True).distinct()
    print('factures', [facture.facture_no for facture in factures])
    return JsonResponse({
        'html': render(request, 'products/facturetrs.html', {'factures': factures}).content.decode('utf-8')
    })
    # Return your results (e.g. as JSON or to a template)
    # For example:
def searchcompta(request):
    return render(request, 'products/searchcompta.html')
def searchcomptaresult(request):
    word = request.GET.get('word', '').strip()
    facturefilters = (
        Q(client__customer_name__icontains=word) |
        Q(facture_no__icontains=word) |
        Q(note__icontains=word) |
        Q(factureitems__article__icontains=word) |
        Q(factureitems__bl__icontains=word) |
        Q(factureitems__bc__icontains=word) |
        Q(factureitems__mtrc__icontains=word)
    )
    relevefilters = (
        Q(client__customer_name__icontains=word) |
        Q(facture_no__icontains=word) 
    )
    devisfilters = (
        Q(client__customer_name__icontains=word) |
        Q(Devise_no__icontains=word)
    )
    
    # Only add numeric fields if word is a number
    if is_number(word):
        facturefilters |= (
            Q(total=word) 
        )
        devisfilters |= (
            Q(total=word) 
        )
        relevefilters |= (
            Q(total=word) 
        )
    factures = Facture.objects.filter(facturefilters)
    devis = Devise.objects.filter(devisfilters)
    releves = Releve.objects.filter(relevefilters)
    return JsonResponse({
        'html': render(request, 'products/searchcomptatrs.html', {'factures': factures, 'devis':devis, 'releves':releves}).content.decode('utf-8')
    })
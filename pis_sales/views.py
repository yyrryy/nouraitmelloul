# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, View, TemplateView, ListView
from django.utils import timezone
from django.urls import reverse
from pis_product.models import Product, PurchasedProduct, StockOut
from pis_sales.models import SalesHistory
from pis_product.forms import PurchasedProductForm
from pis_sales.forms import BillingForm
from pis_product.forms import ExtraItemForm, StockOutForm
from pis_com.forms import CustomerForm
from pis_ledger.models import Ledger
from pis_ledger.forms import LedgerForm
from django.db import transaction
from pis_com.models import Customer
import os
from pis_product.models import PurchasedProduct
from django.conf import settings
from django.shortcuts import redirect
# with open(settings.MEDIA_ROOT+'/logo.png', 'rb') as f:
#     logo=Image.open(f)
from django.shortcuts import render
logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')


def facture(request, pk):
    inv=SalesHistory.objects.get(id=pk)
    return render(request, 'sales/facture.html', {'inv':inv, 'tva':round(float(inv.grand_total)*0.2, 2), 'totalttc':round(float(inv.grand_total)*1.2, 2)})
    # buffer = BytesIO()

    # # Create the PDF object, using the buffer as its "file."
    # p = canvas.Canvas(buffer)
    # # make it A4 size
    # p.setPageSize(A4)
    # p.setTitle(f"Facture: {inv.receipt_no} ")
    # # write 'Vita drogerie' on the top left corner
    # p.drawImage(logo_path, 10, 700, 150, 150)
    # #p.drawString(15, 770, 'LOGO')
    # #write 'Client' on the top right corner
    # p.setFont("Helvetica", 11)

    # p.drawString(30, 725, 'test address')
    # p.drawString(30, 710, 'ville ')
    # p.drawString(30, 695, '06 55 55 55 55')
    # p.drawString(420, 800, f"Facture: {inv.receipt_no}")
    # # write 'Address' on the top left corner
    # p.drawString(420, 785, f"Date: {datetime.strftime(inv.created_at, '%d/%m/%Y')} ")
    # p.drawString(420, 720, f"Client: {inv.customer.customer_name} ")
    # p.drawString(420, 705, f"ICE: {inv.customer.address} ")

    # # drow a line
    # # write business name at the bottom
    # # reduce the font size of the code bellow
    # # write 'rrerr' with small font size at the bottom
    # p.setFont("Helvetica", 8)
    # p.drawString(30, 660, 'Article')
    # p.line(30-2, 667, 30-2, 655)
    # p.drawString(350, 660, 'Qté')
    # p.line(350-2, 667, 350-2, 655)
    # p.drawString(420, 660, 'Prix unt.')
    # p.line(420-2, 667, 420-2, 655)
    # p.drawString(490, 660, 'Total')
    # p.line(490-2, 667, 490-2, 655)
    # p.line(30-2, 655, 550, 655)
    # p.setFont("Helvetica", 8)
    # n=640
    # for i in purchased:
    #     p.drawString(30, n, i.product.name)
    #     p.line(30-2, 655, 30-2, n-5)
    #     p.drawString(350, n, str(i.quantity))
    #     p.line(350-2, 655, 350-2, n-5)
    #     p.drawString(420, n, str(i.price))
    #     p.line(420-2, 655, 420-2, n-5)
    #     p.drawString(490, n, str(i.purchase_amount))
    #     p.line(490-2, 655, 490-2, n-5)
    #     p.line(30-2, n-5, 550, n-5)
    #     n-=15
    # p.drawString(420, n-15, 'Total HT')
    # p.drawString(490, n-15, str(inv.grand_total))
    # p.line(420, n-20, 550, n-20)
    # p.drawString(420, n-30, 'TVA 20%')
    # p.drawString(490, n-30, str(round(float(inv.grand_total)*0.2, 2)))
    # p.line(420, n-35, 550, n-35)
    # p.drawString(420, n-45, 'TTC')
    # p.drawString(490, n-45, str(round(float(inv.grand_total)*1.2, 2)))
    # p.line(30, 120, 550, 120)
    # p.drawString(30, 100, "Siege social: test address - Biougra")
    # p.drawString(30, 85, "RC: 25937 Taxe professionnelle: 48802831 IF: 52414131 ICE: 003030506000009")
    










    # # # Close the PDF object cleanly, and we're done.
    # p.showPage()
    # p.save()

    # # # FileResponse sets the Content-Disposition header so that browsers
    # # # present the option to save the file.
    # buffer.seek(0)
    # # # return the pdf with intaitle
    
    # return FileResponse(buffer, as_attachment=True, filename=f'facture{inv.receipt_no}.pdf')


def bon(request, pk):

    inv=SalesHistory.objects.get(id=pk)
    items=PurchasedProduct.objects.filter(invoice=inv)
    return render(request, 'sales/bon.html', {'inv':inv, 'items':items})
    # purchased=PurchasedProduct.objects.filter(invoice=inv)
    # buffer = BytesIO()
 
    # # Create the PDF object, using the buffer as its "file."
    # p = canvas.Canvas(buffer)
    # # make it letter size
    # p.setPageSize(letter)
    # p.setTitle(f"Bon de sortie: {inv.receipt_no} ")
    # # write 'Vita drogerie' on the top left corner
    # #draw the logo
    # p.drawImage(logo_path, 10, 685, 120, 120)
    # #p.drawString(15, 770, 'LOGO')
    # p.setFont("Helvetica", 8)
    # p.drawString(15, 725, 'test address')
    # p.drawString(15, 710, 'ville ')
    # p.drawString(15, 695, '06 55 55 ')
    # # write 'Address' on the top left corner
    # p.drawString(330, 770, f"Bon de sortie: {inv.receipt_no} ")
    # p.drawString(330, 755, f"Date: {datetime.strftime(inv.created_at, '%d/%m/%Y')} ")
    # #write 'Client' on the top right corner
    # p.drawString(330, 730, f"Client: {inv.customer.customer_name} ")

    # # drow a line
    # p.drawString(20, 660, 'Article')
    # p.line(15, 680, 15, 650)
    # p.drawString(272, 660, 'Qté')
    # p.line(270, 680, 270, 650)
    # p.drawString(312, 660, 'Prix unt.')
    # p.line(310, 680, 310, 650)
    # p.drawString(362, 660, 'Total')
    # p.line(360, 680, 360, 650)
    # p.line(15, 650, 550, 650)
    # n=640
    # for i in purchased:
    #     p.drawString(20, n, i.product.name)
    #     # vertical line
    #     p.line(15, 650, 15, n)

    #     p.drawString(272, n, str(int(i.quantity)))
    #     # vertical line
    #     p.line(270, 650, 270, n)

    #     p.drawString(312, n, str(i.price))
    #     p.line(310, 650, 310, n)

    #     p.drawString(362, n, str(i.purchase_amount))
    #     p.line(360, 650, 360, n)

    #     # horizontal line
    #     p.line(15, n-2, 550, n-2)
    #     n-=15
    # p.drawString(312, n, 'Total:')
    # p.drawString(362, n, str(inv.grand_total))
    # p.line(312, n-2, 550, n-2)
    # # data=[
    # #     ['Article', 'Qté', 'prix unt.', 'Total'],

    # # ]
    # # for i in purchased:
    # #     data.append([i.product.name, i.quantity, i.price, i.purchase_amount])
    # # data.append(['', '', 'Total', inv.grand_total],)
    # # table=Table(data, colWidths=[300, 50, 60, 70])
    # # # adjust height of the row

    # # table.setStyle(TableStyle([
    # #     # make the first row gray background
    # #     ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
    # #     ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
    # #     ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
    # # ]))
    # # table.wrapOn(p, 800, 600)#
    # # print(count)
    # # table.drawOn(p, 30, 500)
    # p.showPage()
    # p.save()

    # # FileResponse sets the Content-Disposition header so that browsers
    # # present the option to save the file.
    # buffer.seek(0)
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = f'attachment; filename="bon_sortie{inv.receipt_no}.pdf"'
    # response.write(buffer.getvalue())
    # return response


class CreateInvoiceView(FormView):
    template_name = 'sales/create_invoice.html'
    form_class = BillingForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            CreateInvoiceView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateInvoiceView, self).get_context_data(**kwargs)
        products = (
            self.request.user.retailer_user.retailer.
                retailer_product.all()
        )
        customers = (
            self.request.user.retailer_user.
            retailer.retailer_customer.all()
        )
        context.update({
            'products': products,
            'customers': customers,
            'present_date': timezone.now().date(),
            'title':'Ajouterفاتورة جديدة'
        })
        return context


class ProductItemAPIView(View):

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            ProductItemAPIView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        products = Product.objects.filter(stock__gt=0)

        items = []

        for product in products:
            p = {
                'id': product.id,
                'mark': product.mark.name,
                'name': product.name,
                'consumer_price': product.price,
                'pr_achat':product.pr_achat,
                'category': product.category.name,
                'stock': product.stock,
                'ref': product.ref,
                'car': product.car,
                # 'mark': product.mark,
            }

            # if product.stockin_product.exists():

            #     all_stock = product.stockin_product.all()
            #     if all_stock:
            #         all_stock = all_stock.aggregate(Sum('quantity'))
            #         all_stock = float(all_stock.get('quantity__sum') or 0)
            #     else:
            #         all_stock = 0

            #     purchased_stock = product.purchased_product.all()
            #     if purchased_stock:
            #         purchased_stock = purchased_stock.aggregate(
            #             Sum('quantity'))
            #         purchased_stock = float(
            #             purchased_stock.get('quantity__sum') or 0)
            #     else:
            #         purchased_stock = 0

            #     p.update({
            #         'stock': all_stock - purchased_stock
            #     })

            items.append(p)

        return JsonResponse({'products': items})


class GenerateInvoiceAPIView(View):

    def __init__(self, *args, **kwargs):
        super(GenerateInvoiceAPIView, self).__init__(*args, **kwargs)
        self.customer = None
        self.invoice = None

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            GenerateInvoiceAPIView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        customer_name = self.request.POST.get('customer_name')
        customer_phone = self.request.POST.get('customer_phone')
        sub_total = self.request.POST.get('sub_total')
        discount = self.request.POST.get('discount')
        shipping = self.request.POST.get('shipping')
        grand_total = self.request.POST.get('grand_total')
        totalQty = self.request.POST.get('totalQty')
        remaining_payment = self.request.POST.get('remaining_amount')
        paid_amount = self.request.POST.get('paid_amount')
        cash_payment = self.request.POST.get('cash_payment')
        returned_cash = self.request.POST.get('returned_cash')
        items = json.loads(self.request.POST.get('items'))
        purchased_items_id = []
        extra_items_id = []

        with transaction.atomic():

            billing_form_kwargs = {
                'discount': discount,
                'grand_total': grand_total,
                'total_quantity': totalQty,
                'shipping': shipping,
                'paid_amount': paid_amount,
                'remaining_payment': remaining_payment,
                'cash_payment': cash_payment,
                'returned_payment': returned_cash,
                'retailer': self.request.user.retailer_user.retailer.id,
            }

            if self.request.POST.get('customer_id'):
                billing_form_kwargs.update({
                    'customer': self.request.POST.get('customer_id')
                })
            else:
                customer_form_kwargs = {
                    'customer_name': customer_name,
                    'customer_phone': customer_phone,
                    'retailer': self.request.user.retailer_user.retailer.id
                }
                customer_form = CustomerForm(customer_form_kwargs)
                if customer_form.is_valid():
                    self.customer = customer_form.save()
                    billing_form_kwargs.update({
                        'customer': self.customer.id
                    })

            billing_form = BillingForm(billing_form_kwargs)
            self.invoice = billing_form.save()

            for item in items:
                item_id = item.get('item_id')
                try:
                    product = Product.objects.get(
                        pk=item.get('item_id'),
                        retailer=self.request.user.retailer_user.retailer
                    )
                    originref=product.ref.split(' ')[0]
                    
                    form_kwargs = {
                        'product': product.id,
                        'invoice': self.invoice.id,
                        'quantity': item.get('qty'),
                        'price': item.get('price'),
                        # 'discount_percentage': item.get('perdiscount'),
                        'purchase_amount': item.get('total'),
                    }
                    form = PurchasedProductForm(form_kwargs)
                    if form.is_valid():
                        purchased_item = form.save()
                        product.stock=product.product_available_items()
                        product.save()
                        purchased_items_id.append(purchased_item.id)

                        latest_stock_in = (
                            product.stockin_product.all().latest('id'))

                        stock_out_form_kwargs = {
                            'product': product.id,
                            'invoice': self.invoice.id,
                            'purchased_item': purchased_item.id,
                            'stock_out_quantity': float(item.get('qty')),
                            'dated': timezone.now().date()
                        }

                        stock_out_form = StockOutForm(stock_out_form_kwargs)
                        if stock_out_form.is_valid():
                            stock_out = stock_out_form.save()
                    simillar = Product.objects.filter(category=product.category.id).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
                    
                    sim=any([int(i.stock) for i in simillar])
                    if sim:
                        simillar.update(disponibleinother=True)
                        simillar.update(rcommand=False)
                    else:
                        simillar.update(disponibleinother=False)
                        simillar.update(rcommand=True)
                except Product.DoesNotExist:
                    extra_item_kwargs = {
                        'retailer': self.request.user.retailer_user.retailer.id,
                        'item_name': item.get('item_name'),
                        'quantity': item.get('qty'),
                        'price': item.get('price'),
                        'discount_percentage': item.get('perdiscount'),
                        'total': item.get('total'),
                    }
                    extra_item_form = ExtraItemForm(extra_item_kwargs)
                    if extra_item_form.is_valid():
                        extra_item = extra_item_form.save()
                        extra_items_id.append(extra_item.id)

            self.invoice.purchased_items.set(purchased_items_id)
            self.invoice.extra_items.set(extra_items_id)
            self.invoice.save()

            if self.customer or self.request.POST.get('customer_id'):
                ledger_form_kwargs = {
                    'retailer': self.request.user.retailer_user.retailer.id,
                    'customer': (
                        self.request.POST.get('customer_id') or
                        self.customer.id),
                    'invoice': self.invoice.id,
                    'amount': remaining_payment,

                    'dated': timezone.now()
                }

                ledgerform = LedgerForm(ledger_form_kwargs)
                if ledgerform.is_valid():
                    ledger = ledgerform.save()

            return JsonResponse({'invoice_id': self.invoice.id})


class InvoiceDetailView(TemplateView):
    template_name = 'sales/invoice_detail.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            InvoiceDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InvoiceDetailView, self).get_context_data(**kwargs)
        invoice = SalesHistory.objects.get(id=self.kwargs.get('invoice_id'))
        context.update({
            'invoice': invoice,
            'product_details': invoice.product_details,
            'extra_items_details': invoice.extra_items,
            'title':"تفاصيل Facture"
        })
        return context


class InvoicesList(ListView):
    template_name = 'sales/invoice_list.html'
    model = SalesHistory
    paginate_by = 200

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(InvoicesList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (
            self.request.user.retailer_user.retailer.
            retailer_sales.all().order_by('-created_at')
        )
        return queryset

    def get_sales_history(self):
        return (
            self.request.user.retailer_user.retailer.
            retailer_sales.all().order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super(InvoicesList, self).get_context_data(**kwargs)
        context.update({
            'title':'Liste الفواتير',
        })
        return context


class UpdateInvoiceView(FormView):
    template_name = 'sales/update_invoice.html'
    form_class = BillingForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            UpdateInvoiceView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateInvoiceView, self).get_context_data(**kwargs)
        
        invoice = SalesHistory.objects.get(id=self.kwargs.get('id'))
        context.update({
            'invoice': invoice
        })
        return context


class UpdateInvoiceAPIView(View):

    def __init__(self, *args, **kwargs):
        super(UpdateInvoiceAPIView, self).__init__(*args, **kwargs)
        self.customer = None
        self.invoice = None

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            UpdateInvoiceAPIView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        customer_name = self.request.POST.get('customer_name')
        customer_phone = self.request.POST.get('customer_phone')
        sub_total = self.request.POST.get('sub_total')
        discount = self.request.POST.get('discount')
        shipping = self.request.POST.get('shipping')
        grand_total = self.request.POST.get('grand_total')
        totalQty = self.request.POST.get('totalQty')
        remaining_payment = self.request.POST.get('remaining_amount')
        paid_amount = self.request.POST.get('paid_amount')
        invoice_id = self.request.POST.get('invoice_id')
        items = json.loads(self.request.POST.get('items'))
        purchased_items_id = []
        extra_items_id = []

        with transaction.atomic():
            for item in items:
                product=Product.objects.get(id=item.get('id'))
                if item.get('item_id'):
                    # Getting Purchased Item by using Item ID or Invoice ID
                    # We are getting that by using Item ID
                    purchased_item = PurchasedProduct.objects.get(
                        id=item.get('item_id'),
                    )
                    # Delete the previous Stock Out Object,
                    # We need to create new one if quantity would not be same

                    if not purchased_item.quantity == float(item.get('qty')):
                        StockOut.objects.filter(
                            invoice__id=invoice_id,
                            stock_out_quantity='%g' % purchased_item.quantity,
                        ).delete()
                        oldpurchased=purchased_item.quantity
                        # Update Purchased Product Details
                        purchased_item.price = item.get('price')
                        purchased_item.quantity = (item.get('qty'))
                        purchased_item.discount_percentage = item.get('perdiscount')
                        purchased_item.purchase_amount = item.get('total')
                        purchased_item.save()
                        # if float(oldpurchased) > float(item.get('qty')):
                        #     product.stock=float(product.stock)+(float(oldpurchased)-float(item.get('qty')))
                        # elif float(oldpurchased) < float(item.get('qty')):
                        #     product.stock=float(product.stock)-(float(item.get('qty'))-float(oldpurchased))
                        # elif float(item.get('qty')) == 0:
                        #     product.stock=float(product.stock)+float(oldpurchased)
                        product.stock=product.product_available_items()
                        product.save()
                        originref=product.ref.split(' ')[0]
                        simillar = Product.objects.filter(category=product.category.id).filter(Q(ref__startswith=originref+' ') | Q(ref=originref))
                    
                        sim=any([int(i.stock) for i in simillar])
                        if sim:
                            simillar.update(disponibleinother=True)
                            simillar.update(rcommand=False)
                        else:
                            simillar.update(disponibleinother=False)
                            simillar.update(rcommand=True)
                        purchased_items_id.append(purchased_item.id)

                        # Creating New stock iif quantity would get changed
                        stock_out_form_kwargs = {
                            'invoice': invoice_id,
                            'product': purchased_item.product.id,
                            'purchased_item': purchased_item.id,
                            'stock_out_quantity': item.get('qty'),
                            'dated': timezone.now().date()
                        }

                        stock_out_form = StockOutForm(stock_out_form_kwargs)
                        if stock_out_form.is_valid():
                            stock_out_form.save()

            invoice = SalesHistory.objects.get(id=invoice_id)
            invoice.discount = discount
            invoice.grand_total = grand_total
            invoice.total_quantity = totalQty
            invoice.shipping = shipping
            invoice.purchased_items.set(purchased_items_id)
            invoice.extra_items.set(extra_items_id)
            invoice.paid_amount = paid_amount
            invoice.remaining_payment = remaining_payment
            invoice.retailer = self.request.user.retailer_user.retailer

            if self.request.POST.get('customer_id'):
                invoice.customer = Customer.objects.get(
                    id=self.request.POST.get('customer_id'))

            invoice.save()

            if invoice.customer:
                ledger = Ledger.objects.get(
                    customer__id=invoice.customer.id,
                    invoice__id=invoice.id
                )
                ledger.amount = remaining_payment
                ledger.save()

        return JsonResponse({'invoice_id': invoice.id})


class ProductDetailsAPIView(View):

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            ProductDetailsAPIView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            product_item = Product.objects.get(
                bar_code=self.request.POST.get('code'))
        except Product.DoesNotExist:
            return JsonResponse({
                'status': False,
                'message': 'Item with not exists',
            })

        latest_stock = product_item.stockin_product.all().latest('id')

        all_stock = product_item.stockin_product.all()
        if all_stock:
            all_stock = all_stock.aggregate(Sum('quantity'))
            all_stock = float(all_stock.get('quantity__sum') or 0)
        else:
            all_stock = 0

        purchased_stock = product_item.stockout_product.all()
        if purchased_stock:
            purchased_stock = purchased_stock.aggregate(
                Sum('stock_out_quantity'))
            purchased_stock = float(
                purchased_stock.get('stock_out_quantity__sum') or 0)
        else:
            purchased_stock = 0

        return JsonResponse({
            'status': True,
            'message': 'Success',
            'product_id': product_item.id,
            'product_name': product_item.name,
            'product_brand': product_item.brand_name,
            'product_price': '%g' % latest_stock.price_per_item,
            'stock': '%g' % (all_stock - purchased_stock)
        })


# class SalesDeleteView(DeleteView):
#     model = SalesHistory
#     success_url = reverse_lazy('sales:invoice_list')

#     def get(self, request, *args, **kwargs):
#         # pp=PurchasedProduct.objects.filter(
#         #     invoice__id=self.kwargs.get('pk'))
#         # for i in pp:
#         #     product=Product.objects.get(id=i.product.id)
#         #     product.stock=float(product.stock)+float(i.quantity)
#         #pp.delete()
#         # StockOut.objects.filter(
#         #     invoice__id=self.kwargs.get('pk')).delete()
#         # Ledger.objects.filter(
#         #     invoice__id=self.kwargs.get('pk')).delete()
#         return self.delete(request, *args, **kwargs)


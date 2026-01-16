# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import random

from django.db import models
from django.db.models.signals import post_save

from pis_com.models import DatedModel
from django.utils import timezone


class SalesHistory(DatedModel):
    retailer = models.ForeignKey(
        'pis_retailer.Retailer', related_name='retailer_sales',on_delete=models.CASCADE
    )
    receipt_no = models.CharField(
        max_length=20, unique=True, blank=True, null=True
    )
    #bon date
    date=models.DateField(default=None, null=True, blank=True)
    customer = models.ForeignKey(
        'pis_com.Customer',
        related_name='customer_sales',
        blank=True, null=True,on_delete=models.CASCADE
    )

    product_details = models.TextField(
        max_length=512, blank=True, null=True,
        help_text='Quantity and Product name would save in JSON format')

    purchased_items = models.ManyToManyField(
        'pis_product.PurchasedProduct',
        max_length=100, blank=True
    )

    extra_items = models.ManyToManyField(
        'pis_product.ExtraItems',
        max_length=200, blank=True,
    )

    total_quantity = models.CharField(
        max_length=10, blank=True, null=True, default=1)

    sub_total = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )

    paid_amount = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )

    remaining_payment = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )

    discount = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )

    shipping = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )

    grand_total = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )

    cash_payment = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )

    returned_payment = models.DecimalField(
        max_digits=65, decimal_places=2, default=0, blank=True, null=True
    )

    def __unicode__(self):
        return self.retailer.name
    
# Signals Function
def create_save_receipt_no(sender, instance, created, **kwargs):
    if created and not instance.receipt_no:
        year_month = timezone.now().strftime("%y")
        latest_receipt = SalesHistory.objects.filter(
            receipt_no__startswith=f"BL{year_month}"
        ).last()
        if latest_receipt:
            latest_receipt_no = int(latest_receipt.receipt_no[-6:])
            receipt_no = f"BL{year_month}{latest_receipt_no + 1:06}"
        else:
            receipt_no = f"BL{year_month}000001"
        instance.receipt_no = receipt_no
        instance.save()


# Signal Calls
post_save.connect(create_save_receipt_no, sender=SalesHistory)

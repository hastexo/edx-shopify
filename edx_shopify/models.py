from django.db import models
from django.utils import timezone


class Order(models.Model):
    UNPROCESSED = 0
    PROCESSING = 1
    PROCESSED = 2
    ERROR = 3

    STATUS_CHOICES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSING, 'Processing'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )

    id = models.IntegerField(primary_key=True, editable=False)
    status = models.IntegerField(choices=STATUS_CHOICES, default=UNPROCESSED)
    received = models.DateTimeField(default=timezone.now)
    email = models.EmailField()
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)


class OrderItem(models.Model):
    order = models.ForeignKey(Order)
    sku = models.CharField(max_length=254)
    email = models.EmailField()
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)

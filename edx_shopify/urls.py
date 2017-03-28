from django.conf.urls import patterns, url

from .views import order_create

urlpatterns = patterns(
    '',
    url(r'^shopify/order/create', order_create, name='shopify_order_create'),
)

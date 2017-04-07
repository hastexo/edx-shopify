import copy, json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .utils import hmac_is_valid
from .models import Order
from .tasks import ProcessOrder

@csrf_exempt
@require_POST
def order_create(request):
    # Load configuration
    conf = settings.WEBHOOK_SETTINGS['edx_shopify']

    # Process request
    try:
        hmac  = request.META['HTTP_X_SHOPIFY_HMAC_SHA256']
        shop_domain = request.META['HTTP_X_SHOPIFY_SHOP_DOMAIN']
        data = json.loads(request.body)
    except (KeyError, ValueError):
        return HttpResponse(status=400)

    if (not hmac_is_valid(conf['api_key'], request.body, hmac) or
            conf['shop_domain'] != shop_domain):
        return HttpResponse(status=403)

    # Record order
    order, created = Order.objects.get_or_create(
        id=data['id'],
        defaults={
            'email': data['customer']['email'],
            'first_name': data['customer']['first_name'],
            'last_name': data['customer']['last_name']
        }
    )

    # Process order
    if order.status == Order.UNPROCESSED:
        order.status = Order.PROCESSING
        ProcessOrder().apply_async(args=(data,))

    return HttpResponse(status=200)

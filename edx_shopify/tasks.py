from celery import Task
from celery.utils.log import get_task_logger

from .models import Order, OrderItem
from .utils import auto_enroll_email

logger = get_task_logger(__name__)


class ProcessOrder(Task):
    """
    Process order creation event.

    """
    def run(self, data):
        # Get the order
        order = Order.objects.get(id=data['id'])

        # Process line items
        order_error = False
        for item in data['line_items']:
            try:
                sku = item['sku']
                email = next(
                    p['value'] for p in item['properties']
                    if p['name'] == 'email'
                )
            except KeyError, StopIteration:
                order_error = True
                continue

            # Store line item
            order_item, created = OrderItem.objects.get_or_create(
                order = order,
                sku = sku,
                email = email
            )

            if order_item.status == OrderItem.UNPROCESSED:
                try:
                    # Enroll the email in the course
                    auto_enroll_email(sku, email)
                except:
                    order_error = True
                    order_item.status = OrderItem.ERROR
                    continue

                # Mark the item as processed
                order_item.status = OrderItem.PROCESSED

            elif order_item.status == OrderItem.ERROR:
                order_error = True

        # Mark the order status
        if order_error:
            order.status = Order.ERROR
        else:
            order.status = Order.PROCESSED

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
        logger.debug('Processing order data: %s' % data)
        order = Order.objects.get(id=data['id'])

        # If the order is anything but UNPROCESSED, abandon the attempt.
        if order.status != Order.UNPROCESSED:
            logger.warning('Order %s has already '
                           'been processed, ignoring' % order.id)
            return

        # Mark the order as being processed.
        order.status = Order.PROCESSING
        order.save()

        # Process line items
        order_error = False
        for item in data['line_items']:
            logger.debug('Processing line item: %s' % item)
            try:
                sku = item['sku']
                email = next(
                    p['value'] for p in item['properties']
                    if p['name'] == 'email'
                )
            except (KeyError, StopIteration):
                order_error = True
                logger.error('Malformed line item %s in order %s, '
                             'unable to process' % (item, order.id))
                continue

            # Store line item
            order_item, created = OrderItem.objects.get_or_create(
                order=order,
                sku=sku,
                email=email
            )

            if order_item.status == OrderItem.UNPROCESSED:
                try:
                    # Enroll the email in the course
                    auto_enroll_email(sku, email)
                except:
                    logger.error('Unable to enroll '
                                 '%s in %s' % (email, sku))
                    order_error = True
                    order_item.status = OrderItem.ERROR
                    order_item.save()
                    continue

                # Mark the item as processed
                order_item.status = OrderItem.PROCESSED
                order_item.save()
                logger.debug('Successfully processed line item '
                             '%s for order %s' % (item, order.id))

            elif order_item.status == OrderItem.ERROR:
                order_error = True

        # Mark the order status
        if order_error:
            order.status = Order.ERROR
            logger.error('Failed to fully '
                         'process order %s' % order.id)
        else:
            order.status = Order.PROCESSED
            logger.error('Successfully processed '
                         'order %s' % order.id)
        order.save()

from celery import Task
from celery.utils.log import get_task_logger

from .models import Order, OrderItem
from .utils import auto_enroll_email

logger = get_task_logger(__name__)


class ProcessOrder(Task):
    """Process a newly received order, and enroll learners in courses
    using their email address.

    On failure, store the order in an ERROR state.
    """

    def __init__(self):
        """Set up an order as an instance member, so we can manipulate it both
        from run() and from on_failure().
        """

        self.order = None

    def run(self, data):
        """Parse input data for line items, and create enrollments.

        On any error, raise the exception in order to be handled by
        on_failure().
        """

        logger.debug('Processing order data: %s' % data)
        self.order = Order.objects.get(id=data['id'])

        # If the order is anything but UNPROCESSED, abandon the attempt.
        if self.order.status != Order.UNPROCESSED:
            logger.warning('Order %s has already '
                           'been processed, ignoring' % self.order.id)
            return

        # Mark the order as being processed.
        self.order.status = Order.PROCESSING
        self.order.save()

        # Process line items
        for item in data['line_items']:
            logger.debug('Processing line item: %s' % item)
            try:
                sku = item['sku']
                email = next(
                    p['value'] for p in item['properties']
                    if p['name'] == 'email'
                )
            except:
                logger.error('Malformed line item %s in order %s, '
                             'unable to process' % (item, self.order.id))
                raise

            # Store line item
            order_item, created = OrderItem.objects.get_or_create(
                order=self.order,
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
                    raise

                # Mark the item as processed
                order_item.status = OrderItem.PROCESSED
                order_item.save()
                logger.debug('Successfully processed line item '
                             '%s for order %s' % (item, self.order.id))

        # Mark the order status
        self.order.status = Order.PROCESSED
        logger.error('Successfully processed '
                     'order %s' % self.order.id)
        self.order.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle the run() method having raised an exception: log an
        exception stack trace and a prose message, save the order with
        an ERROR status.
        """

        logger.error(exc, exc_info=True)
        logger.error('Failed to fully '
                     'process order %s '
                     '(task ID %s)' % (self.order.id,
                                       task_id))
        self.order.status = Order.ERROR
        self.order.save()

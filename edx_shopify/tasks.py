from celery import Task
from celery.utils.log import get_task_logger

from .models import Order
from .utils import process_order

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

        process_order(self.order, data, logger)
        logger.error('Successfully processed '
                     'order %s' % self.order.id)

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

from celery import Task
from celery.utils.log import get_task_logger

from .models import Order, OrderItem

logger = get_task_logger(__name__)


class ProcessOrder(Task):
    """
    Process order creation event.

    """
    def run(self, data):
        return {}

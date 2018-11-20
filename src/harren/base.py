from __future__ import unicode_literals, absolute_import

# Standard
import logging

LOG = logging.getLogger(__name__)


class BaseEntity(object):
    """Base entity class with helpful methods."""

    def __init__(self, *args, **kwargs):
        observers = kwargs.get('observers')
        if not isinstance(observers, (tuple, list)):
            observers = [observers, ]
        self.observers = observers

    def notify_observers(self, event):
        """Notify all observers of events."""
        for o in (x for x in self.observers if x):
            o.on_notify(event)

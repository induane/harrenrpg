from __future__ import unicode_literals, absolute_import

# Standard
import logging
import string

LOG = logging.getLogger(__name__)


def dialog_from_props(properties):
    """Given an entity, get it's dialog."""
    dialog_data = {}
    for key, value in properties.items():
        if not key:
            continue
        if key.startswith('dialog'):
            num = ''.join(
                [x for x in key if x in string.digits]
            )
            try:
                dialog_data[int(num)] = value
            except ValueError:
                # Was likely from somewhere else, maybe
                # 'dialogue length' or some other prop
                pass

    LOG.debug('Dialog Data: %s', dialog_data)
    dialog = []
    for key in sorted(dialog_data.keys()):
        dialog.append(dialog_data[key])

    if not dialog and 'properties' in properties:
        return dialog_from_props(properties['properties'])
    else:
        return dialog

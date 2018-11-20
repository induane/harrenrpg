# Standard
import argparse
import logging
import os
import pkg_resources
import sys
from logging.config import dictConfig

# Third Party
from log_color import ColorStripper, ColorFormatter

LOG = logging.getLogger(__name__)


# Setup the version string globally
try:
    pkg_version = '%(prog)s {0}'.format(
        pkg_resources.get_distribution('harren-rpg').version
    )
except pkg_resources.DistributionNotFound:
    pkg_version = '%(prog)s Development'
except Exception:
    pkg_version = '%(prog)s Unknown'


def run_game():
    parser = argparse.ArgumentParser(description='Legend of Zelda')
    parser.add_argument(
        '-l',
        '--log-level',
        default='INFO',
        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
        help='Logging level for command output.'
    )
    parser.add_argument(
        '-L',
        '--logfile',
        dest='logfile',
        default=None,
        help='Location to place a log of the process output'
    )
    parser.add_argument(
        '-V',
        '--version',
        dest='version',
        action='version',
        version=pkg_version,
        help='Display the version number.'
    )

    parsed_args = parser.parse_args()

    # Get logging related arguments & the configure logging
    if parsed_args.logfile:
        logfile = os.path.abspath(parsed_args.logfile)
    else:
        logfile = None

    # Don't bother with a file handler if we're not logging to a file
    handlers = ['console', 'filehandler'] if logfile else ['console', ]

    # The base logging configuration
    BASE_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'ConsoleFormatter': {
                '()': ColorFormatter,
                'format': '%(levelname)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'VerboseFormatter': {
                '()': ColorFormatter,
                'format': ("%(levelname)-8s: %(asctime)s '%(message)s' "
                           '%(name)s:%(lineno)s'),
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'FileFormatter': {
                '()': ColorStripper,
                'format': ("%(levelname)-8s: %(asctime)s '%(message)s' "
                           '%(name)s:%(lineno)s'),
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'ConsoleFormatter',
            },
        },
        'loggers': {
            'harren': {
                'handlers': handlers,
                'level': parsed_args.log_level,
            },
            'pygame': {
                'handlers': handlers,
                'level': parsed_args.log_level,
            },
            'pyaudio': {
                'handlers': handlers,
                'level': parsed_args.log_level,
            },
            'pytmx': {
                'handlers': handlers,
                'level': parsed_args.log_level,
            },
        }
    }

    # If we have a log file, modify the dict to add in the filehandler conf
    if logfile:
        BASE_CONFIG['handlers']['filehandler'] = {
            'level': parsed_args.log_level,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logfile,
            'formatter': 'FileFormatter',
        }

    if parsed_args.log_level == 'DEBUG':
        # Set a more noisy formatter
        BASE_CONFIG['handlers']['console']['formatter'] = 'VerboseFormatter'

    # print('sadl;fkjsdkl;fjsdkl;fdjsfljsdal;kfjsdl;kja')
    # Setup the loggers
    dictConfig(BASE_CONFIG)

    LOG.info('#g<Launching Harren RPG!>')

    try:
        import pygame
    except ImportError:
        LOG.exception('PyGame not found... exiting.')
        sys.exit(1)

    # Now we can import the setup tools and other pieces
    from harren.data import setup
    from harren.data.main import main

    setup.GAME
    main()
    pygame.quit()
    sys.exit()


def main():
    try:
        run_game()
    except KeyboardInterrupt:
        # Write a nice message to stderr
        sys.stderr.write(u'\n\u2717 Operation canceled by user.\n')
        sys.exit(1)


if __name__ == '__main__':
    main()

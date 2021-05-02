# Standard
import argparse
import logging
import os
import sys
from logging.config import dictConfig
from pkg_resources import DistributionNotFound, get_distribution

# Third Party
from boltons.fileutils import mkdir_p
from log_color import ColorStripper, ColorFormatter

# Project
from harren import resources

LOG = logging.getLogger(__name__)


def get_version() -> str:
    try:
        return f"%(prog)s {get_distribution('harren_rpg').version}"
    except DistributionNotFound:
        return '%(prog)s Development'
    except Exception:
        return '%(prog)s Unknown'


def run_game():
    parser = argparse.ArgumentParser(description='Legend of Harren')
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
        action='version',
        version=get_version(),
        help='Display the version number.'
    )
    parser.add_argument(
        '-g',
        '--fullscreen',
        dest='fullscreen',
        action='store_true',
        help='Launch the new game in fullscreen mode',
    )
    parser.add_argument(
        '--no-splash',
        dest='no_splash',
        action='store_true',
        help='Skip the initial loading splash screen',
    )
    parser.add_argument(
        '--no-sound',
        dest='no_sound',
        action='store_true',
        help='Disable sound',
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
            'pytmx': {
                'handlers': handlers,
                'level': parsed_args.log_level,
            },
            'pyscroll': {
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

    # Setup the loggers
    dictConfig(BASE_CONFIG)

    LOG.info('#g<Launching Harren RPG!>')
    # Setup SDL Environment Variables
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    try:
        import pygame  # noqa
    except ImportError:
        LOG.exception('#y<PyGame not found... exiting.>')
        sys.exit(1)

    # Make the config folder if it doesn't already exist
    mkdir_p(resources.CONFIG_FOLDER)

    # Disable or enable sound
    if parsed_args.no_sound:
        sound_enabled = False
    else:
        sound_enabled = True

    from harren.game_loop import GameState
    game = GameState(
        fullscreen=parsed_args.fullscreen,
        no_splash=parsed_args.no_splash,
        sound_enabled=sound_enabled,
    )
    game.main()
    __exit()


def __exit(code=0):
    try:
        import pygame
    except ImportError:
        LOG.exception('#y<PyGame not found... exiting...>')
        sys.exit(1)
    try:
        pygame.display.quit()
    except Exception:
        pass
    try:
        pygame.quit()
    except Exception:
        pass
    sys.exit(code)


def main():
    try:
        run_game()
    except KeyboardInterrupt:
        # Write a nice message to stderr
        sys.stderr.write(u'\n\u2717 Operation canceled by user.\n')
        __exit(code=1)


if __name__ == '__main__':
    main()

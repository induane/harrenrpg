# Standard
import logging
import os

LOG = logging.getLogger(__name__)


RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources")
FONT_FOLDER = os.path.join(RESOURCE_FOLDER, "fonts")
MUSIC_FOLDER = os.path.join(RESOURCE_FOLDER, "music")
GFX_FOLDER = os.path.join(RESOURCE_FOLDER, "graphics")
SFX_FOLDER = os.path.join(RESOURCE_FOLDER, "sound")
TMX_FOLDER = os.path.join(RESOURCE_FOLDER, "tmx")
DATA_FOLDER = os.path.join(RESOURCE_FOLDER, "data")
HOME_FOLDER = os.path.expanduser("~")
CONFIG_FOLDER = os.path.join(HOME_FOLDER, ".harren-rpg")

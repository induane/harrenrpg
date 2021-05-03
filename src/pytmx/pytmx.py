# -*- coding: utf-8 -*-
"""
Copyright (C) 2012-2017, Leif Theden <leif.theden@gmail.com>

This file is part of pytmx.

pytmx is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pytmx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pytmx.  If not, see <http://www.gnu.org/licenses/>.
"""
import array
import gzip
import logging
import os
import struct
import zlib
from base64 import b64decode
from collections import defaultdict
from io import BytesIO
from itertools import chain, product
from operator import attrgetter
from collections.abc import MutableSequence
try:
    from lxml import etree as et
except ImportError:
    from xml.etree import ElementTree as et
import importlib

# Project
from .lib import AnimationFrame, DefaultORM, TileFlags, HWIntORM

__all__ = (
    'TiledElement',
    'TiledMap',
    'TiledTileset',
    'TiledTileLayer',
    'TiledObject',
    'TiledObjectGroup',
    'TiledImageLayer',
    'parse_properties',
)

LOG = logging.getLogger(__name__)
HW_ORM = HWIntORM()
DEFAULT_ORM = DefaultORM()

# internal flags
TRANS_FLIPX = 1
TRANS_FLIPY = 2
TRANS_ROT = 4

# Tiled gid flags
GID_TRANS_FLIPX = 1 << 31
GID_TRANS_FLIPY = 1 << 30
GID_TRANS_ROT = 1 << 29


def default_image_loader(filename, flags, **kwargs):
    """This default image loader just returns filename, rect, and any flags."""

    def load(rect=None, flags=None):
        return filename, rect, flags

    return load


def decode_gid(raw_gid):
    """Decode a GID from TMX data

    as of 0.7.0 it determines if the tile should be flipped when rendered
    as of 0.8.0 bit 30 determines if GID is rotated

    :param raw_gid: 32-bit number from TMX layer data
    :return: gid, flags
    """
    flags = TileFlags(
        raw_gid & GID_TRANS_FLIPX == GID_TRANS_FLIPX,
        raw_gid & GID_TRANS_FLIPY == GID_TRANS_FLIPY,
        raw_gid & GID_TRANS_ROT == GID_TRANS_ROT)
    gid = raw_gid & ~(GID_TRANS_FLIPX | GID_TRANS_FLIPY | GID_TRANS_ROT)
    return gid, flags


def parse_properties(node):
    """
    Parse a Tiled xml node and return a dict that represents a tiled "property"

    :param node: etree element
    :return: dict
    """
    d = {}
    for child in node.findall('properties'):
        for subnode in child.findall('property'):
            cls = None
            try:
                if 'type' in subnode.keys():
                    module = importlib.import_module('builtins')
                    cls = getattr(module, subnode.get('type'))
            except AttributeError:
                LOG.info('Not a built-in type. Defaulting to string-cast.')
            d[subnode.get('name')] = cls(subnode.get('value')) if cls is not None else subnode.get('value')
    return d


class TiledElement:
    """Base class for all pytmx types."""
    __slots__ = ('properties', 'allow_duplicate_names', )

    def __init__(self):
        self.properties = {}
        self.allow_duplicate_names = False

    @classmethod
    def from_xml_string(cls, xml_string):
        """Return a TileElement object from a xml string

        :param xml_string: string containing xml data
        :rtype: TiledElement instance
        """
        return cls().parse_xml(et.fromstring(xml_string))

    def _contains_invalid_property_name(self, items):
        if self.allow_duplicate_names:
            return False

        for k, v in items:
            if hasattr(self, k):
                LOG.warning(
                    "Cannot set user %s property on %s '%s'; Tiled property "
                    "already exists.", k, self.__class__.__name__, self.name
                )
                return True
        return False

    def set_attributes(self, node_items, orm=DEFAULT_ORM):
        for key, value in node_items:
            casted_value = orm.convert_value(key, value)
            try:
                setattr(self, key, casted_value)
            except AttributeError:
                LOG.warning('%s Dropping attribute %s: %s', self.__class__.__name__, key, casted_value)
                pass

    def set_properties(self, node):
        properties = parse_properties(node)
        if self._contains_invalid_property_name(properties.items()):
            raise ValueError(
                'Reserved names and duplicate names are not allowed. Please '
                'rename your property inside the .tmx-file'
            )
        self.properties = properties

    def __getattr__(self, item):
        try:
            return self.properties[item]
        except KeyError:
            raise AttributeError

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.name}">'


class TiledMap(TiledElement):
    """
    Contains the layers, objects, and images from a Tiled TMX map

    This class is meant to handle most of the work you need to do to use a map.
    """

    __slots__ = (
        'filename', 'image_loader', 'optional_gids', 'load_all_tiles',
        'invert_y', 'layers', 'tilesets', 'tile_properties', 'layernames',
        'gidmap', 'imagemap', 'tiledgidmap', 'maxgid', 'images', 'version',
        'tiledversion', 'orientation', 'renderorder', 'width', 'height',
        'tilewidth', 'tileheight', 'hexsidelength', 'staggeraxis',
        'staggerindex', 'backgroundcolor', 'nextobjectid', 'infinite',
        'nextlayerid',
     )

    def __init__(self, filename=None, image_loader=default_image_loader, **kwargs):
        """Create new TiledMap

        :param filename: filename of tiled map to load
        :param image_loader: function that will load images (see below)
        :param optional_gids: load specific tile image GID, even if never used
        :param invert_y: invert the y axis
        :param load_all_tiles: load all tile images, even if never used
        :param allow_duplicate_names: allow duplicates in objects' metatdata

        image_loader:
          this must be a reference to a function that will accept a tuple:
          (filename of image, bounding rect of tile in image, flags)
          the function must return a reference to to the tile.
        """
        super().__init__()
        self.filename = filename
        self.image_loader = image_loader

        # optional keyword arguments checked here
        self.optional_gids = kwargs.get('optional_gids', set())
        self.load_all_tiles = kwargs.get('load_all', True)
        self.invert_y = kwargs.get('invert_y', True)

        # Allow duplicate names to be parsed and loaded
        self.allow_duplicate_names = kwargs.get('allow_duplicate_names', False)

        self.layers = []  # All layers in proper order
        self.tilesets = []  # TiledTileset objects
        self.tile_properties = {}  # Tiles that have properties
        self.layernames = {}

        # Only used tiles are actually loaded, so there will be a difference
        # between the GIDs in the Tiled map data (tmx) and the data in this
        # object and the layers.  This dictionary keeps track of that.
        self.gidmap = defaultdict(list)
        self.imagemap = {}  # mapping of gid and trans flags to real gids
        self.tiledgidmap = {}  # mapping of tiledgid to pytmx gid
        self.maxgid = 1

        # should be filled in by a loader function
        self.images = []

        # defaults from the TMX specification
        self.version = '0.0'
        self.tiledversion = ''
        self.orientation = 'orthogonal'
        self.renderorder = 'right-down'
        self.width = 0  # width of map in tiles
        self.height = 0  # height of map in tiles
        self.tilewidth = 0  # width of a tile in pixels
        self.tileheight = 0  # height of a tile in pixels
        self.hexsidelength = 0
        self.staggeraxis = None
        self.staggerindex = None
        self.backgroundcolor = None
        self.nextobjectid = 0
        self.nextlayerid = -1
        self.infinite = 0

        # initialize the gid mapping
        self.imagemap[(0, 0)] = 0

        if filename:
            self.parse_xml(et.parse(self.filename).getroot())

    def __repr__(self):
        return f"<{self.__class__.__name__}: '{self.filename}'>"

    # iterate over layers and objects in map
    def __iter__(self):
        return chain(self.layers, self.objects)

    def parse_xml(self, node):
        """
        Parse a map from ElementTree xml node

        :param node: ElementTree xml node
        :return: self
        """
        self.set_properties(node)
        self.set_attributes(node.items())
        self.backgroundcolor = node.get(
            'backgroundcolor',
            self.backgroundcolor,
        )

        # ***         do not change this load order!         *** #
        # ***    gid mapping errors will occur if changed    *** #
        for subnode in node.findall('layer'):
            self.add_layer(TiledTileLayer(self, subnode))

        for subnode in node.findall('imagelayer'):
            self.add_layer(TiledImageLayer(self, subnode))

        for subnode in node.findall('objectgroup'):
            self.add_layer(TiledObjectGroup(self, subnode))

        for subnode in node.findall('tileset'):
            self.add_tileset(TiledTileset(self, subnode))

        # "tile objects", objects with a GID, have need to have their attributes
        # set after the tileset is loaded, so this step must be performed last
        # also, this step is performed for objects to load their tiles.

        # tiled stores the origin of GID objects by the lower right corner
        # this is different for all other types, so i just adjust it here
        # so all types loaded with pytmx are uniform.

        # iterate through tile objects and handle the image
        for o in [o for o in self.objects if o.gid]:

            # gids might also have properties assigned to them
            # in that case, assign the gid properties to the object as well
            p = self.get_tile_properties_by_gid(o.gid)
            if p:
                for key in p:
                    o.properties.setdefault(key, p[key])

            if self.invert_y:
                o.y -= o.height

        self.reload_images()
        return self

    def reload_images(self):
        """
        Load the map images from disk

        This method will use the image loader passed in the constructor
        to do the loading or will use a generic default, in which case no
        images will be loaded.

        :return: None
        """
        self.images = [None] * self.maxgid

        # iterate through tilesets to get source images
        for ts in self.tilesets:

            # skip tilesets without a source
            if ts.source is None:
                continue

            path = os.path.join(os.path.dirname(self.filename), ts.source)
            colorkey = getattr(ts, 'trans', None)
            loader = self.image_loader(path, colorkey, tileset=ts)

            p = product(range(ts.margin,
                              ts.height + ts.margin - ts.tileheight + 1,
                              ts.tileheight + ts.spacing),
                        range(ts.margin,
                              ts.width + ts.margin - ts.tilewidth + 1,
                              ts.tilewidth + ts.spacing))

            # iterate through the tiles
            for real_gid, (y, x) in enumerate(p, ts.firstgid):
                rect = (x, y, ts.tilewidth, ts.tileheight)
                gids = self.map_gid(real_gid)

                # gids is None if the tile is never used
                # but give another chance to load the gid anyway
                if gids is None:
                    if self.load_all_tiles or real_gid in self.optional_gids:
                        # TODO: handle flags? - might never be an issue, though
                        gids = [self.register_gid(real_gid, flags=0)]

                if gids:
                    # flags might rotate/flip the image, so let the loader
                    # handle that here
                    for gid, flags in gids:
                        self.images[gid] = loader(rect, flags)

        # Load image layer images
        for layer in (i for i in self.layers if isinstance(i, TiledImageLayer)):
            source = getattr(layer, 'source', None)
            if source:
                colorkey = getattr(layer, 'trans', None)
                real_gid = len(self.images)
                gid = self.register_gid(real_gid)
                layer.gid = gid
                path = os.path.join(os.path.dirname(self.filename), source)
                loader = self.image_loader(path, colorkey)
                image = loader()
                self.images.append(image)

        # load images in tiles.
        # instead of making a new gid, replace the reference to the tile that
        # was loaded from the tileset
        for real_gid, props in self.tile_properties.items():
            source = props.get('source', None)
            if source:
                colorkey = props.get('trans', None)
                path = os.path.join(os.path.dirname(self.filename), source)
                loader = self.image_loader(path, colorkey)
                image = loader()
                self.images[real_gid] = image

    def get_tile_image(self, x, y, layer):
        """
        Return the tile image for this location

        :param x: x coordinate
        :param y: y coordinate
        :param layer: layer number
        :rtype: surface if found, otherwise 0
        """
        try:
            assert (x >= 0 and y >= 0)
        except AssertionError:
            raise ValueError

        try:
            layer = self.layers[layer]
        except IndexError:
            raise ValueError

        assert isinstance(layer, TiledTileLayer)

        try:
            gid = layer.data[y][x]
        except (IndexError, ValueError):
            raise ValueError
        except TypeError:
            raise TypeError('Tiles must be specified in integers.')
        else:
            return self.get_tile_image_by_gid(gid)

    def get_tile_image_by_gid(self, gid):
        """Return the tile image for this location

        :param gid: GID of image
        :rtype: surface if found, otherwise ValueError
        """
        try:
            assert (int(gid) >= 0)
            return self.images[gid]
        except TypeError:
            raise TypeError(f'GIDs must be expressed as a number.  Got: {gid}')
        except (AssertionError, IndexError):
            raise ValueError(f'Invalid GID: {gid}')

    def get_tile_gid(self, x, y, layer):
        """ Return the tile image GID for this location

        :param x: x coordinate
        :param y: y coordinate
        :param layer: layer number
        :rtype: surface if found, otherwise ValueError
        """
        try:
            assert (x >= 0 and y >= 0 and layer >= 0)
        except AssertionError:
            raise ValueError

        try:
            return self.layers[int(layer)].data[int(y)][int(x)]
        except (IndexError, ValueError):
            raise ValueError(f'Coord: ({x},{y}) in layer {layer} is invalid')

    def get_tile_properties(self, x, y, layer):
        """ Return the tile image GID for this location

        :param x: x coordinate
        :param y: y coordinate
        :param layer: layer number
        :rtype: python dict if found, otherwise None
        """
        try:
            assert (x >= 0 and y >= 0 and layer >= 0)
        except AssertionError:
            raise ValueError

        try:
            gid = self.layers[int(layer)].data[int(y)][int(x)]
        except (IndexError, ValueError):
            raise Exception(f'Coord: ({x},{y}) in layer {layer} is invalid.')

        else:
            try:
                return self.tile_properties[gid]
            except (IndexError, ValueError):
                raise Exception(f'Coords: ({x},{y}) in layer {layer} has invalid GID: {3}')
            except KeyError:
                return None

    def get_tile_locations_by_gid(self, gid):
        """ Search map for tile locations by the GID

        Return (int, int, int) tuples, where the layer is index of
        the visible tile layers.

        Note: Not a fast operation.  Cache results if used often.

        :param gid: GID to be searched for
        :rtype: generator of tile locations
        """
        for l in self.visible_tile_layers:
            for x, y, _gid in [i for i in self.layers[l].iter_data() if i[2] == gid]:
                yield x, y, l

    def get_tile_properties_by_gid(self, gid):
        """ Get the tile properties of a tile GID

        :param gid: GID
        :rtype: python dict if found, otherwise None
        """
        try:
            return self.tile_properties[gid]
        except KeyError:
            return None

    def set_tile_properties(self, gid, properties):
        """ Set the tile properties of a tile GID

        :param gid: GID
        :param properties: python dict of properties for GID
        """
        self.tile_properties[gid] = properties

    def get_tile_properties_by_layer(self, layer):
        """ Get the tile properties of each GID in layer

        :param layer: layer number
        :rtype: iterator of (gid, properties) tuples
        """
        try:
            assert (int(layer) >= 0)
            layer = int(layer)
        except (TypeError, AssertionError):
            raise ValueError(f'Layer must be a positive integer.  Got {type(layer)} instead.')

        p = product(range(self.width), range(self.height))
        layergids = set(self.layers[layer].data[y][x] for x, y in p)

        for gid in layergids:
            try:
                yield gid, self.tile_properties[gid]
            except KeyError:
                continue

    def add_layer(self, layer):
        """ Add a layer (TileTileLayer, TiledImageLayer, or TiledObjectGroup)

        :param layer: TileTileLayer, TiledImageLayer, TiledObjectGroup object
        """
        assert isinstance(
            layer,
            (TiledTileLayer, TiledImageLayer, TiledObjectGroup)
        )
        self.layers.append(layer)
        self.layernames[layer.name] = layer

    def add_tileset(self, tileset):
        """ Add a tileset to the map

        :param tileset: TiledTileset
        """
        assert (isinstance(tileset, TiledTileset))
        self.tilesets.append(tileset)

    def get_layer_by_name(self, name):
        """Return a layer by name

        :param name: Name of layer.  Case-sensitive.
        :rtype: Layer object if found, otherwise ValueError
        """
        try:
            return self.layernames[name]
        except KeyError:
            raise ValueError(f"Layer '{name}' not found.")

    def get_object_by_name(self, name):
        """
        Find an object

        :param name: Name of object. Case-sensitive.
        :rtype: Object if found, otherwise ValueError
        """
        for obj in self.objects:
            if obj.name == name:
                return obj
        raise ValueError

    def get_tileset_from_gid(self, gid):
        """
        Return tileset that owns the gid

        Note: this is a slow operation, so if you are expecting to do this
              often, it would be worthwhile to cache the results of this.

        :param gid: gid of tile image
        :rtype: TiledTileset if found, otherwise ValueError
        """
        try:
            tiled_gid = self.tiledgidmap[gid]
        except KeyError:
            raise ValueError

        for tileset in sorted(self.tilesets, key=attrgetter('firstgid'),
                              reverse=True):
            if tiled_gid >= tileset.firstgid:
                return tileset

        raise ValueError

    @property
    def objectgroups(self):
        """Return iterator of all object groups

        :rtype: Iterator
        """
        return (layer for layer in self.layers
                if isinstance(layer, TiledObjectGroup))

    @property
    def objects(self):
        """Return iterator of all the objects associated with this map

        :rtype: Iterator
        """
        return chain(*self.objectgroups)

    @property
    def visible_layers(self):
        """Return iterator of Layer objects that are set 'visible'."""
        return (l for l in self.layers if l.visible)

    @property
    def visible_tile_layers(self):
        """Return iterator of layer indexes that are set 'visible'."""
        return (i for (i, l) in enumerate(self.layers)
                if l.visible and isinstance(l, TiledTileLayer))

    @property
    def visible_object_groups(self):
        """Return iterator of object group indexes that are set 'visible'."""
        return (i for (i, l) in enumerate(self.layers)
                if l.visible and isinstance(l, TiledObjectGroup))

    def register_gid(self, tiled_gid, flags=None):
        """
        Used to manage the mapping of GIDs between the tmx and pytmx

        :param tiled_gid: GID that is found in TMX data
        :rtype: GID that pytmx uses for the the GID passed
        """
        if flags is None:
            flags = TileFlags(0, 0, 0)

        if tiled_gid:
            try:
                return self.imagemap[(tiled_gid, flags)][0]
            except KeyError:
                gid = self.maxgid
                self.maxgid += 1
                self.imagemap[(tiled_gid, flags)] = (gid, flags)
                self.gidmap[tiled_gid].append((gid, flags))
                self.tiledgidmap[gid] = tiled_gid
                return gid
        else:
            return 0

    def map_gid(self, tiled_gid):
        """
        Used to lookup a GID read from a TMX file's data

        :param tiled_gid: GID that is found in TMX data
        :rtype: (GID, flags) for the the GID passed, None if not found
        """
        try:
            return self.gidmap[int(tiled_gid)]
        except KeyError:
            return None
        except TypeError:
            raise TypeError('GIDs must be an integer')

    def map_gid2(self, tiled_gid):
        """
        WIP.  need to refactor the gid code

        :param tiled_gid:
        :return:
        """
        tiled_gid = int(tiled_gid)

        # gidmap is a default dict, so cannot trust to raise KeyError
        if tiled_gid in self.gidmap:
            return self.gidmap[tiled_gid]
        else:
            gid = self.register_gid(tiled_gid)
            return [(gid, None)]


class TiledTileset(TiledElement):
    """
    Represents a Tiled Tileset

    External tilesets are supported.  GID/ID's from Tiled are not guaranteed to
    be the same after loaded.
    """
    __slots__ = (
        'parent', 'offset', 'firstgid', 'source', 'name', 'tilewidth',
        'tileheight', 'spacing', 'margin', 'tilecount', 'columns', 'trans',
        'width', 'height',
    )

    def __init__(self, parent, node):
        super().__init__()
        self.parent = parent
        self.offset = (0, 0)

        # Defaults from the specification
        self.firstgid = 0
        self.source = None
        self.name = None
        self.tilewidth = 0
        self.tileheight = 0
        self.spacing = 0
        self.margin = 0
        self.tilecount = 0
        self.columns = 0

        # Image properties
        self.trans = None
        self.width = 0
        self.height = 0

        self.parse_xml(node)

    def parse_xml(self, node):
        """
        Parse a Tileset from ElementTree xml element

        A bit of mangling is done here so that tilesets that have external
        TSX files appear the same as those that don't.

        :param node: ElementTree element
        :return: self
        """
        # If true, then node references an external tileset
        source = node.get('source', None)
        if source:
            if source[-4:].lower() == '.tsx':
                # External tilesets don't save this, store it for later
                self.firstgid = int(node.get('firstgid'))

                # We need to mangle the path - tiled stores relative paths
                dirname = os.path.dirname(self.parent.filename)
                path = os.path.abspath(os.path.join(dirname, source))
                try:
                    node = et.parse(path).getroot()
                except IOError:
                    raise Exception(f'Cannot load external tileset: {path}')
            else:
                raise Exception(f'Found external tileset, but cannot handle type: {self.source}')

        self.set_properties(node)
        self.set_attributes(node.items())

        # Since tile objects [probably] don't have a lot of metadata,
        # we store it separately in the parent (a TiledMap instance)
        register_gid = self.parent.register_gid
        for child in node.getiterator('tile'):
            tiled_gid = int(child.get('id'))

            p = {k: DEFAULT_ORM.convert_value(k, v) for k, v in child.items()}
            p.update(parse_properties(child))

            # images are listed as relative to the .tsx file, not the .tmx file:
            if source:
                p['path'] = os.path.join(os.path.dirname(source), p['path'])

            # handle tiles that have their own image
            image = child.find('image')
            if image is None:
                p['width'] = self.tilewidth
                p['height'] = self.tileheight
            else:
                p['source'] = image.get('source')
                p['trans'] = image.get('trans', None)
                p['width'] = image.get('width')
                p['height'] = image.get('height')

            # handle tiles with animations
            anim = child.find('animation')
            frames = []
            p['frames'] = frames
            if anim is not None:
                for frame in anim.findall('frame'):
                    duration = int(frame.get('duration'))
                    gid = register_gid(int(frame.get('tileid')) + self.firstgid)
                    frames.append(AnimationFrame(gid, duration))

            for gid, flags in self.parent.map_gid2(tiled_gid + self.firstgid):
                self.parent.set_tile_properties(gid, p)

        # handle the optional 'tileoffset' node
        self.offset = node.find('tileoffset')
        if self.offset is None:
            self.offset = (0, 0)
        else:
            self.offset = (self.offset.get('x', 0), self.offset.get('y', 0))

        image_node = node.find('image')
        if image_node is not None:
            self.source = image_node.get('source')

            # When loading from tsx, tileset image path is relative to the tsx
            # file, not the tmx:
            if source:
                self.source = os.path.join(os.path.dirname(source), self.source)

            self.trans = image_node.get('trans', None)
            self.width = int(image_node.get('width'))
            self.height = int(image_node.get('height'))

        return self


class TiledTileLayer(TiledElement):
    """
    Represents a TileLayer

    To just get the tile images, use TiledTileLayer.tiles()
    """

    __slots__ = (
        'parent', 'data', 'name', 'width', 'height', 'opacity', 'visible',
        'offsetx', 'offsety', 'id',
    )

    def __init__(self, parent, node):
        super().__init__()
        self.parent = parent
        self.data = []

        # defaults from the specification
        self.id = -1
        self.name = None
        self.width = 0
        self.height = 0
        self.opacity = 1.0
        self.visible = True
        self.offsetx = 0
        self.offsety = 0

        self.parse_xml(node)

    def __iter__(self):
        return self.iter_data()

    def iter_data(self):
        """Iterate over layer data yielding X, Y, GID tuples."""
        for y, row in enumerate(self.data):
            for x, gid in enumerate(row):
                yield (x, y, gid)

    def tiles(self):
        """ Iterate over tile images of this layer

        This is an optimised generator function that returns
        (tile_x, tile_y, tile_image) tuples,

        :rtype: Generator
        :return: (x, y, image) tuples
        """
        images = self.parent.images
        for x, y, gid in [i for i in self.iter_data() if i[2]]:
            yield x, y, images[gid]

    def parse_xml(self, node):
        """
        Parse a Tile Layer from ElementTree xml node

        :param node: ElementTree xml node
        :return: self
        """
        self.set_properties(node)
        self.set_attributes(node.items(), orm=HW_ORM)
        data = None
        next_gid = None
        data_node = node.find('data')
        encoding = data_node.get('encoding', None)

        if encoding == 'base64':
            data = b64decode(data_node.text.strip())

        elif encoding == 'csv':
            next_gid = map(
                int,
                ''.join(line.strip() for line in
                        data_node.text.strip()).split(',')
            )

        elif encoding:
            raise Exception(f'TMX encoding type: {encoding} is not supported.')

        compression = data_node.get('compression', None)
        if compression == 'gzip':
            with gzip.GzipFile(fileobj=BytesIO(data)) as fh:
                data = fh.read()

        elif compression == 'zlib':
            data = zlib.decompress(data)

        elif compression:
            raise Exception(f'TMX compression type: {compression} is not supported.')

        # If data is None, then it was not decoded or decompressed, so
        # we assume here that it is going to be a bunch of tile elements
        # TODO: this will/should raise an exception if there are no tiles
        if encoding == next_gid is None:
            def get_children(parent):
                for child in parent.findall('tile'):
                    yield int(child.get('gid'))

            next_gid = get_children(data_node)

        elif data:
            if isinstance(data, bytes):
                fmt = struct.Struct('<L')
                iterator = (data[i:i + 4] for i in range(0, len(data), 4))
                next_gid = (fmt.unpack(i)[0] for i in iterator)
            else:
                raise Exception(f'Layer data not in expected format. Got: ({type(data)})')

        init = lambda: [0] * self.width
        reg = self.parent.register_gid

        self.data = tuple(array.array('L', init()) for i in range(self.height))
        for (y, x) in product(range(self.height), range(self.width)):
            self.data[y][x] = reg(*decode_gid(next(next_gid)))
        return self


class TiledObjectGroup(TiledElement, MutableSequence):
    """Represents a Tiled ObjectGroup."""

    __slots__ = (
        'parent', 'sequence_data', 'name', 'color', 'opacity', 'visible',
        'offsetx', 'offsety', 'draworder', 'id',
    )

    def __init__(self, parent, node):
        super().__init__()
        self.parent = parent
        self.sequence_data = []

        # defaults from the specification
        self.name = None
        self.color = None
        self.opacity = 1
        self.visible = 1
        self.offsetx = 0
        self.offsety = 0
        self.draworder = 'topdown'
        self.id = -1
        self.parse_xml(node)

    def __lt__(self, other):
        return self.sequence_data < self.__cast(other)

    def __le__(self, other):
        return self.sequence_data <= self.__cast(other)

    def __eq__(self, other):
        return self.sequence_data == self.__cast(other)

    def __gt__(self, other):
        return self.sequence_data > self.__cast(other)

    def __ge__(self, other):
        return self.sequence_data >= self.__cast(other)

    def __cast(self, other):
        return other.list_data if isinstance(other, TiledObjectGroup) else other

    def __contains__(self, item):
        return item in self.sequence_data

    def __len__(self):
        return len(self.sequence_data)

    def __getitem__(self, i):
        return self.sequence_data[i]

    def __setitem__(self, i, item):
        self.sequence_data[i] = item

    def __delitem__(self, i):
        del self.sequence_data[i]

    def __add__(self, other):
        if isinstance(other, TiledObjectGroup):
            return self.__class__(self.sequence_data + other.sequence_data)
        elif isinstance(other, type(self.sequence_data)):
            return self.__class__(self.sequence_data + other)
        return self.__class__(self.sequence_data + list(other))

    def __radd__(self, other):
        if isinstance(other, TiledObjectGroup):
            return self.__class__(other.sequence_data + self.sequence_data)
        elif isinstance(other, type(self.sequence_data)):
            return self.__class__(other + self.sequence_data)
        return self.__class__(list(other) + self.sequence_data)

    def __iadd__(self, other):
        if isinstance(other, TiledObjectGroup):
            self.sequence_data += other.sequence_data
        elif isinstance(other, type(self.sequence_data)):
            self.sequence_data += other
        else:
            self.sequence_data += list(other)
        return self

    def __mul__(self, n):
        return self.__class__(self.sequence_data * n)

    __rmul__ = __mul__

    def __imul__(self, n):
        self.sequence_data *= n
        return self

    def append(self, item):
        self.sequence_data.append(item)

    def insert(self, i, item):
        self.sequence_data.insert(i, item)

    def pop(self, i=-1):
        return self.sequence_data.pop(i)

    def remove(self, item):
        self.sequence_data.remove(item)

    def clear(self):
        self.sequence_data.clear()

    def copy(self):
        return self.__class__(self)

    def count(self, item):
        return self.sequence_data.count(item)

    def index(self, item, *args):
        return self.sequence_data.index(item, *args)

    def reverse(self):
        self.sequence_data.reverse()

    def sort(self, *args, **kwds):
        self.sequence_data.sort(*args, **kwds)

    def extend(self, other):
        if isinstance(other, TiledObjectGroup):
            self.sequence_data.extend(other.sequence_data)
        else:
            self.sequence_data.extend(other)

    def parse_xml(self, node):
        """
        Parse an Object Group from ElementTree xml node

        :param node: ElementTree xml node
        :return: self
        """
        self.set_properties(node)
        self.set_attributes(node.items())
        self.extend(TiledObject(self.parent, child)
                    for child in node.findall('object'))
        return self


class TiledObject(TiledElement):
    """
    Represents a any Tiled Object

    Supported types: Box, Ellipse, Tile Object, Polyline, Polygon
    """
    __slots__ = (
        'parent', 'id', 'name', 'type', 'x', 'y', 'width', 'height',
        'rotation', 'gid', 'visible', 'template',
    )

    def __init__(self, parent, node):
        super().__init__()
        self.parent = parent

        # Defaults from the specification
        self.id = 0
        self.name = None
        self.type = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.rotation = 0
        self.gid = 0
        self.visible = 1
        self.template = None

        self.parse_xml(node)

    @property
    def image(self):
        if self.gid:
            return self.parent.images[self.gid]
        return None

    def parse_xml(self, node):
        """
        Parse an Object from ElementTree xml node

        :param node: ElementTree xml node
        :return: self
        """

        def read_points(text):
            """Parse a text string of float tuples and return [(x,...),...]."""
            return tuple(tuple(map(float, i.split(','))) for i in text.split())

        self.set_properties(node)
        self.set_attributes(node.items())

        # correctly handle "tile objects" (object with gid set)
        if self.gid:
            self.gid = self.parent.register_gid(self.gid)

        points = None
        polygon = node.find('polygon')
        if polygon is not None:
            points = read_points(polygon.get('points'))
            self.closed = True

        polyline = node.find('polyline')
        if polyline is not None:
            points = read_points(polyline.get('points'))
            self.closed = False

        if points:
            x1 = x2 = y1 = y2 = 0
            for x, y in points:
                if x < x1:
                    x1 = x
                if x > x2:
                    x2 = x
                if y < y1:
                    y1 = y
                if y > y2:
                    y2 = y
            self.width = abs(x1) + abs(x2)
            self.height = abs(y1) + abs(y2)
            self.points = tuple(
                [(i[0] + self.x, i[1] + self.y) for i in points])

        return self


class TiledImageLayer(TiledElement):
    """
    Represents Tiled Image Layer

    The image associated with this layer will be loaded and assigned a GID.
    """
    __slots__ = (
        'parent', 'source', 'trans', 'gid', 'name', 'opacity', 'visible',
    )

    def __init__(self, parent, node):
        super().__init__()
        self.parent = parent
        self.source = None
        self.trans = None
        self.gid = 0

        # defaults from the specification
        self.name = None
        self.opacity = 1
        self.visible = 1

        self.parse_xml(node)

    @property
    def image(self):
        if self.gid:
            return self.parent.images[self.gid]
        return None

    def parse_xml(self, node):
        """ Parse an Image Layer from ElementTree xml node

        :param node: ElementTree xml node
        :return: self
        """
        self.set_properties(node)
        self.set_attributes(node.items())
        self.name = node.get('name', None)
        self.opacity = node.get('opacity', self.opacity)
        self.visible = node.get('visible', self.visible)
        image_node = node.find('image')
        self.source = image_node.get('source', None)
        self.trans = image_node.get('trans', None)
        return self


class TiledProperty(TiledElement):
    """Represents Tiled Property."""
    __slots__ = ('name', 'type', 'value', )

    def __init__(self, parent, node):
        super().__init__()

        # Defaults from the specification
        self.name = None
        self.type = None
        self.value = None

        self.parse_xml(node)

    def parse_xml(self, node):
        pass

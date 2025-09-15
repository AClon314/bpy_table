"""like jQuery, but for Blender Python API (bpy)
```python
from bpyQuery import b q
scale_x, scale_y = bq.ui_scale
```
"""

import bpy
from typing import Sequence
from .typo import *
import logging


def getLogger(name=__name__):
    _log_handler = logging.StreamHandler()
    _log_handler.setLevel(logging.DEBUG)
    _log_handler.setFormatter(
        logging.Formatter(
            "%(levelname)s %(asctime)s %(name)s\t%(message)s",
            datefmt="%H:%M:%S",
        )
    )
    Log = logging.getLogger(name)
    Log.handlers.clear()
    Log.addHandler(_log_handler)  # bpy hijack the logging output
    return Log


Log = getLogger(__name__)


def Get(obj, attr: str | Sequence[str], root=False):
    """injected recursive getattr, could pollute objects on chain in whole session"""
    IS_STR = isinstance(attr, str)
    if IS_STR and attr.startswith("__") and attr != "__getattribute__":
        return object.__getattribute__(obj, attr)
    E: Exception | None = None
    objs = obj if root else (obj,)
    for i, o in enumerate(objs):
        at = attr if IS_STR else attr[i]
        try:
            obj_inject = getattr(o, at)
            setattr(obj_inject, "__getattribute__", Get)
            return obj_inject
        except AttributeError as e:
            if " object attribute '__getattribute__' is read-only" in str(e):
                return obj_inject
            E = e
    if E:
        raise E
    else:
        raise


class var:
    """var"""

    def __init__(
        self, default=None, initValue=None, name="bqTmpVar", reg=True, **kwargs
    ):
        """
        split = var('') # reg in scene.split temperarily

        class Group:
            split = var('')
        """
        self.default = default
        self.initValue = initValue
        self.name = name
        self.kwargs = kwargs
        if initValue is not None:
            self.default = initValue
        if reg and name:
            self.reg()

    @property
    def raw(self):
        return propString(name=self.name, default=self.default, **self.kwargs)  # type: ignore

    @property
    def value(self): ...

    def draw(self): ...

    def reg(self):
        setattr(bpy.types.Scene, self.name, self.raw)

    def __getattr__(self, name: str):
        def init(default=None, initValue=None, name=name, reg=True, **kwargs):
            return var(default, initValue, name, reg, **kwargs)

        return init


class bpq(GlobalContext):
    """Usage:
    - bq.scene
    - bq.ui_scale
    """

    new = var()

    def __getattr__(self, name: str):
        Name = globalContextType.get(name, None)
        if Name is None:
            return object.__getattribute__(bpy.context, name)
        return Get([bpy.context, bpy.types], [name, Name], root=True)

    @property
    def ui_scale(self):
        """https://blenderartists.org/t/node-editor-zoom-level/1478930"""
        region = bpy.context.region
        if not region:
            raise ValueError("region is None")
        v2d = region.view2d

        # Convert region size into view2d rectangle (absolute).
        x1, y1 = v2d.region_to_view(0, 0)
        x2, y2 = v2d.region_to_view(region.width, region.height)

        # Convert to view2d size.
        v2d_w = x2 - x1
        v2d_h = y2 - y1

        # Convert to scale.
        scale_x = region.width / v2d_w
        scale_y = region.height / v2d_h
        base = bpy.context.preferences.system.ui_scale  # type: ignore
        scale_x, scale_y = scale_x * base, scale_y * base
        return scale_x, scale_y

    @staticmethod
    def reg(
        Class: type[bpy.types.PropertyGroup],
        prop: "bpy_props_Property | None",
        name: str = "",
    ):
        """register_class & setattr"""
        if not name:
            name = Class.__name__
        bpy.utils.register_class(Class)
        setattr(bpy.types.Scene, name, prop)

    @staticmethod
    def unreg(Class: type[bpy.types.PropertyGroup], name: str = ""):
        """delattr & unregister_class"""
        if not name:
            name = Class.__name__
        delattr(bpy.types.Scene, name)
        bpy.utils.unregister_class(Class)

    @staticmethod
    def regCollectionProp(
        cls_name: str,
        cls_bases: "Sequence[bpy_types_Property]",
        var_type: "dict[str, bpy_props_Property]",
    ):
        """Because the registered class member is strictly readonly , so you have to mount dynamic class to bpy.types.Scene"""
        if not cls_name.isidentifier():
            raise ValueError(f"Invalid class name: {cls_name}")
        attrs = {"__annotations__": var_type}
        Log.debug(f"{attrs=}")
        cls = type(cls_name, cls_bases, attrs)  # type:ignore
        bpq.reg(cls, bpy.props.CollectionProperty(type=cls))
        return cls

    @staticmethod
    def draw(layout: bpy.types.UILayout, data: "var", *args, **kwargs):
        """Draw the UI elements"""
        layout.prop(bpq.scene, "name")


bq = bpq()
bpy.bq = bq  # type: ignore
bpy.var = var  # type: ignore

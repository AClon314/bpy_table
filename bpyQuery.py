"""jQuery, but in Blender Python API (bpy)
```python
from bpyQuery import b q
scale_x, scale_y = bq.ui_scale
```
"""

import os
import bpy
import functools
from datetime import datetime
from typing import Sequence
from .typo import *

__version__ = (
    datetime.fromtimestamp(os.path.getmtime(__file__))
    if globals().get("__file__")
    else datetime.now()
).strftime("%Y.%m.%d.%H.%M.%S")
Log = getLogger(__name__)
NONE = object()


def rgetattr(obj, *attr: str, default=NONE):
    """Recursive getattr, like jQuery `$('a.b.c')`"""
    if not attr:
        return obj

    def _getattr(obj, attr: str):
        # Log.debug(f"_getattr {obj=}, {attr=}")
        v = getattr(obj, attr, default)
        if v is NONE:
            raise AttributeError(f"{obj}.{attr} not found")
        return v

    return functools.reduce(_getattr, attr, obj)


def rsetattr(obj, *attr: str, value):
    """Recursive setattr, like jQuery `$('a.b.c', value)`"""
    if len(attr) < 1:
        raise ValueError("At least one attribute name must be provided")

    *pre, post = attr  # 使用解包获取路径和属性名
    if pre:  # 如果有路径部分
        target = rgetattr(obj, *pre)
    else:  # 如果只有一个属性名
        target = obj

    return setattr(target, post, value)


def ref(obj, *attr):
    """Generate property that get/set obj.a.b.c"""

    def getter(self):
        return rgetattr(obj, *attr)

    def setter(self, value):
        rsetattr(obj, *attr, value=value)

    prop = property(getter, setter)
    return prop


class var:
    """
    blender RNA property wrapper, like `ref()` in vue.
    Always lazy load, so you need call `reg()` or access `value` property to register it.

    Args:
        default : the default value, that will restore when hit `backspace` key on UI property field.
        initValue : the initial value, that only set **ONCE** when register the property, compared to `default`
        name : the property name in blender RNA system, must be
            - not startwith `_`
            - name.isidentifier(), comply python variable naming rules
            - unique, prevent override existing property

    Usage:
    ```python
    txt = var('')

    class VarGroup:
        txt = var('')
    ```
    """

    def __init__(self, varname: str, **kwargs):
        if not varname.isidentifier() or varname.startswith("_"):
            raise ValueError(
                f"Invalid property {varname=}, must not startwith _ and comply python variable naming rules"
            )
        self.varname = varname

    def __call__(
        self,
        default: Any | None = None,
        initValue: Any | None = None,
        **kwargs,
    ):
        self.default = default
        self.initValue = initValue
        self.kwargs = kwargs

    @property
    def value(self):
        if self.varname:
            self.reg()
        return getattr(bq.var, self.varname)

    @property
    def prop(self):
        return Prop(self)

    def draw(self, layout: bpy.types.UILayout, **kwargs):
        bpq.draw(layout, self, **kwargs)

    def reg(self, on: TypesTypes = bpy.types.Scene):
        def unreg():
            self.unreg(on)

        if self.varname in dir(bq.var):
            Log.warning(f"Property {self.varname} already registered")
        else:
            setattr(bq.var, self.varname, self)
        if hasattr(on, self.varname):
            Log.debug(msg=f"Property {self.varname} already exists on {on}")
            return unreg
        setattr(on, self.varname, self.prop)
        return unreg

    def unreg(self, on: TypesTypes = bpy.types.Scene):
        if hasattr(on, self.varname):
            delattr(on, self.varname)
        else:
            Log.warning(f"{type(self.prop)} {self.varname} not found {on=}")


def is_bpy_prop(instance: object, *clsName: str):
    _class_ = instance.__class__.__class__
    name = _class_.__name__
    # if _class_.__module__ != "builtins":
    #     name = f"{_class_.__module__}.{_class_.__name__}"
    # isinstance(instance, (bool, int, float, str)) or
    return name in clsName


class GlobalVar:
    """类似pinia，无须顾虑挂载在scene还是object上

    Usage:
    ```python
    myProp = var(0)             # var(), lazy load, with random varname
    myProp = bq.var.myProp(0)   # var(), lazy load, raise Exception if registered
    bq.var.myProp == bq.scene.myProp   # can get/set the var
    dir(bq.var)  # list all registered vars
    bq.draw(bq.var.myProp) # draw on UI layout
    ```
    """

    def __refresh__(
        self,
        scope: Sequence[
            Literal["_RNAMetaPropGroup", "bpy_prop_array", "_PropertyDeferred"]
        ] = [
            "_RNAMetaPropGroup",
            "bpy_prop_array",
        ],
    ):
        """Refresh __dict__ == setattr"""
        for k_gv in dir(self):
            if k_gv.startswith("__"):
                continue
            delattr(self, k_gv)
        for k_cd in dir(ContextData):
            if k_cd.startswith("__"):
                continue
            prop = getattr(ContextData, k_cd)
            if isinstance(prop, property):
                # fget: descriptor protocol
                value = prop.fget(ContextData) if prop.fget else None
            else:
                value = prop
            for k_v in dir(value):
                if k_v.startswith("__"):
                    continue
                _v_ = getattr(value, k_v)
                # Log.debug(f"  {k_v} = {_v_} {type(_v_)} {type(_v_.__class__)}")
                if is_bpy_prop(_v_, *scope):
                    # TODO: weakref? memory GC issue?
                    setattr(self, k_v, _v_)
                    Log.debug(f"Refresh✅ {k_cd}.{k_v} = {_v_}")
                elif isinstance(_v_, (bool, int, float, str)):
                    self.__ref__(k_cd, k_v)
                    Log.debug(f"__ref__✅ {k_cd}.{k_v} = {_v_}")

    def __ref__(self, *attr):
        prop = ref(bpy.context, *attr)
        setattr(self, attr[-1], prop)

    def __getattribute__(self, name: str):
        """# TODO:"""
        # try:
        return object.__getattribute__(self, name)
        # except AttributeError as e:
        #     self.__dict__.pop(name)
        #     if name not in self.__dict__.keys():
        #         return var(name)


class bpq(ContextData):
    """jQuery but in blender python API (bpy)"""

    var = GlobalVar()
    version = __version__

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
        prop: "PropsProperty | None",
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
        cls_bases: "Sequence[TypesProperty]",
        var_type: "dict[str, PropsProperty]",
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
    def draw(layout: bpy.types.UILayout, data: "var", **kwargs):
        """Draw the UI elements"""
        layout.prop(bpq.scene, "name", **kwargs)

    @staticmethod
    def hook():
        """hook bpy.utils.register_class & unregister_class"""
        old_reg = bpy.utils.register_class
        old_unreg = bpy.utils.unregister_class

        @functools.wraps(old_reg)
        def hooked_register_class(cls):
            Log.debug(f"register_class {cls}")
            return old_reg(cls)

        @functools.wraps(old_unreg)
        def hooked_unregister_class(cls):
            Log.debug(f"unregister_class {cls}")
            return old_unreg(cls)

        # 应用钩子
        bpy.utils.register_class = hooked_register_class
        bpy.utils.unregister_class = hooked_unregister_class
        return old_reg, old_unreg

    def inject(self, force=False):
        """only inject the newest version by default"""
        import builtins

        BQ = getattr(builtins, "bq", None)
        if force or not BQ or self.version > BQ.version:
            builtins.bq = self  # type: ignore
            Log.debug(f"injected bq (v{self.version})")
        else:
            Log.warning(
                f"{__package__}.bq (v{self.version}) < injected {BQ.version}, skip"
            )


bq = bpq()
bq.inject()

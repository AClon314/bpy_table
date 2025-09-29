"""jQuery, but in Blender Python API (bpy)
```python
from bpyQuery import b q
scale_x, scale_y = bq.ui_scale
```
"""

import os
import re
import bpy
import inspect
import functools
from datetime import datetime
from typing import Sequence
from .typo import *
from .typo import _TV

__version__ = (
    datetime.fromtimestamp(os.path.getmtime(__file__))
    if globals().get("__file__")
    else datetime.now()
).strftime("%Y.%m.%d.%H.%M.%S")
Log = getLogger(__name__)
RE_VARNAME = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


def rgetattr(obj, *attr: str, default=Undef):
    """Recursive getattr, like jQuery `$('a.b.c')`"""
    if not attr:
        return obj

    def _getattr(obj, attr: str):
        # Log.debug(f"_getattr {obj=}, {attr=}")
        v = getattr(obj, attr, default)
        if v is Undef:
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


def prop_cls(obj, *attr, self: Any = None):
    """Generate property that get/set obj.a.b.c

    Usage:
    ```python
    setattr(self.__class__, attr[-1], prop) # @property must set in `self.__class__`, not `self`
    ```
    """
    if self:
        setattr(self, "_obj_attr_", (obj, attr))

        def getter(self):
            return rgetattr(self._obj_attr_[0], *self._obj_attr_[1])

        def setter(self, value):
            rsetattr(self._obj_attr_[0], *self._obj_attr_[1], value=value)

    else:

        def getter(self):
            return rgetattr(obj, *attr)

        def setter(self, value):
            rsetattr(obj, *attr, value=value)

    prop = property(getter, setter)
    return prop


def get_varname(index=2):
    """inspect `varname = Var()`, could fallback to "tmp"
    # TODO: support var1, var2, *vars, var3 = ..."""
    stack = inspect.stack()
    varname = "tmp"
    # Log.debug(f"{[st.code_context for st in stack]}")
    frame_info = stack[index]
    code_context = frame_info.code_context
    if not code_context:
        # https://docs.blender.org/api/current/bpy.types.SpaceConsole.html
        con: bpy.types.SpaceConsole = bpy.context.area.spaces.active  # type: ignore
        code = con.history.items()[-1][-1].body
    else:
        code = "".join(code_context).strip()
    # Log.debug(f"{code=}")
    if "=" in code:
        match = RE_VARNAME.search(code)
        if match:
            varname = match.group(0)
    if not varname.isidentifier() or varname.startswith("_"):
        raise ValueError(
            f"Invalid property {varname=}, must not startwith _ and comply python variable naming rules"
        )
    elif varname == "tmp":
        Log.warning(
            f"inspect varname failed, specify varname explicitly, now {varname=}"
        )
    return varname


_TV_ID = TypeVar("_TV_ID", bound=bpy.types.ID)
_TV_PROP_GROUP = TypeVar("_TV_PROP_GROUP", bound=bpy.types.PropertyGroup)


class Var(Generic[_TV]):
    """
    blender RNA property wrapper, like `ref()` in vue.
    Always lazy load, so you need call `reg()` or access `value` property to register it.

    Args:
        default : the default value, that will restore when hit `backspace` key on UI property field.
        value : the initial value, that only set **ONCE** when register the property, compared to `default`
        name : the property name in blender RNA system, must be
            - not startwith `_`
            - name.isidentifier(), comply python variable naming rules
            - unique, prevent override existing property

    Usage:
    ```python
    txt = Var('')

    class VarGroup:
        txt = Var('')
    ```
    """

    @property
    def value(self) -> _TV:
        return rgetattr(self._obj_attr_[0], *self._obj_attr_[1])  # type: ignore

    @value.setter
    def value(self, value: _TV):
        rsetattr(self._obj_attr_[0], *self._obj_attr_[1], value=value)

    @property
    def prop(self):
        """Generate an instance of _DeferredProperty, used for mounted on bpy.types.*.*"""
        prop, initValue = DeferredProp(
            value=self.initValue, size=self.size, **self.kwargs
        )
        self.value = initValue
        return prop

    def draw(self, layout: bpy.types.UILayout, **kwargs):
        bpq.draw(layout, self, **kwargs)

    def reg(self, at: TypesTypes | None = None):
        if at is None:
            Log.debug(f"{at=}, Var.reg() use {self.regAt=}")
            at = self.regAt
        if hasattr(at, self.varname):
            Log.error(f"Property {self.varname} already exists {at=}")
            return self
        prop = self.prop
        setattr(at, self.varname, prop)
        _prop = prop_cls(bpy.context, at.__name__.lower(), self.varname, self=self)
        setattr(GlobalVar, self.varname, _prop)
        if self.value:
            self.value = self.value
        Log.debug(f"reg {self.varname}{prop} {at=}")
        return self

    def unreg(self, at: TypesTypes | None = None):
        if at is None:
            Log.debug(f"{at=}, Var.unreg() use {self.regAt=}")
            at = self.regAt
        if hasattr(at, self.varname):
            delattr(at, self.varname)
            delattr(bq.var, self.varname)
        else:
            Log.warning(f"{type(self.prop)} {self.varname} not found {at=}")

    def __del__(self) -> None:
        self.unreg()

    @overload
    def __init__(
        self: "Var[bool]",
        value: bool | type[bool],
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropBool],
    ): ...

    @overload
    def __init__(
        self: "Var[int]",
        value: int | type[int],
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropInt],
    ): ...

    @overload
    def __init__(
        self: "Var[float]",
        value: float | type[float],
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropFloat],
    ): ...

    @overload
    def __init__(
        self: "Var[str]",
        value: str | type[str],
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropStr],
    ): ...

    @overload
    def __init__(
        self: "Var[Iterable[bool]]",
        value: Iterable[bool] | type[bool],
        *,
        size: int | None = None,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropBool],
    ): ...

    @overload
    def __init__(
        self: "Var[Iterable[int]]",
        value: Iterable[int] | type[int],
        *,
        size: int | None = None,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropInt],
    ): ...

    @overload
    def __init__(
        self: "Var[Iterable[float]]",
        value: Iterable[float] | type[float],
        *,
        size: int | None = None,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropFloat],
    ): ...

    @overload
    def __init__(
        self: "Var[_TV_PROP_GROUP]",
        type: type[_TV_PROP_GROUP],
        /,
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropPointer],
    ):
        """PointerProperty of PropertyGroup"""

    @overload
    def __init__(
        self: "Var[_TV_ID]",
        type: type[_TV_ID],
        /,
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropPointer],
    ):
        """PointerProperty of bpy.types.ID type"""

    @overload
    def __init__(
        self,
        items: (
            Iterable[tuple[str, str, str]]
            | Callable[
                [bpy.types.bpy_struct, bpy.types.Context | None],
                Iterable[tuple[str, str, str]],
            ]
        ),
        /,
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[_PropDUGS[str]],
    ):
        """EnumProperty
        
        Args:
            items (Iterable[identifier, name, description] or function(self, context) -> Iterable[identifier, name, description]):
                full: [(identifier, name, description, icon, number), ...]
                > There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
                使用回调存在一个已知的错误，Python 必须保留对回调返回的字符串的引用，否则 Blender 会行为异常甚至崩溃。
        """

    @overload
    def __init__(
        self: "Var[CollectionProperty[_TV_PROP_GROUP]]",
        type: type[_TV_PROP_GROUP],
        /,
        *,
        size: int | None = None,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[_PropBase],
    ):
        """CollectionProperty"""

    def __init__(
        self,
        value: Any = None,
        *,
        size: int | None = None,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs,
    ):
        """

        Args:
            reg: if None, don't register to bpy.types.* automatically.
        """
        if not varname:
            varname = get_varname()
        if not varname.isidentifier() or varname.startswith("_"):
            raise ValueError(
                f"Invalid property {varname=}, must not startwith _ and comply python variable naming rules"
            )
        self.varname = varname
        self.initValue = value
        self.size = size
        self.kwargs = kwargs
        self._obj_attr_ = (self, ())
        Log.debug(f"__init__ {self.__dict__=}")
        if reg:
            self.regAt = reg
            self.reg(self.regAt)


def is_bpy_prop(instance: object, *clsName: str):
    _class_ = instance.__class__.__class__
    name = _class_.__name__
    # if _class_.__module__ != "builtins":
    #     name = f"{_class_.__module__}.{_class_.__name__}"
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

    def _refresh_(
        self,
        scope: Sequence[
            Literal["bifs", "_RNAMetaPropGroup", "bpy_prop_array", "_PropertyDeferred"]
        ] = ["bifs", "_RNAMetaPropGroup", "bpy_prop_array"],
    ):
        """Refresh __dict__ == setattr(self.__class__, k, v)

        Args:
            scope: the class name filter. `bifs` means `bool, int, float, str`
        """
        is_bifs = "bifs" in scope
        for k_gv in dir(self):
            if not k_gv.startswith("_"):
                try:
                    delattr(self.__class__, k_gv)
                except AttributeError:
                    delattr(self, k_gv)
        for k_cd in dir(ContextData):
            if k_cd.startswith("_"):
                continue
            prop = getattr(ContextData, k_cd)
            if isinstance(prop, property):
                # fget: descriptor protocol
                value = prop.fget(ContextData) if prop.fget else None
            else:
                value = prop
            for k_v in dir(value):
                if k_v.startswith("_"):
                    continue
                _v_ = getattr(value, k_v)
                # Log.debug(f"  {k_v} = {_v_} {type(_v_)} {type(_v_.__class__)}")
                if is_bpy_prop(_v_, *scope):
                    # TODO: weakref? memory GC issue?
                    setattr(self, k_v, _v_)
                    # Log.debug(f"Refresh✅ {k_cd}.{k_v} = {_v_}")
                elif is_bifs and isinstance(_v_, (bool, int, float, str)):
                    self._prop_(k_cd, k_v)
                    # Log.debug(f"__ref__✅ {k_cd}.{k_v} = {_v_}")

    def _prop_(self, *attr):
        """__class__ effect the new created GlobalVar(), so GlobalVar need to be singleton"""
        prop = prop_cls(bpy.context, *attr)
        setattr(self.__class__, attr[-1], prop)

    def __getattribute__(self, name: str):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            self._refresh_()
            try:
                return object.__getattribute__(self, name)
            except AttributeError as e:
                raise e from None

    def __delattr__(self, name: str):
        delattr(self.__class__, name) if hasattr(self.__class__, name) else None

    @overload
    def __call__(
        self,
        value: bool | type[bool],
        *,
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropBool],
    ) -> Var[bool]: ...

    @overload
    def __call__(
        self,
        value: int | type[int],
        *,
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropInt],
    ) -> Var[int]: ...

    @overload
    def __call__(
        self,
        value: float | type[float],
        *,
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropFloat],
    ) -> Var[float]: ...

    @overload
    def __call__(
        self,
        value: str | type[str],
        *,
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropStr],
    ) -> Var[str]: ...

    @overload
    def __call__(
        self,
        value: Iterable[bool] | type[bool],
        *,
        size: int | None = None,
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropBool],
    ) -> Var[Iterable[bool]]: ...

    @overload
    def __call__(
        self,
        value: Iterable[int] | type[int],
        *,
        size: int | None = None,
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropInt],
    ) -> Var[Iterable[int]]: ...

    @overload
    def __call__(
        self,
        value: Iterable[float] | type[float],
        *,
        size: int | None = None,
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropFloat],
    ) -> Var[Iterable[float]]: ...

    @overload
    def __call__(
        self: "Var[_TV_PROP_GROUP]",
        type: type[_TV_PROP_GROUP],
        /,
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropPointer],
    ):
        """PointerProperty of PropertyGroup"""

    @overload
    def __call__(
        self: "Var[_TV_ID]",
        type: type[_TV_ID],
        /,
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[PropPointer],
    ):
        """PointerProperty of bpy.types.ID type"""

    @overload
    def __call__(
        self,
        items: (
            Iterable[tuple[_TV, str, str]]
            | Callable[
                [bpy.types.bpy_struct, bpy.types.Context | None],
                Iterable[tuple[_TV, str, str]],
            ]
        ),
        /,
        *,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[_PropDUGS[_TV]],
    ):
        """EnumProperty"""

    @overload
    def __call__(
        self: "Var[CollectionProperty[_TV_PROP_GROUP]]",
        type: type[_TV_PROP_GROUP],
        /,
        *,
        size: int | None = None,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs: Unpack[_PropBase],
    ):
        """CollectionProperty"""

    def __call__(
        self,
        value: Any = None,
        *,
        size: int | None = None,
        varname="",
        reg: TypesTypes | None = bpy.types.Scene,
        **kwargs,
    ) -> Var:
        """see Var()"""
        if not varname:
            varname = get_varname()
        return Var(value, size=size, varname=varname, reg=reg, **kwargs)


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

    @ui_scale.setter
    def ui_scale(self, scale: float | int | tuple[float | int, float | int]):
        """# TODO: Set UI scale by zooming view2d"""
        region = bpy.context.region
        if not region:
            raise ValueError("region is None")
        v2d = region.view2d
        base = bpy.context.preferences.system.ui_scale  # type: ignore
        scale = (scale, scale) if isinstance(scale, (float, int)) else scale
        sx, sy = scale
        if sx <= 0 or sy <= 0:
            raise ValueError(f"Invalid current scale {self.ui_scale=}")
        bpy.ops.view2d.zoom(deltax=sx, deltay=sy)

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
        # TODO
        if not cls_name.isidentifier():
            raise ValueError(f"Invalid class name: {cls_name}")
        attrs = {"__annotations__": var_type}
        Log.debug(f"{attrs=}")
        cls = type(cls_name, cls_bases, attrs)  # type:ignore
        bpq.reg(cls, bpy.props.CollectionProperty(type=cls))
        return cls

    @staticmethod
    def draw(layout: bpy.types.UILayout, var: Var, **kwargs: Unpack[LayoutProp]):
        """Draw the UI elements. Equal to:
        ```python
        layout.prop(bpy.context.scene, var.varname, **kwargs)
        ```
        """
        return layout.prop(var.regAt, var.varname, **kwargs)

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

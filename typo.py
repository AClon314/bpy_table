"""typing"""

import bpy
import logging
import itertools
from functools import partial
from typing import *  # type: ignore


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

dict_strAny = dict[str, Any]
_PS = ParamSpec("_PS")
_TV = TypeVar("_TV")
FLOAT_MAX_3E38 = 3.402823e38
TypesProperty = Union[
    type(bpy.types.BoolProperty),
    type(bpy.types.IntProperty),
    type(bpy.types.FloatProperty),
    type(bpy.types.StringProperty),
    type(bpy.types.EnumProperty),
    type(bpy.types.PointerProperty),
    type(bpy.types.CollectionProperty),
    type(bpy.types.PropertyGroup),
]
PropsProperty = Union[
    type(bpy.props.BoolProperty),
    type(bpy.props.BoolVectorProperty),
    type(bpy.props.IntProperty),
    type(bpy.props.IntVectorProperty),
    type(bpy.props.FloatProperty),
    type(bpy.props.FloatVectorProperty),
    type(bpy.props.StringProperty),
    type(bpy.props.EnumProperty),
    type(bpy.props.PointerProperty),
    type(bpy.props.CollectionProperty),
]
PY_TO_PROP: dict[type | tuple[type, ...], Callable[..., PropsProperty]] = (
    {  # type:ignore
        # Iterable[bool]: bpy.props.BoolVectorProperty,
        # Iterable[int]: bpy.props.IntVectorProperty,
        # Iterable[float]: bpy.props.FloatVectorProperty,
        bool: bpy.props.BoolProperty,
        int: bpy.props.IntProperty,
        float: bpy.props.FloatProperty,
        str: bpy.props.StringProperty,
        # enum: bpy.props.EnumProperty,
        # object: bpy.props.PointerProperty,
    }
)
TypesTypes = Union[
    type(bpy.types.WindowManager),
    type(bpy.types.Screen),
    type(bpy.types.Scene),
    type(bpy.types.ViewLayer),
    type(bpy.types.WorkSpace),
    type(bpy.types.Collection),
    type(bpy.types.Object),
    type(bpy.types.GreasePencilv3),
]
ContextTypes = {
    "window_manager": "WindowManager",
    "screen": "Screen",
    "scene": "Scene",
    "view_layer": "ViewLayer",
    "workspace": "WorkSpace",
    "collection": "Collection",
    "object": "Object",
    "grease_pencil": "GreasePencilv3",
}
Log.debug(f"ContextTypes: {ContextTypes}")


class _Undef:
    """https://cloud.tencent.com/developer/ask/sof/113806020/answer/128423472"""

    def __new__(cls):
        return Undef

    def __reduce__(self):
        return (_Undef, ())

    def __copy__(self):
        return Undef

    def __deepcopy__(self, memo):
        return Undef

    def __call__(self, default): ...

    def __bool__(self):
        return False


Undef = object.__new__(_Undef)


class ContextData:
    """
    len()=7. Sort by variable scope. 根据变量作用域排序

    \\| attr | save | note |
    | ---- | ---- | ---- |
    | **window_manager** | X | temporary global:<br> keep during entire blender session,<br> but will **LOSE** all data after re-open .blend file |
    | **scene** | √ | **Default**, data won't share across scene.<br> we have 1 scene at least, so datas are mounted here by default |
    | scenes | √ | once keyname is const, it's a const pointer, eg: bpy.data.scenes['Scene'] |
    """

    @property
    def window_manager(self) -> bpy.types.WindowManager:
        """# The ONLY ONE that is global but NO SAVE
        keep during entire blender session, but will **LOSE** all data after re-open .blend file.
        """
        return bpy.context.window_manager  # type: ignore

    @property
    def screen(self) -> bpy.types.Screen:
        """No share data across windows+workspace, eg:
        - **temp**: when you open a window, like render result
        - Default: when you open another **MAIN** window
        - workspace: Layout/Modeling..."""
        return bpy.context.screen  # type: ignore

    @property
    def scene(self) -> bpy.types.Scene:
        """**Default**, no share data across scenes. We have 1 scene at least, so datas are mounted here by default"""
        return bpy.context.scene  # type: ignore

    @property
    def view_layer(self) -> bpy.types.ViewLayer:
        """No share data across view layers, similar to scene. We have 1 view layer at least."""
        return bpy.context.view_layer  # type: ignore

    @property
    def workspace(self) -> bpy.types.WorkSpace:
        """No share data across workspace, eg: Layout/Modeling/Sculpting... We have 1 workspace at least."""
        return bpy.context.workspace  # type: ignore

    @property
    def collection(self) -> bpy.types.Collection:
        """Collection of Object data-blocks. We have 1 scene collection at least."""
        return bpy.context.collection  # type: ignore

    @property
    def object(self):
        """Object data-block defining an object in a scene"""
        return bpy.context.object  # type: ignore

    @property
    def grease_pencil(self):
        """Grease Pencil data-block. # TODO: v3"""
        return bpy.context.grease_pencil  # type: ignore

    @property
    def window_managers(self):
        return bpy.data.window_managers

    @property
    def screens(self):
        return bpy.data.screens

    @property
    def scenes(self):
        """bpy.data.scenes, return a list"""
        return bpy.data.scenes

    @property
    def workspaces(self):
        return bpy.data.workspaces

    @property
    def collections(self):
        return bpy.data.collections

    @property
    def objects(self):
        return bpy.data.objects

    @property
    def grease_pencils(self):
        return bpy.data.grease_pencils_v3

    @property
    def libraries(self):
        return bpy.data.libraries

    @property
    def masks(self):
        return bpy.data.masks

    @property
    def armatures(self):
        return bpy.data.armatures

    @property
    def volumes(self):
        return bpy.data.volumes

    @property
    def node_groups(self):
        return bpy.data.node_groups

    @property
    def cache_files(self):
        return bpy.data.cache_files

    @property
    def particles(self):
        return bpy.data.particles

    @property
    def speakers(self):
        return bpy.data.speakers

    @property
    def paint_curves(self):
        return bpy.data.paint_curves

    @property
    def cameras(self):
        return bpy.data.cameras

    @property
    def movieclips(self):
        return bpy.data.movieclips

    @property
    def texts(self):
        return bpy.data.texts

    @property
    def curves(self):
        return bpy.data.curves

    @property
    def linestyles(self):
        return bpy.data.linestyles

    @property
    def shape_keys(self):
        return bpy.data.shape_keys

    @property
    def worlds(self):
        return bpy.data.worlds

    @property
    def lightprobes(self):
        return bpy.data.lightprobes

    @property
    def lattices(self):
        return bpy.data.lattices

    @property
    def meshes(self):
        return bpy.data.meshes

    @property
    def metaballs(self):
        return bpy.data.metaballs

    @property
    def actions(self):
        return bpy.data.actions

    @property
    def images(self):
        return bpy.data.images

    @property
    def brushes(self):
        return bpy.data.brushes

    @property
    def materials(self):
        return bpy.data.materials

    @property
    def palettes(self):
        return bpy.data.palettes

    @property
    def sounds(self):
        return bpy.data.sounds

    @property
    def textures(self):
        return bpy.data.textures

    @property
    def lights(self):
        return bpy.data.lights

    @property
    def pointclouds(self):
        return bpy.data.pointclouds

    @property
    def hair_curves(self):
        return bpy.data.hair_curves

    @property
    def fonts(self):
        return bpy.data.fonts


class CollectionProperty(list[_TV], Generic[_TV]):
    """typing for bpy.props.CollectionProperty"""

    def add(self) -> _TV: ...


class _PropBase(TypedDict, total=False):
    """Collection has least 6 args. Total 10 kinds of props"""

    name: str
    description: str
    translation_context: str
    options: set[
        Literal[
            "HIDDEN",
            "SKIP_SAVE",
            "SKIP_PRESENT",
            "ANIMATABLE",
            "LIBRARY_EDITABLE",
            "PROPORTIONAL",
            "TEXTEDIT_UPDATE",
            "OUTPUT_PATH",
            "PATH_SUPPORTS_BLEND_RELATIVE",
            "SUPPORTS_TEMPLATES",
        ]
    ]
    override: set[Literal["LIBRARY_OVERRIDABLE"]]
    tags: set[str]


# @dataclass
class PropCollection(_PropBase):
    """len(args)=7"""

    type: type[bpy.types.PropertyGroup]


SELF_CONTEXT = Callable[[bpy.types.bpy_struct, bpy.types.Context], None]


class PropPointer(_PropBase, total=False):
    """len(args)=9, bpy.types.* = bpy.props.PointerProperty(type=PropertyGroup)"""

    type: type[bpy.types.ID | bpy.types.PropertyGroup]
    poll: Callable[[bpy.types.bpy_struct, bpy.types.ID], bool]
    update: SELF_CONTEXT


class _PropDUGS(Generic[_TV], _PropBase, total=False):
    """len(args)=10"""

    default: _TV
    Update: SELF_CONTEXT
    Get: Callable[[bpy.types.bpy_struct], _TV]
    set: Callable[[bpy.types.bpy_struct, _TV], None]


class PropEnum(_PropDUGS[_TV]):
    """len(args)=11"""

    items: (
        Iterable[tuple[_TV, str, str]]
        | Callable[
            [bpy.types.bpy_struct, bpy.types.Context | None],
            Iterable[tuple[_TV, str, str]],
        ]
    )


class _Subtype(TypedDict, total=False):
    """`subtype` arg, except Pointer, Collection, Enum"""

    subtype: Literal[
        "PIXEL",
        "UNSIGNED",
        "PERCENTAGE",
        "FACTOR",
        "ANGLE",
        "TIME",
        "TIME_ABSOLUTE",
        "DISTANCE",
        "DISTANCE_CAMERA",
        "POWER",
        "TEMPERATURE",
        "WAVELENGTH",
        "COLOR_TEMPERATURE",
        "FREQUENCY",
        "NONE",
    ]


class PropBool(_PropDUGS[bool], _Subtype):
    """len(args)=11"""


class _PropNum(TypedDict, total=False):
    """len(args)=5"""

    min: int | float
    max: int | float
    soft_min: int | float
    soft_max: int | float
    step: int


class PropInt(_PropNum, _PropDUGS[int], _Subtype):
    """len(args)=16"""


class PropFloat(_PropNum, _PropDUGS[float], _Subtype, total=False):
    """len(args)=18"""

    precision: int
    unit: Literal[
        "NONE",
        "LENGTH",
        "AREA",
        "VOLUME",
        "ROTATION",
        "TIME",
        "TIME_ABSOLUTE",
        "VELOCITY",
        "ACCELERATION",
        "MASS",
        "CAMERA",
        "POWER",
        "TEMPERATURE",
        "WAVELENGTH",
        "COLOR_TEMPERATURE",
        "FREQUENCY",
    ]


# class _PropVec(TypedDict, total=False):
#     """size in [1, 32], default 3"""
#     size: int
# class PropBoolVector(_PropDUGS[Iterable[bool]], _PropVec): ...
# class PropIntVector(_PropDUGS[Iterable[int]], _PropVec): ...
# class PropFloatVector(_PropDUGS[Iterable[float]], _PropVec): ...
class PropStr(_PropDUGS, total=False):
    """len(args)=14"""

    maxlen: int
    search: Callable[
        [bpy.types.bpy_struct, bpy.types.Context, str], Iterable[str | tuple[str, str]]
    ]
    search_options: set[Literal["SORT", "SUGGESTION"]]


@overload
def PropDeferred(initValue: bool | type[bool], **kwargs: Unpack[PropBool]): ...


@overload
def PropDeferred(initValue: int | type[int], **kwargs: Unpack[PropInt]): ...


@overload
def PropDeferred(initValue: float | type[float], /, **kwargs: Unpack[PropFloat]): ...


@overload
def PropDeferred(initValue: str | type[str], **kwargs: Unpack[PropStr]): ...


@overload
def PropDeferred(
    initValue: Iterable[bool] | type[bool],
    size: int | None = None,
    **kwargs: Unpack[PropBool],
): ...


@overload
def PropDeferred(
    initValue: Iterable[int] | type[int],
    size: int | None = None,
    **kwargs: Unpack[PropInt],
): ...


@overload
def PropDeferred(
    initValue: Iterable[float] | type[float],
    size: int | None = None,
    **kwargs: Unpack[PropFloat],
): ...


@overload
def PropDeferred(initValue, size=None, **kwargs: Unpack[PropPointer]):
    """PointerProperty

    Args:
        type (bpy.types.PropertyGroup or bpy.types.ID):
        poll (function(self, value) -> bool):
        update (function(self, context)):
    """


@overload
def PropDeferred(**kwargs: Unpack[PropEnum]):
    """EnumProperty

    Args:
        items (Iterable[identifier, name, description] or function(self, context) -> Iterable[identifier, name, description]):
            full: [(identifier, name, description, icon, number), ...]
            > There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
            使用回调存在一个已知的错误，Python 必须保留对回调返回的字符串的引用，否则 Blender 会行为异常甚至崩溃。
    """


@overload
def PropDeferred(initValue, size=0, **kwargs: Unpack[PropCollection]):
    """CollectionProperty

    Args:
        type (bpy.types.PropertyGroup):
    """


def peek_iter(iterable: Iterable[_TV]):
    """Detect the 1st item type of an iterable without consuming it. Don't use on dict.

    Returns
    -------
    first_item

    iterable: not consumed


    ## raise
    - IndexError if empty sequence
    - StopIteration if empty iterator
    """
    if hasattr(iterable, "__getitem__"):
        try:
            return iterable[0], iterable  # type: ignore
        except KeyError:
            return next(iter(iterable)), iterable
    it1, it2 = itertools.tee(iterable)
    first = next(it1)
    return first, it2


def iterable(obj):
    """return (is_iterable, obj)"""
    try:
        init_0, obj = peek_iter(obj)
        return True, obj
    except Exception:
        return False, obj


def PropDeferred(initValue: Any = None, size: int | None = None, **kwargs):
    """return bpy.props.* based on initValue type

    Args:
        get (function(self) -> value):
        set (function(self, value)):
            called when value is _written_.
        update (function(self, context)):
            called when value is modified.

        search (function(self, context, edit_text) -> list(str) or list(str_title, str_description)):
        poll (function(self, value) -> bool):
            determines whether an item is valid for this property.
        items (list(identifier, name, description) or function(self, context) -> list(identifier, name, description)):
            full: [(identifier, name, description, icon, number), ...]

    Usage:
    - Prop(0) : int
    - Prop(int) : int
    - Prop([0]) : intVector
    - Prop(int, size=32) : intVector
    - Prop(int, size=0) : Collection, dynamic length
    - Prop(int, size=**-3**) : Collection, dynamic length, filled with 3 default values initially
    - Prop(myPropertyGroup) : PointerProperty
    - Prop(myPropertyGroup, size=0) : Collection of PropertyGroup, dynamic length
    """
    prop = None
    if "Update" in kwargs.keys():
        kwargs["update"] = kwargs.pop("Update")
    if "Get" in kwargs.keys():
        kwargs["get"] = kwargs.pop("Get")
    if "default" in kwargs.keys():
        default = kwargs["default"]
        if initValue is None:
            initValue = default
        elif type(initValue) != type(default):
            raise TypeError(f"initValue {type(initValue)=} != {type(default)=}")

    try:
        len_initValue = len(initValue)
    except TypeError:
        len_initValue = None
    if size == None:
        size = len_initValue

    if isinstance(initValue, str):
        is_iterable = False
    else:
        is_iterable, initValue = iterable(initValue)
    if isinstance(initValue, type) and issubclass(
        initValue, (bpy.types.PropertyGroup, bpy.types.ID)
    ):
        kwargs["type"] = initValue
        initValue = None
    elif callable(initValue) or is_iterable:
        Log.debug(f"peek {initValue=}, {is_iterable=}")
        kwargs["items"] = initValue
        initValue = None
    if "type" in kwargs.keys():
        if issubclass(kwargs["type"], bpy.types.ID):
            prop = bpy.props.PointerProperty(**kwargs)
        elif issubclass(kwargs["type"], bpy.types.PropertyGroup):
            if size is None:
                prop = bpy.props.PointerProperty(**kwargs)
            elif isinstance(size, int) and size >= 0:
                initValue = [None] * size
                prop = bpy.props.CollectionProperty(**kwargs)
            else:
                raise ValueError(f"Invalid size for PropertyGroup: {size=}")
    elif "items" in kwargs.keys():
        prop = bpy.props.EnumProperty(**kwargs)
    elif is_iterable and not isinstance(initValue, str):
        if len_initValue != size:
            raise ValueError(f"size of default {len_initValue=} != {size=}")
        if initValue is bool:
            prop = bpy.props.BoolVectorProperty(size=size, **kwargs)
        elif initValue is int:
            prop = bpy.props.IntVectorProperty(size=size, **kwargs)
        elif initValue is float:
            prop = bpy.props.FloatVectorProperty(size=size, **kwargs)
        else:
            init_0, initValue = peek_iter(initValue)
            if isinstance(init_0, bool):
                prop = bpy.props.BoolVectorProperty(size=size, **kwargs)
            elif isinstance(init_0, int):
                prop = bpy.props.IntVectorProperty(size=size, **kwargs)
            elif isinstance(init_0, float):
                prop = bpy.props.FloatVectorProperty(size=size, **kwargs)
            else:
                # TODO: dynamic collection class for type
                prop = bpy.props.CollectionProperty(**kwargs)
    else:
        if isinstance(initValue, bool):
            prop = bpy.props.BoolProperty(**kwargs)
        elif isinstance(initValue, int):
            prop = bpy.props.IntProperty(**kwargs)
        elif isinstance(initValue, float):
            prop = bpy.props.FloatProperty(**kwargs)
        elif isinstance(initValue, str):
            prop = bpy.props.StringProperty(**kwargs)
        elif initValue is bool:
            prop = bpy.props.BoolProperty(**kwargs)
        elif initValue is int:
            prop = bpy.props.IntProperty(**kwargs)
        elif initValue is float:
            prop = bpy.props.FloatProperty(**kwargs)
        elif initValue is str:
            prop = bpy.props.StringProperty(**kwargs)
        # elif "enum" in initValue.__class__.__name__.lower():
        #     prop = partial(bpy.props.EnumProperty, **kwargs)
        else:
            raise ValueError(f"Unsupported initValue type: {type(initValue)}")
    return prop, initValue

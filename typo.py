"""typing"""

import bpy
import logging
import itertools
import functools
from typing import *  # type: ignore

try:
    import bpy.stub_internal.rna_enums as rna_enums
except ImportError:
    ...


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
_PS1 = ParamSpec("_PS1")
_TV = TypeVar("_TV")
_TV1 = TypeVar("_TV1")
_TV2 = TypeVar("_TV2")
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
    """return (is_iterable, obj), only EnumProp use Iterable, else use Sequence."""
    try:
        init_0, obj = peek_iter(obj)
        return True, obj
    except Exception:
        return False, obj


def copyArgs(
    From: Callable[_PS, Any],
) -> Callable[[Callable[..., _TV]], Callable[_PS, _TV]]:
    """https://dev59.com/NnMOtIcB2Jgan1znX5jv"""

    def return_func(decorated: Callable[..., _TV]) -> Callable[_PS, _TV]:
        return cast(Callable[_PS, _TV], decorated)

    return return_func


def prependArg(
    From: Callable[_PS, Any], value: type[_TV1], TYPE: _TV1
) -> Callable[[Callable[..., _TV]], Callable[Concatenate[_TV1, _PS], _TV]]:
    def return_func(decorated: Callable[..., _TV]):
        return cast(Callable[Concatenate[_TV1, _PS], _TV], decorated)

    return return_func


def copyInitArg(
    From: Callable[Concatenate[_TV, _PS], None],
) -> Callable[[Callable[..., _TV]], Callable[Concatenate[Any, _PS], _TV]]:
    def decorator(func: Callable[..., _TV]) -> Callable[Concatenate[Any, _PS], _TV]:
        return cast(Callable[Concatenate[Any, _PS], _TV], func)

    return decorator


@overload
@prependArg(bpy.props.BoolProperty, bool, bool)
def DeferredProp(*a, **kw): ...


@overload
@prependArg(bpy.props.IntProperty, int, int)
def DeferredProp(*a, **kw): ...


@overload
@prependArg(bpy.props.FloatProperty, float, float)
def DeferredProp(*a, **kw): ...


@overload
@prependArg(bpy.props.StringProperty, str, str)
def DeferredProp(*a, **kw): ...


@overload
@prependArg(bpy.props.BoolVectorProperty, Sequence[bool], bool)
def DeferredProp(*a, **kw): ...


@overload
@prependArg(bpy.props.IntVectorProperty, Sequence[int], int)
def DeferredProp(*a, **kw): ...


@overload
@prependArg(bpy.props.FloatVectorProperty, Sequence[float], float)
def DeferredProp(*a, **kw): ...


@overload
@copyArgs(bpy.props.EnumProperty)
def DeferredProp(*a, **kw): ...


@overload
@copyArgs(bpy.props.PointerProperty)
def DeferredProp(*a, **kw): ...


class KwProp(TypedDict, total=False):
    """len(kwargs)=5. Total 10 kinds of bpy.props"""

    varname: str
    """bq.var"""
    reg: TypesTypes | None
    """default bpy.types.Scene, bpq.var"""

    name: str
    description: str
    translation_context: str
    """https://docs.blender.org/api/current/bpy.app.translations.html#bpy.app.translations.contexts"""
    options: "rna_enums.PropertyFlagItems"
    """https://docs.blender.org/api/current/bpy_types_enum_items/property_flag_items.html#rna-enum-property-flag-items"""
    tags: set[str]
    """Enum of tags that are defined by parent class."""


SELF_CONTEXT = Callable[[bpy.types.bpy_struct, bpy.types.Context], None]


class KwPointerProp(KwProp, total=False):
    """⭐len(kwargs):9 , bpy.types.* = bpy.props.PointerProperty(type=PropertyGroup)"""

    # type: type[bpy.types.ID | bpy.types.PropertyGroup]
    override: "rna_enums.PropertyOverrideFlagItems"
    poll: Callable[[bpy.types.bpy_struct, bpy.types.ID], bool]
    update: SELF_CONTEXT


class KwDOUGS(Generic[_TV], KwProp, total=False):
    """len(args)=10"""

    default: _TV
    override: "rna_enums.PropertyOverrideFlagItems"
    """https://docs.blender.org/api/current/bpy_types_enum_items/property_override_flag_items.html#rna-enum-property-override-flag-items"""
    Update: SELF_CONTEXT
    Get: Callable[[bpy.types.bpy_struct], _TV]
    set: Callable[[bpy.types.bpy_struct, _TV], None]


class KwEnumProp(KwProp, total=False):
    """⭐len(args)=11"""

    items: (
        Iterable[tuple[str, str, str]]
        | Callable[
            [bpy.types.bpy_struct, bpy.types.Context | None],
            Iterable[tuple[str, str, str]],
        ]
    )
    default: str | int | set[str]
    """The default value for this enum, a string from the identifiers used in items, or integer matching an item number. If the ENUM_FLAG option is used this must be a set of such string identifiers instead.

    ⚠️WARNING: Strings cannot be specified for dynamic enums (i.e. if a callback function is given as items parameter)."""
    override: "rna_enums.PropertyOverrideFlagItems"
    """https://docs.blender.org/api/current/bpy_types_enum_items/property_override_flag_items.html#rna-enum-property-override-flag-items"""
    update: SELF_CONTEXT
    get: Callable[[bpy.types.bpy_struct], int]
    set: Callable[[bpy.types.bpy_struct, int], None]


class KwBoolProp(KwDOUGS[bool], total=False):
    """⭐len(args)=11"""

    subtype: "rna_enums.PropertySubtypeNumberItems"


class KwNum(TypedDict, total=False):
    """len(args)=5"""

    min: int | float
    max: int | float
    soft_min: int | float
    soft_max: int | float
    step: int
    """1~100, default 3. will ÷ 100, so default is 0.03"""


class KwIntProp(KwNum, KwDOUGS[int], total=False):
    """⭐len(args)=16"""

    subtype: "rna_enums.PropertySubtypeNumberItems"


class KwFloatProp(KwNum, KwDOUGS[float], total=False):
    """⭐len(args)=18"""

    precision: int
    """0~6, default 3"""
    subtype: "rna_enums.PropertySubtypeNumberItems"
    unit: "rna_enums.PropertyUnitItems"


class KwStrProp(KwDOUGS, total=False):
    """⭐len(args)=14"""

    maxlen: int
    """default 0"""
    subtype: "rna_enums.PropertySubtypeStringItems"
    search: Callable[
        [bpy.types.bpy_struct, bpy.types.Context, str], Iterable[str | tuple[str, str]]
    ]
    search_options: "rna_enums.PropertyStringSearchFlagItems"


class KwCollectionProp(KwProp, total=False):
    """⭐len(kwargs):6 + type_arg:1 = 7"""

    override: "rna_enums.PropertyOverrideFlagCollectionItems"
    """https://docs.blender.org/api/current/bpy_types_enum_items/property_override_flag_collection_items.html#rna-enum-property-override-flag-collection-items"""


@overload
def DeferredProp(
    type: type[bpy.types.PropertyGroup] | None = None,
    value: Sequence[Sequence] | None = None,  # TODO: dynamic gen collection class
    *,
    size: int | None = None,
    **kw: Unpack[KwCollectionProp],
): ...


def DeferredProp(value: Any = None, **kwargs):
    """
    Returns:
        `bpy.props.*Property()` -> `_DeferredProp` based on value type.
        You need to setattr the `_DeferredProp` on `bpy.types.*` class, for accessing the value in bpy.context

    Args:
        value: init value, or type. Differ from `default` kwarg as below👇

            while mouse over UI prop, press <kbd>backspace</kbd> will reset prop to **default value** rather than **init value**.
        size: for vector/collection property, length of the array.
            - None: len(value) if hasattr(value, '__len__') else None
            - 0: dynamic length collection
            - negative: dynamic length collection, filled with abs(size) default values initially
        **kwargs: passed to `bpy.props.*Property()`

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
        if value is None:
            value = default
        elif type(value) != type(default):
            raise TypeError(f"value {type(value)=} != {type(default)=}")

    try:
        len_value = len(value)
    except TypeError:
        len_value = None
    size = kwargs.pop("size", None)
    if size == None:
        size = len_value

    if isinstance(value, str):
        is_iterable = False
    else:
        is_iterable, value = iterable(value)
    if isinstance(value, type) and issubclass(
        value, (bpy.types.PropertyGroup, bpy.types.ID)
    ):
        kwargs["type"] = value
        value = None
    elif callable(value) or is_iterable:
        Log.debug(f"peek {value=}, {is_iterable=}")
        kwargs["items"] = value
        value = None
    if "type" in kwargs.keys():
        if issubclass(kwargs["type"], bpy.types.ID):
            prop = bpy.props.PointerProperty(**kwargs)
        elif issubclass(kwargs["type"], bpy.types.PropertyGroup):
            if size is None:
                prop = bpy.props.PointerProperty(**kwargs)
            elif isinstance(size, int) and size >= 0:
                value = [None] * size
                prop = bpy.props.CollectionProperty(**kwargs)
            else:
                raise ValueError(f"Invalid size for PropertyGroup: {size=}")
    elif "items" in kwargs.keys():
        prop = bpy.props.EnumProperty(**kwargs)
    elif is_iterable and not isinstance(value, str):
        if len_value != size:
            raise ValueError(f"size of default {len_value=} != {size=}")
        if value is bool:
            prop = bpy.props.BoolVectorProperty(size=size, **kwargs)
        elif value is int:
            prop = bpy.props.IntVectorProperty(size=size, **kwargs)
        elif value is float:
            prop = bpy.props.FloatVectorProperty(size=size, **kwargs)
        else:
            init_0, value = peek_iter(value)
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
        if isinstance(value, bool):
            prop = bpy.props.BoolProperty(**kwargs)
        elif isinstance(value, int):
            prop = bpy.props.IntProperty(**kwargs)
        elif isinstance(value, float):
            prop = bpy.props.FloatProperty(**kwargs)
        elif isinstance(value, str):
            prop = bpy.props.StringProperty(**kwargs)
        elif value is bool:
            prop = bpy.props.BoolProperty(**kwargs)
        elif value is int:
            prop = bpy.props.IntProperty(**kwargs)
        elif value is float:
            prop = bpy.props.FloatProperty(**kwargs)
        elif value is str:
            prop = bpy.props.StringProperty(**kwargs)
        # elif "enum" in value.__class__.__name__.lower():
        #     prop = partial(bpy.props.EnumProperty, **kwargs)
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")
    return prop, value


class LayoutProp(TypedDict, total=False):
    """len(kwargs)=5"""

    text: str
    text_ctxt: str
    translate: bool
    icon: "rna_enums.IconItems"
    placeholder: str
    expand: bool
    slider: bool
    toggle: int
    icon_only: bool
    event: bool
    full_event: bool
    emboss: bool
    index: int
    icon_value: int
    invert_checkbox: bool

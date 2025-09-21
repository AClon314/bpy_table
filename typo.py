"""typing"""

import bpy
import logging
from dataclasses import dataclass, field
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
# _PS = ParamSpec("_PS")
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


class CollectionProperty(list[_TV], Generic[_TV]):
    """typing for bpy.props.CollectionProperty"""

    def add(self):
        _TV: ...


@dataclass(kw_only=True)
class _PropBase:
    """Collection has least 6 args. Total 10 kinds of props"""

    name: str = ""
    description: str = ""
    translation_context: str = ""
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
    ] = field(default_factory=set)
    override: set[Literal["LIBRARY_OVERRIDABLE"]] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class PropCollection(_PropBase):
    """len(args)=7"""

    type: type[bpy.types.PropertyGroup]


SELF_CONTEXT = Callable[[bpy.types.bpy_struct, bpy.types.Context], None]


@dataclass
class PropPointer(_PropBase):
    """len(args)=9, bpy.types.* = bpy.props.PointerProperty(type=PropertyGroup)"""

    type: type[bpy.types.ID | bpy.types.PropertyGroup]
    poll: Callable[[bpy.types.bpy_struct, bpy.types.ID], bool] = field(
        default=None, kw_only=True  # type: ignore
    )
    update: SELF_CONTEXT = field(default=None, kw_only=True)  # type: ignore


@dataclass(kw_only=True)
class _PropDUGS(_PropBase, Generic[_TV]):
    """len(args)=10"""

    default: _TV = None  # type: ignore
    update: SELF_CONTEXT = None  # type: ignore
    get: Callable[[bpy.types.bpy_struct], _TV] = None  # type: ignore
    set: Callable[[bpy.types.bpy_struct, _TV], None] = None  # type: ignore


@dataclass
class PropEnum(_PropDUGS[_TV]):
    """len(args)=11"""

    items: (
        Iterable[tuple[_TV, str, str]]
        | Callable[
            [bpy.types.bpy_struct, bpy.types.Context | None],
            Iterable[tuple[_TV, str, str]],
        ]
    )


@dataclass(kw_only=True)
class _Subtype:
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
    ] = "NONE"


@dataclass
class PropBool(_Subtype, _PropDUGS[bool]): ...


@dataclass(kw_only=True)
class _PropNum:
    """len(args)=5"""

    min: int | float = -FLOAT_MAX_3E38
    max: int | float = FLOAT_MAX_3E38
    soft_min: int | float = -FLOAT_MAX_3E38
    soft_max: int | float = FLOAT_MAX_3E38
    step: int = 3


@dataclass
class PropInt(_Subtype, _PropNum, _PropDUGS[int]): ...


@dataclass(kw_only=True)
class PropFloat(_Subtype, _PropNum, _PropDUGS[float]):
    """len(args)=18"""

    precision: int = 2
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
    ] = "NONE"


@dataclass(kw_only=True)
class _PropVec:
    """size in [1, 32]"""

    size: int = 3


@dataclass
class PropBoolVector(_PropDUGS[Iterable[bool]], _PropVec): ...


@dataclass
class PropIntVector(_PropDUGS[Iterable[int]], _PropVec): ...


@dataclass
class PropFloatVector(_PropDUGS[Iterable[float]], _PropVec): ...


@dataclass(kw_only=True)
class PropStr(_PropDUGS):
    """len(args)=14"""

    maxlen: int = 0
    search: Callable[
        [bpy.types.bpy_struct, bpy.types.Context, str], Iterable[str | tuple[str, str]]
    ] = None  # type: ignore
    search_options: set[Literal["SORT", "SUGGESTION"]] = field(default_factory=set)


def iterable(obj):
    return hasattr(obj, "__iter__") or hasattr(obj, "__getitem__")


def Prop(initValue, *args, size=1, **kwargs):
    """init dataclass props

    Usage:
    - Prop(0) : PropInt
    - Prop(int) : PropInt
    - Prop([0]) : PropIntVector
    - Prop((0,0,0)) : PropIntVector
    - Prop(int, size=32) : PropIntVector
    - Prop(int, size=0) : PropCollection, dynamic length
    - Prop(int, size=**-3**) : PropCollection, dynamic length, filled with 3 default values initially
    """
    # TODO: initdata after register
    if size > 0 or (iterable(initValue) and not isinstance(initValue, str)):
        if len(initValue) != size:
            raise ValueError(f"size of default {len(initValue)=} != {size=}")
        if isinstance(initValue[0], bool) and isinstance(initValue, (list, tuple)):
            return PropBoolVector(*args, size=size, **kwargs)
        elif initValue is bool:
            return PropBoolVector(*args, size=size, **kwargs)
        elif initValue is int:
            return PropIntVector(*args, size=size, **kwargs)
        elif initValue is float:
            return PropFloatVector(*args, size=size, **kwargs)
        else:
            # TODO: dynamic collection class for type
            return PropCollection(*args, **kwargs)
    else:
        if initValue is bool:
            return PropBool(*args, **kwargs)
        elif initValue is int:
            return PropInt(*args, **kwargs)
        elif initValue is float:
            return PropFloat(*args, **kwargs)
        elif initValue is str:
            return PropStr(*args, **kwargs)

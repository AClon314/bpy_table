"""typing"""

import bpy
from typing import *  # type: ignore


globalContextType = {
    "area": "Area",
    "asset": "AssetRepresentation",
    "blend_data": "BlendData",
    "collection": "Collection",
    "gizmo_group": "GizmoGroup",
    "layer_collection": "LayerCollection",
    "preferences": "Preferences",
    "region": "Region",
    "region_data": "RegionView3D",
    "region_popup": "Region",
    "scene": "Scene",
    "screen": "Screen",
    "space_data": "Space",
    "tool_settings": "ToolSettings",
    "view_layer": "ViewLayer",
    "window": "Window",
    "window_manager": "WindowManager",
    "workspace": "WorkSpace",
}


class GlobalContext:
    area: bpy.types.Area
    asset: bpy.types.AssetRepresentation
    blend_data: bpy.types.BlendData
    collection: bpy.types.Collection
    gizmo_group: bpy.types.GizmoGroup
    layer_collection: bpy.types.LayerCollection
    preferences: bpy.types.Preferences
    region: bpy.types.Region
    region_data: bpy.types.RegionView3D
    region_popup: bpy.types.Region
    scene: bpy.types.Scene
    screen: bpy.types.Screen
    space_data: bpy.types.Space
    tool_settings: bpy.types.ToolSettings
    view_layer: bpy.types.ViewLayer
    window: bpy.types.Window
    window_manager: bpy.types.WindowManager
    workspace: bpy.types.WorkSpace


class propKwargs(TypedDict, total=False):
    name: str
    description: str
    translation_context: str
    default: str | int | float | bool
    min: int | float
    max: int | float
    soft_min: int | float
    soft_max: int | float
    step: int
    precision: int
    size: int
    maxlen: int
    options: set[str]
    override: set[str]
    tags: set[str]
    subtype: str
    update: Callable | None
    get: Callable | None
    set: Callable | None
    search: Callable | None
    search_options: Set[str]


def propString(**kwargs: Unpack[propKwargs]):
    """
    bpy.props.StringProperty(**kwargs)

    Args:
        name (str, optional): name. Defaults to "".
    """
    return kwargs


bpy_types_Property = Union[
    type(bpy.types.BoolProperty),
    type(bpy.types.IntProperty),
    type(bpy.types.FloatProperty),
    type(bpy.types.StringProperty),
    type(bpy.types.EnumProperty),
    type(bpy.types.PointerProperty),
    type(bpy.types.CollectionProperty),
    type(bpy.types.PropertyGroup),
]
bpy_props_Property = Union[
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
PY_TO_PROP: dict[type | tuple[type, ...], Callable[..., bpy_props_Property]] = (
    {  # type:ignore
        Sequence[bool]: bpy.props.BoolVectorProperty,
        Sequence[int]: bpy.props.IntVectorProperty,
        Sequence[float]: bpy.props.FloatVectorProperty,
        bool: bpy.props.BoolProperty,
        int: bpy.props.IntProperty,
        float: bpy.props.FloatProperty,
        str: bpy.props.StringProperty,
        # enum: bpy.props.EnumProperty,
        # object: bpy.props.PointerProperty,
    }
)
dict_strAny = dict[str, Any]
_PS = ParamSpec("_PS")
_TV = TypeVar("_TV")


class CollectionProperty(list[_TV], Generic[_TV]):
    """typing for bpy.props.CollectionProperty"""

    def add(self) -> _TV: ...


def copy_args(func: Callable[_PS, _TV]):
    """Decorator does nothing and returning the casted original function"""

    def return_func(func: Callable[..., _TV]) -> Callable[_PS, _TV]:
        return cast(Callable[_PS, _TV], func)

    return return_func

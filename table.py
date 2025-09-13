"""
UI list(template_list)
expose template_list, general operators
"""

BL_LABEL = "Table"
BL_IDNAME = "table_sheet"
BL_SPACE_TYPE = "VIEW_3D"
BL_REGION_TYPE = "UI"
BL_CATEGORY = "Development"
MIN_RATIO = 0.03
ACTIVE_DATACLASS = "RowData"
TIMER = 0
TIMEOUT = 3
MOCK_DATA = [
    {"text": "00:00", "FLOAT": 0.0},
    {"text": "00:01", "FLOAT": 1.0},
    {"text": "01:00", "FLOAT": 2.0},
    {"text": "01:23", "FLOAT": 3.0},
]
import bpy
import numpy as np
import logging
from typing import Any, Callable, Generic, Literal, Sequence, TypeVar, Union


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
DATA_TYPE = np.ndarray | Sequence[Sequence | dict_strAny]
TV = TypeVar("TV")
Log = getLogger(__name__)


class CollectionProperty(list[TV], Generic[TV]):
    """typing for bpy.props.CollectionProperty"""

    def add(self) -> TV: ...


RowDataCollectionProperty = CollectionProperty["RowData"]


class Global:
    """Have to use @property to defer access to bpy.context.scene"""

    _data = CollectionProperty()

    @property
    def table(self) -> "TableSystem":
        return bpy.context.scene.TableSystem  # type:ignore

    @property
    def cols(self) -> CollectionProperty["ColumnEntity"]:
        return self.table.cols

    @property
    def data(self) -> RowDataCollectionProperty:
        if not self._data:
            self._data = getattr(bpy.context.scene, ACTIVE_DATACLASS)
        return self._data  # type: ignore

    @data.setter
    def data(self, value: type[bpy.types.PropertyGroup]):
        self._data = value  # type: ignore

    @property
    def propsNames(self):
        return list(self.data[0].keys())


G = Global()


class Panel:
    bl_space_type = BL_SPACE_TYPE
    bl_region_type = BL_REGION_TYPE
    bl_category = BL_CATEGORY
    bl_label = BL_LABEL
    bl_idname = BL_IDNAME
    # bl_options = {"DEFAULT_CLOSED"}


class RowData(bpy.types.PropertyGroup):
    """⭐ Your custom data struct"""

    ID_: bpy.props.IntProperty(name="Index")  # type:ignore
    SELECTED_: bpy.props.BoolProperty(name="Selected")  # type:ignore
    # text: bpy.props.StringProperty(
    #     # update=update_text, options={"TEXTEDIT_UPDATE"}
    # )  # type: ignore
    # FLOAT: bpy.props.FloatProperty()  # type:ignore
    # V_INT: bpy.props.IntVectorProperty()  # type:ignore
    # V_FLOAT: bpy.props.FloatVectorProperty()  # type:ignore
    # ENUM: bpy.props.EnumProperty()  # type:ignore


def reg(cls: type[bpy.types.PropertyGroup], name: str, prop: bpy_props_Property | None):
    """register_class & setattr"""
    bpy.utils.register_class(cls)
    setattr(bpy.types.Scene, name, prop)


def unreg(cls: type[bpy.types.PropertyGroup], name: str):
    """delattr & unregister_class"""
    delattr(bpy.types.Scene, name)
    bpy.utils.unregister_class(cls)


def _genCollectionProp(
    name: str,
    bases: Sequence[bpy_types_Property],
    var_type: dict[str, bpy_props_Property],
):
    """Because G.table.RowData is readonly , so you have to mount dynamic class to bpy.types.Scene"""
    if not name.isidentifier():
        raise ValueError(f"Invalid class name: {name}")
    attrs = {"__annotations__": var_type}
    Log.debug(f"{attrs=}")
    cls: type[bpy.types.PropertyGroup] = type(name, bases, attrs)  # type:ignore
    reg(cls, name, bpy.props.CollectionProperty(type=cls))

    def unregister():
        unreg(cls, name)

    UNREG.append(unregister)
    return cls, unregister


def _genPropertyGroup(
    name: str, var_type: dict[str, bpy_props_Property] = {}, data: DATA_TYPE = []
):
    """
    动态创建一个继承自 bpy.types.PropertyGroup 的类，一定包含 ID\\_ & SELECTED\\_ 字段，并注册到 bpy.types.Scene.{name} 上。

    TODO: 存储动态类的列名，到 text_editor，并设为启动时载入，以便在启动时读取、恢复

    Args
    ----
    name:
        class name, python varname style.
    var_type:
        {colName: bpy.props.*Property}
    data:
        optional, if provided, will infer fields from data keys and values.

    Returns
    -------
    class:
        the dynamically created class
    unregister:
        function to unregister the class
    """
    if not var_type:
        var_type, failed = _pyObj_as_bpyProp(data)
    var_type.setdefault("ID_", bpy.props.IntProperty(name="Index"))  # type: ignore
    var_type.setdefault("SELECTED_", bpy.props.BoolProperty(name="Selected"))  # type: ignore
    cls, unreg = _genCollectionProp(
        name=name,
        bases=(bpy.types.PropertyGroup,),
        var_type=var_type,
    )
    global ACTIVE_DATACLASS
    ACTIVE_DATACLASS = name
    return cls, unreg


def _pyObj_as_bpyProp(data: DATA_TYPE):
    """
    guess dict(colName = bpy.props.*Property) from data

    Args
    ----
    row: 1 dimensional data
        a single row of data, can be dict or sequence

    Returns
    -------
    dict:
        {colName: bpy.props.*Property}
    list:
        list of (colName, value) that failed to infer property type
    """
    row = data[0]
    var_type: dict[str, bpy_props_Property] = {}
    failed = []
    if not row:
        Log.warning("No data to infer fields from.")
        return var_type, failed
    elif isinstance(row, dict):
        Iter = row.items()
    else:
        Iter = enumerate(row)
    for k, v in Iter:
        k = str(k)
        prop = PY_TO_PROP.get(type(v))
        if prop:
            var_type[k] = prop()
        else:
            failed.append((k, v))
    Log.debug(f"{var_type=}")
    Log.error(f"{failed=}") if failed else ...
    return var_type, failed


def _pyObj_fill_bpyProp(data: DATA_TYPE):
    """实际执行导入数据的函数"""
    for idx, row in enumerate(data):
        New = G.data.add()
        # TODO: setdefault value here!!!
        New.ID_ = idx
        New.SELECTED_ = False
        if isinstance(row, dict):
            Iter = row.items()
        else:
            Iter = enumerate(row)
        for k, v in Iter:
            k = str(k)
            if hasattr(New, k):
                setattr(New, k, v)
    if len(G.data) > 0:
        for idx in range(len(G.propsNames)):
            Col = G.cols.add()
        Col.split = 1  # the last has remaining space
    Log.info(f"filled {len(G.data)} rows, {len(G.cols)} cols")


class ColumnEntity(bpy.types.PropertyGroup):
    split: bpy.props.FloatProperty(
        name="Column Width",
        description="列宽",
        default=0.3,
        min=0,
        max=1,
        soft_min=MIN_RATIO,
        soft_max=1 - MIN_RATIO,
        step=1,
        subtype="FACTOR",
    )  # type:ignore
    selected: bpy.props.BoolProperty(
        name="Selected", description="选择该列进行排序"
    )  # type:ignore
    search_keyword: bpy.props.StringProperty(
        name="Search", description="搜索/筛选关键词，支持模糊/正则匹配"
    )  # type:ignore
    search_from: bpy.props.CollectionProperty(
        name="Filter", description="preserved for filter"  # type=... in dynamic class
    )  # type:ignore


class TableSystem(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(
        default=0,
        name="Active Index",
        description="Index of the active item in the list",
    )  # type: ignore
    cols: bpy.props.CollectionProperty(
        type=ColumnEntity, name="Columns", description="Table Columns"
    )  # type: ignore


def Import(
    data: DATA_TYPE,
    act: Literal["add", "refresh", "once"] = "add",
    Class: type[bpy.types.PropertyGroup] | str = RowData,
    fields: dict[str, bpy_props_Property] = {},
):
    """import data into table UI list

    Args
    ----
    data: np.ndarray | Sequence[Sequence | dict]
        data to import
    act:
        "add": add data to existing data

        "refresh": clear existing data and add new data

        "once": only import if no existing data
    Class:
        custom dataclass for typing constrain and static code analysis.
        if str, will construct dynamic PropertyGroup class, named `Class` that you give.
    fields:
        if Class is str, can provide fields to define the dynamic class.
        if not provided, will try to infer from data.
    """
    if act == "once" and len(G.data) > 0:
        return
    scene: bpy.types.Scene = bpy.context.scene  # type: ignore
    if act == "refresh":
        try:
            G.data.clear()
            G.cols.clear()
        except AttributeError as e:
            Log.error(f"clearing columns: {e}")
    if isinstance(Class, str):
        _, unreg = _genPropertyGroup(name=Class, var_type=fields, data=data)
        if hasattr(scene, Class):
            G.data = getattr(scene, Class)
    global ACTIVE_DATACLASS
    ACTIVE_DATACLASS = Class if isinstance(Class, str) else Class.__name__
    _pyObj_fill_bpyProp(data)


def export() -> list[dict_strAny]:
    """export data from table UI list"""
    res = [{k: v for k, v in item.items()} for item in G.data]
    Log.debug(res)
    return res


def _draw_prop(
    split: bpy.types.UILayout, data: DATA_TYPE, property: str, text="", **kwargs
):
    try:
        is_bool = isinstance(getattr(data, property), bool)
    except AttributeError:
        is_bool = False
    split.prop(data, property, text=text, emboss=is_bool, **kwargs)


def _get_factor(data, remain):
    return min(1 - MIN_RATIO, max(MIN_RATIO, data.split / remain))


class TableUIList(bpy.types.UIList):
    def draw_item(
        self,
        context,
        layout: bpy.types.UILayout,
        data,
        item,
        icon,
        active_data,
        active_propname,
    ):
        propNames = G.propsNames
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            factor = G.cols[0].split
            remain = 1 - factor
            split = layout.split(factor=factor, align=True)
            # 绘制第一列
            _draw_prop(split, item, propNames[0])
            for idx, prop in enumerate(propNames[1:], start=1):
                factor = _get_factor(G.cols[idx], remain)
                remain = 1 - factor
                split = split.split(factor=factor, align=True)
                _draw_prop(split, item, prop)
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class TablePanel(bpy.types.Panel, Panel):
    def draw(self, context):
        layout: bpy.types.UILayout = self.layout  # type: ignore
        scene: bpy.types.Scene = context.scene  # type: ignore
        if not (hasattr(G, "table") and hasattr(G, "data") and G.table and G.data):
            return
        row = layout.row(align=True)
        propNames = G.propsNames
        COLS = G.cols
        remain = 1 - COLS[0].split
        split = row.split(factor=COLS[0].split, align=True)
        _colHead(split, propNames, COLS, 0)
        for idx, data in enumerate(COLS[1:], start=1):
            # if not at the end of cols, split:
            is_last = idx == (len(COLS) - 1)
            if not is_last:
                factor = _get_factor(data, remain)
                remain = 1 - factor
                split = split.split(factor=factor, align=True)

            _colHead(split, propNames, COLS, idx)
        row = layout.row(align=True)
        row.template_list("TableUIList", "", scene, ACTIVE_DATACLASS, G.table, "index")


def _colHead(
    split: bpy.types.UILayout,
    propNames: list[str],
    COLS: list[ColumnEntity],
    idx: int,
    **kwargs,
):
    """⭐ draw column header"""
    col = split.column(align=True)
    col.prop(COLS[idx], "split", text="", emboss=False)
    col.prop(COLS[idx], "selected", text=propNames[idx])
    # col.prop_search(
    #     COLS[idx],
    #     "search_keyword",
    #     COLS[idx],
    #     "search_from",
    #     text="",
    #     icon="FILTER",  # TODO: 'NONE' but still show icon, upstream bug.
    #     results_are_suggestions=True,
    #     **kwargs,
    # )


def _gen_col_search_data(data: DATA_TYPE):
    """为每列创建独立的搜索数据集合，每次更新时触发"""
    if not G.data:
        return
    propNames = G.propsNames

    # 为每列创建一个唯一的PropertyGroup类
    for col_idx, col_name in enumerate(propNames):
        # 创建动态类名
        className = f"{ACTIVE_DATACLASS}_search_{col_name}_{col_idx}"

        # 定义属性
        var_prop = {
            "value": bpy.props.StringProperty,
            "index": bpy.props.IntProperty,
        }

        cls, unreg = _genCollectionProp(
            name=className,
            bases=(bpy.types.PropertyGroup,),
            var_type=var_prop,
        )

        # 填充数据
        search_from = getattr(bpy.context.scene, className)
        unique_values = set()

        for row_idx, row in enumerate(G.data):
            if isinstance(row, dict) and col_name in row:
                value = str(row[col_name])
            else:
                value = ""

            # 只添加唯一值
            if value not in unique_values:
                unique_values.add(value)
                search_item = search_from.add()
                search_item.value = value
                search_item.index = row_idx
    return cls, unreg


class ImportOperator(bpy.types.Operator):
    bl_idname = "table.import"
    bl_label = "Import mock table data, for debug"
    bl_options = {"REGISTER"}

    def execute(self, context):
        Import(
            MOCK_DATA,
            act="refresh",
            Class="RowData",
        )
        return {"FINISHED"}


class ExportOperator(bpy.types.Operator):
    bl_idname = "table.export"
    bl_label = "Export table data, for debug"
    bl_options = {"REGISTER"}

    def execute(self, context):
        export()
        return {"FINISHED"}


CLASS_DATA = [RowData, ColumnEntity, TableSystem]
CLASS_UI = [TableUIList, TablePanel, ImportOperator, ExportOperator]
UNREG: list[Callable] = []


def register():
    [bpy.utils.register_class(cls) for cls in CLASS_DATA]
    bpy.types.Scene.TableSystem = bpy.props.PointerProperty(  # type:ignore
        type=TableSystem
    )
    bpy.types.Scene.RowData = bpy.props.CollectionProperty(  # type: ignore
        type=RowData,
    )
    [bpy.utils.register_class(cls) for cls in CLASS_UI]


def unregister():
    Log.debug("🗑 Unregistering...")
    del bpy.types.Scene.TableSystem  # type: ignore
    for func in UNREG:
        try:
            func()
        except Exception as e:
            Log.error("", exc_info=e)
    for cls in reversed(CLASS_DATA + CLASS_UI):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            Log.error("", exc_info=e)


if __name__ == "__main__":
    register()

"""
Dev Notes
# 2025
## 9.11
- bpy.context.scene vs bpy.types.Scene
在UI的draw()方法中，必须用前者；否则用后者，因为bpy.context会被鼠标所在区域而受限制，而后者是全局的。
- PropertyGroup要被CollectionProperty包裹。

## 9.13
"""

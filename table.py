"""table sheet"""

BL_LABEL = "Table"
BL_IDNAME = "table_sheet"
BL_SPACE_TYPE = "VIEW_3D"
BL_REGION_TYPE = "UI"
BL_CATEGORY = "Development"
MIN_RATIO = 0.03
ACTIVE_DATACLASS = "RowData"
MOCK_DATA = [
    {"text": "00:00", "FLOAT": 0.0},
    {"text": "00:01", "FLOAT": 1.0},
    {"text": "01:00", "FLOAT": 2.0},
    {"text": "01:23", "FLOAT": 3.0},
]
import bpy
import numpy as np
from typing import Callable, Literal
from .typo import *
from .bpyQuery import bpq, getLogger

DATA_TYPE = np.ndarray | Sequence[Sequence | dict_strAny]
Log = getLogger(__name__)


class Global:
    """Have to use @property to defer access to bpy.context.scene"""

    _rows = CollectionProperty()

    @property
    def tab(self) -> "TableTab":
        return getattr(bpy.context.scene, TableTab.__name__)

    @property
    def cols(self) -> CollectionProperty["ColumnHead"]:
        return self.tab.cols

    @property
    def colsNames(self):
        return list(self.rows[0].keys())

    @property
    def rows(self) -> CollectionProperty["RowData"]:
        if not self._rows:
            self._rows = getattr(bpy.context.scene, ACTIVE_DATACLASS)
        return self._rows  # type: ignore

    @rows.setter
    def rows(self, value: type[bpy.types.PropertyGroup]):
        self._rows = value  # type: ignore


G = Global()


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


def _regPropertyGroup(
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
    """
    if not var_type:
        var_type, failed = _pyObj_as_bpyProp(data)
    var_type.setdefault("ID_", bpy.props.IntProperty(name="Index"))  # type: ignore
    var_type.setdefault("SELECTED_", bpy.props.BoolProperty(name="Selected"))  # type: ignore
    cls = bpq.regCollectionProp(
        cls_name=name,
        cls_bases=(bpy.types.PropertyGroup,),
        var_type=var_type,
    )
    global ACTIVE_DATACLASS
    ACTIVE_DATACLASS = name
    return cls


def _pyObj_as_bpyProp(data: DATA_TYPE):
    """
    guess dict(colName = bpy.props.*Property) from data first row. (#TODO: extract from all rows)

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


def _pyObj_fill_bpyProp(From: DATA_TYPE, to: "TableTab"):
    """实际执行导入数据的函数"""
    for idx, row in enumerate(From):
        New = to.rows.add()
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
    if len(to.rows) > 0:
        for idx in range(len(G.colsNames)):
            Col = G.cols.add()
        Col.split = 1  # the last has remaining space
    Log.info(f"filled {len(to.rows)} rows, {len(to.cols)} cols")


class ColumnHead(bpy.types.PropertyGroup):
    split: Union[
        float,
        bpy.props.FloatProperty(
            name="Column Width",
            description="列宽",
            default=0.3,
            min=0,
            max=1,
            soft_min=MIN_RATIO,
            soft_max=1 - MIN_RATIO,
            step=1,
            subtype="FACTOR",
        ),  # type:ignore
    ]
    SELECTED_: Union[
        bool,
        bpy.props.BoolProperty(
            name="Selected", description="选择该列进行排序"
        ),  # type:ignore
    ]
    search_keyword: Union[
        str,
        bpy.props.StringProperty(
            name="Search", description="搜索/筛选关键词，支持模糊/正则匹配"
        ),  # type:ignore
    ]
    search_from: Union[
        CollectionProperty,
        bpy.props.CollectionProperty(
            name="Filter", description="preserved for filter"  # TODO: type=xxx
        ),  # type:ignore
    ]


class TableTab(bpy.types.PropertyGroup):
    at_row: Union[
        int,
        bpy.props.IntProperty(
            default=0,
            name="Active",
            description="Active Row",
        ),  # type: ignore
    ]
    rows: Union[
        CollectionProperty[RowData],
        bpy.props.CollectionProperty(
            type=RowData, name="Rows", description="Table Rows"
        ),  # type: ignore
    ]
    cols: Union[
        CollectionProperty[ColumnHead],
        bpy.props.CollectionProperty(
            type=ColumnHead, name="Columns", description="Table Column Headers"
        ),  # type: ignore
    ]
    tabs: bpy.props.EnumProperty(
        name="Spreadsheet",
        description="Table Tabs",
    )  # type: ignore


def Import(
    data: DATA_TYPE,
    act: Literal["add", "refresh", "once"] = "add",
    Class: type[bpy.types.PropertyGroup] | str = RowData,
    fields: dict[str, bpy_props_Property] = {},
):
    """⭐ import data into table UI list

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
    if act == "once" and len(G.rows) > 0:
        return
    scene: bpy.types.Scene = bpy.context.scene  # type: ignore
    if act == "refresh":
        try:
            G.rows.clear()
            G.cols.clear()
        except AttributeError as e:
            Log.error(f"clearing columns: {e}")
    if isinstance(Class, str):
        cls = _regPropertyGroup(name=Class, var_type=fields, data=data)
        if hasattr(scene, Class):
            G.rows = getattr(scene, Class)
    global ACTIVE_DATACLASS
    ACTIVE_DATACLASS = Class if isinstance(Class, str) else Class.__name__
    # _pyObj_fill_bpyProp(data)


def export() -> list[dict_strAny]:
    """⭐ export data from table UI list"""
    res = [{k: v for k, v in item.items()} for item in G.rows]
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


class Panel:
    bl_space_type = BL_SPACE_TYPE
    bl_region_type = BL_REGION_TYPE
    bl_category = BL_CATEGORY
    bl_label = BL_LABEL
    bl_idname = BL_IDNAME
    # bl_options = {"DEFAULT_CLOSED"}


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
        propNames = G.colsNames
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
        if not (hasattr(G, "table") and hasattr(G, "data") and G.tab and G.rows):
            return
        row = layout.row(align=True)
        propNames = G.colsNames
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
        row.template_list("TableUIList", "", scene, ACTIVE_DATACLASS, G.tab, "index")


def _colHead(
    split: bpy.types.UILayout,
    propNames: list[str],
    COLS: list[ColumnHead],
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
    if not G.rows:
        return
    propNames = G.colsNames

    # 为每列创建一个唯一的PropertyGroup类
    for col_idx, col_name in enumerate(propNames):
        # 创建动态类名
        className = f"{ACTIVE_DATACLASS}_search_{col_name}_{col_idx}"

        # 定义属性
        var_prop = {
            "value": bpy.props.StringProperty,
            "index": bpy.props.IntProperty,
        }

        cls = regCollectionProp(
            cls_name=className,
            cls_bases=(bpy.types.PropertyGroup,),
            var_type=var_prop,
        )

        # 填充数据
        search_from = getattr(bpy.context.scene, className)
        unique_values = set()

        for row_idx, row in enumerate(G.rows):
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
    return cls


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


CLASS_DATA = [TableTab]
CLASS_UI = [TableUIList, TablePanel, ImportOperator, ExportOperator]
UNREG: list[Callable] = []


def register():
    [bpy.utils.register_class(cls) for cls in CLASS_DATA]
    bpy.types.Scene.TableSystem = bpy.props.PointerProperty(  # type:ignore
        type=TableTab
    )
    bpy.types.Scene.RowData = bpy.props.CollectionProperty(  # type: ignore
        type=RowData,
    )
    [bpy.utils.register_class(cls) for cls in CLASS_UI]
    # Import() # TODO


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

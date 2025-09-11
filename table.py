"""
UI list(template_list)
expose template_list, general operators
"""

import bpy
import numpy as np
import argparse
import logging
from typing import Any, Callable, Literal, Sequence, Union

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(filename)s:%(lineno)d\t%(message)s",
    datefmt="%H:%M:%S",
)
Log = logging.getLogger(__name__)

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
PY_TO_PROP = {
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
DATA_TYPE = np.ndarray | Sequence[Sequence | dict]

BL_LABEL = "Table"
BL_IDNAME = "table_sheet"
BL_SPACE_TYPE = "VIEW_3D"
BL_REGION_TYPE = "UI"
BL_CATEGORY = "Development"
MIN_RATIO = 0.03
ACTIVE_DATACLASS = "StaticData"
TIMER = 0
TIMEOUT = 3
MOCK_DATA = [
    {"text": "00:00", "SELECTED": False, "FLOAT": 0.0},
    {"text": "00:01", "SELECTED": True, "FLOAT": 1.0},
    {"text": "01:00", "SELECTED": True, "FLOAT": 2.0},
    {"text": "01:23", "SELECTED": True, "FLOAT": 3.0},
]


class PropertyList(list):
    def add(self) -> argparse.Namespace: ...


class Global:
    _data = PropertyList()

    @property
    def table(self) -> "TableSystem":
        return bpy.context.scene.TableData  # type:ignore

    @property
    def data(self) -> PropertyList:
        if not self._data:
            self._data = getattr(bpy.context.scene, ACTIVE_DATACLASS)
        return self._data  # type: ignore

    @data.setter
    def data(self, value: type[bpy.types.PropertyGroup]):
        self._data = value  # type: ignore


G = Global()


class Panel:
    bl_space_type = BL_SPACE_TYPE
    bl_region_type = BL_REGION_TYPE
    bl_category = BL_CATEGORY
    bl_label = BL_LABEL
    bl_idname = BL_IDNAME
    # bl_options = {"DEFAULT_CLOSED"}


class StaticData(bpy.types.PropertyGroup):
    """Your custom data struct"""

    ID_: bpy.props.IntProperty()  # type:ignore
    SELECTED_: bpy.props.BoolProperty()  # type:ignore
    text: bpy.props.StringProperty(
        # update=update_text, options={"TEXTEDIT_UPDATE"}
    )  # type: ignore
    FLOAT: bpy.props.FloatProperty()  # type:ignore
    V_INT: bpy.props.IntVectorProperty()  # type:ignore
    V_FLOAT: bpy.props.FloatVectorProperty()  # type:ignore
    # ENUM: bpy.props.EnumProperty()  # type:ignore

    @classmethod
    def len(cls):
        return len(cls.__annotations__)


def unreg(cls: type[bpy.types.PropertyGroup], name: str):
    """delattr & unregister_class"""
    delattr(bpy.types.Scene, name)
    bpy.utils.unregister_class(cls)


def _genPropertyGroup(
    name: str, fields: dict[str, bpy_props_Property] = {}, data: DATA_TYPE = []
):
    """
    动态创建一个继承自 bpy.types.PropertyGroup 的类，一定包含 ID_ & SELECTED_ 字段，并注册到 bpy.types.Scene.{name} 上。

    TODO: 存储动态类的列名，以便在启动时读取、恢复

    Args
    ----
    name:
        class name, python varname style.
    fields:
        can use partial with args.
    data:
        optional, if provided, will infer fields from data keys and values.


    Returns
    -------
    class:
        the dynamically created class
    unregister:
        function to unregister the class
    """
    if not name.isidentifier():
        raise ValueError(f"Invalid class name: {name}")
    if not fields:
        fields = _pyObj_as_bpyProp(data)
    fields.setdefault("ID_", bpy.props.IntProperty())  # type: ignore
    fields.setdefault("SELECTED_", bpy.props.BoolProperty())  # type: ignore
    attrs = {"__annotations__": fields}
    # 动态创建类
    cls = type(name, (bpy.types.PropertyGroup,), attrs)
    bpy.utils.register_class(cls)
    setattr(bpy.types.Scene, name, bpy.props.CollectionProperty(type=cls))

    def unregister():
        unreg(cls, name)

    # CLASS_DATA.append(cls)
    UNREG.append(unregister)
    global ACTIVE_DATACLASS
    ACTIVE_DATACLASS = name
    return cls, unregister


def get_row(data: DATA_TYPE) -> np.ndarray | Sequence | dict | None:
    try:
        if data and len(data) > 0:
            return data[0]
    except TypeError:
        ...
    return data


def _pyObj_as_bpyProp(data: DATA_TYPE):
    """guess dict(colName = bpy.props.*Property) from data"""
    fields: dict[str, bpy_props_Property] = {}
    failed = []
    row = get_row(data)
    if not row:
        Log.warning("No data to infer fields from.")
        return fields
    if isinstance(data, np.ndarray):
        ...  # TODO
    elif isinstance(row, dict):
        for k, v in row.items():
            prop = PY_TO_PROP.get(type(v))
            if prop:
                fields[k] = prop()
            else:
                failed.append((k, v))
    elif isinstance(row, Sequence):
        for idx, v in enumerate(row):
            prop = PY_TO_PROP.get(type(v))
            if prop:
                fields[f"{idx}"] = prop()
            else:
                failed.append((idx, v))
    if failed:
        Log.error(f"Failed to infer fields for: {failed}")
    return fields


def _pyObj_fill_bpyProp(data: DATA_TYPE):
    """实际执行导入数据的函数"""
    for idx, row in enumerate(data):
        New = G.data.add()
        New.ID_ = idx
        if isinstance(row, dict):
            for k, v in row.items():
                if hasattr(New, k):
                    setattr(New, k, v)
        elif isinstance(row, Sequence):
            for i, v in enumerate(row):
                if hasattr(New, f"{i}"):
                    setattr(New, f"{i}", v)
    if len(G.data) > 0:
        for idx in range(len(G.data[0].keys())):
            Col: ColumnEntity = G.table.cols.add()
        Col.split = 1  # the last has remaining space
    Log.info(f"filled {len(G.data)} rows, {len(G.table.cols)} cols")


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
        name="Selected", description="选择该列进行排序", default=False
    )  # type:ignore


class TableSystem(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(
        default=0,
    )  # type: ignore
    cols: bpy.props.CollectionProperty(
        type=ColumnEntity,
    )  # type: ignore
    sort_col: bpy.props.EnumProperty(
        name="Sort By",
        description="选择排序列",
        items=lambda self, context: [
            (col, col, "") for col in TableSystem.get_columns()
        ],
    )  # type:ignore
    sort_reverse: bpy.props.BoolProperty(
        name="Descending", description="降序排列", default=False
    )  # type:ignore

    @classmethod
    def get_columns(cls):
        if G.data:
            return list(G.data[0].keys())
        return []

    @classmethod
    def sort_data(cls, data, sort_col, reverse=False):
        if not sort_col:
            return data
        return sorted(data, key=lambda x: x.get(sort_col, ""), reverse=reverse)


def Import(
    data: DATA_TYPE,
    act: Literal["add", "refresh", "once"] = "add",
    Class: type[bpy.types.PropertyGroup] | str = StaticData,
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
            G.table.cols.clear()
        except AttributeError as e:
            Log.error(f"clearing columns: {e}")
    if isinstance(Class, str):
        _, unreg = _genPropertyGroup(name=Class, fields=fields, data=data)
        if hasattr(scene, Class):
            G.data = getattr(scene, Class)
    if isinstance(data, np.ndarray):
        ...  # TODO
    else:
        ...
    global ACTIVE_DATACLASS
    ACTIVE_DATACLASS = Class if isinstance(Class, str) else Class.__name__
    _pyObj_fill_bpyProp(data)


def export() -> list[dict[str, Any]]:
    """export data from table UI list"""
    res = [{k: v for k, v in item.items()} for item in G.data]
    Log.debug(res)
    return res


def _draw_prop(split: bpy.types.UILayout, data, property: str, text="", **kwargs):
    is_bool = isinstance(getattr(data, property), bool)
    split.prop(data, property, text=text, emboss=is_bool, **kwargs)


def _get_factor(data, remain):
    return min(1 - MIN_RATIO, max(MIN_RATIO, data.split / remain))


class Table(bpy.types.UIList):
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
        propNames: list[str] = list(G.data[0].keys())
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            factor = G.table.cols[0].split
            remain = 1 - factor
            split = layout.split(factor=factor, align=True)
            # 绘制第一列
            _draw_prop(split, item, propNames[0])
            for idx, prop in enumerate(propNames[1:], start=1):
                factor = _get_factor(G.table.cols[idx], remain)
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
        propNames: list[str] = list(G.data[0].keys())
        COLS = G.table.cols
        remain = 1 - COLS[0].split
        split = row.split(factor=COLS[0].split, align=True)
        col = split.column(align=True)
        col.prop(COLS[0], "split", text="", emboss=False)
        col.prop(COLS[0], "selected", text=propNames[0])
        for idx, data in enumerate(COLS[1:], start=1):
            # if not at the end of cols, split:
            is_last = idx == (len(COLS) - 1)
            if not is_last:
                factor = _get_factor(data, remain)
                remain = 1 - factor
                split = split.split(factor=factor, align=True)

            col = split.column(align=True)
            if is_last:
                col.label(text=f"{data.split}")
            else:
                col.prop(data, "split", text="", emboss=False)
            col.prop(COLS[idx], "selected", text=propNames[idx])
            # TODO: 添加列筛选功能
            # col.prop_search(
            #     COLS[idx], "selected_object_name", bpy.data, "objects", text="Object"
            # )

        row = layout.row(align=True)
        row.template_list("Table", "", scene, ACTIVE_DATACLASS, G.table, "index")


class ImportOperator(bpy.types.Operator):
    bl_idname = "table.import"
    bl_label = "Import mock table data, for debug"
    bl_options = {"REGISTER"}

    def execute(self, context):
        Import(
            MOCK_DATA,
            act="refresh",
            Class="StaticData",
        )
        return {"FINISHED"}


class ExportOperator(bpy.types.Operator):
    bl_idname = "table.export"
    bl_label = "Export table data, for debug"
    bl_options = {"REGISTER"}

    def execute(self, context):
        export()
        return {"FINISHED"}


CLASS_DATA = [StaticData, ColumnEntity, TableSystem]
CLASS_UI = [Table, TablePanel, ImportOperator, ExportOperator]
UNREG: list[Callable] = []


def register():
    [bpy.utils.register_class(cls) for cls in CLASS_DATA]
    bpy.types.Scene.TableData = bpy.props.PointerProperty(  # type:ignore
        type=TableSystem
    )
    bpy.types.Scene.StaticData = bpy.props.CollectionProperty(  # type: ignore
        type=StaticData,
    )
    [bpy.utils.register_class(cls) for cls in CLASS_UI]


def unregister():
    Log.debug("🗑 Unregistering...")
    del bpy.types.Scene.TableData  # type: ignore
    for func in UNREG:
        func()
    for cls in reversed(CLASS_DATA + CLASS_UI):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            Log.error("", exc_info=e)


if __name__ == "__main__":
    register()

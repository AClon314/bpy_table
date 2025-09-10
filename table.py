"""
UI list(template_list)
expose template_list, general operators
"""

import bpy
import numpy as np
import argparse
from typing import Any, Literal, Sequence, Union

# from .lib import get_scale

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
    def table(self) -> "TableData":
        return bpy.context.scene.bpy_table  # type:ignore

    @property
    def data(self) -> PropertyList:
        if not self._data:
            self._data = self.table.data
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

    ID: bpy.props.IntProperty()  # type:ignore
    SELECTED: bpy.props.BoolProperty()  # type:ignore
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
    delattr(bpy.types.Scene, name)
    bpy.utils.unregister_class(cls)


def genPropertyGroup(
    name: str, fields: dict[str, bpy_props_Property] = {}, data: DATA_TYPE = []
):
    """
    动态创建一个继承自 bpy.types.PropertyGroup 的类，一定包含 ID 字段，并注册到 bpy.types.Scene.{name} 上。

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
    class_instance:
        instance of the dynamically created class, contains ID(IntProperty) field.
    class:
        the dynamically created class
    unregister:
        function to unregister the class
    """
    if not name.isidentifier():
        raise ValueError(f"Invalid class name: {name}")
    # 确保 ID 字段存在
    fields.setdefault("ID", bpy.props.IntProperty())  # type: ignore
    fields.setdefault("SELECTED", bpy.props.BoolProperty())  # type: ignore
    # 创建类属性字典
    if not fields:
        fields = guess_fields(data)
    attrs = {"__annotations__": fields}
    # 动态创建类
    cls = type(name, (bpy.types.PropertyGroup,), attrs)
    bpy.utils.register_class(cls)
    setattr(bpy.types.Scene, name, bpy.props.CollectionProperty(type=cls))

    def unregister():
        unreg(cls, name)

    class_data.append(cls)
    instance = getattr(bpy.types.Scene, name)
    return instance, cls, unregister


def guess_fields(data: DATA_TYPE):
    fields: dict[str, bpy_props_Property] = {}
    failed = []
    row = get_row(data)
    if not row:
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
        print(f"❌ Failed to infer fields for: {failed}")
    return fields


def get_row(data: DATA_TYPE) -> np.ndarray | Sequence | dict | None:
    try:
        if data and len(data) > 0:
            return data[0]
        return data
    except TypeError:
        return data


class ColumnSettings(bpy.types.PropertyGroup):
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


class TableData(bpy.types.PropertyGroup):
    data: bpy.props.CollectionProperty(
        type=StaticData,
    )  # type: ignore
    index: bpy.props.IntProperty(
        default=0,
    )  # type: ignore
    cols: bpy.props.CollectionProperty(
        type=ColumnSettings,
    )  # type: ignore
    sort_col: bpy.props.EnumProperty(
        name="Sort By",
        description="选择排序列",
        items=lambda self, context: [(col, col, "") for col in TableData.get_columns()],
    )  # type:ignore
    sort_reverse: bpy.props.BoolProperty(
        name="Descending", description="降序排列", default=False
    )  # type:ignore

    @classmethod
    def get_columns(cls):
        if cls.data:
            return list(cls.data[0].keys())
        return []

    @classmethod
    def sort_data(cls, data, sort_col, reverse=False):
        if not sort_col:
            return data
        return sorted(data, key=lambda x: x.get(sort_col, ""), reverse=reverse)


def _perform_import(data: DATA_TYPE):
    """实际执行导入数据的函数"""
    for idx, row in enumerate(data):
        New = G.data.add()
        New.ID = idx
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
            Col: ColumnSettings = G.table.cols.add()
        Col.split = 1  # the last has remaining space
    print(f"imported {len(G.data)} rows, {len(G.table.cols)} cols")


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
    if act == "refresh":
        G.table.cols.clear()
        G.data.clear()
        unreg(StaticData, "bpy_table")
    if isinstance(data, np.ndarray):
        ...  # TODO
    else:
        if isinstance(Class, str):
            instance, _, _ = genPropertyGroup(name=Class, fields=fields, data=data)
            G.data = instance  # TODO: AttributeError: '_PropertyDeferred' object has no attribute 'add'
            print("😭")

    def delayed_import():
        """检查对象是否已正确初始化"""
        if hasattr(G.data, "add"):
            _perform_import(data)
            return None  # 返回None表示定时器不需要重复执行
        else:
            print("Waiting for G.data to be ready...")
            return 0.1  # 100ms后再次检查

    bpy.app.timers.register(delayed_import, first_interval=0.01)


def export() -> list[dict[str, Any]]:
    """export data from table UI list"""
    res = [{k: v for k, v in item.items()} for item in G.data]
    print(res)
    return res


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
        if not G.data:
            return
        propNames: list[str] = list(G.data[0].keys())
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            factor = G.table.cols[0].split
            split = layout.split(factor=factor, align=True)
            remain = 1 - factor
            is_bool = isinstance(getattr(item, propNames[0]), bool)
            split.prop(item, propNames[0], text="", emboss=is_bool, icon_value=icon)
            for idx, prop in enumerate(propNames[1:], start=1):
                factor = _get_factor(G.table.cols[idx], remain)
                remain = 1 - factor
                split = split.split(factor=factor, align=True)
                is_bool = isinstance(getattr(item, prop), bool)
                split.prop(item, prop, text="", emboss=is_bool, icon_value=icon)
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class TablePanel(bpy.types.Panel, Panel):
    def draw(self, context):
        layout: bpy.types.UILayout = self.layout  # type: ignore
        scene: bpy.types.Scene = context.scene  # type: ignore
        table = scene.bpy_table  # type: ignore
        if not (G.table.cols and G.data):
            return

        propNames: list[str] = list(G.data[0].keys())
        COLS = G.table.cols
        row = layout.row(align=True)
        split = row.split(factor=COLS[0].split, align=True)
        remain = 1 - COLS[0].split
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
            # col.prop_search(
            #     COLS[idx], "selected_object_name", bpy.data, "objects", text="Object"
            # )

        row = layout.row(align=True)
        row.template_list(
            "Table", "", table, "data", table, "index"  # type:ignore
        )


def _get_factor(data, remain):
    return min(1 - MIN_RATIO, max(MIN_RATIO, data.split / remain))


class ImportOperator(bpy.types.Operator):
    bl_idname = "table.import"
    bl_label = "Import mock table data, for debug"
    bl_options = {"REGISTER"}

    def execute(self, context):
        Import(MOCK_DATA, act="refresh", Class="DynamicData")
        return {"FINISHED"}


class ExportOperator(bpy.types.Operator):
    bl_idname = "table.export"
    bl_label = "Export table data, for debug"
    bl_options = {"REGISTER"}

    def execute(self, context):
        export()
        return {"FINISHED"}


class_data = [StaticData, ColumnSettings, TableData]
class_ui = [Table, TablePanel, ImportOperator, ExportOperator]


def register():
    [bpy.utils.register_class(cls) for cls in class_data]
    bpy.types.Scene.bpy_table = bpy.props.PointerProperty(  # type:ignore
        type=TableData
    )
    [bpy.utils.register_class(cls) for cls in class_ui]


def unregister():
    del bpy.types.Scene.bpy_table  # type: ignore
    for cls in reversed(class_data + class_ui):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    register()

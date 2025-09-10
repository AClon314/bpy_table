"""
UI list(template_list)
expose template_list, general operators
"""

import bpy
import numpy as np
from typing import Literal, Sequence

# from .lib import get_scale

BL_LABEL = "Table"
BL_IDNAME = "table_sheet"
BL_SPACE_TYPE = "VIEW_3D"
BL_REGION_TYPE = "UI"
BL_CATEGORY = "Development"
MIN_RATIO = 0.03
MOCK_DATA = [
    {"id": "001", "start_time": "10:00", "end_time": "10:30", "text": "Hello"},
    {"id": "002", "start_time": "11:30", "end_time": "12:00", "text": "World"},
    {"id": "003", "start_time": "12:15", "end_time": "13:00", "text": "Blender"},
    {"id": "004", "start_time": "09:00", "end_time": "09:45", "text": "AI"},
]


class Global:
    @property
    def table(self) -> "TableData":
        return bpy.context.scene.bpy_table  # type:ignore


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
    text: bpy.props.StringProperty(
        # update=update_text, options={"TEXTEDIT_UPDATE"}
    )  # type: ignore
    text2: bpy.props.StringProperty(
        # update=update_text, options={"TEXTEDIT_UPDATE"}
    )  # type: ignore
    BOOL: bpy.props.BoolProperty()  # type:ignore
    FLOAT: bpy.props.FloatProperty()  # type:ignore
    V_INT: bpy.props.IntVectorProperty()  # type:ignore
    V_FLOAT: bpy.props.FloatVectorProperty()  # type:ignore
    # ENUM: bpy.props.EnumProperty()  # type:ignore

    @classmethod
    def len(cls):
        return len(cls.__annotations__)


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


def Import(
    data: np.ndarray | Sequence[Sequence | dict],
    act: Literal["add", "refresh", "once"] = "add",
):
    """import data into table UI list"""
    if act == "once" and len(G.table.data) > 0:
        return
    if act == "refresh":
        G.table.cols.clear()
        G.table.data.clear()
    if isinstance(data, np.ndarray):
        ...  # TODO
    else:
        for idx, row in enumerate(data):
            New: StaticData = G.table.data.add()
            New.ID = idx
            if isinstance(row, dict):
                New.text = row.get("start_time", "")
                New.text2 = row.get("text", "")
    if len(G.table.data) > 0:
        for idx in range(len(G.table.data[0].keys())):
            Col: ColumnSettings = G.table.cols.add()
        Col.split = 1  # the last has remaining space
    print(f"imported {len(G.table.data)} rows, {len(G.table.cols)} cols")


def export() -> list[dict[str, str | int | float]]:
    """export data from table UI list"""
    res = [{k: v for k, v in item.items()} for item in G.table.data]
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
        if not G.table.data:
            return
        propNames: list[str] = list(G.table.data[0].keys())
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            factor = G.table.cols[0].split
            split = layout.split(factor=factor, align=True)
            remain = 1 - factor
            split.prop(item, propNames[0], text="", emboss=False, icon_value=icon)
            for idx, property in enumerate(propNames[1:], start=1):
                factor = _get_factor(G.table.cols[idx], remain)
                remain = 1 - factor
                split = split.split(factor=factor, align=True)
                split.prop(item, property, text="", emboss=False, icon_value=icon)
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class TablePanel(bpy.types.Panel, Panel):
    def draw(self, context):
        layout: bpy.types.UILayout = self.layout  # type: ignore
        scene: bpy.types.Scene = context.scene  # type: ignore
        table = scene.bpy_table  # type: ignore
        if not (G.table.cols and G.table.data):
            return

        propNames: list[str] = list(G.table.data[0].keys())
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
        Import(MOCK_DATA, act="refresh")
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
    Import(MOCK_DATA, act="refresh")

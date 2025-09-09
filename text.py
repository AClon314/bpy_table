"""
只读 label → 可编辑 prop → 多行临时 text_editor
暴露内部modal


import bpy
textField = bpy.context.edit_text
c, l = textField.current_character, textField.current_line_index
print(l, c)
# bpy.context.edit_text.cursor_set(line=0, character=1)
"""

import bpy

class DetectCursorPos(bpy.types.Operator):
    bl_idname = "wm.input_text_cursor_pos"
    bl_label = "detect text cursor pos"

    text: StringProperty(name="Input") # type: ignore
    cursor_pos: IntProperty(name="Cursor", default=0)  # type: ignore

    def invoke(self, context, event):
        # 初始化输入框
        wm = context.window_manager
        if not wm:
            return
        self.text = ""
        self.cursor_pos = 0
        wm.invoke_props_dialog(self)
        print("invoke")
        return {"RUNNING_MODAL"}

    def modal(self, context, event:bpy.types.Event):
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            return self.execute(context)
        elif event.type == "ESCAPE":
            return {"CANCELLED"}
        elif event.type == "RET" and event.value == "PRESS":
            return self.execute(context)
        elif event.type == "TEXT_EDIT" and event.value == "CHANGE":
            # 更新光标位置
            self.cursor_pos = event.cursor
        print("modal")
        return {"RUNNING_MODAL"}

    def execute(self, context):
        print(f"Input Text: {self.text}")
        print(f"Cursor Position: {self.cursor_pos}")
        print('execute')
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        if not layout:
            return
        row = layout.row()
        row.prop(self, "text", text="")
        row.prop(self, "cursor_pos", text="Cursor")

if __name__ == '__main__':
    try:
        bpy.utils.unregister_class(DetectCursorPos)
    except:
        ...
    bpy.utils.register_class(DetectCursorPos)

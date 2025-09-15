"""dev/test only, malware abuse warning!"""

import bpy


def Eval(self, context):
    data: EvalData = bpy.context.scene.Eval  # type: ignore
    try:
        _eval = eval(data.In)
        data.Str = str(_eval)
        data.Repr = repr(_eval)
    except Exception as e:
        print("❌", e)
        data.Str = str(e)
        data.Repr = repr(e)


class EvalData(bpy.types.PropertyGroup):
    In: bpy.props.StringProperty(  # type: ignore
        name="Input", description="eval()", default="bpy", update=Eval
    )
    Str: bpy.props.StringProperty(  # type: ignore
        name="String", description="str(eval())"
    )
    Repr: bpy.props.StringProperty(  # type: ignore
        name="Repr", description="repr(eval())"
    )
    var: bpy.props.StringProperty(name="Var", description="test")  # type: ignore


class EvalPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_eval_panel"
    bl_label = "Eval"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Development"

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout  # type: ignore
        data = context.scene.Eval  # type: ignore
        layout.prop(data, "In", text="", icon="CONSOLE")
        layout.prop(data, "Str", text="", icon="TEXT")
        layout.prop(data, "Repr", text="", icon="FILE_SCRIPT")
        layout.label(text=f"{data.var}")
        layout.prop(data, "var", text="")


def register():
    bpy.utils.register_class(EvalData)
    bpy.types.Scene.Eval = bpy.props.PointerProperty(type=EvalData)  # type: ignore
    bpy.utils.register_class(EvalPanel)


def unregister():
    for cls in (EvalData, EvalPanel):
        try:
            bpy.utils.unregister_class(cls)
        except ValueError:
            ...
    del bpy.types.Scene.Eval  # type: ignore


if __name__ == "__main__":
    register()

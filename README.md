# Install/Usage
copy `table.py` and `text.py` to your bpy addon/extension dev project
```python
from .table import Import, export
```

# Feature TODO
- row datas: search/filter/sort
- column head: sort/width
- row copy & paste
- Dynamic register class on bpy.types.Scene (maybe can be abused by malware?😧 send me issue/pr!)
- multiline edit support in another text editor **area**
- animatable with blender RNA system.

# Why
Blender have no native table/sheet UI component. No api exposed like geometry node sheet.
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

# PR standard
- black formatter
- if the function have no input args, then put it in a class and set @property

# Why
Blender have no native table/sheet UI component. No api exposed like geometry node sheet.

<details><summary>Dev Notes</summary>

## 2025
### 9.11
- bpy.context.scene vs bpy.types.Scene
在UI的draw()方法中，必须用前者；否则用后者，因为bpy.context会被鼠标所在区域而受限制，而后者是全局的。
- PropertyGroup要被CollectionProperty包裹。

### 9.13
- 仅在要与blender RNA系统交互时，使用bpy.props.*Property；否则用python原生类型
- 2种方法动态访问：一种是bpy.props.CollectionProperty(type=MyPointerProp) + MyPointerProp: p:bpy.props.PointerProperty，但这种花销比较大；另一种是所有动态类都挂载到bpy.types.Scene下，虽然有点乱，但做好命名规范还是能用的。

### 9.14
- 链式调用： __getattr__.__getattr__...__getattr__...__setattr__

#### 当 递归次数 == 创建类实例数 时

##### 一般情况下，线性创建类实例开销更大，原因：
1. **内存分配**: 每个实例都需要完整的内存分配
2. **对象初始化**: 需要执行构造函数和属性初始化
3. **垃圾回收压力**: 创建大量对象增加GC负担

##### 递归函数相对轻量：
1. **栈帧复用**: 函数执行完后栈帧会被回收
2. **局部变量**: 仅在栈上分配，无需堆内存
3. **无对象管理开销**: 不涉及复杂的对象生命周期管理

##### 递归开销可能更大的情况：
- 递归深度过大导致栈溢出
- 递归函数中包含复杂计算或大量局部变量
- 尾递归优化未生效（Python不支持尾递归优化）

##### 类实例创建开销可能更小的情况：
- 类非常简单，只包含少量数据
- 实例会被重复使用而非一次性创建后丢弃
- 使用了 `__slots__` 等优化手段

##### 建议

1. **优先考虑算法复杂度**而非单纯的性能比较
2. **实际测试**具体用例的性能表现
3. **考虑内存使用模式**和垃圾回收影响
4. 对于当前代码，建议关注递归调用可能导致的栈深度问题

</details>

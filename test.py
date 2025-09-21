from dataclasses import dataclass, field


@dataclass
class ExampleKw:
    name: str
    age: int = field(kw_only=True)


# 必须这样初始化（关键字参数）
ExampleKw("Alice")

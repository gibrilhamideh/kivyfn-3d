from dataclasses import dataclass, field


@dataclass(slots=True)
class MeshData:
    name: str | None = None

    vertex_format: list[tuple[bytes, int, str]] = field(default_factory=lambda: [
        (b"v_pos", 3, "float"),
        (b"v_normal", 3, "float"),
        (b"v_tc0", 2, "float"),
    ])

    vertices: list[float] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)

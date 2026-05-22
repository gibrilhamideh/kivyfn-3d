# kivyfn/three/backends/trimesh.py

from __future__ import annotations


def require_trimesh():
    try:
        import trimesh
    except ImportError as exc:
        raise ImportError(
            "Trimesh backend requires:\n"
            "pip install 'kivyfn-3d[modifiers]'"
        ) from exc

    return trimesh


def require_manifold():
    try:
        import manifold3d
    except ImportError as exc:
        raise ImportError(
            "Manifold backend requires:\n"
            "pip install 'kivyfn-3d[modifiers]'"
        ) from exc

    return manifold3d


def require_boolean_backend():
    trimesh = require_trimesh()
    require_manifold()

    return trimesh

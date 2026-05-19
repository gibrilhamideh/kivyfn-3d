# kivyfn/three/math/matrix.py

from __future__ import annotations

import numpy as np


class Matrix3:
    def __init__(self, values=None):
        if values is None:
            self.values = np.identity(3, dtype=np.float32)
        else:
            self.values = np.array(values, dtype=np.float32).reshape((3, 3))

    @classmethod
    def identity(cls) -> "Matrix3":
        return cls()

    def transpose(self) -> "Matrix3":
        return Matrix3(self.values.T)

    def inverse(self) -> "Matrix3":
        return Matrix3(np.linalg.inv(self.values))

    def tolist(self):
        return self.values.tolist()

    def __matmul__(self, other: "Matrix3") -> "Matrix3":
        return Matrix3(self.values @ other.values)

    def __repr__(self) -> str:
        return f"Matrix3({self.values})"


class Matrix4:
    def __init__(self, values=None):
        if values is None:
            self.values = np.identity(4, dtype=np.float32)
        else:
            self.values = np.array(values, dtype=np.float32).reshape((4, 4))

    @classmethod
    def identity(cls) -> "Matrix4":
        return cls()

    def transpose(self) -> "Matrix4":
        return Matrix4(self.values.T)

    def inverse(self) -> "Matrix4":
        return Matrix4(np.linalg.inv(self.values))

    def compute_normal_matrix(self) -> Matrix3:
        rotation = self.values[:3, :3].astype(np.float64)

        normal = np.linalg.inv(rotation).T

        return Matrix3(normal.astype(np.float32))

    def tolist(self):
        return self.values.tolist()

    def __matmul__(self, other: "Matrix4") -> "Matrix4":
        return Matrix4(self.values @ other.values)

    def __repr__(self) -> str:
        return f"Matrix4({self.values})"

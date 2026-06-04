# kivyfn/three/loaders/obj/parser.py

from __future__ import annotations

from pathlib import Path

import numpy as np

from kivyfn.three.math.transform import Transform
from kivyfn.three.math.vector import Vector3
from kivyfn.three.assets.geometry import Geometry, GeometryBounds
from kivyfn.three.loaders.obj.asset import ObjSceneAsset, ObjAsset


class ObjParser:
    def __init__(
        self,
        swapyz: bool = False,
        normalize: bool = False,
    ):
        self.swapyz = swapyz
        self.normalize = normalize

        self.scene: ObjSceneAsset = ObjSceneAsset()

        self.vertices: list[list[float]] = []
        self.normals: list[list[float]] = []
        self.texcoords: list[list[float]] = []

        self.faces: list[
            tuple[
                list[int],
                list[int],
                list[int],
                object | None,
            ]
        ] = []

        self._current_object: str | None = None

    def load(
        self,
        filename: str | Path,
    ) -> ObjSceneAsset:
        self.scene = ObjSceneAsset()

        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self._current_object = None

        material = None

        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                values = line.split()

                if not values:
                    continue

                command = values[0]

                if command == "s":
                    continue

                if command == "o":
                    self.finish_object()
                    self._current_object = (
                        values[1]
                        if len(values) > 1
                        else f"object_{len(self.scene.objects)}"
                    )

                elif command == "v":
                    vertex = list(map(float, values[1:4]))

                    if self.swapyz:
                        vertex = [
                            vertex[0],
                            vertex[2],
                            vertex[1],
                        ]

                    self.vertices.append(vertex)

                elif command == "vn":
                    normal = list(map(float, values[1:4]))

                    if self.swapyz:
                        normal = [
                            normal[0],
                            normal[2],
                            normal[1],
                        ]

                    self.normals.append(normal)

                elif command == "vt":
                    self.texcoords.append(
                        list(map(float, values[1:3]))
                    )

                elif command == "f":
                    if self._current_object is None:
                        self._current_object = "default"

                    face: list[int] = []
                    texcoords: list[int] = []
                    normals: list[int] = []

                    for vertex_data in values[1:]:
                        parts = vertex_data.split("/")

                        face.append(
                            self._resolve_index(
                                int(parts[0]),
                                len(self.vertices),
                            )
                        )

                        if len(parts) >= 2 and parts[1]:
                            texcoords.append(
                                self._resolve_index(
                                    int(parts[1]),
                                    len(self.texcoords),
                                )
                            )
                        else:
                            texcoords.append(-1)

                        if len(parts) >= 3 and parts[2]:
                            normals.append(
                                self._resolve_index(
                                    int(parts[2]),
                                    len(self.normals),
                                )
                            )
                        else:
                            normals.append(-1)

                    self.faces.append(
                        (
                            face,
                            normals,
                            texcoords,
                            material,
                        )
                    )

        self.finish_object()

        return self.scene

    def finish_object(self) -> None:
        if self._current_object is None:
            return

        if not self.faces:
            return

        positions: list[list[float]] = []
        normals: list[tuple[float, float, float] | list[float]] = []
        texcoords: list[tuple[float, float] | list[float]] = []
        indices: list[int] = []

        index = 0

        for face_data in self.faces:
            face_vertices = face_data[0]
            face_normals = face_data[1]
            face_texcoords = face_data[2]

            for triangle in self._triangulate_face(
                face_vertices,
                face_normals,
                face_texcoords,
            ):
                triangle_vertices = triangle[0]
                triangle_normals = triangle[1]
                triangle_texcoords = triangle[2]

                for i in range(3):
                    vertex = self.vertices[
                        triangle_vertices[i]
                    ]

                    normal: tuple[float, float, float] | list[float] = (
                        0.0,
                        0.0,
                        0.0,
                    )

                    if triangle_normals[i] != -1:
                        normal = self.normals[
                            triangle_normals[i]
                        ]

                    texcoord: tuple[float, float] | list[float] = (
                        0.0,
                        0.0,
                    )

                    if triangle_texcoords[i] != -1:
                        texcoord = self.texcoords[
                            triangle_texcoords[i]
                        ]

                    positions.append(vertex)
                    normals.append(normal)
                    texcoords.append(texcoord)

                indices.extend(
                    [
                        index,
                        index + 1,
                        index + 2,
                    ]
                )

                index += 3

        positions_array = np.array(
            positions,
            dtype=np.float32,
        )

        normals_array = np.array(
            normals,
            dtype=np.float32,
        )

        texcoords_array = np.array(
            texcoords,
            dtype=np.float32,
        )

        transform = Transform()

        if self.normalize and positions_array.size > 0:
            mins = positions_array.min(axis=0)
            maxs = positions_array.max(axis=0)
            center = (mins + maxs) * 0.5

            positions_array = positions_array - center

            transform = Transform(
                translation=Vector3(
                    float(center[0]),
                    float(center[1]),
                    float(center[2]),
                )
            )

        bounds = GeometryBounds.from_positions(
            positions_array
        )

        packed_vertices = np.column_stack(
            [
                positions_array,
                normals_array,
                texcoords_array,
            ]
        ).reshape(-1)

        final_indices = self._ensure_uint16_indices(
            np.array(
                indices,
                dtype=np.int64,
            )
        )

        geometry = Geometry(
            name=self._current_object,
            fmt=[
                (b"v_pos", 3, "float"),
                (b"v_normal", 3, "float"),
                (b"v_uv", 2, "float"),
            ],
            vertices=packed_vertices.astype(
                np.float32,
                copy=False,
            ),
            indices=final_indices,
            bounds=bounds,
        )

        self.scene.objects[self._current_object] = ObjAsset(
            name=self._current_object,
            geometry=geometry,
            transform=transform,
        )

        self.faces = []

    def _triangulate_face(
        self,
        vertices: list[int],
        normals: list[int],
        texcoords: list[int],
    ):
        for index in range(1, len(vertices) - 1):
            yield (
                [
                    vertices[0],
                    vertices[index],
                    vertices[index + 1],
                ],
                [
                    normals[0],
                    normals[index],
                    normals[index + 1],
                ],
                [
                    texcoords[0],
                    texcoords[index],
                    texcoords[index + 1],
                ],
            )

    def _resolve_index(
        self,
        index: int,
        count: int,
    ) -> int:
        if index > 0:
            return index - 1

        return count + index

    def _ensure_uint16_indices(
        self,
        indices: np.ndarray,
    ) -> np.ndarray:
        if indices.size == 0:
            return indices.astype(
                np.uint16,
                copy=False,
            )

        total = int(indices.max())

        if total > 65535:
            raise OverflowError(
                "Indices exceed 65535 in a single OBJ object. "
                "Split the object before loading it."
            )

        return indices.astype(
            np.uint16,
            copy=False,
        )

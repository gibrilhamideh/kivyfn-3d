# kivyfn/three/loaders/obj.py

from __future__ import annotations

from pathlib import Path

from kivyfn.three.loaders.asset import AssetObject, SceneAsset
from kivyfn.three.math.transform import Transform
from kivyfn.three.objects.geometry import Geometry


class ObjLoader:
    def __init__(
        self,
        swapyz: bool = False,
    ):
        self.swapyz = swapyz

        self.scene: SceneAsset = SceneAsset()
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self._current_object: str | None = None

    def load(
        self,
        filename: str | Path,
    ) -> SceneAsset:
        """Load a Wavefront OBJ file."""

        self.scene = SceneAsset()

        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []

        self._current_object = None

        material = None

        with open(filename, "r") as file:
            for line in file:
                if line.startswith("#"):
                    continue

                if line.startswith("s"):
                    continue

                values = line.split()

                if not values:
                    continue

                if values[0] == "o":
                    self.finish_object()
                    self._current_object = values[1]

                elif values[0] == "v":
                    vertex = list(map(float, values[1:4]))

                    if self.swapyz:
                        vertex = [
                            vertex[0],
                            vertex[2],
                            vertex[1],
                        ]

                    self.vertices.append(vertex)

                elif values[0] == "vn":
                    normal = list(map(float, values[1:4]))

                    if self.swapyz:
                        normal = [
                            normal[0],
                            normal[2],
                            normal[1],
                        ]

                    self.normals.append(normal)

                elif values[0] == "vt":
                    self.texcoords.append(
                        list(map(float, values[1:3]))
                    )

                elif values[0] == "f":
                    face = []
                    texcoords = []
                    normals = []

                    for vertex_data in values[1:]:
                        parts = vertex_data.split("/")

                        face.append(int(parts[0]))

                        if len(parts) >= 2 and parts[1]:
                            texcoords.append(int(parts[1]))
                        else:
                            texcoords.append(-1)

                        if len(parts) >= 3 and parts[2]:
                            normals.append(int(parts[2]))
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

        geometry = Geometry(
            name=self._current_object,
        )

        index = 0

        for face_data in self.faces:
            vertices = face_data[0]
            normals = face_data[1]
            texcoords = face_data[2]

            # OBJ faces can be triangles or polygons.
            # Convert polygon faces into triangles using fan triangulation.
            for triangle in self._triangulate_face(
                vertices,
                normals,
                texcoords,
            ):
                triangle_vertices = triangle[0]
                triangle_normals = triangle[1]
                triangle_texcoords = triangle[2]

                for i in range(3):
                    normal = (0.0, 0.0, 0.0)

                    if triangle_normals[i] != -1:
                        normal = self.normals[triangle_normals[i] - 1]

                    texcoord = (0.0, 0.0)

                    if triangle_texcoords[i] != -1:
                        texcoord = self.texcoords[triangle_texcoords[i] - 1]

                    vertex = self.vertices[triangle_vertices[i] - 1]

                    geometry.vertices.extend(
                        [
                            vertex[0],
                            vertex[1],
                            vertex[2],
                            normal[0],
                            normal[1],
                            normal[2],
                            texcoord[0],
                            texcoord[1],
                        ]
                    )

                geometry.indices.extend(
                    [
                        index,
                        index + 1,
                        index + 2,
                    ]
                )

                index += 3

        self.scene.objects[self._current_object] = AssetObject(
            name=self._current_object,
            geometry=geometry,
            transform=Transform(),
            material=None,
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




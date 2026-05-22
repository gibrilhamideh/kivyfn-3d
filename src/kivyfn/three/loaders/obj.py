
from kivyfn.three.objects.geometry import Geometry

class ObjLoader:
    def __init__(self, swapyz=False):
        self.swapyz = swapyz

    def load(self, filename):
        """Load a Wavefront OBJ file."""

        self.objects = {}

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
                    v = list(map(float, values[1:4]))

                    if self.swapyz:
                        v = (v[0], v[2], v[1])

                    self.vertices.append(v)

                elif values[0] == "vn":
                    v = list(map(float, values[1:4]))

                    if self.swapyz:
                        v = (v[0], v[2], v[1])

                    self.normals.append(v)

                elif values[0] == "vt":
                    self.texcoords.append(
                        list(map(float, values[1:3]))
                    )

                elif values[0] == "f":
                    face = []
                    texcoords = []
                    norms = []

                    for v in values[1:]:
                        w = v.split("/")

                        face.append(int(w[0]))

                        if len(w) >= 2 and len(w[1]) > 0:
                            texcoords.append(int(w[1]))
                        else:
                            texcoords.append(-1)

                        if len(w) >= 3 and len(w[2]) > 0:
                            norms.append(int(w[2]))
                        else:
                            norms.append(-1)

                    self.faces.append(
                        (face, norms, texcoords, material)
                    )

        self.finish_object()

        return self.objects

    def finish_object(self):
        if self._current_object is None:
            return

        geometry = Geometry(name=self._current_object)

        idx = 0

        for f in self.faces:
            verts = f[0]
            norms = f[1]
            tcs = f[2]

            for i in range(3):
                # normal
                n = (0.0, 0.0, 0.0)

                if norms[i] != -1:
                    n = self.normals[norms[i] - 1]

                # texture coordinate
                t = (0.0, 0.0)

                if tcs[i] != -1:
                    t = self.texcoords[tcs[i] - 1]

                # vertex
                v = self.vertices[verts[i] - 1]

                geometry.vertices.extend([
                    v[0], v[1], v[2],
                    n[0], n[1], n[2],
                    t[0], t[1],
                ])

            geometry.indices.extend([
                idx,
                idx + 1,
                idx + 2,
            ])

            idx += 3

        self.objects[self._current_object] = geometry

        # mesh.calculate_normals()

        self.faces = []




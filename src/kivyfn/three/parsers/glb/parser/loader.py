# kivyfn/three/parsers/glb/parser/loader.py

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from pygltflib import GLTF2

from kivyfn.three.parsers.glb.blueprint import GlbBlueprint
from kivyfn.three.parsers.glb.parser.context import (
    GlbContext,
    GlbOptions,
)


class GlbLoader:
    def load(
        self,
        filename: str | Path,
        options: GlbOptions,
    ) -> GlbContext:
        path = Path(filename)
        gltf = GLTF2().load_binary(str(path))

        return GlbContext(
            gltf=gltf,
            filename=path,
            base_path=path.parent,
            buffer_bytes=self.buffer_bytes(
                gltf=gltf,
                filename=path,
            ),
            blueprint=GlbBlueprint(),
            options=options,
        )

    def buffer_bytes(
        self,
        *,
        gltf: Any,
        filename: Path,
    ) -> bytes:
        buffer_bytes = gltf.binary_blob()

        if buffer_bytes is not None:
            return buffer_bytes

        if not gltf.buffers:
            raise ValueError("No buffer found in GLB file.")

        uri = gltf.buffers[0].uri

        if uri and uri.startswith("data:"):
            encoded = uri.split(",", 1)[1]
            return base64.b64decode(encoded)

        if uri:
            bin_path = (
                Path(uri)
                if os.path.isabs(uri)
                else filename.parent / uri
            )

            return bin_path.read_bytes()

        raise ValueError("No binary buffer found in GLB file.")



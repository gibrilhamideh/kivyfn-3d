from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class LightLimits:
    """
    Maximum number of lights uploaded to shader uniforms.

    Note:
        Values 2, 3, and 4 are not supported.

        Kivy appears to interpret lists of these lengths as special
        uniform types (e.g. vec2, vec3, vec4) rather than uniform
        arrays, which causes shader array uploads to fail.

        Use 1 or 5+ instead.
    """

    directional: int = 1
    point: int = 5
    spot: int = 5

    def __post_init__(self) -> None:
        invalid = {2, 3, 4}

        for name in ("directional", "point", "spot"):
            value = getattr(self, name)

            if value in invalid:
                raise ValueError(
                    f"LightLimits.{name}={value} is not allowed. "
                    "Values 2, 3, and 4 are interpreted by Kivy as "
                    "special uniform types (vec2/vec3/vec4) rather "
                    "than uniform arrays. Use 1 or 5+ instead."
                )

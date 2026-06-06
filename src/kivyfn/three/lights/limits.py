from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class LightLimits:
    """
    Maximum number of lights uploaded to shader uniforms.

    Note:
        Do not use a limit of 4 for point or spot lights when
        uploading vec3 arrays through Kivy.

        Kivy appears to interpret a list containing exactly four
        vec3 elements differently internally (likely treating it as
        a matrix or another special uniform type), which causes the
        shader arrays to be uploaded incorrectly.

        Use 5 or greater instead and rely on the corresponding
        `*_light_count` uniform in the shader to determine how many
        lights are actually active.
    """
    directional: int = 2
    point: int = 5
    spot: int = 5

from kivyfn.paths import package_path


# ========================================= #
# Root
# ========================================= #

THREE_PATH = package_path("kivyfn.three")


# ========================================= #
# Resources
# ========================================= #

THREE_RESOURCE_PATH = package_path(
    "kivyfn.three",
    "resources",
)

THREE_SHADER_PATH = THREE_RESOURCE_PATH / "shaders"

THREE_TEXTURE_PATH = THREE_RESOURCE_PATH / "textures"

THREE_MODEL_PATH = THREE_RESOURCE_PATH / "models"


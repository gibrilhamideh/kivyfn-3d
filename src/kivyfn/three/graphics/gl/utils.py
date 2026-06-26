def normalize_size(
    size: int | tuple[int, int] | list[int],
) -> tuple[int, int]:
    if isinstance(size, int):
        if size <= 0:
            raise ValueError(
                f"Size must be greater than zero, got {size}."
            )

        return size, size

    if not isinstance(size, (tuple, list)):
        raise TypeError(
            "Size must be an int, tuple[int, int], or list[int]. "
            f"Got {type(size).__name__}."
        )

    if len(size) != 2:
        raise ValueError(
            "Size tuple/list must contain exactly two values: "
            f"(width, height). Got {size!r}."
        )

    width, height = size

    if not isinstance(width, int) or not isinstance(height, int):
        raise TypeError(
            "Size width and height must both be int values. "
            f"Got {type(width).__name__} and {type(height).__name__}."
        )

    if width <= 0 or height <= 0:
        raise ValueError(
            "Size width and height must be greater than zero. "
            f"Got {width}x{height}."
        )

    return width, height



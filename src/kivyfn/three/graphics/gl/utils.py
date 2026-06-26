def normalize_size(
    size: int | tuple[int, int],
) -> tuple[int, int]:
    if isinstance(size, int):
        return size, size

    return int(size[0]), int(size[1])



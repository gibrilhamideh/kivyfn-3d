import math


def triangle_intersect(origin, direction, v0, v1, v2):
    """
    Möller-Trumbore ray-triangle intersection.
    orig, dir: 3-tuples for ray origin & direction.
    v0, v1, v2: 3-tuples for triangle vertices.
    Returns t (distance) if hit, else None.
    """
    EPS = 1e-6
    # Edge vectors
    e1 = (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2])
    e2 = (v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2])
    # Begin calculating determinant - also used to calculate U parameter
    p = (
        direction[1]*e2[2] - direction[2]*e2[1],
        direction[2]*e2[0] - direction[0]*e2[2],
        direction[0]*e2[1] - direction[1]*e2[0]
    )
    det = e1[0]*p[0] + e1[1]*p[1] + e1[2]*p[2]
    if abs(det) < EPS:
        return None, None
    inv_det = 1.0 / det

    # Calculate distance from v0 to ray origin
    t0 = (origin[0]-v0[0], origin[1]-v0[1], origin[2]-v0[2])
    # Calculate U parameter and test bounds
    u = (t0[0]*p[0] + t0[1]*p[1] + t0[2]*p[2]) * inv_det
    if u < 0.0 or u > 1.0:
        return None, None

    # Prepare to test V parameter
    q = (
        t0[1]*e1[2] - t0[2]*e1[1],
        t0[2]*e1[0] - t0[0]*e1[2],
        t0[0]*e1[1] - t0[1]*e1[0]
    )
    v = (direction[0]*q[0] + direction[1]*q[1] + direction[2]*q[2]) * inv_det
    if v < 0.0 or u + v > 1.0:
        return None, None

    # Compute t to intersection point
    t = (e2[0]*q[0] + e2[1]*q[1] + e2[2]*q[2]) * inv_det

    # Calculate hit point
    location = (origin[0]+direction[0]*t, origin[1]+direction[1]*t, origin[2]+direction[2]*t)

    if t < EPS:
        return None, None
    
    return t, location

def sphere_intersect(source_origin, source_direction, obj_origin, obj_radius) -> bool:
    """
    Check if a ray intersects a sphere.
    """
    ox, oy, oz = source_origin
    dx, dy, dz = source_direction
    cx, cy, cz = obj_origin
    r = obj_radius

    # vector from ray origin to center
    ocx, ocy, ocz = ox - cx, oy - cy, oz - cz

    # quadratic coefficients
    a = dx*dx + dy*dy + dz*dz
    b = 2.0 * (ocx*dx + ocy*dy + ocz*dz)
    c = ocx*ocx + ocy*ocy + ocz*ocz - r*r

    disc = b*b - 4*a*c
    if disc < 0:
        return False

    sqrt_d = math.sqrt(disc)
    t1 = (-b - sqrt_d) / (2*a)
    t2 = (-b + sqrt_d) / (2*a)

    # choose the smallest positive t
    t = None
    if t1 > 0 and t2 > 0:
        t = min(t1, t2)
    elif t1 > 0:
        t = t1
    elif t2 > 0:
        t = t2

    if t is not None:
        return True


    return False


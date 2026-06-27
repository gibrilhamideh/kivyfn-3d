#ifdef GL_ES
precision highp float;
#endif

uniform samplerCube shadow_texture;
uniform float shadow_far;

varying vec2 uv;

// ================================== //
// Helpers
// ================================== //

vec3 face_direction(
    int face,
    vec2 face_uv
) {
    // face_uv is in [0, 1]
    // convert to [-1, 1]
    float u = face_uv.x * 2.0 - 1.0;
    float v = face_uv.y * 2.0 - 1.0;

    // Standard-ish cubemap preview mapping.
    // If one face looks mirrored, just flip the needed sign.
    if (face == 0) { // +X
        return normalize(vec3(1.0, -v, -u));
    }

    if (face == 1) { // -X
        return normalize(vec3(-1.0, -v, u));
    }

    if (face == 2) { // +Y
        return normalize(vec3(u, 1.0, v));
    }

    if (face == 3) { // -Y
        return normalize(vec3(u, -1.0, -v));
    }

    if (face == 4) { // +Z
        return normalize(vec3(u, -v, 1.0));
    }

    // face == 5 : -Z
    return normalize(vec3(-u, -v, -1.0));
}

vec3 face_border_color(
    int face
) {
    if (face == 0) return vec3(1.0, 0.2, 0.2); // +X
    if (face == 1) return vec3(0.2, 1.0, 0.2); // -X
    if (face == 2) return vec3(0.2, 0.4, 1.0); // +Y
    if (face == 3) return vec3(1.0, 1.0, 0.2); // -Y
    if (face == 4) return vec3(1.0, 0.3, 1.0); // +Z
    return vec3(0.2, 1.0, 1.0); // -Z
}

float border_mask(
    vec2 local_uv
) {
    float b = 0.02;

    if (
        local_uv.x < b ||
            local_uv.x > 1.0 - b ||
            local_uv.y < b ||
            local_uv.y > 1.0 - b
    ) {
        return 1.0;
    }

    return 0.0;
}

// ================================== //
// Main
// ================================== //

void main(void) {
    vec2 grid = uv;

    // 3 columns, 2 rows
    float cell_w = 1.0 / 3.0;
    float cell_h = 1.0 / 2.0;

    int col = int(floor(grid.x / cell_w));
    int row = int(floor(grid.y / cell_h));

    // flip row so top row is row 0
    row = 1 - row;

    int face = -1;

    // top row
    if (row == 0 && col == 0) face = 0; // +X
    if (row == 0 && col == 1) face = 1; // -X
    if (row == 0 && col == 2) face = 2; // +Y

    // bottom row
    if (row == 1 && col == 0) face = 3; // -Y
    if (row == 1 && col == 1) face = 4; // +Z
    if (row == 1 && col == 2) face = 5; // -Z

    if (face < 0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec2 local_uv = vec2(
            (grid.x - float(col) * cell_w) / cell_w,
            (grid.y - float(1 - row) * cell_h) / cell_h
        );

    vec3 dir = face_direction(face, local_uv);

    // Your shadow cubemap stores normalized depth in .r
    float depth01 = textureCube(shadow_texture, dir).r;

    // Debug contrast boost so near depths are easier to see.
    float preview = pow(depth01, 0.35);

    vec3 color = vec3(preview);

    float border = border_mask(local_uv);
    vec3 border_color = face_border_color(face);

    color = mix(color, border_color, border);

    gl_FragColor = vec4(color, 1.0);
}

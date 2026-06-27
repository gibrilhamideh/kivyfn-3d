

#ifdef GL_ES
precision highp float;
#endif

uniform sampler2D preview_texture;

varying vec2 tex_coord0;

// ================================== //
// Helpers
// ================================== //

float border_mask(
    vec2 uv
) {
    float b = 0.02;

    if (
        uv.x < b ||
            uv.x > 1.0 - b ||
            uv.y < b ||
            uv.y > 1.0 - b
    ) {
        return 1.0;
    }

    return 0.0;
}

// ================================== //
// Main
// ================================== //

void main(void) {
    vec4 sampled = texture2D(
            preview_texture,
            tex_coord0
        );

    vec3 background = vec3(
            0.0,
            0.0,
            0.0
        );

    vec3 color = mix(
            background,
            sampled.rgb,
            sampled.a
        );

    float border = border_mask(
            tex_coord0
        );

    vec3 border_color = vec3(
            1.0,
            0.75,
            0.2
        );

    color = mix(
            color,
            border_color,
            border
        );

    gl_FragColor = vec4(
            color,
            1.0
        );
}

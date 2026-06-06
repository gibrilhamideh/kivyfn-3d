#ifdef GL_ES
precision highp float;
#endif

varying vec3 normal_vec;
varying vec4 vertex_pos;

uniform vec4 base_color;

uniform vec3 light_direction;

void main(void) {
    vec3 N =
        normalize(normal_vec);

    vec3 L =
        normalize(-light_direction);

    float theta =
        clamp(
            dot(N, L),
            0.0,
            1.0
        );

    gl_FragColor =
        vec4(
            base_color.rgb * theta,
            base_color.a
        );
}

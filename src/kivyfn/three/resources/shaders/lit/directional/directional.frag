#ifdef GL_ES
precision highp float;
#endif

varying vec3 frag_normal;
varying vec3 frag_position;

uniform vec4 base_color;

uniform vec3 light_direction;
uniform vec3 light_color;
uniform float light_intensity;

void main(void) {
    vec3 normal = normalize(frag_normal);

    vec3 light_dir = normalize(-light_direction);

    float diffuse = max(
            dot(normal, light_dir),
            0.0
        );

    vec3 color =
        base_color.rgb *
            light_color *
            diffuse *
            light_intensity;

    gl_FragColor = vec4(
            color,
            base_color.a
        );
}

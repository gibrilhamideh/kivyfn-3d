#ifdef GL_ES
precision highp float;
#endif

varying vec3 world_pos;

uniform vec3 camera_position;
uniform float shadow_far;

void main(void) {
    float depth =
        length(world_pos - camera_position) /
            shadow_far;

    gl_FragColor =
        vec4(vec3(depth), 1.0);
}

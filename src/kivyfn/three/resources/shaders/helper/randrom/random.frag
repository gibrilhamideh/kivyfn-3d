#ifdef GL_ES
precision highp float;
#endif

varying vec3 debug_color;

void main(void) {
    gl_FragColor =
        vec4(
            debug_color,
            1.0
        );
}

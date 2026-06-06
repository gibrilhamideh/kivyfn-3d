#ifdef GL_ES
precision highp float;
#endif

uniform vec4 base_color;

void main(void) {
    gl_FragColor = base_color;
}

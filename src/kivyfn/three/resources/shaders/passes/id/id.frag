#ifdef GL_ES
precision highp float;
#endif

uniform vec4 id_color;

void main(void) {
    gl_FragColor = id_color;
}

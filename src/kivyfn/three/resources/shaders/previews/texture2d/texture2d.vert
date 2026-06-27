#ifdef GL_ES
precision highp float;
#endif

attribute vec2 v_pos;
attribute vec2 v_tc0;

varying vec2 tex_coord0;

void main(void) {
    tex_coord0 = v_tc0;
    gl_Position = vec4(v_pos, 0.0, 1.0);
}

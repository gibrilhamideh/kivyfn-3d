#ifdef GL_ES
precision highp float;
#endif

attribute vec3 v_pos;
attribute vec2 v_tc0;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;

varying vec2 uv;

void main(void) {
    uv = v_tc0;
    gl_Position = projection_mat * modelview_mat * vec4(v_pos, 1.0);
}

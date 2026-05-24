---VERTEX SHADER-------------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3 v_pos;
attribute vec3 v_normal;
attribute vec2 v_tc0;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;

void main(void) {
    gl_Position = projection_mat * modelview_mat * vec4(v_pos, 1.0);
}

---FRAGMENT SHADER-----------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

uniform vec4 base_color;

void main(void) {
    gl_FragColor = base_color;
}

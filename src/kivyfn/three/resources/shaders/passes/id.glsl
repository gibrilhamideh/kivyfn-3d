---VERTEX SHADER-------------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3 v_pos;

uniform mat4 model_mat;
uniform mat4 view_mat;
uniform mat4 projection_mat;

void main(void) {
    gl_Position =
        projection_mat *
        view_mat *
        model_mat *
        vec4(v_pos, 1.0);
}


---FRAGMENT SHADER-----------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

uniform vec4 id_color;

void main(void) {
    gl_FragColor = id_color;
    // gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
}

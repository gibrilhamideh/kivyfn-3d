#ifdef GL_ES
precision highp float;
#endif

attribute vec3 v_pos;
attribute vec3 v_normal;
attribute vec2 v_tc0;

uniform mat4 model_mat;
uniform mat4 view_mat;
uniform mat4 projection_mat;

void main(void) {
    vec4 world_pos =
        model_mat *
            vec4(v_pos, 1.0);

    gl_Position =
        projection_mat *
            view_mat *
            world_pos;
}

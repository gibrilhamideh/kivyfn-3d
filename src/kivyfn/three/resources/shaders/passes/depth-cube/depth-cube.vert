#ifdef GL_ES
precision highp float;
#endif

attribute vec3 v_pos;

uniform mat4 model_mat;
uniform mat4 view_mat;
uniform mat4 projection_mat;

varying vec3 world_pos;

void main(void) {
    vec4 world_position =
        model_mat *
            vec4(v_pos, 1.0);

    world_pos =
        world_position.xyz;

    gl_Position =
        projection_mat *
            view_mat *
            world_position;
}

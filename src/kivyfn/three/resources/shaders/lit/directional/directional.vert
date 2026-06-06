#ifdef GL_ES
precision highp float;
#endif

attribute vec3 v_pos;
attribute vec3 v_normal;

uniform mat4 model_mat;
uniform mat4 view_mat;
uniform mat4 projection_mat;
uniform mat4 normal_mat;

varying vec3 frag_normal;
varying vec3 frag_position;

void main(void) {
    vec4 world_pos =
        model_mat *
            vec4(v_pos, 1.0);

    mat3 normal3 =
        mat3(
            normal_mat[0].xyz,
            normal_mat[1].xyz,
            normal_mat[2].xyz
        );

    frag_position =
        world_pos.xyz;

    frag_normal =
        normalize(
            normal3 *
                v_normal
        );

    gl_Position =
        projection_mat *
            view_mat *
            world_pos;
}

// kivyfn/three/resources/3d/shaders/passes/depth/depth.vert
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

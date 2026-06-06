#ifdef GL_ES
precision highp float;
#endif

attribute vec3 v_pos;

uniform mat4 model_mat;
uniform mat4 view_mat;
uniform mat4 projection_mat;

varying vec3 debug_color;

float random_float(float x) {
    return fract(
        sin(x) *
            43758.5453123
    );
}

float hash_vec3(vec3 p) {
    return random_float(
        dot(
            p,
            vec3(12.9898, 78.233, 37.719)
        )
    );
}

vec3 random_color(vec3 seed) {
    float r =
        hash_vec3(seed + vec3(1.0, 0.0, 0.0));

    float g =
        hash_vec3(seed + vec3(0.0, 1.0, 0.0));

    float b =
        hash_vec3(seed + vec3(0.0, 0.0, 1.0));

    return vec3(r, g, b);
}

void main(void) {
    vec4 world_pos =
        model_mat *
            vec4(v_pos, 1.0);

    vec3 object_seed =
        vec3(
            model_mat[3].x,
            model_mat[3].y,
            model_mat[3].z
        );

    debug_color =
        random_color(object_seed);

    gl_Position =
        projection_mat *
            view_mat *
            world_pos;
}

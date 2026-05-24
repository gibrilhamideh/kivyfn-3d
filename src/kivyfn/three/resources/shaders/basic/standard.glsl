---VERTEX SHADER-------------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3 v_pos;
attribute vec3 v_normal;
attribute vec2 v_tc0;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;
uniform mat4 normal_mat;

varying vec3 vertex_pos;
varying vec3 normal_vec;
varying vec2 texcoord_0;

void main(void) {
    vec4 view_pos = modelview_mat * vec4(v_pos, 1.0);

    vertex_pos = view_pos.xyz;
    normal_vec = normalize((normal_mat * vec4(v_normal, 0.0)).xyz);
    texcoord_0 = v_tc0;

    gl_Position = projection_mat * view_pos;
}


---FRAGMENT SHADER-----------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

varying vec3 vertex_pos;
varying vec3 normal_vec;
varying vec2 texcoord_0;

uniform vec4 base_color;
uniform sampler2D base_texture;

uniform float metallic_factor;
uniform float roughness_factor;
uniform sampler2D metallic_roughness_texture;

uniform vec3 emissive_factor;
uniform sampler2D emissive_texture;

uniform sampler2D occlusion_texture;

void main(void) {
    vec3 N = normalize(normal_vec);

    vec3 light_pos = vec3(0.0, 0.0, 0.0);
    vec3 L = normalize(light_pos - vertex_pos);
    vec3 V = normalize(-vertex_pos);
    vec3 H = normalize(L + V);

    vec4 base_sample = texture2D(
        base_texture,
        texcoord_0
    );

    vec4 albedo = base_color * base_sample;

    vec4 mr_sample = texture2D(
        metallic_roughness_texture,
        texcoord_0
    );

    float roughness = clamp(
        roughness_factor * mr_sample.g,
        0.04,
        1.0
    );

    float metallic = clamp(
        metallic_factor * mr_sample.b,
        0.0,
        1.0
    );

    float occlusion = texture2D(
        occlusion_texture,
        texcoord_0
    ).r;

    vec3 emissive = emissive_factor * texture2D(
        emissive_texture,
        texcoord_0
    ).rgb;

    float NdotL = max(dot(N, L), 0.0);
    float NdotH = max(dot(N, H), 0.0);
    float VdotH = max(dot(V, H), 0.0);

    vec3 diffuse = albedo.rgb * NdotL;
    diffuse *= 1.0 - metallic;

    vec3 f0 = mix(
        vec3(0.04),
        albedo.rgb,
        metallic
    );

    vec3 fresnel = f0 + (1.0 - f0) * pow(
        1.0 - VdotH,
        5.0
    );

    float shininess = mix(
        256.0,
        8.0,
        roughness
    );

    vec3 specular = fresnel * pow(
        NdotH,
        shininess
    ) * NdotL;

    vec3 ambient = albedo.rgb * 0.08 * occlusion;

    vec3 color = ambient + diffuse + specular + emissive;

    gl_FragColor = vec4(
        color,
        albedo.a
    );
}

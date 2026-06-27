// kivyfn/three/resources/3d/shaders/passes/depth/depth.frag
#ifdef GL_ES
precision highp float;
#endif

void main(void) {
    gl_FragColor = vec4(vec3(gl_FragCoord.z), 1.0);
}

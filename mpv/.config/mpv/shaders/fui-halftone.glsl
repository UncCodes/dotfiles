// fui // mpv: a colour halftone over every picture and video
//
// The printed-screen look: the picture is broken into a dot screen at 45 degrees, each dot
// growing with the light at that point, the way a halftone grows its dots with the ink. It
// keeps the colour: each channel is reduced to a few levels and the step between two levels
// is drawn with the same clustered dots, so flat areas read as an even grid of dots and edges
// stay sharp. It runs on the output, after scaling, so the dots are screen pixels at any zoom.
//
// mpv.conf loads it; `d` turns it off and on. Tune it with --glsl-shader-opts, e.g.
//   glsl-shader-opts=cell=5,levels=4      (larger dots, more tone)
// Under 4 px the 45-degree screen beats against the pixel grid (moire): keep cell at 4 or more.

//!PARAM cell
//!DESC dot pitch in screen pixels
//!TYPE float
//!MINIMUM 4.0
//!MAXIMUM 12.0
4.0

//!PARAM levels
//!DESC levels per colour channel (2 is a pure dot screen; more keeps more tone)
//!TYPE float
//!MINIMUM 2.0
//!MAXIMUM 8.0
3.0

//!HOOK OUTPUT
//!BIND HOOKED
//!DESC fui halftone

#define TAU 6.28318530718

vec4 hook() {
    vec4 c = HOOKED_texOff(0);
    // the screen: pixel position, turned 45 degrees, in units of one dot
    vec2 px = HOOKED_pos * HOOKED_size;
    vec2 uv = mat2(0.70710678, -0.70710678, 0.70710678, 0.70710678) * px / cell;
    // the spot: 1 at a dot's centre, -1 between dots; as a threshold it lights the centre first
    float spot = 0.5 * (cos(TAU * uv.x) + cos(TAU * uv.y));
    float threshold = clamp(0.5 - 0.5 * spot, 0.0, 1.0);
    // each channel: the level below, plus one more where the dot reaches this pixel
    vec3 x = clamp(c.rgb, 0.0, 1.0) * (levels - 1.0);
    vec3 base = floor(x);
    vec3 lit = step(vec3(threshold), x - base);
    c.rgb = (base + lit) / (levels - 1.0);
    return c;
}

/* =====================================================================
   Montana in Relief — 3D explorer for Allan Cartography's 1991 sheet
   Part 1: data, projection, textures, shaders, scene
   ===================================================================== */
(function(){
'use strict';
const M = window.MT_META;
const $ = s => document.querySelector(s);
const clamp = (v,a,b) => v<a?a:(v>b?b:v);
const lerp  = (a,b,t) => a+(b-a)*t;
const smoothstep = t => t*t*(3-2*t);
const DEG = Math.PI/180;

/* ---------- world constants ---------- */
const W = M.kmw, H = M.kmh;                 // plate size, km
const HMW = M.hm.w, HMH = M.hm.h;           // height raster
const HMIN = M.hmin, HMAX = M.hmax;         // metres
const RELIEF = (HMAX-HMIN)/1000;            // km
const CELLX = W/HMW, CELLZ = H/HMH;         // km per height texel

/* ---------- Lambert conformal conic (inverse) ---------- */
const G = M.grid;
function uvToLonLat(u, vN){
  const X = G.X0 + u*(G.X1-G.X0);
  const Y = G.Y1 - vN*(G.Y1-G.Y0);
  const rho = Math.hypot(X,Y), th = Math.atan2(X,-Y);
  const lon = (G.LON0 + th/G.NN)/DEG;
  const lat = (2*Math.atan(Math.pow(G.F/rho, 1/G.NN)) - Math.PI/2)/DEG;
  return [lon, lat];
}
function lonLatToUV(lon, lat){
  const rho = G.F/Math.pow(Math.tan(Math.PI/4 + lat*DEG/2), G.NN);
  const th  = G.NN*(lon*DEG - G.LON0);
  const X = rho*Math.sin(th), Y = -rho*Math.cos(th);
  return [(X-G.X0)/(G.X1-G.X0), (G.Y1-Y)/(G.Y1-G.Y0)];
}
// world <-> uv (uv.x east, vN south-ward from north edge)
const wx = u => (u-0.5)*W, wz = vN => (vN-0.5)*H;
const ux = x => x/W+0.5,   vz = z => z/H+0.5;

/* ---------- height field (CPU) ---------- */
let hData=null, bData=null;                  // Float32Array metres, Float32Array border-dist
function sampleH(x,z){                       // metres, bilinear
  let fx = ux(x)*HMW-0.5, fz = vz(z)*HMH-0.5;
  fx = clamp(fx,0,HMW-1.001); fz = clamp(fz,0,HMH-1.001);
  const i=fx|0, j=fz|0, tx=fx-i, tz=fz-j, k=j*HMW+i;
  const a=hData[k], b=hData[k+1], c=hData[k+HMW], d=hData[k+HMW+1];
  return (a+(b-a)*tx)*(1-tz) + (c+(d-c)*tx)*tz;
}
function insideMT(x,z){
  let fx = clamp(ux(x)*HMW,0,HMW-1)|0, fz = clamp(vz(z)*HMH,0,HMH-1)|0;
  return bData[fz*HMW+fx] > 0;
}
let EXAG = 5.0;
const terrainY = (x,z) => (sampleH(x,z)-HMIN)/1000*EXAG;

/* ---------- half float ---------- */
const _f32 = new Float32Array(1), _i32 = new Int32Array(_f32.buffer);
function toHalf(val){
  _f32[0]=val; const x=_i32[0];
  let bits=(x>>16)&0x8000, m=(x>>12)&0x07ff; const e=(x>>23)&0xff;
  if(e<103) return bits;
  if(e>142){ bits|=0x7c00; bits|=((e===255)?0:1)&&(x&0x007fffff); return bits; }
  if(e<113){ m|=0x0800; bits|=(m>>(114-e))+((m>>(113-e))&1); return bits; }
  bits|=((e-112)<<10)|(m>>1); bits+=m&1; return bits;
}

/* ---------- loading ---------- */
const ld = {bar:$('#ldbar'), txt:$('#ldtxt')};
function prog(p, t){ ld.bar.style.width = (p*100)+'%'; if(t) ld.txt.textContent = t; }
function loadImage(src){
  return new Promise((res,rej)=>{ const i=new Image(); i.onload=()=>res(i); i.onerror=rej; i.decoding='async'; i.src=src; });
}

let renderer, scene, camera, terrain, skirt, sky, ground, drapeTex, hTex, rampTex, drapeImg;
const U = {};                                   // shared uniforms

/* ================= shaders ================= */
const COMMON = `
precision highp float;
uniform sampler2D uH;
uniform vec2  uTexel;
uniform float uExag, uRelief;
float Hh(vec2 uv){ return texture2D(uH, uv).r; }
vec3 s2l(vec3 c){ return pow(c, vec3(2.2)); }
`;

const TERRAIN_VS = COMMON + `
varying vec2 vUv;
varying vec3 vPos;
varying float vDist;
void main(){
  vUv = uv;
  float h = Hh(uv);
  vec3 p = position;
  p.y = h*uRelief*uExag;
  vPos = p;
  vec4 mv = modelViewMatrix*vec4(p,1.0);
  vDist = -mv.z;
  gl_Position = projectionMatrix*mv;
}`;

const TERRAIN_FS = COMMON + `
uniform sampler2D uDrape, uRamp;
uniform vec3  uSun, uSunCol, uAmbCol, uFogCol, uBorderCol;
uniform float uMix, uShade, uShadow, uContour, uContourInt, uBorder, uFog, uHmin, uHmax;
uniform float uOutside;
varying vec2 vUv;
varying vec3 vPos;
varying float vDist;

float border(vec2 uv){ return texture2D(uH, uv).g; }

float castShadow(vec3 p, vec2 uv){
  if(uShadow < 0.01 || uSun.y <= 0.02) return 1.0;
  float s = 1.0;
  float t = 1.2;
  for(int i=0;i<26;i++){
    t *= 1.22;
    vec3 q = p + uSun*t;
    vec2 quv = uv + vec2(uSun.x*t/%W%, -uSun.z*t/%H%);
    if(quv.x<0.0||quv.x>1.0||quv.y<0.0||quv.y>1.0) break;
    float th = Hh(quv)*uRelief*uExag;
    float d = th - q.y;
    if(d > 0.0) s = min(s, 1.0 - clamp(d/(t*0.10+0.4),0.0,1.0));
    if(s < 0.02) break;
  }
  return mix(1.0, s, uShadow);
}

void main(){
  float lod = clamp(vDist/40.0, 1.0, 5.0);
  vec2 ts = uTexel*lod;
  float hC = Hh(vUv);
  float hL = Hh(vUv-vec2(ts.x,0.0)), hR = Hh(vUv+vec2(ts.x,0.0));
  float hD = Hh(vUv-vec2(0.0,ts.y)), hU = Hh(vUv+vec2(0.0,ts.y));
  float k = uRelief*uExag;
  float sx = (hR-hL)*k/(2.0*%CX%*lod);
  float sz = (hD-hU)*k/(2.0*%CZ%*lod);
  vec3 N = normalize(vec3(-sx, 1.0, -sz));

  float elev = uHmin + hC*(uHmax-uHmin);
  float ft = elev/0.3048;
  vec3 hyp = texture2D(uRamp, vec2(clamp((ft-1400.0)/8800.0,0.003,0.997), 0.5)).rgb;
  vec3 drp = texture2D(uDrape, vUv).rgb;

  float d = border(vUv);
  float ins = smoothstep(-0.6, 1.4, d);
  vec3 col = mix(hyp, drp, uMix*ins);
  float gray = dot(col, vec3(0.299,0.587,0.114));
  col = mix(mix(vec3(gray), col, 0.5)*uOutside, col, ins);

  float shd = castShadow(vPos, vUv);
  float ndl = max(dot(N, uSun), 0.0);
  float skyf = 0.5 + 0.5*N.y;
  vec3 term = uAmbCol*skyf + uSunCol*ndl*shd;
  vec3 ref  = uAmbCol + uSunCol*max(uSun.y,0.05);
  col *= mix(vec3(1.0), term/max(ref,vec3(0.001)), uShade);

  if(uContour > 0.01){
    float e = elev/uContourInt;
    float fw = fwidth(e);
    float g = abs(fract(e-0.5)-0.5)/max(fw,1e-5);
    float ln = (1.0-smoothstep(0.0,1.1,g))*smoothstep(1.6,0.5,fw);
    col = mix(col, col*vec3(0.55,0.52,0.48), ln*uContour);
  }
  if(uBorder > 0.01){
    float fw = fwidth(d);
    float ln = 1.0-smoothstep(0.0, 1.1*fw+0.02, abs(d)-0.15);
    col = mix(col, uBorderCol, ln*uBorder*0.8);
  }

  float f = 1.0-exp(-pow(vDist*uFog, 2.2));
  col = mix(col, uFogCol, clamp(f,0.0,0.9));
  gl_FragColor = vec4(col, 1.0);
}`;

const SKIRT_VS = COMMON + `
attribute float aTop;
uniform float uBase;
varying float vY;
varying vec3 vN;
varying float vDist;
void main(){
  vec3 p = position;
  p.y = aTop > 0.5 ? Hh(uv)*uRelief*uExag : uBase;
  vY = p.y; vN = normal;
  vec4 mv = modelViewMatrix*vec4(p,1.0);
  vDist = -mv.z;
  gl_Position = projectionMatrix*mv;
}`;

const SKIRT_FS = `
precision highp float;
vec3 s2l(vec3 c){ return pow(c, vec3(2.2)); }
uniform vec3 uSun, uFogCol;
uniform float uBase, uFog;
varying float vY;
varying vec3 vN;
varying float vDist;
void main(){
  float t = clamp((vY-uBase)/max(-uBase,0.001), 0.0, 1.0);
  vec3 top = s2l(vec3(0.325,0.283,0.231));
  vec3 bot = s2l(vec3(0.075,0.068,0.058));
  vec3 col = mix(bot, top, pow(t,0.55));
  float band = 0.5+0.5*sin(vY*3.7);
  col *= 1.0 + 0.045*band;
  float ndl = max(dot(normalize(vN), uSun),0.0);
  col *= 0.42 + 0.58*ndl;
  col *= 1.0 - 0.30*smoothstep(0.75,1.0,t)*(1.0-ndl);
  float f = 1.0-exp(-pow(vDist*uFog, 2.2));
  col = mix(col, uFogCol*0.6, clamp(f,0.0,0.85));
  gl_FragColor = vec4(col,1.0);
}`;

const SKY_VS = `varying vec3 vD; void main(){ vD = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`;
const SKY_FS = `
precision highp float;
uniform vec3 uSun, uZen, uHor, uGlow;
varying vec3 vD;
void main(){
  vec3 d = normalize(vD);
  float h = clamp(d.y*1.25+0.06, -1.0, 1.0);
  vec3 col = mix(uHor, uZen, pow(clamp(h,0.0,1.0),0.62));
  col = mix(col, uHor*0.55, clamp(-h*2.4,0.0,1.0));
  float g = max(dot(d, uSun), 0.0);
  col += uGlow*pow(g, 22.0)*0.30 + uGlow*pow(g,300.0)*1.4;
  gl_FragColor = vec4(col,1.0);
}`;

const GROUND_FS = `
precision highp float;
uniform vec3 uFogCol, uTable;
uniform float uFog;
varying float vDist;
varying vec2 vP;
void main(){
  float r = length(vP);
  vec3 col = mix(uTable, uFogCol*0.75, smoothstep(0.25,1.0,r));
  float f = 1.0-exp(-pow(vDist*uFog,2.2));
  col = mix(col, uFogCol*0.75, clamp(f,0.0,0.9));
  gl_FragColor = vec4(col,1.0);
}`;
const GROUND_VS = `
varying float vDist; varying vec2 vP;
uniform float uSpan;
void main(){
  vec4 wp = modelMatrix*vec4(position,1.0);
  vP = wp.xz/uSpan;
  vec4 mv = modelViewMatrix*vec4(position,1.0);
  vDist = -mv.z;
  gl_Position = projectionMatrix*mv;
}`;

/* ================= build ================= */
function makeRampTexture(){
  const c = document.createElement('canvas'); c.width=256; c.height=1;
  const g = c.getContext('2d');
  const stops = M.ramp, ft = M.rampFt;
  const lo=1400, hi=10200;
  const grd = g.createLinearGradient(0,0,256,0);
  for(let i=0;i<stops.length;i++){
    const p = clamp((ft[i]+250-lo)/(hi-lo),0,1);
    grd.addColorStop(p, `rgb(${stops[i][0]},${stops[i][1]},${stops[i][2]})`);
  }
  grd.addColorStop(0, `rgb(${stops[0][0]},${stops[0][1]},${stops[0][2]})`);
  grd.addColorStop(1, `rgb(${stops[stops.length-1][0]},${stops[stops.length-1][1]},${stops[stops.length-1][2]})`);
  g.fillStyle = grd; g.fillRect(0,0,256,1);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.minFilter = t.magFilter = THREE.LinearFilter;
  t.generateMipmaps = false;
  return t;
}

function decodeHeight(img){
  const c = document.createElement('canvas'); c.width=HMW; c.height=HMH;
  const g = c.getContext('2d', {willReadFrequently:false});
  g.drawImage(img,0,0);
  const px = g.getImageData(0,0,HMW,HMH).data;
  const n = HMW*HMH;
  hData = new Float32Array(n);
  bData = new Float32Array(n);
  const data = new Uint16Array(n*2);               // GPU copy is v-flipped:
  const span = HMAX-HMIN;                          // DataTexture ignores flipY
  for(let y=0;y<HMH;y++){
    const row = y*HMW, frow = (HMH-1-y)*HMW;
    for(let x=0;x<HMW;x++){
      const i=row+x, o=i*4;
      const hv = ((px[o]<<4) | (px[o+1]>>4))/4095; // 12-bit
      hData[i] = HMIN + hv*span;
      const bd = (px[o+2]-128)/8;                  // texels, + inside
      bData[i] = bd;
      const j=(frow+x)*2;
      data[j]   = toHalf(hv);
      data[j+1] = toHalf(bd);
    }
  }
  const t = new THREE.DataTexture(data, HMW, HMH, THREE.RGFormat, THREE.HalfFloatType);
  t.magFilter = t.minFilter = THREE.LinearFilter;
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.generateMipmaps = false;
  t.needsUpdate = true;
  return t;
}

function buildSkirt(){
  const N = 300;
  const pos=[], uvs=[], nor=[], top=[], idx=[];
  let base=0;
  const edges = [
    {a:[-W/2,-H/2], b:[ W/2,-H/2], n:[0,0,-1]},   // north
    {a:[ W/2,-H/2], b:[ W/2, H/2], n:[1,0,0]},    // east
    {a:[ W/2, H/2], b:[-W/2, H/2], n:[0,0,1]},    // south
    {a:[-W/2, H/2], b:[-W/2,-H/2], n:[-1,0,0]}    // west
  ];
  for(const e of edges){
    for(let i=0;i<=N;i++){
      const t=i/N;
      const x = lerp(e.a[0],e.b[0],t), z = lerp(e.a[1],e.b[1],t);
      const u = ux(x), v = 1-vz(z);
      pos.push(x,0,z, x,0,z);
      uvs.push(u,v, u,v);
      nor.push(e.n[0],e.n[1],e.n[2], e.n[0],e.n[1],e.n[2]);
      top.push(1,0);
    }
    for(let i=0;i<N;i++){
      const a=base+i*2, b=a+1, c=a+2, d=a+3;
      idx.push(a,b,c, b,d,c);
    }
    base += (N+1)*2;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs,2));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor,3));
  g.setAttribute('aTop', new THREE.Float32BufferAttribute(top,1));
  g.setIndex(idx);
  return g;
}

function buildScene(){
  const canvas = $('#gl');
  renderer = new THREE.WebGLRenderer({canvas, antialias:true, powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio||1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x0d0c0a, 1);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(42, innerWidth/innerHeight, 0.6, 14000);

  drapeTex = new THREE.Texture(drapeImg);
  drapeTex.colorSpace = THREE.SRGBColorSpace;
  drapeTex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  drapeTex.minFilter = THREE.LinearMipmapLinearFilter;
  drapeTex.magFilter = THREE.LinearFilter;
  drapeTex.wrapS = drapeTex.wrapT = THREE.ClampToEdgeWrapping;
  drapeTex.needsUpdate = true;
  rampTex = makeRampTexture();

  const fogCol = new THREE.Color(0x2a2620);
  U.uH        = {value:hTex};
  U.uDrape    = {value:drapeTex};
  U.uRamp     = {value:rampTex};
  U.uTexel    = {value:new THREE.Vector2(1/HMW, 1/HMH)};
  U.uExag     = {value:0.02};
  U.uRelief   = {value:RELIEF};
  U.uSun      = {value:new THREE.Vector3()};
  U.uSunCol   = {value:new THREE.Vector3(1.02,0.955,0.86)};
  U.uAmbCol   = {value:new THREE.Vector3(0.40,0.44,0.52)};
  U.uFogCol   = {value:new THREE.Color(0x2a2620)};
  U.uBorderCol= {value:new THREE.Color(0x1a1713)};
  U.uMix      = {value:1};
  U.uShade    = {value:0.55};
  U.uShadow   = {value:1};
  U.uContour  = {value:0};
  U.uContourInt={value:250};
  U.uBorder   = {value:0.9};
  U.uFog      = {value:0.00040};
  U.uHmin     = {value:HMIN};
  U.uHmax     = {value:HMAX};
  U.uOutside  = {value:0.66};
  U.uBase     = {value:-14};
  U.uSpan     = {value:2600};
  U.uTable    = {value:new THREE.Color(0x171410)};

  const seg = (innerWidth*innerHeight > 1.6e6 && !/Mobi|Android/i.test(navigator.userAgent)) ? [1152,700] : [768,468];
  const geo = new THREE.PlaneGeometry(W, H, seg[0], seg[1]);
  geo.rotateX(-Math.PI/2);
  const src = (s) => s.replace(/%W%/g, W.toFixed(4)).replace(/%H%/g, H.toFixed(4))
                      .replace(/%CX%/g, CELLX.toFixed(7)).replace(/%CZ%/g, CELLZ.toFixed(7));
  const mat = new THREE.ShaderMaterial({
    uniforms:U, vertexShader:src(TERRAIN_VS), fragmentShader:src(TERRAIN_FS), fog:false
  });
  terrain = new THREE.Mesh(geo, mat);
  terrain.frustumCulled = false;
  scene.add(terrain);

  skirt = new THREE.Mesh(buildSkirt(), new THREE.ShaderMaterial({
    uniforms:U, vertexShader:src(SKIRT_VS), fragmentShader:SKIRT_FS, fog:false, side:THREE.DoubleSide
  }));
  skirt.frustumCulled = false;
  scene.add(skirt);

  const cap = new THREE.Mesh(new THREE.PlaneGeometry(W,H), new THREE.MeshBasicMaterial({color:0x0b0a09}));
  cap.rotation.x = Math.PI/2; cap.position.y = U.uBase.value+0.01;
  scene.add(cap);
  U.__cap = cap;

  sky = new THREE.Mesh(new THREE.SphereGeometry(6000, 40, 22), new THREE.ShaderMaterial({
    uniforms:{uSun:U.uSun, uZen:{value:new THREE.Color(0x0a0c11)}, uHor:{value:new THREE.Color(0x373027)},
              uGlow:{value:new THREE.Color(0xb08544)}},
    vertexShader:SKY_VS, fragmentShader:SKY_FS, side:THREE.BackSide, depthWrite:false, fog:false
  }));
  sky.frustumCulled = false;
  scene.add(sky);

  ground = new THREE.Mesh(new THREE.PlaneGeometry(5200,5200,1,1), new THREE.ShaderMaterial({
    uniforms:{uFogCol:U.uFogCol, uFog:U.uFog, uTable:U.uTable, uSpan:U.uSpan},
    vertexShader:GROUND_VS, fragmentShader:GROUND_FS, fog:false
  }));
  ground.rotation.x = -Math.PI/2;
  ground.position.y = U.uBase.value - 0.4;
  scene.add(ground);

  addEventListener('resize', onResize, {passive:true});
  onResize();
}
function onResize(){
  if(!renderer) return;
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight, false);
}

/* ---------- expose to part 2 ---------- */
window.MTX = {
  M, $, clamp, lerp, smoothstep, DEG, W, H, HMW, HMH, HMIN, HMAX, RELIEF,
  uvToLonLat, lonLatToUV, wx, wz, ux, vz,
  sampleH: (x,z)=>sampleH(x,z), insideMT:(x,z)=>insideMT(x,z),
  terrainY:(x,z)=>terrainY(x,z),
  getExag:()=>EXAG, setExag:v=>{
    EXAG=v; U.uExag.value=v;
    const b = -(0.5*RELIEF*Math.max(v,0.2) + 4);
    U.uBase.value = b;
    if(U.__cap) U.__cap.position.y = b+0.01;
    if(ground) ground.position.y = b-0.4;
  },
  U, prog,
  get renderer(){return renderer}, get scene(){return scene}, get camera(){return camera},
  get drapeImg(){return drapeImg},
  boot: async function(){
    prog(0.04,'reading the sheet…');
    try{ if(document.fonts && document.fonts.ready) await Promise.race([document.fonts.ready, new Promise(r=>setTimeout(r,2500))]); }catch(e){}
    prog(0.12,'fetching elevations…');
    const hi = await loadImage(window.MT_HEIGHT);
    prog(0.42,'decoding 4.5 million samples…');
    await new Promise(r=>setTimeout(r,16));
    hTex = decodeHeight(hi);
    prog(0.68,'unrolling the 1991 sheet…');
    drapeImg = await loadImage(window.MT_DRAPE);
    prog(0.88,'building the model…');
    await new Promise(r=>setTimeout(r,16));
    buildScene();
    prog(1,'');
  }
};
})();

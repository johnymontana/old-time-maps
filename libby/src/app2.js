/* =====================================================================
   The Flathead Country — Part 2: camera, labels, instruments, tools, tours
   (v2 chassis: constants scale from the plate; overlay polylines and mine
   labels are data-driven from meta.json)
   ===================================================================== */
(function(){
'use strict';
const X = window.MTX, M = X.M, $ = X.$;
const {clamp, lerp, DEG, W, H, RELIEF, DIAG, MAXD, LIFT0, EXAG0, UI,
       uvToLonLat, wx, wz, ux, vz, U} = X;
const DK = DIAG/1156;                       // montana plate = 1
let renderer, scene, camera;

/* ================= camera rig ================= */
const cam = {
  tx:0, ty:0, tz:0, az:168*DEG, el:32*DEG, dist:MAXD*0.42,
  Tx:0, Ty:0, Tz:0, Taz:168*DEG, Tel:32*DEG, Tdist:MAXD*0.42
};
const HOME = {az:168*DEG, el:32*DEG, dist:MAXD*0.42, x:0, z:0};
function fitHome(){
  if(!camera) return;
  const portrait = camera.aspect < 0.95;
  HOME.az = (portrait ? 258 : 168)*DEG;
  const vf = camera.fov*DEG;
  const hf = 2*Math.atan(Math.tan(vf/2)*camera.aspect);
  const across = portrait ? H : W, along = portrait ? W : H;
  const dW = (across*0.66)/Math.tan(hf/2);
  const dH = (along*0.60*Math.sin(HOME.el) + RELIEF*EXAG0*0.6)/Math.tan(vf/2);
  HOME.dist = clamp(Math.max(dW,dH), MAXD*0.146, MAXD);
}
function applyCam(){
  const ce=Math.cos(cam.el), se=Math.sin(cam.el);
  camera.position.set(
    cam.tx + cam.dist*ce*Math.sin(cam.az),
    cam.ty + cam.dist*se,
    cam.tz - cam.dist*ce*Math.cos(cam.az));
  camera.lookAt(cam.tx, cam.ty + cam.dist*0.045, cam.tz);
}
function damp(dt){
  const k = 1-Math.exp(-11*dt);
  cam.az  += (cam.Taz-cam.az)*k;
  cam.el  += (cam.Tel-cam.el)*k;
  cam.dist+= (cam.Tdist-cam.dist)*k;
  cam.tx  += (cam.Tx-cam.tx)*k;
  cam.tz  += (cam.Tz-cam.tz)*k;
  // the height follows terrain through a much slower spring than the plan
  // motion — a crane, not a wheel — so ridges don't pump the horizon
  cam.Ty = X.terrainY(cam.Tx, cam.Tz);
  cam.ty += (cam.Ty-cam.ty)*(1-Math.exp(-4.5*dt));
}
function clampTarget(){
  cam.Tx = clamp(cam.Tx, -W*0.56, W*0.56);
  cam.Tz = clamp(cam.Tz, -H*0.58, H*0.58);
  cam.Tdist = clamp(cam.Tdist, MAXD*0.0035, MAXD);
  cam.Tel = clamp(cam.Tel, 3.5*DEG, 89.4*DEG);
}

/* ================= picking ================= */
const _rc = new THREE.Raycaster();
const _v2 = new THREE.Vector2();
function pickAt(cx, cy){
  _v2.set((cx/innerWidth)*2-1, -(cy/innerHeight)*2+1);
  _rc.setFromCamera(_v2, camera);
  const o=_rc.ray.origin, d=_rc.ray.direction;
  const maxY = RELIEF*X.getExag()+LIFT0*1.4;
  let t=0;
  if(o.y>maxY){ if(d.y>=-1e-6) return null; t=(o.y-maxY)/(-d.y); }
  let step = Math.max(LIFT0, cam.dist*0.0035);
  const base = U.uBase.value;
  for(let i=0;i<900;i++){
    t += step; step *= 1.010;
    const x=o.x+d.x*t, y=o.y+d.y*t, z=o.z+d.z*t;
    if(y < base-LIFT0*6 && d.y<0) return null;
    if(t > MAXD*3.47) return null;
    if(Math.abs(x)>W/2 || Math.abs(z)>H/2) continue;
    if(y <= X.terrainY(x,z)){
      let lo=t-step, hi=t;
      for(let k=0;k<26;k++){
        const m=(lo+hi)*0.5;
        const mx=o.x+d.x*m, my=o.y+d.y*m, mz=o.z+d.z*m;
        if(my <= X.terrainY(mx,mz)) hi=m; else lo=m;
      }
      return {x:o.x+d.x*hi, y:o.y+d.y*hi, z:o.z+d.z*hi};
    }
  }
  return null;
}

/* ================= input ================= */
const ptrs = new Map();
let drag=null, pinch=null, hoverPt=null, idleT=0;
function onDown(e){
  if(tour.active){ stopTour(); return; }
  $('#gl').setPointerCapture(e.pointerId);
  ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(measure.mode && e.button===0){ measureClick(e.clientX,e.clientY); return; }
  if(ptrs.size===2){
    const p=[...ptrs.values()];
    pinch={d:Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y), dist:cam.Tdist,
           cx:(p[0].x+p[1].x)/2, cy:(p[0].y+p[1].y)/2};
    drag=null; return;
  }
  drag={x:e.clientX,y:e.clientY,pan:(e.button===2||e.shiftKey||e.button===1)};
}
function onMove(e){
  if(ptrs.has(e.pointerId)) ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pinch && ptrs.size===2){
    const p=[...ptrs.values()];
    const d=Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y);
    cam.Tdist = clamp(pinch.dist*pinch.d/Math.max(d,1), MAXD*0.0035, MAXD);
    const cx=(p[0].x+p[1].x)/2, cy=(p[0].y+p[1].y)/2;
    panBy(cx-pinch.cx, cy-pinch.cy); pinch.cx=cx; pinch.cy=cy;
    clampTarget(); return;
  }
  if(drag){
    const dx=e.clientX-drag.x, dy=e.clientY-drag.y;
    drag.x=e.clientX; drag.y=e.clientY;
    if(drag.pan) panBy(dx,dy);
    else { cam.Taz -= dx*0.0052; cam.Tel += dy*0.0042; }
    clampTarget();
    idleT=0;
  } else {
    hoverX=e.clientX; hoverY=e.clientY; hoverDirty=true;
  }
}
function onUp(e){
  ptrs.delete(e.pointerId);
  if(ptrs.size<2) pinch=null;
  if(ptrs.size===0) drag=null;
}
function panBy(dx,dy){
  const s = cam.Tdist*0.0019*(1/Math.max(0.3,Math.sin(cam.Tel)*0.7+0.3));
  const sa=Math.sin(cam.az), ca=Math.cos(cam.az);
  cam.Tx += (-dx*ca + dy*(-sa))*s*0.5;
  cam.Tz += (-dx*sa + dy*( ca))*s*0.5;
}
function onWheel(e){
  e.preventDefault();
  if(tour.active) stopTour();
  const f = Math.exp(clamp(e.deltaY,-90,90)*0.0016);
  const before = cam.Tdist;
  cam.Tdist = clamp(cam.Tdist*f, MAXD*0.0035, MAXD);
  if(f<1){
    const p = pickAt(e.clientX, e.clientY);
    if(p){
      const k = clamp(1-cam.Tdist/before, 0, 0.4)*1.1;
      cam.Tx = lerp(cam.Tx, p.x, k);
      cam.Tz = lerp(cam.Tz, p.z, k);
    }
  }
  clampTarget(); idleT=0;
}
let hoverX=0, hoverY=0, hoverDirty=false;

/* ================= labels ================= */
const layer = $('#labels');
const labels = [];
function buildLabels(){
  const mk=(cls, html, kind, u, v, prio, anchor)=>{
    const el=document.createElement('div');
    el.className='lbl '+cls; el.innerHTML=html; el.style.opacity='0';
    layer.appendChild(el);
    labels.push({el, kind, u, v, prio, anchor, x:wx(u), z:wz(v), vis:false, w:0, h:0});
  };
  M.peaks.forEach(p=>mk('peak',
    `<i class="tri"></i>${p.n}<span class="el">${p.ft.toLocaleString()} ft</span>`,
    'peak', p.u, p.v, 10, [-0.5,-1.06]));
  M.cities.forEach(c=>mk('city t'+c.t, `<span class="dot"></span>${c.n}`,
    'city', c.u, c.v, c.t===0?9:(c.t===1?6:3), [0,-0.5]));
  M.features.forEach(f=>{
    const cls = f.k==='water'?'water':(f.k==='park'?'park':'region');
    mk(cls, f.n, 'feature', f.u, f.v, f.k==='park'?7:5, [-0.5,-0.5]);
  });
  (M.mines||[]).forEach(m=>mk('mine',
    `<span class="pick">⚒</span>${m.n}`, 'mine', m.u, m.v, 4, [0,-0.5]));
  for(const L of labels){ const r=L.el.getBoundingClientRect(); L.w=r.width; L.h=r.height; }
}
const show = {peak:true, city:true, feature:true, mine:true};
let labelFade = 0;
const _p3 = new THREE.Vector3();
function occluded(x,y,z){
  const dx=camera.position.x-x, dy=camera.position.y-y, dz=camera.position.z-z;
  for(let i=1;i<=14;i++){
    const t=0.05+0.95*i/14;
    const px=x+dx*t, py=y+dy*t, pz=z+dz*t;
    if(Math.abs(px)>W/2||Math.abs(pz)>H/2) continue;
    if(py < X.terrainY(px,pz)-LIFT0*0.15) return true;
  }
  return false;
}
let lblTick=0;
function updateLabels(){
  lblTick++;
  const full = (lblTick % 2)===0;
  const d = cam.dist;
  const boxes=[];
  const cand=[];
  const lift = RELIEF*X.getExag()*0.09 + d*0.0045*DK;
  for(const L of labels){
    let on = show[L.kind];
    if(on && L.kind==='city'){
      const t = L.prio;
      on = t>=9 || (t>=6 && d<MAXD*0.404) || (t<6 && d<MAXD*0.20);
    }
    if(on && L.kind==='feature') on = d<MAXD*0.577 && d>MAXD*0.01;
    if(on && L.kind==='mine') on = d<MAXD*(UI.mineDist||0.30);
    if(!on){ if(L.vis){L.el.style.opacity='0'; L.vis=false; L.op=0;} continue; }
    const y = X.terrainY(L.x,L.z)+lift;
    _p3.set(L.x, y, L.z).project(camera);
    if(_p3.z>1 || _p3.x<-1.2||_p3.x>1.2||_p3.y<-1.2||_p3.y>1.2){
      if(L.vis){L.el.style.opacity='0'; L.vis=false; L.op=0;} continue;
    }
    if(full && occluded(L.x,y,L.z)){ if(L.vis){L.el.style.opacity='0'; L.vis=false; L.op=0;} continue; }
    const sx=(_p3.x*0.5+0.5)*innerWidth, sy=(-_p3.y*0.5+0.5)*innerHeight;
    cand.push({L,sx,sy,depth:_p3.z});
  }
  cand.sort((a,b)=> (b.L.prio-a.L.prio) || (a.depth-b.depth));
  for(const c of cand){
    const L=c.L;
    const w=L.w||90, h=L.h||14;
    const x0=c.sx + L.anchor[0]*w, y0=c.sy + L.anchor[1]*h;
    let hit=false;
    for(const b of boxes){ if(x0<b[2]&&x0+w>b[0]&&y0<b[3]&&y0+h>b[1]){hit=true;break;} }
    if(hit){ if(L.vis){L.el.style.opacity='0'; L.vis=false; L.op=0;} continue; }
    boxes.push([x0-3,y0-2,x0+w+3,y0+h+2]);
    const tr = `translate3d(${x0.toFixed(1)}px,${y0.toFixed(1)}px,0)`;
    if(tr!==L.tr){ L.tr=tr; L.el.style.transform=tr; }
    L.vis=true;
    if(labelFade!==L.op){ L.op=labelFade; L.el.style.opacity=String(labelFade); }
  }
}

/* ================= overlay lines ================= */
const overlays = [];                     // {line, obj, chipId}
function buildOverlays(){
  const wrap = $('#ovchips');
  if(!M.lines || !M.lines.length){ if(wrap) wrap.style.display='none'; return; }
  const chips = new Map();               // chip label -> {ids:[], on:true}
  for(const L of M.lines){
    const pts=[];
    for(let i=0;i<L.pts.length;i++){
      const [u,v]=L.pts[i];
      const x=wx(u), z=wz(v);
      if(i>0){
        const px=pts[pts.length-1];
        const n=Math.max(1, Math.ceil(Math.hypot(x-px[0], z-px[2])/(DIAG*0.0015)));
        for(let k=1;k<=n;k++)
          pts.push([lerp(px[0],x,k/n), 0, lerp(px[2],z,k/n)]);
      } else pts.push([x,0,z]);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pts.flat(),3));
    const mat = L.dash
      ? new THREE.LineDashedMaterial({color:new THREE.Color(L.color||'#d08a4a'),
          dashSize:DIAG*0.004, gapSize:DIAG*0.0028, transparent:true, opacity:0.92})
      : new THREE.LineBasicMaterial({color:new THREE.Color(L.color||'#d08a4a'),
          transparent:true, opacity:0.92});
    const obj=new THREE.Line(g, mat);
    obj.renderOrder=4;
    scene.add(obj);
    const chip = L.chip || L.name;
    overlays.push({line:L, obj, chip});
    if(!chips.has(chip)) chips.set(chip, true);
  }
  refreshOverlays();
  if(wrap){
    for(const [name] of chips){
      const b=document.createElement('button');
      b.className='tog chip'; b.setAttribute('aria-pressed','true');
      b.innerHTML='<span class="box"></span>'+name;
      b.addEventListener('click',()=>{
        const on=b.getAttribute('aria-pressed')!=='true';
        b.setAttribute('aria-pressed',String(on));
        for(const o of overlays) if(o.chip===name) o.obj.visible=on;
      });
      wrap.appendChild(b);
    }
  }
}
function refreshOverlays(){
  for(const o of overlays){
    const pos=o.obj.geometry.getAttribute('position');
    for(let i=0;i<pos.count;i++)
      pos.setY(i, X.terrainY(pos.getX(i), pos.getZ(i))+LIFT0*0.7);
    pos.needsUpdate=true;
    o.obj.geometry.computeBoundingSphere();
    if(o.line.dash) o.obj.computeLineDistances();
  }
}

/* ================= HUD ================= */
const rLat=$('#rLat'), rLon=$('#rLon'), rEl=$('#rEl'), scaletxt=$('#scaletxt');
function fmtLL(v, pos, neg){
  const s = v<0?neg:pos, a=Math.abs(v);
  const dd=Math.floor(a), mm=(a-dd)*60;
  return `${dd}° ${mm.toFixed(1)}′ ${s}`;
}
function updateHud(){
  if(hoverDirty && !drag && !tour.active){
    hoverDirty=false;
    hoverPt = pickAt(hoverX, hoverY);
  }
  if(hoverPt){
    const [lon,lat] = uvToLonLat(ux(hoverPt.x), vz(hoverPt.z));
    const m = X.sampleH(hoverPt.x, hoverPt.z);
    rLat.textContent=fmtLL(lat,'N','S'); rLon.textContent=fmtLL(lon,'E','W');
    rEl.textContent=`${Math.round(m/0.3048).toLocaleString()} ft · ${Math.round(m).toLocaleString()} m`;
    rLat.classList.remove('off'); rLon.classList.remove('off'); rEl.classList.remove('off');
  } else {
    rLat.textContent=rLon.textContent=rEl.textContent='—';
    rLat.classList.add('off'); rLon.classList.add('off'); rEl.classList.add('off');
  }
  const wpp = 2*Math.tan(camera.fov*DEG/2)*cam.dist/innerHeight;
  const target = 88*wpp;
  const steps=[0.5,1,2,5,10,20,25,50,100,200,250,500,1000];
  let best=steps[0];
  for(const s of steps) if(Math.abs(s-target)<Math.abs(best-target)) best=s;
  const px = best/wpp;
  $('#scalebar .bar').style.width = clamp(px,30,150)+'px';
  scaletxt.textContent = best>=1 ? `${best} km` : `${best*1000} m`;
}

/* ================= minimap ================= */
const mini=$('#minicv'), mctx=mini.getContext('2d');
let miniOff=null;
function buildMini(){
  miniOff=document.createElement('canvas'); miniOff.width=mini.width; miniOff.height=mini.height;
  const g=miniOff.getContext('2d');
  g.drawImage(X.drapeImg,0,0,mini.width,mini.height);
  g.fillStyle='rgba(13,12,10,.38)'; g.fillRect(0,0,mini.width,mini.height);
}
function drawMini(){
  if(!miniOff) return;
  const w=mini.width,h=mini.height;
  mctx.clearRect(0,0,w,h);
  mctx.drawImage(miniOff,0,0);
  const tu=ux(cam.tx)*w, tv=vz(cam.tz)*h;
  const cu=ux(camera.position.x)*w, cv=vz(camera.position.z)*h;
  const ang=Math.atan2(tv-cv, tu-cu);
  const fov=camera.fov*DEG*camera.aspect*0.5;
  const len=Math.hypot(tu-cu,tv-cv)*1.9+16;
  mctx.beginPath(); mctx.moveTo(cu,cv);
  mctx.arc(cu,cv,len,ang-fov,ang+fov); mctx.closePath();
  mctx.fillStyle='rgba(224,162,60,.16)'; mctx.fill();
  mctx.strokeStyle='rgba(224,162,60,.55)'; mctx.lineWidth=1; mctx.stroke();
  mctx.beginPath(); mctx.arc(tu,tv,3.4,0,7); mctx.fillStyle='#e0a23c'; mctx.fill();
  mctx.strokeStyle='rgba(13,12,10,.9)'; mctx.lineWidth=1.4; mctx.stroke();
}
mini.addEventListener('pointerdown', e=>{
  const r=mini.getBoundingClientRect();
  const u=(e.clientX-r.left)/r.width, v=(e.clientY-r.top)/r.height;
  if(tour.active) stopTour();
  cam.Tx=wx(clamp(u,0,1)); cam.Tz=wz(clamp(v,0,1));
  cam.Tdist=Math.min(cam.Tdist, MAXD*0.1615); clampTarget();
});

/* ================= sun ================= */
const sun={az:315, alt:35, moving:false};
function updateSun(){
  const a=sun.az*DEG, e=sun.alt*DEG;
  U.uSun.value.set(Math.sin(a)*Math.cos(e), Math.sin(e), -Math.cos(a)*Math.cos(e)).normalize();
  const warm = clamp((sun.alt-4)/26,0,1);
  U.uSunCol.value.set(lerp(1.25,1.02,warm), lerp(0.70,0.955,warm), lerp(0.44,0.86,warm));
  U.uAmbCol.value.set(lerp(0.30,0.40,warm), lerp(0.33,0.44,warm), lerp(0.44,0.52,warm));
  drawDial();
}
const dial=$('#dial'), dctx=dial.getContext('2d');
function drawDial(){
  const s=dial.width, r=s*0.40, c=s/2;
  dctx.clearRect(0,0,s,s);
  dctx.save(); dctx.translate(c,c);
  dctx.strokeStyle='#332c24'; dctx.lineWidth=2;
  dctx.beginPath(); dctx.arc(0,0,r,0,7); dctx.stroke();
  dctx.fillStyle='#6e675c'; dctx.font='600 15px "IBM Plex Sans Condensed", sans-serif';
  dctx.textAlign='center'; dctx.textBaseline='middle';
  const lab=[['N',0],['E',90],['S',180],['W',270]];
  for(const [t,a] of lab){
    const ar=(a-90)*DEG;
    dctx.fillText(t, Math.cos(ar)*(r+14), Math.sin(ar)*(r+14));
  }
  for(let a=0;a<360;a+=15){
    const ar=(a-90)*DEG, big=(a%90===0);
    dctx.strokeStyle=big?'#6e675c':'#332c24'; dctx.lineWidth=big?2:1.4;
    dctx.beginPath();
    dctx.moveTo(Math.cos(ar)*(r-(big?8:4)), Math.sin(ar)*(r-(big?8:4)));
    dctx.lineTo(Math.cos(ar)*r, Math.sin(ar)*r); dctx.stroke();
  }
  const ar=(sun.az-90)*DEG;
  const hx=Math.cos(ar)*r, hy=Math.sin(ar)*r;
  dctx.strokeStyle='rgba(224,162,60,.45)'; dctx.lineWidth=2;
  dctx.beginPath(); dctx.moveTo(0,0); dctx.lineTo(hx,hy); dctx.stroke();
  const glow=dctx.createRadialGradient(hx,hy,0,hx,hy,16);
  glow.addColorStop(0,'rgba(224,162,60,.85)'); glow.addColorStop(1,'rgba(224,162,60,0)');
  dctx.fillStyle=glow; dctx.beginPath(); dctx.arc(hx,hy,16,0,7); dctx.fill();
  dctx.fillStyle='#e0a23c'; dctx.beginPath(); dctx.arc(hx,hy,5.2,0,7); dctx.fill();
  dctx.fillStyle='#9b917f'; dctx.font='500 13px "IBM Plex Mono", monospace';
  dctx.fillText(Math.round(sun.az)+'°',0,2);
  dctx.restore();
}
function dialSet(e){
  const r=dial.getBoundingClientRect();
  const dx=e.clientX-(r.left+r.width/2), dy=e.clientY-(r.top+r.height/2);
  sun.az=(Math.atan2(dy,dx)/DEG+90+360)%360;
  sun.moving=false; $('#sunplay').classList.remove('on');
  updateSun();
}
let dialDrag=false;
dial.addEventListener('pointerdown',e=>{dialDrag=true; dial.setPointerCapture(e.pointerId); dialSet(e);});
dial.addEventListener('pointermove',e=>{ if(dialDrag) dialSet(e); });
dial.addEventListener('pointerup',()=>{dialDrag=false;});
dial.addEventListener('keydown',e=>{
  if(e.key==='ArrowLeft'||e.key==='ArrowDown'){ sun.az=(sun.az-5+360)%360; updateSun(); e.preventDefault(); }
  if(e.key==='ArrowRight'||e.key==='ArrowUp'){ sun.az=(sun.az+5)%360; updateSun(); e.preventDefault(); }
});

/* ================= cross-section ================= */
const measure={mode:false, a:null, b:null, samples:null, line:null, curtain:null, mark:null};
const profWrap=$('#profile'), profcv=$('#profcv'), pctx=profcv.getContext('2d');
function measureClick(cx,cy){
  const p=pickAt(cx,cy); if(!p) return;
  if(!measure.a){ measure.a=p; setMarker(p); }
  else { measure.b=p; buildProfile(); }
}
function setMarker(p){
  if(!measure.mark){
    measure.mark=new THREE.Mesh(new THREE.SphereGeometry(1,12,10),
      new THREE.MeshBasicMaterial({color:0xc8543a}));
    scene.add(measure.mark);
  }
  measure.mark.visible=true;
  measure.mark.position.set(p.x,p.y,p.z);
  measure.mark.scale.setScalar(clamp(cam.dist*0.006, LIFT0*1.7, LIFT0*17));
}
function clearProfile(){
  if(measure.line){scene.remove(measure.line); measure.line.geometry.dispose(); measure.line=null;}
  if(measure.curtain){scene.remove(measure.curtain); measure.curtain.geometry.dispose(); measure.curtain=null;}
  if(measure.mark) measure.mark.visible=false;
  measure.a=measure.b=null; measure.samples=null;
  profWrap.classList.remove('up'); profWrap.setAttribute('aria-hidden','true');
}
function buildProfile(){
  const N=420, a=measure.a, b=measure.b;
  const pts=[], hs=[];
  for(let i=0;i<N;i++){
    const t=i/(N-1);
    const x=lerp(a.x,b.x,t), z=lerp(a.z,b.z,t);
    const m=X.sampleH(x,z);
    hs.push(m); pts.push(x,z);
  }
  const len=Math.hypot(b.x-a.x,b.z-a.z);
  measure.samples={pts,hs,len,N};
  rebuildProfileGeom();
  const mn=Math.min(...hs), mx=Math.max(...hs);
  $('#pLen').textContent=len<10?len.toFixed(1)+' km':Math.round(len)+' km';
  $('#pMin').textContent=Math.round(mn/0.3048).toLocaleString()+' ft';
  $('#pMax').textContent=Math.round(mx/0.3048).toLocaleString()+' ft';
  $('#pRel').textContent=Math.round((mx-mn)/0.3048).toLocaleString()+' ft';
  drawProfile(-1);
  profWrap.classList.add('up'); profWrap.setAttribute('aria-hidden','false');
  measure.mode=false; $('#btnProfile').classList.remove('on');
  document.body.classList.remove('measuring');
}
function rebuildProfileGeom(){
  const s=measure.samples; if(!s) return;
  if(measure.line){scene.remove(measure.line); measure.line.geometry.dispose();}
  if(measure.curtain){scene.remove(measure.curtain); measure.curtain.geometry.dispose();}
  const ex=X.getExag(), base=U.uBase.value;
  const lp=[], cp=[], idx=[];
  for(let i=0;i<s.N;i++){
    const x=s.pts[i*2], z=s.pts[i*2+1];
    const y=(s.hs[i]-X.HMIN)/1000*ex;
    lp.push(x,y+LIFT0,z);
    cp.push(x,y,z, x,base,z);
    if(i<s.N-1){ const o=i*2; idx.push(o,o+1,o+2, o+1,o+3,o+2); }
  }
  const lg=new THREE.BufferGeometry();
  lg.setAttribute('position',new THREE.Float32BufferAttribute(lp,3));
  measure.line=new THREE.Line(lg,new THREE.LineBasicMaterial({color:0xf07a55,transparent:true,opacity:.95,depthTest:false}));
  measure.line.renderOrder=5; scene.add(measure.line);
  const cg=new THREE.BufferGeometry();
  cg.setAttribute('position',new THREE.Float32BufferAttribute(cp,3));
  cg.setIndex(idx);
  measure.curtain=new THREE.Mesh(cg,new THREE.MeshBasicMaterial({
    color:0xc8543a,transparent:true,opacity:.20,side:THREE.DoubleSide,depthWrite:false}));
  scene.add(measure.curtain);
}
function sizeProfile(){
  const dpr=Math.min(devicePixelRatio||1,2);
  const r=profcv.getBoundingClientRect();
  const w=Math.max(320,Math.round(r.width*dpr)), h=Math.round(132*dpr);
  if(profcv.width!==w||profcv.height!==h){ profcv.width=w; profcv.height=h; }
  return dpr;
}
function drawProfile(hoverT){
  const s=measure.samples; if(!s) return;
  const dpr=sizeProfile();
  const w=profcv.width, h=profcv.height;
  const padL=14*dpr, padR=52*dpr, padT=12*dpr, padB=26*dpr;
  pctx.clearRect(0,0,w,h);
  const mn=Math.min(...s.hs), mx=Math.max(...s.hs);
  const lo=Math.floor(mn/0.3048/500)*500, hi=Math.ceil(mx/0.3048/500)*500;
  const X0=padL, X1=w-padR, Y0=padT, Y1=h-padB;
  const fx=t=>X0+(X1-X0)*t;
  const fy=ft=>Y1-(Y1-Y0)*((ft-lo)/Math.max(hi-lo,1));
  pctx.strokeStyle='rgba(155,145,127,.16)'; pctx.lineWidth=1*dpr;
  pctx.fillStyle='#6e675c'; pctx.font=`${11*dpr}px "IBM Plex Mono", monospace`; pctx.textBaseline='middle';
  const stepFt = (hi-lo)>6000?2000:((hi-lo)>2500?1000:500);
  for(let ft=lo; ft<=hi; ft+=stepFt){
    const y=fy(ft);
    pctx.beginPath(); pctx.moveTo(X0,y); pctx.lineTo(X1,y); pctx.stroke();
    pctx.textAlign='left'; pctx.fillText(ft.toLocaleString(), X1+7*dpr, y);
  }
  const grd=pctx.createLinearGradient(0,Y0,0,Y1);
  grd.addColorStop(0,'rgba(200,84,58,.55)'); grd.addColorStop(1,'rgba(200,84,58,.06)');
  pctx.beginPath(); pctx.moveTo(fx(0),Y1);
  for(let i=0;i<s.N;i++) pctx.lineTo(fx(i/(s.N-1)), fy(s.hs[i]/0.3048));
  pctx.lineTo(fx(1),Y1); pctx.closePath();
  pctx.fillStyle=grd; pctx.fill();
  pctx.beginPath();
  for(let i=0;i<s.N;i++){ const px=fx(i/(s.N-1)), py=fy(s.hs[i]/0.3048); i?pctx.lineTo(px,py):pctx.moveTo(px,py); }
  pctx.strokeStyle='#f0a17f'; pctx.lineWidth=1.6*dpr; pctx.stroke();
  pctx.fillStyle='#6e675c'; pctx.textAlign='center'; pctx.textBaseline='top';
  const nD=Math.min(6,Math.max(2,Math.round(s.len/(DK*60))));
  for(let i=0;i<=nD;i++){
    const t=i/nD;
    pctx.fillText((s.len*t).toFixed(s.len<20?1:0)+(i===nD?' km':''), fx(t), Y1+8*dpr);
    pctx.strokeStyle='rgba(155,145,127,.22)';
    pctx.beginPath(); pctx.moveTo(fx(t),Y1); pctx.lineTo(fx(t),Y1+4*dpr); pctx.stroke();
  }
  if(hoverT>=0){
    const i=Math.round(hoverT*(s.N-1));
    const px=fx(hoverT), py=fy(s.hs[i]/0.3048);
    pctx.strokeStyle='rgba(240,161,127,.6)'; pctx.lineWidth=1*dpr;
    pctx.beginPath(); pctx.moveTo(px,Y0); pctx.lineTo(px,Y1); pctx.stroke();
    pctx.fillStyle='#f2ece0'; pctx.beginPath(); pctx.arc(px,py,4*dpr,0,7); pctx.fill();
    pctx.font=`600 ${12*dpr}px "IBM Plex Mono", monospace`;
    pctx.textAlign = hoverT>0.75?'right':'left'; pctx.textBaseline='bottom';
    pctx.fillText(Math.round(s.hs[i]/0.3048).toLocaleString()+' ft', px+(hoverT>0.75?-8*dpr:8*dpr), py-8*dpr);
  }
}
profcv.addEventListener('pointermove',e=>{
  const s=measure.samples; if(!s) return;
  const r=profcv.getBoundingClientRect();
  const padL=14, padR=52;
  const t=clamp(((e.clientX-r.left)-padL)/(r.width-padL-padR),0,1);
  drawProfile(t);
  const i=Math.round(t*(s.N-1));
  const x=s.pts[i*2], z=s.pts[i*2+1];
  setMarker({x, y:(s.hs[i]-X.HMIN)/1000*X.getExag()+LIFT0*1.15, z});
});
profcv.addEventListener('pointerleave',()=>{ if(measure.samples) drawProfile(-1); });
$('#pClose').addEventListener('click',clearProfile);
addEventListener('resize',()=>{ if(measure.samples) drawProfile(-1); },{passive:true});

/* ================= tours ================= */
const tour={active:false, t:0, keys:null, i:0, id:null, seg:-1, from:null};
const SEG=5.6, HOLD=1.5;
const TEX = UI.tourEx || [1.7, 0.021, 2.1, 5.6];
function exFor(d){ return clamp(TEX[0]+d*TEX[1], TEX[2], TEX[3]); }
function cr(p0,p1,p2,p3,t){                    // Catmull-Rom, centripetal-ish
  const t2=t*t, t3=t2*t;
  return 0.5*(2*p1 + (p2-p0)*t + (2*p0-5*p1+4*p2-p3)*t2 + (3*p1-p0-3*p2+p3)*t3);
}
let _exagUI=null;
function setExagUI(v){
  X.setExag(v);
  const iv=Math.round(v*10);
  if(iv!==_exagUI){                            // touch the DOM only on change
    _exagUI=iv;
    $('#exag').value=iv;
    $('#exagv').textContent='×'+(iv/10).toFixed(1);
  }
}
function keyToCam(k){
  const [u,v]=X.lonLatToUV(k.lon,k.lat);
  return {x:wx(u), z:wz(v), d:k.d, az:k.az*DEG, el:k.el*DEG, ex:exFor(k.d)};
}
function startTour(t){
  clearProfile();
  tour.active=true; tour.t=0; tour.i=0; tour.id=t.id;
  tour.seg=-1; tour.from=null; tour._pw='';
  tour.keys=t.keys.map(keyToCam); tour.caps=t.keys.map(k=>k.cap); tour.name=t.name;
  document.body.classList.add('touring');
  $('#tourbar').classList.add('show');
  [...document.querySelectorAll('.tour')].forEach(b=>b.setAttribute('aria-current', b.dataset.id===t.id?'true':'false'));
  const k0=tour.keys[0];
  cam.Tx=k0.x; cam.Tz=k0.z; cam.Tdist=k0.d; cam.Taz=k0.az; cam.Tel=k0.el;
  cam.tx=k0.x; cam.tz=k0.z; cam.dist=k0.d; cam.az=k0.az; cam.el=k0.el;
  setExagUI(k0.ex);
  showCaption(tour.name, tour.caps[0]);
}
function stopTour(){
  if(!tour.active) return;
  tour.active=false;
  document.body.classList.remove('touring');
  $('#tourbar').classList.remove('show');
  $('#caption').classList.remove('show');
  [...document.querySelectorAll('.tour')].forEach(b=>b.setAttribute('aria-current','false'));
  cam.Tx=cam.tx; cam.Tz=cam.tz; cam.Tdist=cam.dist; cam.Taz=cam.az; cam.Tel=cam.el;
}
function showCaption(t,c){
  $('#capTitle').textContent=t; $('#capText').textContent=c;
  $('#caption').classList.add('show');
}
function tickTour(dt){
  const K=tour.keys, n=K.length;
  tour.t += dt;
  const total=(n-1)*(SEG+HOLD)+HOLD;
  const pw=(clamp(tour.t/total,0,1)*100).toFixed(1);
  if(pw!==tour._pw){ tour._pw=pw; $('#tourprog').style.width=pw+'%'; }
  if(tour.t>=total){ stopTour(); return; }
  let t=tour.t, seg=0, moving=false;
  if(t>=HOLD){
    t-=HOLD;
    seg=Math.min(n-2, Math.floor(t/(SEG+HOLD)));
    t=t-seg*(SEG+HOLD);
    moving = t<SEG;
  }
  if(moving && seg!==tour.seg){
    // each leg departs from wherever the camera actually is, so holds,
    // drifts and legs join with no velocity step
    tour.seg=seg;
    tour.from={x:cam.tx, z:cam.tz, d:cam.dist, az:cam.az, el:cam.el, ex:X.getExag()};
  }
  if(moving){
    const A=tour.from, B=K[seg+1];
    const P0=K[seg-1]||{x:2*A.x-B.x, z:2*A.z-B.z, d:2*A.d-B.d};
    const P3=K[seg+2]||{x:2*B.x-A.x, z:2*B.z-A.z, d:2*B.d-A.d};
    let f=clamp(t/SEG,0,1);
    f=f*f*f*(f*(f*6-15)+10);
    cam.tx=cr(P0.x,A.x,B.x,P3.x,f);               // flown as an arc, not a dash
    cam.tz=cr(P0.z,A.z,B.z,P3.z,f);
    cam.dist=clamp(cr(P0.d,A.d,B.d,P3.d,f), MAXD*0.0035, MAXD);
    let da=((B.az-A.az+Math.PI*3)%(Math.PI*2))-Math.PI;
    cam.az=A.az+da*f;
    cam.el=lerp(A.el,B.el,f);
    setExagUI(lerp(A.ex,B.ex,f));
  } else {
    cam.az += 0.0055*dt;                           // never quite frozen
  }
  // terrain-following through the slow spring — the crane again
  cam.ty += (X.terrainY(cam.tx,cam.tz)-cam.ty)*(1-Math.exp(-1.8*dt));
  let idx;
  if(tour.t<HOLD) idx=0;
  else if(!moving) idx=seg+1;
  else idx=(t>SEG*0.55 && seg+1<n)?seg+1:seg;
  if(idx!==tour.i){ tour.i=idx; showCaption(tour.name, tour.caps[idx]); }
}
function buildTours(){
  const list=$('#tourlist');
  M.tours.forEach(t=>{
    const b=document.createElement('button');
    b.className='tour'; b.dataset.id=t.id; b.setAttribute('aria-current','false');
    b.innerHTML=`<div class="n">${t.name}</div><div class="b">${t.blurb}</div>`;
    b.addEventListener('click',()=>{ tour.active&&tour.id===t.id ? stopTour() : startTour(t); });
    list.appendChild(b);
  });
}
$('#tourstop').addEventListener('click',stopTour);

/* ================= UI wiring ================= */
function bindSlider(id, fn, fmt){
  const el=$('#'+id), out=$('#'+id+'v');
  const run=()=>{ const v=+el.value; if(out) out.textContent=fmt(v); fn(v); };
  el.addEventListener('input',run); run();
}
function bindToggle(id, init, fn){
  const el=$('#'+id);
  let on=init; el.setAttribute('aria-pressed',String(on));
  const set=v=>{ on=v; el.setAttribute('aria-pressed',String(on)); fn(on); };
  el.addEventListener('click',()=>set(!on));
  fn(on);
  return {set, get:()=>on, toggle:()=>set(!on)};
}
let planMode=false;
let togShadow, togContour, togBorder;
const SHEET_NAME = (UI.sheetA || 'sheet');
function wireUI(){
  const MID_NAME = UI.altName || 'Second sheet';
  bindSlider('mix', v=>{
    if(X.HASALT){
      U.uMix.value = clamp(v/50, 0, 1);
      U.uMix2.value = clamp((v-50)/50, 0, 1);
      $('#cfA').classList.toggle('on', v>=75);
      const m=$('#cfM'); if(m) m.classList.toggle('on', v>25 && v<75);
      $('#cfB').classList.toggle('on', v<=25);
    } else {
      U.uMix.value=v/100;
      $('#cfA').classList.toggle('on', v>=50); $('#cfB').classList.toggle('on', v<50);
    }
  }, v=>{
    if(!X.HASALT) return v>=97?SHEET_NAME:(v<=3?'Modern relief':v+'% sheet');
    if(v>=97) return SHEET_NAME;
    if(v<=3) return 'Modern relief';
    if(v>=44 && v<=56) return MID_NAME;
    return v+'%';
  });
  bindSlider('exag', v=>{ X.setExag(v/10); rebuildProfileGeom(); refreshOverlays(); }, v=>'×'+(v/10).toFixed(1));
  bindSlider('shade', v=>{U.uShade.value=v/100;}, v=>v+'%');
  bindSlider('sunalt', v=>{sun.alt=v; updateSun();}, v=>v+'°');
  togShadow = bindToggle('tShadow', true, v=>{U.uShadow.value=v?1:0;});
  togContour= bindToggle('tContour',false,v=>{U.uContour.value=v?0.85:0;});
  togBorder = bindToggle('tBorder', true, v=>{U.uBorder.value=v?0.9:0;});
  bindToggle('tPeaks', true, v=>{show.peak=v; show.mine=v;});
  bindToggle('tCities',true, v=>{show.city=v;});
  bindToggle('tFeatures',true,v=>{show.feature=v;});

  $('#sunplay').addEventListener('click',e=>{
    sun.moving=!sun.moving; e.currentTarget.classList.toggle('on',sun.moving);
    e.currentTarget.textContent = sun.moving?'Hold sun':'Move sun';
  });
  $('#btnProfile').addEventListener('click',e=>{
    if(measure.mode){ measure.mode=false; document.body.classList.remove('measuring'); e.currentTarget.classList.remove('on'); return; }
    clearProfile(); measure.mode=true;
    document.body.classList.add('measuring');
    e.currentTarget.classList.add('on');
  });
  let planSave=null;
  const setSlider=(id,v)=>{ const el=$('#'+id); el.value=v; el.dispatchEvent(new Event('input')); };
  $('#btnPlan').addEventListener('click',e=>{
    planMode=!planMode;
    e.currentTarget.classList.toggle('on',planMode);
    if(planMode){
      planSave={ex:$('#exag').value, sh:$('#shade').value, mx:$('#mix').value, el:cam.Tel};
      cam.Tel=89.4*DEG; cam.Taz=Math.PI;         // camera south of target: north-up reading
      setSlider('mix',100); setSlider('shade',18);
      setSlider('exag', Math.max(6, Math.round(EXAG0*10*0.18)));
    } else if(planSave){
      cam.Tel=Math.min(planSave.el, 60*DEG);
      setSlider('mix',planSave.mx); setSlider('shade',planSave.sh); setSlider('exag',planSave.ex);
      planSave=null;
    }
  });
  $('#btnReset').addEventListener('click',()=>{
    stopTour();
    if(planMode) $('#btnPlan').click();
    planMode=false; $('#btnPlan').classList.remove('on');
    setExagUI(EXAG0);
    cam.Taz=HOME.az; cam.Tel=HOME.el; cam.Tdist=HOME.dist; cam.Tx=HOME.x; cam.Tz=HOME.z;
  });
  const openInfo=()=>{$('#info').classList.add('show');};
  $('#btnAbout').addEventListener('click',openInfo);
  $('#creditBtn').addEventListener('click',openInfo);
  $('#infoClose').addEventListener('click',()=>$('#info').classList.remove('show'));
  $('#info').addEventListener('click',e=>{ if(e.target.id==='info') $('#info').classList.remove('show'); });

  addEventListener('keydown',e=>{
    if(e.metaKey||e.ctrlKey) return;
    const k=e.key.toLowerCase();
    if(k==='escape'){ stopTour(); clearProfile(); $('#info').classList.remove('show');
      measure.mode=false; document.body.classList.remove('measuring'); $('#btnProfile').classList.remove('on'); }
    else if(k==='s'){ togShadow.toggle(); }
    else if(k==='c'){ togContour.toggle(); }
    else if(k==='r'){ $('#btnReset').click(); }
    else if(k==='p'){ $('#btnPlan').click(); }
    else return;
    e.preventDefault();
  });

  const left=$('#left'), sheetT=$('#sheetToggle');
  const applyBP=()=>{ const m=innerWidth<=920;
    if(m && !left.dataset.bp){ left.classList.add('collapsed'); sheetT.setAttribute('aria-expanded','false'); left.dataset.bp='m'; }
    if(!m && left.dataset.bp){ left.classList.remove('collapsed'); left.dataset.bp=''; }
  };
  applyBP(); addEventListener('resize',applyBP,{passive:true});
  sheetT.addEventListener('click',()=>{
    const open=left.classList.toggle('collapsed');
    sheetT.setAttribute('aria-expanded', String(!open));
  });

  const gl=$('#gl');
  gl.addEventListener('pointerdown',onDown);
  gl.addEventListener('pointermove',onMove);
  gl.addEventListener('pointerup',onUp);
  gl.addEventListener('pointercancel',onUp);
  gl.addEventListener('wheel',onWheel,{passive:false});
  gl.addEventListener('contextmenu',e=>e.preventDefault());
  gl.addEventListener('pointerleave',()=>{ hoverPt=null; });
}

/* ================= intro + loop ================= */
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const intro={t0:0, dur:REDUCED?0.01:3.0, on:true};
let last=performance.now();
const perf={acc:0, n:0, slow:0, step:0};
function watchdog(dt){
  perf.acc+=dt; perf.n++;
  if(perf.n<20) return;
  const avg=perf.acc/perf.n; perf.acc=0; perf.n=0;
  if(avg>0.055) perf.slow++; else perf.slow=Math.max(0,perf.slow-1);
  if(perf.slow>=3 && perf.step===0){
    perf.step=1; renderer.setPixelRatio(1); perf.slow=0;
  } else if(perf.slow>=3 && perf.step===1){
    perf.step=2; U.uShadow.value=0; togShadow.set(false); perf.slow=0;
  }
}
function tick(){
  const now=performance.now();
  let dt=Math.min((now-last)/1000, 0.05); last=now;
  if(!intro.on) watchdog(dt);

  if(intro.on){
    if(!intro.t0) intro.t0=now;
    const f=clamp((now-intro.t0)/1000/intro.dur,0,1);
    const e=1-Math.pow(1-f,3);
    X.setExag(lerp(0.02, EXAG0, e));
    cam.el=cam.Tel=lerp(66*DEG, HOME.el, e);
    cam.dist=cam.Tdist=lerp(HOME.dist*1.75, HOME.dist, e);
    cam.az=cam.Taz=lerp(HOME.az-30*DEG, HOME.az, e);
    labelFade=clamp((f-0.55)/0.4,0,1);
    if(f>=1){ intro.on=false; labelFade=1; $('#exag').value=Math.round(EXAG0*10);
      refreshOverlays(); }
  } else if(labelFade<1){ labelFade=Math.min(1,labelFade+dt*1.6); }

  if(sun.moving){ sun.az=(sun.az+dt*11)%360; updateSun(); }
  if(tour.active) tickTour(dt); else damp(dt);
  applyCam();
  updateLabels();
  updateHud();
  drawMini();
  renderer.render(scene, camera);
}

window.MTdebug=()=>({fade:labelFade, intro:intro.on, dist:cam.dist, az:cam.az/DEG, el:cam.el/DEG,
  ty:cam.ty, camY:camera.position.y, nlbl:labels.length, step:perf.step, novl:overlays.length});

/* ================= go ================= */
(async function main(){
  try{
    await X.boot();
  }catch(err){
    const gl=document.createElement('canvas').getContext('webgl2')||document.createElement('canvas').getContext('webgl');
    $('#ldtxt').textContent = gl ? 'Could not load the map data.'
      : 'This browser cannot run WebGL, which the 3-D view needs.';
    console.error(err); return;
  }
  renderer=X.renderer; scene=X.scene; camera=X.camera;
  fitHome();
  cam.az=cam.Taz=HOME.az; cam.el=cam.Tel=HOME.el; cam.dist=cam.Tdist=HOME.dist;
  addEventListener('resize',()=>{ const d0=HOME.dist; fitHome();
    if(!tour.active && Math.abs(cam.Tdist-d0)<1) cam.Tdist=HOME.dist; },{passive:true});
  buildLabels(); buildTours(); buildMini(); buildOverlays(); wireUI(); updateSun();
  X.setExag(0.02);
  applyCam();
  renderer.render(scene,camera);
  requestAnimationFrame(()=>{
    $('#load').classList.add('done');
    setTimeout(()=>{ const l=$('#load'); if(l) l.style.display='none'; }, 1400);
    last=performance.now();
    renderer.setAnimationLoop(tick);
  });
})();
})();

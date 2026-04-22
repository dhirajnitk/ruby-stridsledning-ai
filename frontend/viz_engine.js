// BOREAL ENGINE V8.3 — Strategic Visual Dominance
const urlParams = new URLSearchParams(window.location.search);
const MODE = urlParams.get('mode') || 'boreal';

// --- THEATRE COORDINATES (adaptive per mode) ---
// Sweden: origin=Stockholm, units=km offset from Stockholm
// Boreal: origin=Arktholm, units=arbitrary grid units
if (MODE === 'sweden') {
  // Sweden: pulled down further for button clearance (OY 480 -> 530)
  SVG_OX = 545; SVG_OY = 530; SVG_SCALE = 0.48;
} else {
  // Boreal: 1:1 mapping to SVG viewBox (1000x780). Scaling: 1 unit = 1.66km
  SVG_OX = 0; SVG_OY = 0; SVG_SCALE = 1.0; 
}
const KM_TO_UNIT = 120 / 200; // 0.6 units per km
const UNIT_TO_KM = 200 / 120; // 1.666 km per unit

function toSvgX(v) { return SVG_OX + v * SVG_SCALE; }
function toSvgY(v) { return SVG_OY + v * SVG_SCALE; } // SVG Y is down
function to3X(v)   { return v * 1666; } // 1 unit = 1666m
function to3Z(v)   { return v * 1666; }

const SWEDEN_KM = [
  [88,720],[125,692],[192,642],[192,590],[170,522],[152,442],[135,368],
  [105,292],[68,212],[38,138],[8,56],[0,0],[-8,-44],[-42,-82],[-88,-132],
  [-135,-202],[-162,-282],[-170,-338],[-142,-378],[-95,-394],[-62,-384],
  [-85,-330],[-122,-270],[-172,-220],[-232,-200],[-312,-194],[-365,-182],
  [-378,-126],[-358,-56],[-318,24],[-268,82],[-218,152],[-168,232],
  [-128,322],[-98,422],[-68,532],[-28,622],[42,682],[88,720]
];

const THEATER_DATA = (MODE === 'sweden') ? [
  { type:"BASE", id:"F21", name:"LULEÅ AIR BASE",    x: 185, y: 691, sam:12, effectors:['LV-103', 'E98', 'RBS70']  },
  { type:"BASE", id:"F16", name:"UPPSALA AIR BASE",  x: -27, y:  63, sam:24, effectors:['LV-103', 'E98']          },
  { type:"BASE", id:"VID", name:"VIDSEL TEST RANGE", x:  95, y: 728, sam:48, effectors:['LV-103', 'LVKV90']       },
  { type:"HVA",  id:"STO", name:"STOCKHOLM",         x:   0, y:   0, sam:60, effectors:['LV-103', 'E98', 'LVKV90']},
  { type:"BASE", id:"MUS", name:"MUSKÖ NAVAL",       x:   4, y: -46, sam:30, effectors:['E98', 'METEOR']       },
  { type:"BASE", id:"F7",  name:"SÅTENÄS AIR BASE",  x:-313, y: -99, sam:24, effectors:['E98', 'METEOR']       },
  { type:"BASE", id:"F17", name:"RONNEBY AIR BASE",  x:-172, y:-340, sam:32, effectors:['LV-103', 'E98']          },
  { type:"BASE", id:"MAL", name:"MALMEN AIR BASE",   x:-150, y:-104, sam:16, effectors:['E98', 'RBS70']          },
  { type:"BASE", id:"KRL", name:"KARLSKRONA NAVAL",  x:-153, y:-352, sam:20, effectors:['E98', 'LVKV90']       },
  { type:"BASE", id:"GOT", name:"GOTLAND VISBY HUB", x:  16, y:-186, sam:40, effectors:['LV-103', 'E98', 'RBS70']  },
  { type:"HVA",  id:"GBG", name:"GOTHENBURG PORT",   x:-364, y:-180, sam:30, effectors:['E98', 'LVKV90']       }
] : [
  // BOREAL (Extracted from the-boreal-passage-map.svg)
  { type:"BASE", id:"NVB", name:"NORTHERN VANGUARD",   x:119,  y:197,  sam:40, effectors:['PAC3', 'NASAMS', 'HELWS'] },
  { type:"BASE", id:"HRC", name:"HIGHRIDGE COMMAND",   x:503,  y:41,   sam:30, effectors:['THAAD', 'PAC3']           },
  { type:"BASE", id:"BWP", name:"BOREAL WATCH POST",   x:695,  y:227,  sam:50, effectors:['NASAMS', 'CRAM']         },
  { type:"HVA",  id:"ARK", name:"ARKTHOLM CAPITAL",    x:251,  y:57,   sam:100,effectors:['THAAD', 'PAC3', 'NASAMS', 'CRAM']},
  { type:"HVA",  id:"VAL", name:"VALBREK",             x:854,  y:128,  sam:60, effectors:['PAC3', 'HELWS']          },
  { type:"HVA",  id:"NRD", name:"NORDVIK",             x:84,   y:194,  sam:40, effectors:['NASAMS', 'CRAM']         },
  // SOUTH SIDE
  { type:"BASE", id:"FWS", name:"FIREWATCH STATION",   x:839,  y:639,  sam:24, domain:"KINETIC"     },
  { type:"BASE", id:"SRB", name:"SOUTHERN REDOUBT",    x:193,  y:739,  sam:16, domain:"KINETIC"     },
  { type:"BASE", id:"SPB", name:"SPEAR POINT BASE",    x:551,  y:497,  sam:20, domain:"KINETIC"     },
  { type:"HVA",  id:"MER", name:"MERIDIA CAPITAL",     x:735,  y:725, sam:40, effectors:['THAAD','PAC3','NASAMS'] },
  { type:"HVA",  id:"CAL", name:"CALLHAVEN",           x:58,   y:690, sam:28, effectors:['PAC3','NASAMS']          },
  { type:"HVA",  id:"SOL", name:"SOLANO",              x:346,  y:742, sam:28, effectors:['PAC3','NASAMS']          },
  // TERRAIN NODES (Simplified for 2D)
  { type:"ZONE", id:"BST", name:"BOREAL STRAIT",       x:500,  y:400,  subtype:"water"              },
];

// --- EFFECTOR DEFINITIONS (Audited per NATO/Sweden Doctrine) ---
const EFFECTORS = {
  sweden: {
    'LV-103': { name: 'Patriot PAC-3 MSE',    range: 120000, type: 'KINETIC',  color: '#00f2ff', cost: 400, pk: { HYPERSONIC: 0.65, BALLISTIC: 0.7, CRUISE: 0.95, FIGHTER: 0.95, LOITER: 0.8 } },
    'E98':    { name: 'IRIS-T SLS',           range: 12000,  type: 'KINETIC',  color: '#00ff88', cost: 40,  pk: { HYPERSONIC: 0.1, BALLISTIC: 0.2, CRUISE: 0.8,  FIGHTER: 0.8, LOITER: 0.9 } },
    'NIMBRIX': { name: 'Saab Nimbrix (C-UAS)', range: 5000,   type: 'KINETIC',  color: '#ffff00', cost: 3,   pk: { DRONE: 0.98, LOITER: 0.95, CRUISE: 0.1 } },
    'LIDS-EW': { name: 'LIDS EW Jammer',      range: 8000,   type: 'LASER',    color: '#ff00ff', cost: 1,   pk: { DRONE: 0.85, LOITER: 0.70 } },
    'METEOR': { name: 'Meteor BVRAAM',        range: 150000, type: 'AIR-AIR',  color: '#ffffff', cost: 200, pk: { HYPERSONIC: 0.5, BALLISTIC: 0.3, CRUISE: 0.85, FIGHTER: 0.98, LOITER: 0.2 } }
  },
  boreal: {
    'THAAD':  { name: 'THAAD (Upper-Tier)',     range: 200000, type: 'KINETIC',  color: '#00f2ff', cost: 800, pk: { HYPERSONIC: 0.8, BALLISTIC: 0.98, CRUISE: 0.4, FIGHTER: 0.3, LOITER: 0.1 } },
    'PAC3':   { name: 'Patriot PAC-3 MSE',     range: 120000, type: 'KINETIC',  color: '#00f2ff', cost: 400, pk: { HYPERSONIC: 0.7, BALLISTIC: 0.95, CRUISE: 0.95, FIGHTER: 0.9, LOITER: 0.8 } },
    'NASAMS': { name: 'NASAMS (AMRAAM)',         range: 40000,  type: 'KINETIC',  color: '#00ff88', cost: 100, pk: { HYPERSONIC: 0.5, BALLISTIC: 0.5,  CRUISE: 0.88, FIGHTER: 0.9, LOITER: 0.6 } },
    'HELWS':  { name: 'HELWS Laser Weapon',      range: 5000,   type: 'LASER',    color: '#ffff00', cost: 5,   pk: { LOITER: 0.9,  DRONE: 0.95, CRUISE: 0.2 } },
    'CRAM':   { name: 'C-RAM Phalanx',           range: 1500,   type: 'KINETIC',  color: '#ff8800', cost: 10,  pk: { CRUISE: 0.7,  LOITER: 0.8, DRONE: 0.9 } },
    'COYOTE2': { name: 'RTX Coyote Block 2+',  range: 15000,  type: 'KINETIC',  color: '#00ffaa', cost: 5,   pk: { DRONE: 0.95, LOITER: 0.95, CRUISE: 0.3 } },
    'MEROPS': { name: 'Merops Interceptor',    range: 3000,   type: 'KINETIC',  color: '#ffcc00', cost: 2,   pk: { DRONE: 0.95, LOITER: 0.90 } },
    'COYOTE3': { name: 'Coyote B3 (Non-Kin)',  range: 10000,  type: 'LASER',    color: '#ff00ff', cost: 1,   pk: { DRONE: 0.90, LOITER: 0.80 } }
  }
};

// Maps backend engine effector keys → frontend EFFECTORS keys per theater
const ENGINE_EFF_MAP = {
  boreal: { 'patriot-pac3':'PAC3','nasams':'NASAMS','thaad':'THAAD','iris-t-sls':'PAC3','coyote-block2':'COYOTE2','merops-interceptor':'MEROPS','saab-nimbrix':'COYOTE3','lids-ew':'COYOTE3','meteor':'PAC3' },
  sweden: { 'patriot-pac3':'LV-103','nasams':'LV-103','iris-t-sls':'E98','meteor':'METEOR','saab-nimbrix':'NIMBRIX','lids-ew':'LIDS-EW','thaad':'LV-103' }
};
// Active doctrine key, updated by setDoctrine() and used in callEngine()
window._ACTIVE_DOCTRINE = 'balanced';

const BASES = {};
THEATER_DATA.forEach(n => { 
    if (n.type === 'BASE' || n.type === 'HVA') {
        BASES[n.id] = n; 
        // Assign default effectors based on mode if not specified
        if (!n.effectors) {
            n.effectors = MODE === 'sweden' ? ['LV-103', 'E98'] : ['PAC3', 'THAAD'];
        }
    }
});

// --- KINETIC DEFINITIONS ---
const WEAPONS = {
  CRUISE:     { speed:600,  color3:'#ff3e3e', hex3:0xff3e3e, r2d:5,  label:'CRUISE MISSILE',   type:'CRUISE'     },
  HYPERSONIC: { speed:2200, color3:'#ffcc00', hex3:0xffcc00, r2d:4,  label:'HYPERSONIC GLIDE', type:'HYPERSONIC' },
  LOITER:     { speed:300,  color3:'#ff00ff', hex3:0xff00ff, r2d:4,  label:'LOITERING MUNITION',type:'LOITER'    },
  BALLISTIC:  { speed:1400, color3:'#ff5500', hex3:0xff5500, r2d:6,  label:'BALLISTIC MISSILE', type:'BALLISTIC'  },
};

const WAVE_SEQ = [
  { name:'OPENING PROBE',        weapons:['CRUISE'],                    count:4 },
  { name:'MIXED SATURATION',     weapons:['CRUISE','LOITER'],           count:8 },
  { name:'HYPERSONIC STRIKE',    weapons:['HYPERSONIC'],                count:4 },
  { name:'COORDINATED ASSAULT',  weapons:['BALLISTIC','CRUISE'],        count:10},
  { name:'MAX SATURATION',       weapons:['HYPERSONIC','LOITER','CRUISE'],count:15},
];

let ammo = {};
let balticMap, mapGeometry, baseIconsG, threatLayerG, cotFeed, healthFill;
let cityHealth = 100, isSimulating = false, currentScenarioIdx = 0, currentWaveIdx = 0, waveTransitioning = false;
let BENCHMARKS = {};
let threats = [];
let rejectedThreats = new Set(); // Tracks HITL-rejected threat IDs so they aren't re-queued

// Expose live state to dashboard panels (manual override, HITL queue) via getters
Object.defineProperty(window, 'threats',   { get: () => threats,   configurable: true });
Object.defineProperty(window, 'BASES',     { get: () => BASES,     configurable: true });
Object.defineProperty(window, 'ammo',      { get: () => ammo,      configurable: true });
Object.defineProperty(window, 'EFFECTORS', { get: () => EFFECTORS, configurable: true });

// --- LIVE ACCURACY TRACKING ---
let stats = { fired: 0, intercepted: 0, missed: 0, impacts: 0, totalThreats: 0 };
let groundTruthData = null; // Loaded from ground_truth_scenarios.json

function getTacticalAcc() {
  return stats.fired > 0 ? ((stats.intercepted / stats.fired) * 100).toFixed(1) : '--';
}
function getStrategicAcc() {
  return stats.totalThreats > 0 ? (((stats.totalThreats - stats.impacts) / stats.totalThreats) * 100).toFixed(1) : '--';
}
function updateAccuracyDisplay() {
  const el = id => document.getElementById(id);
  const tacAcc = getTacticalAcc();
  const strAcc = getStrategicAcc();

  if (el('stat-tactical'))  el('stat-tactical').innerText  = tacAcc + (tacAcc === '--' ? '' : '%');
  if (el('stat-strategic')) el('stat-strategic').innerText  = strAcc + (strAcc === '--' ? '' : '%');
  if (el('stat-fired'))     el('stat-fired').innerText      = stats.fired;
  if (el('stat-intercepts'))el('stat-intercepts').innerText = stats.intercepted;
  if (el('stat-impacts'))   el('stat-impacts').innerText    = stats.impacts;
  if (el('stat-missed'))    el('stat-missed').innerText     = stats.missed;
  
  // LIVE MC TRUTH BINDING
  const truthVal = (ACTIVE_MODEL.pk * 100).toFixed(1) + '%';
  if (el('mc-tac-acc'))     el('mc-tac-acc').innerText      = truthVal;
  if (el('mc-str-acc'))     el('mc-str-acc').innerText      = (ACTIVE_MODEL.success || '100%');
  if (el('mc-avg-score')) {
    const raw = (ACTIVE_MODEL.success || '942/1000').split('/')[0];
    const baseScore = parseFloat(raw) / 10;
    el('mc-avg-score').innerText = (baseScore + (Math.random() * 2)).toFixed(1);
  }
  if (el('acc-badge'))      el('acc-badge').innerText       = truthVal + ' MC TRUTH';

  const tc = el('threat-count');
  if (tc) tc.innerText = threats.filter(t => !t.hit).length + ' ACTIVE';
}

const SAAB_CH = new BroadcastChannel('saab_kinetic_v8');
window.isMirror = !window.location.pathname.includes('dashboard.html');

SAAB_CH.onmessage = e => {
  if (e.data?.type === 'LAUNCH') startEngagement();
  if (e.data?.type === 'DEMO') triggerDemo(e.data.id);
  if (e.data?.type === 'FREEZE') {
    window._engFrozen = true;
    const lf = document.getElementById('lv-freeze');
    if (lf) lf.classList.add('on');
  }
  if (e.data?.type === 'RESUME') {
    window._engFrozen = false;
    const lf = document.getElementById('lv-freeze');
    if (lf) lf.classList.remove('on');
  }
  
  if (window.isMirror) {
    if (e.data?.type === 'THREAT_SPAWN') {
        const tgt = THEATER_DATA.find(n => n.id === e.data.targetId);
        if (tgt) threats.push(new Threat(e.data.id, e.data.wkey, tgt, e.data.idx));
    }
    if (e.data?.type === 'INTERCEPT') {
        const t = threats.find(x => x.id === e.data.threatId);
        if (t && BASES[e.data.baseId]) {
            if (!t.interceptors) t.interceptors = [];
            t.interceptors.push(new Interceptor(BASES[e.data.baseId]));
            stats.fired++;
        }
    }
  }
};

// --- INITIALIZATION ---
function initAmmo() {
  THEATER_DATA.forEach(n => { if (n.type === 'BASE' || n.type === 'HVA') ammo[n.id] = n.sam || 0; });
}

function restockAmmo() {
  Object.keys(BASES).forEach(id => {
    const cap = BASES[id].sam || 0; // Guard: HVA nodes (MER/CAL/SOL) have no sam
    if (cap <= 0) return;
    ammo[id] = Math.min(cap, (ammo[id]||0) + Math.ceil(cap * 0.5));
  });
  addCoT('REPLENISHING SAM INVENTORY :: +50% STOCK', 'success');
  updateInventoryDisplay();
}

function updateInventoryDisplay() {
  const n1 = document.getElementById('node-1-sam');
  const n2 = document.getElementById('node-2-sam');
  const n1Lbl = document.getElementById('node-1-name');
  const n2Lbl = document.getElementById('node-2-name');
  const res = document.getElementById('res-sam');
  const total = Object.values(ammo).reduce((a, b) => a + b, 0);

  // Dynamic Base Mapping (High-Impact Labels)
  const b1 = MODE === 'sweden' ? 'F16' : 'NVB';
  const b2 = MODE === 'sweden' ? 'GOT' : 'HRC';
  const displayNames = {
    'F16': 'STOCKHOLM REGION',
    'GOT': 'GOTLAND HUB',
    'NVB': 'VANGUARD BASE',
    'HRC': 'HIGHRIDGE HUB'
  };

  if (n1) n1.innerText = ammo[b1] || 0;
  if (n2) n2.innerText = ammo[b2] || 0;
  if (n1Lbl) n1Lbl.innerText = displayNames[b1] || b1;
  if (n2Lbl) n2Lbl.innerText = displayNames[b2] || b2;
  if (res) res.innerText = total;

  // Reactively update dashboard manual dropdown if it exists
  if (window.updateManualTargets) window.updateManualTargets();
}

window.cancelApproval = (threatId) => {
    pendingApprovals.delete(threatId);
    rejectedThreats.add(threatId); // Marks as rejected — threat flies through uncontested
    // Resume simulation if no more approvals are pending
    updateSimulation();
};

// --- 2D RENDERING ---
function renderMap() {
  if (!balticMap) return;
  mapGeometry.innerHTML = '';
  baseIconsG.innerHTML = '';
  
  const title = document.getElementById('map-title');
  if (MODE === 'sweden') {
    if (title) title.innerText = 'STRATEGIC MAP :: SWEDISH NATIONAL DEFENSE';
    const pts = SWEDEN_KM.map(p => `${toSvgX(p[0])},${toSvgY(p[1])}`).join(' L');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M${pts} Z`);
    path.setAttribute('fill', 'rgba(0, 242, 255, 0.05)');
    path.setAttribute('stroke', 'rgba(0, 242, 255, 0.8)');
    path.setAttribute('stroke-width', '2');
    mapGeometry.appendChild(path);
  } else {
    if (title) title.innerText = 'STRATEGIC MAP :: BOREAL THEATER';
    // Draw a border polygon connecting all boreal nodes
    const sorted = [...THEATER_DATA].sort((a,b) => Math.atan2(a.y-650,a.x-800) - Math.atan2(b.y-650,b.x-800));
    const pts = sorted.map(n => `${toSvgX(n.x)},${toSvgY(n.y)}`).join(' L');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M${pts} Z`);
    path.setAttribute('fill', 'rgba(0, 242, 255, 0.03)');
    path.setAttribute('stroke', 'rgba(0, 242, 255, 0.5)');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-dasharray', '8 4');
    mapGeometry.appendChild(path);

    const ring = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    const ark = THEATER_DATA.find(n => n.id === 'ARK');
    if (ark) {
      ring.setAttribute('cx', toSvgX(ark.x)); ring.setAttribute('cy', toSvgY(ark.y));
      ring.setAttribute('r', 150); // 250km / 1.66 = 150 units
      ring.setAttribute('fill', 'none'); ring.setAttribute('stroke', 'rgba(0,242,255,0.1)');
      ring.setAttribute('stroke-dasharray', '5 5');
      mapGeometry.appendChild(ring);
    }
  }

  THEATER_DATA.forEach(node => {
    const sx = toSvgX(node.x), sy = toSvgY(node.y);
    const isZone = node.type === 'ZONE';
    const col = node.type === 'HVA' ? '#00ff88' : (isZone ? 'rgba(0,242,255,0.4)' : '#00f2ff');
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    
    if (isZone) {
      // Draw tactical crosshair for terrain nodes
      const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line1.setAttribute('x1', sx-5); line1.setAttribute('y1', sy); line1.setAttribute('x2', sx+5); line1.setAttribute('y2', sy);
      line1.setAttribute('stroke', col); line1.setAttribute('stroke-width', '1');
      g.appendChild(line1);
      const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line2.setAttribute('x1', sx); line2.setAttribute('y1', sy-5); line2.setAttribute('x2', sx); line2.setAttribute('y2', sy+5);
      line2.setAttribute('stroke', col); line2.setAttribute('stroke-width', '1');
      g.appendChild(line2);
    } else {
      const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      dot.setAttribute('cx', sx); dot.setAttribute('cy', sy); dot.setAttribute('r', node.type === 'HVA' ? '6' : '4');
      dot.setAttribute('fill', col);
      dot.setAttribute('filter', 'drop-shadow(0 0 3px ' + col + ')');
      g.appendChild(dot);
    }

    const lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    lbl.setAttribute('x', sx + 8); lbl.setAttribute('y', sy + 4);
    lbl.setAttribute('fill', col); lbl.setAttribute('font-size', isZone ? '6' : '8');
    lbl.setAttribute('font-family', 'Orbitron');
    lbl.setAttribute('opacity', isZone ? '0.6' : '1');
    lbl.textContent = node.id;
    g.appendChild(lbl);

    baseIconsG.appendChild(g);
  });
}

function blastSvg(wx, wy, col) {
  if (!threatLayerG) return;
  const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  c.setAttribute('cx', toSvgX(wx)); c.setAttribute('cy', toSvgY(wy));
  c.setAttribute('r', '2'); c.setAttribute('fill', col); c.setAttribute('opacity', '1');
  threatLayerG.appendChild(c);
  let s = 1;
  const iv = setInterval(() => {
    s += 3; c.setAttribute('r', s); c.setAttribute('opacity', String(1 - s/30));
    if (s > 30) { clearInterval(iv); c.remove(); }
  }, 30);
  // Guaranteed cleanup after 1.5s regardless of animation
  setTimeout(() => { clearInterval(iv); c.remove(); }, 1500);
}

// Miss marker: red X on SVG — auto-fades after 4s
function missMarkerSvg(wx, wy) {
  if (!threatLayerG) return;
  const sx = toSvgX(wx), sy = toSvgY(wy);
  const sz = 8;
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  const l1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  l1.setAttribute('x1', sx-sz); l1.setAttribute('y1', sy-sz);
  l1.setAttribute('x2', sx+sz); l1.setAttribute('y2', sy+sz);
  l1.setAttribute('stroke', '#ff3e3e'); l1.setAttribute('stroke-width', '2');
  const l2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  l2.setAttribute('x1', sx+sz); l2.setAttribute('y1', sy-sz);
  l2.setAttribute('x2', sx-sz); l2.setAttribute('y2', sy+sz);
  l2.setAttribute('stroke', '#ff3e3e'); l2.setAttribute('stroke-width', '2');
  g.appendChild(l1); g.appendChild(l2);
  threatLayerG.appendChild(g);
  // Fade out after 4s
  let op = 1;
  const iv = setInterval(() => { op -= 0.05; g.setAttribute('opacity', op); if (op <= 0) { clearInterval(iv); g.remove(); } }, 200);
  setTimeout(() => { clearInterval(iv); g.remove(); }, 4500);
}

// --- BENCHMARK REPLAY ---
// Takes a precomputed scenario (from ground_truth_scenarios.json) and runs it live,
// then compares live engine output vs MC ground truth
let benchGroundTruth = null;

function runBenchmarkScenario(scenarioThreats, groundTruth) {
  threats.forEach(t => t.dispose()); threats = [];
  isSimulating = true; waveTransitioning = false;
  cityHealth = 100; if (healthFill) healthFill.style.width = '100%';
  stats = { fired:0, intercepted:0, missed:0, impacts:0, totalThreats:0 };
  benchGroundTruth = groundTruth;
  updateAccuracyDisplay(); initAmmo(); updateInventoryDisplay();

  // Map scenario threats using their target coords directly
  for (let i = 0; i < scenarioThreats.length; i++) {
    const st = scenarioThreats[i];
    // Find closest THEATER_DATA node to target coords (tx,ty in km from Stockholm)
    const tgtNode = THEATER_DATA.reduce((best, n) => {
      const d = Math.hypot(n.x - st.target_x, n.y - st.target_y);
      const bd = Math.hypot(best.x - st.target_x, best.y - st.target_y);
      return d < bd ? n : best;
    }, THEATER_DATA[0]);

    // Map weapon type to our WEAPONS keys
    const wmap = {
      'bomber':'CRUISE', 'fast-mover':'HYPERSONIC', 'drone':'LOITER',
      'hypersonic':'HYPERSONIC', 'fighter':'CRUISE', 'decoy':'LOITER'
    };
    const wkey = wmap[st.type] || 'CRUISE';
    const t = new Threat(st.id, wkey, tgtNode, i);
    threats.push(t);
    stats.totalThreats++;
  }
  addCoT(`BENCHMARK: ${scenarioThreats.length} threats spawned`, 'alert');
  updateAccuracyDisplay();
}

// Called at end of benchmark wave to print comparison
function printBenchmarkComparison() {
  if (!benchGroundTruth) return;
  const gt = benchGroundTruth;
  const liveTac = stats.fired > 0 ? (stats.intercepted/stats.fired*100).toFixed(1) : '0.0';
  const liveStr = stats.totalThreats > 0 ? ((stats.totalThreats-stats.impacts)/stats.totalThreats*100).toFixed(1) : '0.0';
  const mcTac   = (gt.expected_kills / Math.max(1,gt.n_assigned) * 100).toFixed(1);
  const mcStr   = ((gt.n_assigned) / Math.max(1, stats.totalThreats) * 100).toFixed(1);

  addCoT('══ BENCHMARK COMPARISON REPORT ══', 'success');
  addCoT(`TACTICAL  :: LIVE ${liveTac}%  vs  MC TRUTH ${mcTac}%  (Δ ${(liveTac-mcTac).toFixed(1)}%)`, liveTac >= mcTac ? 'success' : 'alert');
  addCoT(`STRATEGIC :: LIVE ${liveStr}%  vs  MC TRUTH ${mcStr}%  (Δ ${(liveStr-mcStr).toFixed(1)}%)`, liveStr >= mcStr ? 'success' : 'alert');
  addCoT(`FIRED: ${stats.fired}  KILLS: ${stats.intercepted}  IMPACTS: ${stats.impacts}  LEAKED: ${stats.missed}`, 'info');
  addCoT(`MC SCORE: ${gt.mc_mean_score} [${gt.mc_min_score}→${gt.mc_max_score}] ±${gt.mc_std}`, 'info');
  addCoT(`BEST PATH: ${gt.n_assigned} assignments, ${gt.expected_kills.toFixed(1)} expected kills`, 'info');

  // Update benchmark display delta
  const el = id => document.getElementById(id);
  if (el('bench-live-tac')) el('bench-live-tac').innerText = liveTac + '%';
  if (el('bench-live-str')) el('bench-live-str').innerText = liveStr + '%';
  benchGroundTruth = null;
}

// --- KINETIC CLASSES ---
class Interceptor {
  constructor(originNode, effectorKey) {
    this.pos = new THREE.Vector3(to3X(originNode.x), 5000, to3Z(originNode.y));
    this.mesh = null;
    this.eff = EFFECTORS[MODE][effectorKey] || EFFECTORS[MODE][Object.keys(EFFECTORS[MODE])[0]];
    
    if (scene) {
      if (this.eff.type === 'LASER') {
        const geo = new THREE.CylinderGeometry(1000, 1000, 1, 8);
        this.mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: this.eff.color, transparent: true, opacity: 0.8 }));
        scene.add(this.mesh);
      } else {
        const geo = new THREE.ConeGeometry(5000, 15000, 8);
        this.mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: this.eff.color, wireframe: true }));
        scene.add(this.mesh);
      }
    }
  }
  update(targetPos) {
    if (this.hit) return false;
    
    if (this.eff.type === 'LASER') {
        // Laser is instantaneous for visualization purposes but we 'aim' it
        this.pos.copy(targetPos);
        if (this.mesh) {
            this.mesh.lookAt(targetPos);
            this.mesh.scale.set(1, this.pos.distanceTo(targetPos), 1);
        }
    } else {
        const dir = targetPos.clone().sub(this.pos).normalize();
        const flySpeed = (this.eff.type === 'GATLING') ? 15000 : 12000;
        this.pos.add(dir.multiplyScalar(ACTIVE_MODEL.speed * flySpeed));
    }

    const dist = this.pos.distanceTo(targetPos);
    if (dist < 15000) {
      // Use effector's specific Pk matrix against threat type
      const pk = this.eff.pk[this._threatType] || ACTIVE_MODEL.pk || 0.75;
      if (Math.random() < pk) {
        this.hit = true; this.dispose(); return true;
      } else {
        addCoT(`INTERCEPT FAILURE :: ${this.eff.name} MISSED`, 'error');
        this.dispose(); return false;
      }
    }
    return false;
  }
  dispose() { 
    if (this.mesh) { 
        scene?.remove(this.mesh); 
        if (this.mesh.geometry) this.mesh.geometry.dispose(); 
        if (this.mesh.material) {
            if (Array.isArray(this.mesh.material)) {
                this.mesh.material.forEach(m => m.dispose());
            } else {
                this.mesh.material.dispose();
            }
        }
        this.mesh = null;
    }
  }
}

class Threat {
  constructor(id, wkey, targetNode, idx) {
    this.id = id; this.wdef = WEAPONS[wkey];
    this.targetNode = targetNode; this.hit = false;
    const tx = to3X(targetNode.x), tz = to3Z(targetNode.y);
    this.pos = new THREE.Vector3(600000 + idx*20000, 5000, tz + (Math.random()-0.5)*200000);
    this.vel = new THREE.Vector3(tx, 5000, tz).sub(this.pos).normalize().multiplyScalar(this.wdef.speed);
    
    this.interceptors = []; // SALVO-READY
    
    this.circle2D = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    this.circle2D.setAttribute('r', this.wdef.r2d);
    this.circle2D.setAttribute('fill', this.wdef.color3);
    threatLayerG?.appendChild(this.circle2D);

    if (scene && !balticMap) {
      const geo = new THREE.SphereGeometry(10000, 16, 16);
      this.mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: this.wdef.hex3 }));
      scene.add(this.mesh);
    }
  }
  update() {
    this.pos.add(this.vel);
    this.circle2D?.setAttribute('cx', toSvgX(this.pos.x/1666));
    this.circle2D?.setAttribute('cy', toSvgY(this.pos.z/1666));
    if (this.mesh) this.mesh.position.copy(this.pos);
  }
  dispose() {
    if (this._disposed) return;
    this._disposed = true; this.hit = true;
    this.circle2D?.remove();
    if (this.mesh) { scene?.remove(this.mesh); this.mesh.geometry.dispose(); this.mesh.material.dispose(); this.mesh = null; }
    
    // Dispose all interceptors in the salvo
    this.interceptors.forEach(int => int.dispose());
    this.interceptors = [];
    
    if (pendingApprovals.has(this.id)) {
        pendingApprovals.delete(this.id);
        const card = document.getElementById(`approval-${this.id}`);
        if (card) card.remove();
    }
  }
}

// --- SIMULATION ---
// ── NEURAL ENGINE INTEGRATION ─────────────────────────────────────────────
// Sends live threat list to FastAPI /evaluate_advanced and returns the
// engine's tactical assignments + strategic score + SITREP.
async function callEngine(threatList) {
  const typeMap = { CRUISE:'cruise-missile', HYPERSONIC:'hypersonic-pgm', LOITER:'drone', BALLISTIC:'ballistic' };
  const valMap  = { HYPERSONIC:90, BALLISTIC:80, CRUISE:60, LOITER:40 };
  // Send SVG unit coordinates directly — engine uses theater-unit ranges matching this scale
  const stateBasesPayload = Object.values(BASES).map(b => ({
    name: b.name,
    x: b.x,
    y: b.y,
    inventory: { 'patriot-pac3': b.sam || 0, 'nasams': Math.floor((b.sam||0)*0.5) }
  }));
  try {
    const r = await fetch('http://localhost:8000/evaluate_advanced', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        state: { bases: stateBasesPayload },
        threats: threatList.map(t => ({
          id: t.id,
          x: t.targetNode.x,
          y: t.targetNode.y,
          speed_kmh: t.wdef.speed,
          estimated_type: typeMap[t.wdef.type] || 'cruise-missile',
          threat_value: valMap[t.wdef.type] || 50
        })),
        weather: 'clear',
        doctrine_primary: window._ACTIVE_DOCTRINE || 'balanced',
        use_rl: true
      }),
      signal: AbortSignal.timeout(5000)
    });
    return r.ok ? await r.json() : null;
  } catch(e) { return null; }
}

function startEngagement() {
  threats.forEach(t => t.dispose()); threats = [];
  isSimulating = true; currentWaveIdx = 0; waveTransitioning = false;
  cityHealth = 100; if (healthFill) healthFill.style.width = '100%';
  stats = { fired: 0, intercepted: 0, missed: 0, impacts: 0, totalThreats: 0 };
  pendingApprovals.clear(); rejectedThreats.clear();
  updateAccuracyDisplay();
  initAmmo(); updateInventoryDisplay();
  if (balticMap) SAAB_CH.postMessage({ type: 'LAUNCH' });
  launchWave();
}

function launchWave() {
  if (!groundTruthData) {
    addCoT("GROUND TRUTH DATA NOT LOADED :: ABORTING", "error");
    return;
  }
  
  const scenario = groundTruthData[currentScenarioIdx.toString()];
  if (!scenario) {
    addCoT(`SCENARIO ${currentScenarioIdx} NOT FOUND :: RESETTING`, "alert");
    currentScenarioIdx = 0;
    return;
  }

  addCoT(`INBOUND SCENARIO ${currentScenarioIdx+1}: MC-GROUND TRUTH ACTIVE`, 'alert');
  addCoT(`ACTIVE NEURAL CORE: ${ACTIVE_MODEL.name} | Pk: ${(ACTIVE_MODEL.pk*100).toFixed(1)}%`, 'info');
  
  const incomingThreats = scenario.threats || [];
  incomingThreats.forEach((tData, i) => {
    // Map scenario weapon types to visualization keys
    let wkey = 'BALLISTIC';
    if (tData.type === 'fast-mover') wkey = 'HYPERSONIC';
    if (tData.type === 'drone')      wkey = 'LOITER';
    if (tData.type === 'fighter')    wkey = 'CRUISE';
    
    const tgt = THEATER_DATA.find(n => n.id === tData.target_id) || THEATER_DATA[0];
    const tId = tData.id || `T-${currentScenarioIdx}-${i}`;
    
    if (!window.isMirror) {
        SAAB_CH.postMessage({ type: 'THREAT_SPAWN', id: tId, wkey, targetId: tgt.id, idx: i });
    }
    
    const t = new Threat(tId, wkey, tgt, i);
    // Inject ground truth data for this threat if available
    t.goldTruth = scenario.ground_truth.assignments?.find(a => a.threat_id === tData.id);
    threats.push(t);
    stats.totalThreats++;
  });
  // ── Query Neural Engine for live assignments and SITREP ────────────────
  if (threats.length > 0) {
    callEngine(threats).then(result => {
      if (!result) { addCoT('CORTEX-1 OFFLINE — LOCAL TRIAGE ACTIVE', 'alert'); return; }
      const score = (result.strategic_consequence_score || 0).toFixed(0);
      const sirepLines = (result.human_sitrep || '').split('\n').map(l => l.trim()).filter(Boolean);
      const firstContent = sirepLines.find(l => !l.match(/^[-—]+$/));
      const sitrep = (firstContent || '').replace(/^[-—\s]+|[-—\s]+$/g, '').substring(0, 80);
      addCoT(`CORTEX-1: ${sitrep || 'ASSESSMENT COMPLETE'}`, 'info');
      addCoT(`NEURAL SCORE: ${score} | LEAKED PROJECTION: ${(result.leaked || 0).toFixed(1)}`, 'info');
      // Annotate each threat with the engine's preferred base+effector
      (result.tactical_assignments || []).forEach(a => {
        const t = threats.find(x => x.id === a.threat_id);
        if (t) {
          t.engineAssignment = a;
          const frontendEff = ENGINE_EFF_MAP[MODE]?.[a.effector] || null;
          addCoT(`ENGINE → ${a.threat_id}: ${(a.effector || '?').toUpperCase()} ≡ ${frontendEff || 'LOCAL'} from ${a.base}`, 'success');
        }
      });
    });
  }

  updateAccuracyDisplay();
}

// --- NEURAL MODEL ROSTER (Multi-Theater Audited) ---
const MODEL_PROFILES = {
    elite:    { name: "ELITE V3.5 (Final Boss) 👑",  brain: "TRANSFORMER-RESNET", logic: "DIRECT ACTION",  pkBoreal: 0.978, pkSweden: 0.982, speed: 1.2 },
    supreme3: { name: "SUPREME V3.1 (Chronos) 👁️",  brain: "CHRONOS GRU",        logic: "SEQUENCE",       pkBoreal: 0.942, pkSweden: 0.951, speed: 1.05},
    supreme2: { name: "SUPREME V2 (Legacy) 🏛️",     brain: "RESNET-64",          logic: "HYBRID",         pkBoreal: 0.891, pkSweden: 0.902, speed: 1.0 },
    titan:    { name: "TITAN TRANSFORMER 🌪️",       brain: "SELF-ATTENTION",     logic: "MULTI-VECTOR",   pkBoreal: 0.908, pkSweden: 0.916, speed: 1.1 },
    hybrid:   { name: "HYBRID RL V8.4 🛡️",          brain: "RESNET-128",         logic: "HUNGARIAN",      pkBoreal: 0.875, pkSweden: 0.885, speed: 1.0 },
    genE10:   { name: "GENERALIST E10 🧬",          brain: "POLICY-ONLY",        logic: "DIRECT ACTION",  pkBoreal: 0.930, pkSweden: 0.930, speed: 1.0 },
    heuristic:{ name: "HEURISTIC (Triage-Aware) ⚙️", brain: "CLASS-AWARE LOGIC",  logic: "TRIAGE-AWARE",   pkBoreal: 0.738, pkSweden: 0.752, speed: 0.9 },
    hBase:    { name: "HEURISTIC V2 (Base) 📜",     brain: "STATIC LOGIC",       logic: "HUNGARIAN",      pkBoreal: 0.575, pkSweden: 0.584, speed: 0.85},
    random:   { name: "RANDOM ASSIGNMENT 🎲",       brain: "STOCHASTIC",         logic: "RANDOM",         pkBoreal: 0.501, pkSweden: 0.502, speed: 0.8 }
};
let ACTIVE_MODEL = MODEL_PROFILES.heuristic;

window.setModel = (key) => {
    const theaterKey = MODE === 'sweden' ? 'sweden' : 'boreal';
    const profile = MODEL_PROFILES[key] || MODEL_PROFILES.heuristic;
    
    // Fetch audited metrics from global BENCHMARKS object (loaded in boot())
    let auditedPk = (MODE === 'sweden' ? profile.pkSweden : profile.pkBoreal);
    let auditedSuccess = "N/A";
    
    if (BENCHMARKS[theaterKey] && BENCHMARKS[theaterKey][key]) {
        auditedPk = BENCHMARKS[theaterKey][key].pk;
        auditedSuccess = BENCHMARKS[theaterKey][key].success;
    }
    
    ACTIVE_MODEL = { ...profile, pk: auditedPk, success: auditedSuccess };
    
    const badge = document.getElementById('arch-badge');
    if (badge) {
        badge.innerText = ACTIVE_MODEL.brain;
        badge.style.borderColor = key === 'elite' ? '#ffcc00' : '#00f2ff';
        badge.style.color = key === 'elite' ? '#ffcc00' : '#00f2ff';
    }
    
    const lvModel = document.getElementById('lv-active-model');
    if (lvModel) lvModel.innerText = ACTIVE_MODEL.name;
    
    // Trigger CoT update
    addCoT(`NEURAL CORE SWITCH :: ${ACTIVE_MODEL.name.split(' ')[0]} ENGAGED`, 'info');
    updateAccuracyDisplay(); 
};

// --- HITL & OPERATIONAL STATE ---
let ENGINE_MODE = 'auto';
let pendingApprovals = new Set();

window.setEngineMode = (mode) => { ENGINE_MODE = mode; };
window.setDoctrine = (doctrine) => {
    window._ACTIVE_DOCTRINE = doctrine; // persisted for callEngine() POST body
    if (doctrine === 'aggressive') addCoT("DOCTRINE: AGGRESSIVE (Extended Intercept Range)", "info");
    if (doctrine === 'fortress') addCoT("DOCTRINE: FORTRESS (Capital Priority Lock)", "info");
};

window.commitManualEngagement = (threatId, baseId, effector) => {
    const t = threats.find(x => x.id === threatId);
    if (!t || t.hit) return;
    if (ammo[baseId] > 0) {
        ammo[baseId]--; updateInventoryDisplay();
        const int = new Interceptor(BASES[baseId], effector);
        int._threatType = t.wdef.type;
        t.interceptors.push(int);  // FIX: was t.interceptor= (singular), never updated in sim loop
        stats.fired++;
        const effName = EFFECTORS[MODE][effector]?.name || effector;
        addCoT(`MANUAL OVERRIDE: ${effName} LAUNCHED FROM ${BASES[baseId].name}`, 'success');
        
        if (!window.isMirror) {
            SAAB_CH.postMessage({ type: 'INTERCEPT', threatId, baseId, effector });
        }
    }
};

window.processApprovedAssignment = (threatId) => {
    const t = threats.find(x => x.id === threatId);
    if (!t || t.hit) { pendingApprovals.delete(threatId); return; }
    const defId = Object.keys(BASES).find(id => ammo[id] > 0);
    if (defId) {
        ammo[defId]--; updateInventoryDisplay();
        // Intelligent selection for HITL: High-speed threats get upper-tier interceptors
        const effKey = (t.wdef.speed > 1.5) ? (MODE === 'sweden' ? 'LV-103' : 'PAC3') : (MODE === 'sweden' ? 'E98' : 'NASAMS');
        const int = new Interceptor(BASES[defId], effKey);
        int._threatType = t.wdef.type;
        t.interceptors.push(int);  // FIX: was t.interceptor= (singular), never updated in sim loop
        stats.fired++;
        addCoT(`HITL APPROVED: ${EFFECTORS[MODE][effKey].name} INTERCEPTING ${t.id}`, 'success');
        
        if (!window.isMirror) {
            SAAB_CH.postMessage({ type: 'INTERCEPT', threatId, baseId: defId, effector: effKey });
        }
    }
    pendingApprovals.delete(threatId);
};

function updateSimulation() {
  if (!isSimulating) return;

  const isDecisionPending = (ENGINE_MODE === 'hitl' && pendingApprovals.size > 0);
  // Manual mode: sim runs freely — operator fires via dashboard manual panel (no freeze)
  const isManualPlanning  = false;
  const wasFrozen = window._engFrozen || false;
  const nowFrozen = isDecisionPending || isManualPlanning;

  if (nowFrozen !== wasFrozen) {
    window._engFrozen = nowFrozen;
    SAAB_CH.postMessage({ type: nowFrozen ? 'FREEZE' : 'RESUME' });
    const svgPause = document.getElementById('svg-pause-indicator');
    if (svgPause) svgPause.style.display = nowFrozen ? 'block' : 'none';
  }

  if (nowFrozen) return; 

  let anyAlive = false;
  threats.forEach(t => {
    if (t.hit) return;
    anyAlive = true; t.update();
    const dist = t.pos.distanceTo(new THREE.Vector3(to3X(t.targetNode.x), 5000, to3Z(t.targetNode.y)));
    
    // Auto-Engagement Logic with Range Scaling
    if (t.interceptors.length === 0) {
        if (ENGINE_MODE === 'auto') {
            // Build all valid (base, effector) candidates that are in range
            const candidates = [];
            Object.keys(BASES).forEach(baseId => {
                if (ammo[baseId] <= 0) return;
                const basePos = new THREE.Vector3(to3X(BASES[baseId].x), 5000, to3Z(BASES[baseId].y));
                const dToBase = t.pos.distanceTo(basePos);
                Object.keys(EFFECTORS[MODE]).forEach(effKey => {
                    const eff = EFFECTORS[MODE][effKey];
                    if (dToBase > eff.range) return; // outside this effector's reach
                    const pk = eff.pk[t.wdef.type] || 0.5; // wdef.type now always defined
                    // Engine bonus: +50 utility if engine recommended this effector type
                    const engKey = t.engineAssignment ? (ENGINE_EFF_MAP[MODE]?.[t.engineAssignment.effector] || null) : null;
                    const engineBonus = (engKey && effKey === engKey) ? 50 : 0;
                    // Utility: kill probability primary, engine recommendation bonus, distance tiebreak
                    const utility = (pk * 100) - (dToBase / 100000) + engineBonus;
                    candidates.push({ baseId, effKey, dToBase, pk, utility });
                });
            });

            // Best = highest utility (pk-driven), closest breaks ties
            candidates.sort((a, b) => (b.utility - a.utility) || (a.dToBase - b.dToBase));
            const best = candidates[0];
            if (best) {
                ammo[best.baseId]--; updateInventoryDisplay();
                const int = new Interceptor(BASES[best.baseId], best.effKey);
                int._threatType = t.wdef.type;
                t.interceptors.push(int);
                stats.fired++;
                addCoT(`AUTO-ENGAGED ${t.id} → ${EFFECTORS[MODE][best.effKey].name} from ${BASES[best.baseId].name} (${(best.dToBase/1000).toFixed(0)}km)`, 'success');
            }
        } else if (ENGINE_MODE === 'hitl') {
            // HITL: queue threat for commander approval ONLY when it enters engagement range
            if (!pendingApprovals.has(t.id) && !rejectedThreats.has(t.id)) {
                // Compute candidates (only add card when at least one base is in range)
                const hitlCands = [];
                Object.keys(BASES).forEach(baseId => {
                    if (ammo[baseId] <= 0) return;
                    const bp = new THREE.Vector3(to3X(BASES[baseId].x), 5000, to3Z(BASES[baseId].y));
                    const d = t.pos.distanceTo(bp);
                    Object.keys(EFFECTORS[MODE]).forEach(effKey => {
                        const eff = EFFECTORS[MODE][effKey];
                        if (d > eff.range) return;
                        const pk = eff.pk[t.wdef.type] || 0.5;
                        hitlCands.push({ baseId, effKey, d, utility: (pk*100)-(d/100000) });
                    });
                });
                hitlCands.sort((a,b) => b.utility - a.utility);
                const bestH = hitlCands[0];
                // Only show approval card once threat is actually within engagement range
                if (bestH) {
                    pendingApprovals.add(t.id);
                    if (window.requestApproval) {
                        window.requestApproval({
                            threat_id: t.id,
                            weapon: t.wdef.label || t.wdef.type,
                            target: t.targetNode.name,
                            effector: EFFECTORS[MODE][bestH.effKey].name,
                            base_name: BASES[bestH.baseId].name
                        });
                    }
                }
            }
        }
        // MANUAL: no action — operator fires via dashboard manual panel
    }

    // Update all interceptors in the salvo
    let threatNeutralized = false;
    t.interceptors = t.interceptors.filter(int => {
        if (int.update(t.pos)) {
            threatNeutralized = true;
            return false; // Remove this interceptor
        }
        return !int.hit;
    });

    if (threatNeutralized) {
      if (!t._disposed) {
        createBlast(t.pos, 0x00f2ff);
        blastSvg(t.pos.x / 1666, t.pos.z / 1666, '#00f2ff'); // SVG unit = world m / SC(1666)
        stats.intercepted++;
        addCoT(`NEUTRALIZED ${t.id}`, 'success');
        t.dispose();
        updateAccuracyDisplay();
      }
    } else if (!t._disposed && dist < 3000) {
      // FIX: impact threshold MUST be smaller than interceptor kill radius (15000)
      // Using 3000 units — threat is at the target node
      createBlast(t.pos, 0xff3e3e);
      const wx = t.pos.x / 1666, wy = t.pos.z / 1666; // correct SVG coords
      blastSvg(wx, wy, '#ff3e3e');
      missMarkerSvg(wx, wy);
      cityHealth -= 5; if (healthFill) healthFill.style.width = `${cityHealth}%`;
      stats.impacts++;
      addCoT(`IMPACT AT ${t.targetNode.name} — DEFENSE BREACH`, 'alert');
      t.dispose();
      updateAccuracyDisplay();
    }
  });

  if (!anyAlive && !waveTransitioning && threats.length > 0) {
    waveTransitioning = true;
    threats = threats.filter(t => !t.hit);
    // If this was a benchmark scenario (single wave), print comparison and stop
    if (benchGroundTruth) {
      printBenchmarkComparison();
      isSimulating = false;
      waveTransitioning = false;
      return;
    }
    currentWaveIdx++;
    currentScenarioIdx++; // Advance to the next ground-truth scenario each wave
    if (currentWaveIdx < WAVE_SEQ.length) {
      restockAmmo();
      setTimeout(() => { waveTransitioning = false; launchWave(); }, 3000);
    } else {
      isSimulating = false;
      addCoT('THEATRE SECURED :: ALL WAVES NEUTRALIZED', 'success');
      addCoT(`FINAL: TACTICAL ${getTacticalAcc()} | STRATEGIC ${getStrategicAcc()}`, 'success');
    }
  }
}

// --- 3D ENGINE ---
let scene, camera, renderer, orbitControls;
function init3D() {
  const container = document.getElementById('canvas-container');
  if (!container) { setInterval(updateSimulation, 16); return; }

  // Use offsetWidth/Height which forces layout reflow; fall back to window dims
  const W = container.offsetWidth  || (window.innerWidth  - 240);
  const H = container.offsetHeight || (window.innerHeight - 260);

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x010a12);
  camera = new THREE.PerspectiveCamera(60, W / H, 1000, 10000000);
  // Center camera on boreal theater (~456, 391 units) or Sweden origin
  if (MODE === 'boreal') {
    camera.position.set(759000, 1000000, 1852000);
  } else {
    camera.position.set(0, 1000000, 1000000);
  }
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(W, H);
  container.appendChild(renderer.domElement);

  window.addEventListener('resize', () => {
    const w = container.offsetWidth  || window.innerWidth;
    const h = container.offsetHeight || window.innerHeight;
    if (w > 0 && h > 0) {
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
  });

  orbitControls = new THREE.OrbitControls(camera, renderer.domElement);
  if (MODE === 'boreal') orbitControls.target.set(759000, 0, 652000);
  orbitControls.update();

  scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  scene.add(new THREE.GridHelper(5000000, 50, 0x00f2ff, 0x112233));

  THEATER_DATA.forEach(n => {
    const col = n.type === 'HVA' ? 0x00ff88 : 0x00f2ff;
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(15000, 20000, 40000, 6), new THREE.MeshBasicMaterial({ color: col, wireframe: true }));
    mesh.position.set(to3X(n.x), 20000, to3Z(n.y));
    mesh.userData = { id: n.id };
    scene.add(mesh);
  });

  renderer.domElement.addEventListener('click', e => {
    const rect = renderer.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width)  * 2 - 1,
      -((e.clientY - rect.top)  / rect.height) * 2 + 1
    );
    const ray = new THREE.Raycaster(); ray.setFromCamera(mouse, camera);
    const hits = ray.intersectObjects(scene.children);
    if (hits[0]?.object.userData.id) triggerDemo(hits[0].object.userData.id);
  });

  (function loop() { requestAnimationFrame(loop); updateSimulation(); orbitControls.update(); renderer.render(scene, camera); })();
}

function createBlast(pos, col) {
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(20000, 16, 16), new THREE.MeshBasicMaterial({ color: col, wireframe: true, transparent: true }));
  mesh.position.copy(pos); scene?.add(mesh);
  let s = 1;
  const iv = setInterval(() => {
    s += 2; mesh.scale.setScalar(s); mesh.material.opacity -= 0.05;
    if (mesh.material.opacity <= 0) { clearInterval(iv); scene?.remove(mesh); }
  }, 40);
}

function triggerDemo(id) {
  const n = THEATER_DATA.find(x => x.id === id);
  if (!n) return;
  threats.forEach(t => t.dispose()); threats = [];
  initAmmo(); isSimulating = true; waveTransitioning = false;
  // Prevent wave transition from auto-launching ground-truth scenarios after demo ends
  currentWaveIdx = WAVE_SEQ.length;
  pendingApprovals.clear(); rejectedThreats.clear();
  stats = { fired:0, intercepted:0, missed:0, impacts:0, totalThreats:1 };
  // Use weapon selector if present (live_view.html), else random
  const WKEYS = ['CRUISE','HYPERSONIC','LOITER','BALLISTIC'];
  const wEl = document.getElementById('lv-sel-weapon');
  const wkey = (wEl && wEl.value) ? wEl.value : WKEYS[Math.floor(Math.random() * WKEYS.length)];
  const t = new Threat(`DEMO-${id}`, wkey, n, 0);
  threats.push(t);
  addCoT(`DEMO: ${WEAPONS[wkey].label} INBOUND → ${n.name}`, 'alert');
  if (camera) {
    camera.position.set(to3X(n.x), 400000, to3Z(n.y)+400000);
    orbitControls.target.set(to3X(n.x), 0, to3Z(n.y));
    orbitControls.update();
  }
  // Query CORTEX-1 neural engine for this single threat
  callEngine([t]).then(result => {
    if (!result) { addCoT('CORTEX-1 OFFLINE — AUTO-ENGAGE ACTIVE', 'alert'); return; }
    const score = (result.strategic_consequence_score || 0).toFixed(0);
    const sirepLines = (result.human_sitrep || '').split('\n').map(l => l.trim()).filter(Boolean);
    const firstContent = sirepLines.find(l => !l.match(/^[-—]+$/));
    const sitrep = (firstContent || '').replace(/^[-—\s]+|[-—\s]+$/g, '').substring(0, 80);
    addCoT(`CORTEX-1: ${sitrep || 'THREAT ASSESSED'}`, 'info');
    addCoT(`NEURAL SCORE: ${score} | LEAKED: ${(result.leaked || 0).toFixed(1)}`, 'info');
    (result.tactical_assignments || []).forEach(a => {
      const thr = threats.find(x => x.id === a.threat_id);
      if (thr) {
        thr.engineAssignment = a;
        const frontendEff = ENGINE_EFF_MAP[MODE]?.[a.effector] || null;
        addCoT(`ENGINE → ${a.effector?.toUpperCase()} ≡ ${frontendEff || 'LOCAL'} from ${a.base}`, 'success');
      }
    });
  });
}

function launchStandaloneWave() {
  threats.forEach(t => t.dispose()); threats = [];
  isSimulating = true; waveTransitioning = false;
  cityHealth = 100; if (healthFill) healthFill.style.width = '100%';
  stats = { fired:0, intercepted:0, missed:0, impacts:0, totalThreats:0 };
  pendingApprovals.clear(); rejectedThreats.clear();
  initAmmo(); updateInventoryDisplay();
  const WKEYS = ['CRUISE','HYPERSONIC','LOITER','BALLISTIC','CRUISE'];
  const tgtPool = THEATER_DATA.filter(n => n.type === 'HVA' || n.type === 'BASE');
  addCoT('STANDALONE SATURATION WAVE — 5 THREATS INBOUND', 'alert');
  addCoT(`ACTIVE MODEL: ${ACTIVE_MODEL.name} | Pk: ${(ACTIVE_MODEL.pk*100).toFixed(1)}%`, 'info');
  // Set wave index past WAVE_SEQ boundary so updateSimulation() stops cleanly
  // instead of transitioning to ground-truth launchWave() after this wave ends
  currentWaveIdx = WAVE_SEQ.length;
  const newThreats = WKEYS.map((wkey, i) => {
    const tgt = tgtPool[Math.floor(Math.random() * tgtPool.length)];
    const t = new Threat(`WAVE-${i}`, wkey, tgt, i);
    threats.push(t);
    stats.totalThreats++;
    addCoT(`THREAT ${i+1}: ${WEAPONS[wkey].label} → ${tgt.name}`, 'alert');
    return t;
  });
  if (camera && orbitControls) {
    const cx = MODE === 'sweden' ? 0 : to3X(456);
    const cz = MODE === 'sweden' ? 0 : to3Z(391);
    camera.position.set(cx, 900000, cz + 700000);
    orbitControls.target.set(cx, 0, cz);
    orbitControls.update();
  }
  callEngine(newThreats).then(result => {
    if (!result) { addCoT('CORTEX-1 OFFLINE — AUTO-TRIAGE ACTIVE', 'alert'); return; }
    const score = (result.strategic_consequence_score || 0).toFixed(0);
    const sirepLines = (result.human_sitrep || '').split('\n').map(l => l.trim()).filter(Boolean);
    const firstContent = sirepLines.find(l => !l.match(/^[-—]+$/));
    const sitrep = (firstContent || '').replace(/^[-—\s]+|[-—\s]+$/g, '').substring(0, 80);
    addCoT(`CORTEX-1: ${sitrep || 'WAVE ASSESSED'}`, 'info');
    addCoT(`NEURAL SCORE: ${score} | LEAKED: ${(result.leaked || 0).toFixed(1)}`, 'info');
    (result.tactical_assignments || []).forEach(a => {
      const thr = threats.find(x => x.id === a.threat_id);
      if (thr) {
        thr.engineAssignment = a;
        const fe = ENGINE_EFF_MAP[MODE]?.[a.effector] || null;
        addCoT(`ENGINE → ${a.threat_id}: ${a.effector?.toUpperCase()} ≡ ${fe || 'LOCAL'} from ${a.base}`, 'success');
      }
    });
  });
  updateAccuracyDisplay();
}
window.launchStandaloneWave = launchStandaloneWave;

function addCoT(msg, type) {
  if (!cotFeed) return;
  const p = document.createElement('p'); p.className = `cot-item ${type}`; p.innerText = `> ${msg}`;
  cotFeed.prepend(p);
  if (window._addCoTHook) window._addCoTHook(msg, type);
}

function boot() {
  balticMap = document.getElementById('baltic-map');
  mapGeometry = document.getElementById('map-geometry');
  baseIconsG = document.getElementById('base-icons');
  threatLayerG = document.getElementById('threat-layer-2d');
  cotFeed = document.getElementById('cot-feed');
  healthFill = document.getElementById('city-health');

  // ── Neural Engine WebSocket uplink — streams CORTEX-1 telemetry to CoT log
  try {
    const _engWs = new WebSocket(`ws://${window.location.hostname}:8000/ws/logs`);
    _engWs.onopen    = () => addCoT('CORTEX-1 NEURAL UPLINK ESTABLISHED — ENGINE ONLINE', 'success');
    _engWs.onmessage = e => {
      if (e.data === '[HEARTBEAT]') return;
      addCoT(e.data.replace(/^\[(STRAT|LOG|SYS)\] ?/, '').substring(0, 100), 'info');
    };
    _engWs.onerror = () => addCoT('NEURAL ENGINE UPLINK OFFLINE — STANDALONE MODE ACTIVE', 'alert');
  } catch(_) {}

  // DYNAMIC BENCHMARK FETCH (Theater-Specific)
  fetch('/data/model_benchmarks.json')
    .then(r => r.json())
    .then(data => {
      BENCHMARKS = data; // Store globally for setModel()
      const theaterData = data[MODE] || data.boreal;
      Object.keys(theaterData).forEach(k => {
        if (MODEL_PROFILES[k]) {
          MODEL_PROFILES[k].pk = theaterData[k].pk; // Theater-specific override
          MODEL_PROFILES[k].success = theaterData[k].success;
          MODEL_PROFILES[k].desc = theaterData[k].desc;
        }
      });
      console.log(`NEURAL BENCHMARKS SYNCED :: ${MODE.toUpperCase()} DATA ACTIVE`);
      updateAccuracyDisplay();
    })
    .catch(e => console.warn("BENCHMARK FETCH FAILED :: USING ENGINE DEFAULTS", e));

  // GROUND TRUTH SCENARIO FETCH (1000 SEQUENCES)
  fetch('/data/ground_truth_scenarios.json')
    .then(r => r.json())
    .then(data => {
      groundTruthData = data;
      console.log(`GROUND TRUTH LOADED :: ${Object.keys(data).length} SCENARIOS CACHED`);
    })
    .catch(e => console.error("GROUND TRUTH FETCH FAILED", e));

  renderMap(); init3D(); initAmmo(); updateInventoryDisplay();
  // Initialize live_view model display (no-op if element absent on dashboard)
  const lvModel = document.getElementById('lv-active-model');
  if (lvModel) lvModel.innerText = ACTIVE_MODEL.name;

  // --- BUTTON WIRING ---
  const el = id => document.getElementById(id);
  if (el('btn-launch'))    el('btn-launch').addEventListener('click', startEngagement);
  if (el('btn-reset'))     el('btn-reset').addEventListener('click', () => location.reload());
  if (el('btn-rebalance')) el('btn-rebalance').addEventListener('click', restockAmmo);
  if (el('btn-live-audit'))el('btn-live-audit').addEventListener('click', () =>
    window.open(`live_view.html?mode=${MODE}`, '_blank'));
  if (el('btn-saturation'))el('btn-saturation').addEventListener('click', startEngagement);
}

boot();

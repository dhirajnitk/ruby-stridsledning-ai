// BOREAL ENGINE V8.3 — Strategic Visual Dominance
const urlParams = new URLSearchParams(window.location.search);
const MODE = urlParams.get('mode') || 'boreal';

// --- THEATRE COORDINATES (adaptive per mode) ---
// Sweden: origin=Stockholm, units=km offset from Stockholm
// Boreal: origin=Arktholm, units=arbitrary grid units
let SVG_OX, SVG_OY, SVG_SCALE;
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
// BUG-FIX UI-2: Sweden CSV uses north-positive y (latitude increases upward).
// SVG y increases downward, so Sweden requires negation to render north at top.
function toSvgY(v) { return MODE === 'sweden' ? SVG_OY - v * SVG_SCALE : SVG_OY + v * SVG_SCALE; }
function to3X(v) { return v * 1666; } // 1 unit = 1666m
function to3Z(v) { return v * 1666; }

const SWEDEN_KM = [
  [88, 720], [125, 692], [192, 642], [192, 590], [170, 522], [152, 442], [135, 368],
  [105, 292], [68, 212], [38, 138], [8, 56], [0, 0], [-8, -44], [-42, -82], [-88, -132],
  [-135, -202], [-162, -282], [-170, -338], [-142, -378], [-95, -394], [-62, -384],
  [-85, -330], [-122, -270], [-172, -220], [-232, -200], [-312, -194], [-365, -182],
  [-378, -126], [-358, -56], [-318, 24], [-268, 82], [-218, 152], [-168, 232],
  [-128, 322], [-98, 422], [-68, 532], [-28, 622], [42, 682], [88, 720]
];

const THEATER_DATA = (MODE === 'sweden') ? [
  { type: "BASE", id: "F21", name: "LULEÅ AIR BASE", x: 185, y: 691, sam: 12, effectors: ['LV-103', 'E98', 'RBS70'] },
  { type: "BASE", id: "F16", name: "UPPSALA AIR BASE", x: -27, y: 63, sam: 24, effectors: ['LV-103', 'E98'] },
  { type: "BASE", id: "VID", name: "VIDSEL TEST RANGE", x: 95, y: 728, sam: 48, effectors: ['LV-103', 'LVKV90'] },
  { type: "HVA", id: "STO", name: "STOCKHOLM", x: 0, y: 0, sam: 60, effectors: ['LV-103', 'E98', 'LVKV90'] },
  { type: "BASE", id: "MUS", name: "MUSKÖ NAVAL", x: 4, y: -46, sam: 30, effectors: ['E98', 'METEOR'] },
  { type: "BASE", id: "F7", name: "SÅTENÄS AIR BASE", x: -313, y: -99, sam: 24, effectors: ['E98', 'METEOR'] },
  { type: "BASE", id: "F17", name: "RONNEBY AIR BASE", x: -172, y: -340, sam: 32, effectors: ['LV-103', 'E98'] },
  { type: "BASE", id: "MAL", name: "MALMEN AIR BASE", x: -150, y: -104, sam: 16, effectors: ['E98', 'RBS70'] },
  { type: "BASE", id: "KRL", name: "KARLSKRONA NAVAL", x: -153, y: -352, sam: 20, effectors: ['E98', 'LVKV90'] },
  { type: "BASE", id: "GOT", name: "GOTLAND VISBY HUB", x: 16, y: -186, sam: 40, effectors: ['LV-103', 'E98', 'RBS70'] },
  { type: "HVA", id: "GBG", name: "GOTHENBURG PORT", x: -364, y: -180, sam: 30, effectors: ['E98', 'LVKV90'] }
] : [
  // BOREAL (Extracted from the-boreal-passage-map.svg)
  { type: "BASE", id: "NVB", name: "NORTHERN VANGUARD", x: 119, y: 197, sam: 40, effectors: ['PAC3', 'NASAMS', 'HELWS'] },
  { type: "BASE", id: "HRC", name: "HIGHRIDGE COMMAND", x: 503, y: 41, sam: 30, effectors: ['THAAD', 'PAC3'] },
  { type: "BASE", id: "BWP", name: "BOREAL WATCH POST", x: 695, y: 227, sam: 50, effectors: ['NASAMS', 'CRAM'] },
  { type: "HVA", id: "ARK", name: "ARKTHOLM CAPITAL", x: 251, y: 57, sam: 100, effectors: ['THAAD', 'PAC3', 'NASAMS', 'CRAM'] },
  { type: "HVA", id: "VAL", name: "VALBREK", x: 854, y: 128, sam: 60, effectors: ['PAC3', 'HELWS'] },
  { type: "HVA", id: "NRD", name: "NORDVIK", x: 84, y: 194, sam: 40, effectors: ['NASAMS', 'CRAM'] },
  // SOUTH SIDE
  { type: "BASE", id: "FWS", name: "FIREWATCH STATION", x: 839, y: 639, sam: 24, domain: "KINETIC" },
  { type: "BASE", id: "SRB", name: "SOUTHERN REDOUBT", x: 193, y: 739, sam: 16, domain: "KINETIC" },
  { type: "BASE", id: "SPB", name: "SPEAR POINT BASE", x: 551, y: 497, sam: 20, domain: "KINETIC" },
  { type: "HVA", id: "MER", name: "MERIDIA CAPITAL", x: 735, y: 725, sam: 40, effectors: ['THAAD', 'PAC3', 'NASAMS'] },
  { type: "HVA", id: "CAL", name: "CALLHAVEN", x: 58, y: 690, sam: 28, effectors: ['PAC3', 'NASAMS'] },
  { type: "HVA", id: "SOL", name: "SOLANO", x: 346, y: 742, sam: 28, effectors: ['PAC3', 'NASAMS'] },
  // TERRAIN POLYGONS (Sync from Boreal_passage_coordinates.csv)
  { type: "TERRAIN", id: "TN1", name: "NORTH MAINLAND", side: "north", poly: [[0, 0], [1000, 0], [1000, 170], [920, 188], [860, 174], [800, 170], [742, 205], [678, 190], [616, 178], [556, 212], [488, 194], [428, 188], [366, 220], [302, 192], [236, 200], [178, 230], [118, 204], [54, 212], [0, 228]] },
  { type: "TERRAIN", id: "TN2", name: "SOUTH MAINLAND", side: "south", poly: [[0, 780], [1000, 780], [1000, 640], [948, 616], [882, 628], [818, 642], [756, 608], [688, 622], [624, 640], [560, 606], [492, 626], [428, 646], [362, 612], [294, 622], [232, 648], [168, 618], [98, 630], [30, 648], [0, 638]] },
  { type: "TERRAIN", id: "TN3", name: "STRAIT ISLAND W", side: "north", poly: [[355, 268], [378, 256], [410, 258], [424, 278], [436, 296], [426, 322], [406, 328], [386, 334], [362, 318], [354, 298]] },
  { type: "TERRAIN", id: "TN4", name: "STRAIT ISLAND E", side: "north", poly: [[678, 214], [692, 204], [710, 208], [716, 224], [722, 238], [712, 254], [696, 256], [680, 258], [668, 244], [668, 228]] },
  { type: "ZONE", id: "BST", name: "BOREAL STRAIT", x: 500, y: 400, subtype: "water" },
];

// --- EFFECTOR DEFINITIONS (Audited per NATO/Sweden Doctrine) ---
const EFFECTORS = {
  sweden: {
    // LV-103 (PAC-3 MSE) is the ONLY system capable of engaging MARVs in Swedish inventory
    // E98 (IRIS-T SLS) is short-range air defense — cannot engage ballistic MARVs
    'LV-103': { name: 'Patriot PAC-3 MSE', range: 120000, type: 'KINETIC', color: '#00f2ff', cost: 400, pk: { HYPERSONIC: 0.65, BALLISTIC: 0.7, MARV: 0.75, MIRV: 0.70, CRUISE: 0.95, FIGHTER: 0.95, LOITER: 0.8 } },
    'E98': { name: 'IRIS-T SLS', range: 12000, type: 'KINETIC', color: '#00ff88', cost: 40, pk: { HYPERSONIC: 0.1, BALLISTIC: 0.2, MARV: 0.04, MIRV: 0.04, CRUISE: 0.8, FIGHTER: 0.8, LOITER: 0.9 } },
    'NIMBRIX': { name: 'Saab Nimbrix (C-UAS)', range: 5000, type: 'KINETIC', color: '#ffff00', cost: 3, pk: { DRONE: 0.98, LOITER: 0.95, CRUISE: 0.1, MARV: 0.0, MIRV: 0.0 } },
    'LIDS-EW': { name: 'LIDS EW Jammer', range: 8000, type: 'LASER', color: '#ff00ff', cost: 1, pk: { DRONE: 0.85, LOITER: 0.70, MARV: 0.0, MIRV: 0.0 } },
    'METEOR': { name: 'Meteor BVRAAM', range: 150000, type: 'AIR-AIR', color: '#ffffff', cost: 200, pk: { HYPERSONIC: 0.5, BALLISTIC: 0.3, MARV: 0.15, MIRV: 0.10, CRUISE: 0.85, FIGHTER: 0.98, LOITER: 0.2 } }
  },
  boreal: {
    // THAAD & PAC3 are the ONLY systems capable of engaging MARVs/MIRVs
    // NASAMS/NASAMS has minimal Pk vs maneuvering RVs — wrong altitude/speed class
    // CRAM/HELWS/COYOTE have ZERO capability vs ballistic MARVs
    'THAAD': { name: 'THAAD (Upper-Tier)', range: 200000, type: 'KINETIC', color: '#00f2ff', cost: 800, pk: { HYPERSONIC: 0.8, BALLISTIC: 0.98, MARV: 0.80, MIRV: 0.75, CRUISE: 0.4, FIGHTER: 0.3, LOITER: 0.1 } },
    'PAC3': { name: 'Patriot PAC-3 MSE', range: 120000, type: 'KINETIC', color: '#00f2ff', cost: 400, pk: { HYPERSONIC: 0.7, BALLISTIC: 0.95, MARV: 0.75, MIRV: 0.70, CRUISE: 0.95, FIGHTER: 0.9, LOITER: 0.8 } },
    'NASAMS': { name: 'NASAMS (AMRAAM)', range: 40000, type: 'KINETIC', color: '#00ff88', cost: 100, pk: { HYPERSONIC: 0.5, BALLISTIC: 0.5, MARV: 0.12, MIRV: 0.10, CRUISE: 0.88, FIGHTER: 0.9, LOITER: 0.6 } },
    'HELWS': { name: 'HELWS Laser Weapon', range: 5000, type: 'LASER', color: '#ffff00', cost: 5, pk: { LOITER: 0.9, DRONE: 0.95, CRUISE: 0.2, MARV: 0.0, MIRV: 0.0 } },
    'CRAM': { name: 'C-RAM Phalanx', range: 1500, type: 'KINETIC', color: '#ff8800', cost: 10, pk: { CRUISE: 0.7, LOITER: 0.8, DRONE: 0.9, MARV: 0.0, MIRV: 0.0 } },
    'COYOTE2': { name: 'RTX Coyote Block 2+', range: 15000, type: 'KINETIC', color: '#00ffaa', cost: 5, pk: { DRONE: 0.95, LOITER: 0.95, CRUISE: 0.3, MARV: 0.0, MIRV: 0.0 } },
    'MEROPS': { name: 'Merops Interceptor', range: 3000, type: 'KINETIC', color: '#ffcc00', cost: 2, pk: { DRONE: 0.95, LOITER: 0.90, MARV: 0.0, MIRV: 0.0 } },
    'COYOTE3': { name: 'Coyote B3 (Non-Kin)', range: 10000, type: 'LASER', color: '#ff00ff', cost: 1, pk: { DRONE: 0.90, LOITER: 0.80, MARV: 0.0, MIRV: 0.0 } }
  }
};

// Maps backend engine effector keys → frontend EFFECTORS keys per theater
const ENGINE_EFF_MAP = {
  boreal: { 'patriot-pac3': 'PAC3', 'nasams': 'NASAMS', 'thaad': 'THAAD', 'iris-t-sls': 'PAC3', 'coyote-block2': 'COYOTE2', 'merops-interceptor': 'MEROPS', 'saab-nimbrix': 'COYOTE3', 'lids-ew': 'COYOTE3', 'meteor': 'PAC3' },
  sweden: { 'patriot-pac3': 'LV-103', 'nasams': 'LV-103', 'iris-t-sls': 'E98', 'meteor': 'METEOR', 'saab-nimbrix': 'NIMBRIX', 'lids-ew': 'LIDS-EW', 'thaad': 'LV-103' }
};
// Active doctrine key, updated by setDoctrine() and used in callEngine()
window._ACTIVE_DOCTRINE = 'balanced';

// Unified Strategic Sync Channel
const SAAB_CH = new BroadcastChannel('saab_kinetic_v8');
const SYNC_STATE_KEY = 'saab_last_state_sync';
const SYNC_INVENTORY_KEY = 'saab_last_inventory_sync';
const SESSION_ACTIVE_KEY = 'saab_session_active';
const SESSION_SNAPSHOT_KEY = 'saab_live_session_state';
const LAUNCH_REQUEST_KEY = 'saab_launch_request';

function safeSetStorage(key, value) {
  try { localStorage.setItem(key, value); } catch (_) {}
}

function safeGetStorage(key) {
  try { return localStorage.getItem(key); } catch (_) { return null; }
}

function cacheInventorySync(payload) {
  safeSetStorage(SYNC_INVENTORY_KEY, JSON.stringify(payload));
}

function cacheStateSync(payload) {
  safeSetStorage(SYNC_STATE_KEY, JSON.stringify(payload));
}

function getCachedStateSync() {
  const raw = safeGetStorage(SYNC_STATE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch (_) { return null; }
}

function getCachedInventorySync() {
  const raw = safeGetStorage(SYNC_INVENTORY_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch (_) { return null; }
}

function serializeInterceptor(int) {
  return {
    baseId: int.baseId || null,
    effKey: int._effKey || null,
    pos: { x: int.pos?.x || 0, y: int.pos?.y || 0, z: int.pos?.z || 0 },
    hit: !!int.hit,
    done: !!int.done,
    expired: !!int.expired,
  };
}

function serializeThreatState(t) {
  return {
    id: t.id,
    wkey: t.wdef?.type || 'CRUISE',
    targetId: t.targetNode?.id || null,
    targetName: t.targetNode?.name || null,
    engineAssignment: t.engineAssignment || null,
    pos: { x: t.pos?.x || 0, y: t.pos?.y || 0, z: t.pos?.z || 0 },
    vel: { x: t.vel?.x || 0, y: t.vel?.y || 0, z: t.vel?.z || 0 },
    spawnPos: { x: t._spawnPos?.x || 0, y: t._spawnPos?.y || 0, z: t._spawnPos?.z || 0 },
    hit: !!t.hit,
    marvActive: !!t.marvActive,
    mirvReleased: !!t.mirvReleased,
    dogOutcome: t.dogOutcome || null,
    rtbActive: !!t.rtbActive,
    frame: t._frame || 0,
    totalFrames: t._totalFrames || 300,
    jinkPhase: t.jinkPhase || 0,
    jinkV: { x: t.jinkV?.x || 0, z: t.jinkV?.z || 0 },
    path: (t.path || []).map(p => ({ x: p.x || 0, y: p.y || 0, z: p.z || 0 })),
    interceptors: (t.interceptors || []).map(serializeInterceptor),
  };
}

function saveSessionSnapshot() {
  if (window.isMirror) return;
  const snapshot = {
    version: 1,
    mode: MODE,
    currentTheater,
    currentScenarioIdx,
    currentWaveIdx,
    waveTransitioning,
    isSimulating,
    cityHealth,
    engineMode: ENGINE_MODE,
    activeDoctrine: window._ACTIVE_DOCTRINE,
    stats,
    ammo,
    baseHealth,
    destroyedBases: Array.from(destroyedBases),
    pendingApprovals: Array.from(pendingApprovals),
    rejectedThreats: Array.from(rejectedThreats),
    simFrames: window.simFrames || 0,
    waveTransitionStartedAt: window.waveTransitionStartedAt || 0,
    threats: threats.filter(t => !t._disposed).map(serializeThreatState),
  };
  safeSetStorage(SESSION_SNAPSHOT_KEY, JSON.stringify(snapshot));
}

function restoreSessionSnapshot() {
  if (safeGetStorage(SESSION_ACTIVE_KEY) !== '1') return false;
  const raw = safeGetStorage(SESSION_SNAPSHOT_KEY);
  if (!raw) return false;
  let snapshot = null;
  try { snapshot = JSON.parse(raw); } catch (_) { return false; }
  if (!snapshot || !Array.isArray(snapshot.threats)) return false;

  const targetMode = snapshot.mode || MODE;
  if (targetMode && targetMode !== currentTheater) {
    currentTheater = targetMode;
    const sel = document.getElementById('sel-theater');
    if (sel) sel.value = currentTheater;
    renderMap();
    init3D();
  } else {
    renderMap();
    init3D();
  }

  initAmmo();
  Object.keys(snapshot.ammo || {}).forEach(id => { ammo[id] = snapshot.ammo[id]; });
  Object.keys(snapshot.baseHealth || {}).forEach(id => { baseHealth[id] = snapshot.baseHealth[id]; });
  destroyedBases.clear();
  (snapshot.destroyedBases || []).forEach(id => destroyedBases.add(id));

  threats.forEach(t => t.dispose());
  threats = [];

  currentScenarioIdx = snapshot.currentScenarioIdx || 0;
  currentWaveIdx = snapshot.currentWaveIdx || 0;
  waveTransitioning = !!snapshot.waveTransitioning;
  window.waveTransitionStartedAt = snapshot.waveTransitionStartedAt || 0;
  window.simFrames = snapshot.simFrames || 0;
  isSimulating = !!snapshot.isSimulating;
  cityHealth = snapshot.cityHealth ?? cityHealth;
  stats = snapshot.stats || stats;
  stats.kills = stats.intercepted || 0;
  ENGINE_MODE = snapshot.engineMode || ENGINE_MODE;
  if (snapshot.activeDoctrine) window._ACTIVE_DOCTRINE = snapshot.activeDoctrine;
  pendingApprovals.clear();
  (snapshot.pendingApprovals || []).forEach(id => pendingApprovals.add(id));
  rejectedThreats.clear();
  (snapshot.rejectedThreats || []).forEach(id => rejectedThreats.add(id));

  (snapshot.threats || []).forEach((ts, idx) => {
    const target = THEATER_DATA.find(n => n.id === ts.targetId) || THEATER_DATA.find(n => n.name === ts.targetName) || THEATER_DATA[0];
    const threat = new Threat(ts.id, ts.wkey || 'CRUISE', target, idx);
    threat.engineAssignment = ts.engineAssignment || null;
    threat.pos.set(ts.pos.x, ts.pos.y, ts.pos.z);
    threat.vel.set(ts.vel.x, ts.vel.y, ts.vel.z);
    threat._spawnPos = new THREE.Vector3(ts.spawnPos?.x || ts.pos.x, ts.spawnPos?.y || ts.pos.y, ts.spawnPos?.z || ts.pos.z);
    threat.hit = !!ts.hit;
    threat.marvActive = !!ts.marvActive;
    threat.mirvReleased = !!ts.mirvReleased;
    threat.dogOutcome = ts.dogOutcome || null;
    threat.rtbActive = !!ts.rtbActive;
    threat._frame = ts.frame || 0;
    threat._totalFrames = ts.totalFrames || 300;
    threat.jinkPhase = ts.jinkPhase || 0;
    threat.jinkV = { x: ts.jinkV?.x || 0, z: ts.jinkV?.z || 0 };
    threat.path = (ts.path || []).map(p => new THREE.Vector3(p.x, p.y, p.z));
    threat.interceptors.forEach(int => int.dispose());
    threat.interceptors = [];
    (ts.interceptors || []).forEach(is => {
      const base = BASES[is.baseId] || Object.values(BASES)[0];
      const int = new Interceptor(base, is.effKey || 'PAC3');
      int.baseId = is.baseId || base?.id || null;
      int._effKey = is.effKey || int._effKey;
      int.pos.set(is.pos.x, is.pos.y, is.pos.z);
      if (int.mesh) int.mesh.position.copy(int.pos);
      int.hit = !!is.hit;
      int.done = !!is.done;
      int.expired = !!is.expired;
      int._threatType = threat.wdef?.type || 'CRUISE';
      threat.interceptors.push(int);
    });
    threats.push(threat);
  });

  if (waveTransitioning && isSimulating) {
    const startedAt = window.waveTransitionStartedAt || Date.now();
    const remaining = Math.max(0, 3000 - (Date.now() - startedAt));
    if (window.waveTransitionTimer) clearTimeout(window.waveTransitionTimer);
    window.waveTransitionTimer = setTimeout(() => {
      waveTransitioning = false;
      window.waveTransitionStartedAt = 0;
      launchWave();
    }, remaining);
  } else if (isSimulating && !waveTransitioning && threats.length === 0) {
    // Snapshot was captured in the gap between wave-end and launchWave() — resume next wave
    setTimeout(() => launchWave(), 200);
  }

  updateAccuracyDisplay();
  updateInventoryDisplay();
  if (healthFill) healthFill.style.width = `${Math.max(0, cityHealth)}%`;
  return true;
}

function consumeLaunchRequest() {
  if (safeGetStorage(LAUNCH_REQUEST_KEY) !== '1') return false;
  safeSetStorage(LAUNCH_REQUEST_KEY, '0');
  if (!isSimulating) {
    startEngagement();
    return true;
  }
  return false;
}

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
  CRUISE: { speed: 600, color3: '#ff3e3e', hex3: 0xff3e3e, r2d: 5, label: 'CRUISE MISSILE', type: 'CRUISE' },
  HYPERSONIC: { speed: 2200, color3: '#ffcc00', hex3: 0xffcc00, r2d: 4, label: 'HYPERSONIC GLIDE', type: 'HYPERSONIC' },
  LOITER: { speed: 300, color3: '#ff00ff', hex3: 0xff00ff, r2d: 4, label: 'LOITERING MUNITION', type: 'LOITER' },
  BALLISTIC: { speed: 1400, color3: '#ff5500', hex3: 0xff5500, r2d: 6, label: 'BALLISTIC MISSILE', type: 'BALLISTIC' },
  // ── Advanced trajectory types ─────────────────────────────────────────────
  // MARV/MIRV use their own threat type so Pk tables can differentiate from standard BALLISTIC
  MARV: {
    speed: 1200, color3: '#ff8800', hex3: 0xff8800, r2d: 5, label: 'MARV (Maneuvering RV)', type: 'MARV',
    isMarv: true, marvTriggerKm: 100, marvJinkFrac: 0.4
  },
  MIRV: {
    speed: 1100, color3: '#ff3300', hex3: 0xff3300, r2d: 7, label: 'MIRV BUS', type: 'MIRV',
    isMirv: true, mirvCount: 3, mirvReleaseFrac: 0.45
  },
  FIGHTER_DOG: {
    speed: 1800, color3: '#00ccff', hex3: 0x00ccff, r2d: 5, label: 'FIGHTER (Dogfight)', type: 'FIGHTER',
    isDogfight: true, dogWinProb: 0.30, canRtb: true
  },
};

const WAVE_SEQ = [
  { name: 'OPENING PROBE', weapons: ['CRUISE'], count: 4 },
  { name: 'MIXED SATURATION', weapons: ['CRUISE', 'LOITER'], count: 8 },
  { name: 'HYPERSONIC STRIKE', weapons: ['HYPERSONIC'], count: 4 },
  { name: 'MARV/MIRV ASSAULT', weapons: ['MARV', 'MIRV'], count: 4 },
  { name: 'FIGHTER WAVE', weapons: ['FIGHTER_DOG', 'CRUISE'], count: 6 },
  { name: 'COORDINATED ASSAULT', weapons: ['BALLISTIC', 'CRUISE'], count: 10 },
  { name: 'MAX SATURATION', weapons: ['HYPERSONIC', 'LOITER', 'CRUISE', 'MARV'], count: 15 },
];

let ammo = {};
let baseHealth = {};        // 0–100 structural integrity per base/HVA node
let destroyedBases = new Set(); // IDs of fully destroyed nodes
let balticMap, mapGeometry, baseIconsG, threatLayerG, cotFeed, healthFill;
let cityHealth = 100, isSimulating = false, currentScenarioIdx = 0, currentWaveIdx = 0, waveTransitioning = false;
let currentTheater = MODE; // active theater/mode key; persisted in session snapshot
let BENCHMARKS = {};
let threats = [];
let rejectedThreats = new Set(); // Tracks HITL-rejected threat IDs so they aren't re-queued

// Expose live state to dashboard panels (manual override, HITL queue) via getters
Object.defineProperty(window, 'threats', { get: () => threats, configurable: true });
Object.defineProperty(window, 'BASES', { get: () => BASES, configurable: true });
Object.defineProperty(window, 'ammo', { get: () => ammo, configurable: true });
Object.defineProperty(window, 'baseHealth', { get: () => baseHealth, configurable: true });
Object.defineProperty(window, 'destroyedBases', { get: () => destroyedBases, configurable: true });
Object.defineProperty(window, 'EFFECTORS', { get: () => EFFECTORS, configurable: true });

// --- LIVE ACCURACY TRACKING ---
let stats = { fired: 0, intercepted: 0, missed: 0, impacts: 0, totalThreats: 0, kills: 0 };
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

  if (el('stat-tactical')) el('stat-tactical').innerText = tacAcc + (tacAcc === '--' ? '' : '%');
  if (el('stat-strategic')) el('stat-strategic').innerText = strAcc + (strAcc === '--' ? '' : '%');
  if (el('stat-fired')) el('stat-fired').innerText = stats.fired;
  if (el('stat-intercepts')) el('stat-intercepts').innerText = stats.intercepted;
  if (el('stat-impacts')) el('stat-impacts').innerText = stats.impacts;
  if (el('stat-missed')) el('stat-missed').innerText = stats.missed;

  // LIVE MC TRUTH BINDING
  const truthVal = (ACTIVE_MODEL.pk * 100).toFixed(1) + '%';
  if (el('mc-tac-acc')) el('mc-tac-acc').innerText = truthVal;
  if (el('mc-str-acc')) el('mc-str-acc').innerText = (ACTIVE_MODEL.success || '100%');
  if (el('mc-avg-score')) {
    const raw = (ACTIVE_MODEL.success || '942/1000').split('/')[0];
    const baseScore = parseFloat(raw) / 10;
    el('mc-avg-score').innerText = (baseScore + (Math.random() * 2)).toFixed(1);
  }
  if (el('acc-badge')) el('acc-badge').innerText = truthVal + ' MC TRUTH';

  const tc = el('threat-count');
  if (tc) tc.innerText = threats.filter(t => !t.hit).length + ' ACTIVE';
}

// SAAB_CH is declared once at the top of the file — no redeclaration here
window.isMirror = !window.location.pathname.includes('dashboard.html');

SAAB_CH.onmessage = e => {
  if (e.data?.type === 'LAUNCH') startEngagement();
  if (e.data?.type === 'DEMO') triggerDemo(e.data.id);
  if (e.data?.type === 'STATE_REQUEST' && !window.isMirror) {
    if (isSimulating && threats && threats.length) {
      // Sim is live — send fresh state immediately so mirrors get current positions
      broadcastState();
    } else {
      // Sim not running — replay last cached state from localStorage
      const cachedInventory = getCachedInventorySync();
      const cachedState = getCachedStateSync();
      if (cachedInventory) SAAB_CH.postMessage(cachedInventory);
      if (cachedState) SAAB_CH.postMessage(cachedState);
    }
  }
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
        const int = new Interceptor(BASES[e.data.baseId], e.data.effector || 'PAC3');
        int.baseId = e.data.baseId;
        int._effKey = e.data.effector || int._effKey;
        t.interceptors.push(int);
        stats.fired++;
      }
    }
  }
};

window.startEngagement = startEngagement;
window.launchWave = launchWave;
window.restockAmmo = restockAmmo;
window.addEventListener('saab-launch', () => startEngagement());

function wireDashboardControls() {
  if (window._dashboardControlsWired) return;
  window._dashboardControlsWired = true;
  const el = id => document.getElementById(id);
  if (el('btn-launch')) el('btn-launch').addEventListener('click', startEngagement);
  if (el('btn-reset')) el('btn-reset').addEventListener('click', () => location.reload());
  if (el('btn-rebalance')) el('btn-rebalance').addEventListener('click', restockAmmo);
  if (el('btn-live-audit')) el('btn-live-audit').addEventListener('click', () =>
    window.open(`live_view.html?mode=${MODE}`, '_blank'));
  if (el('btn-saturation')) el('btn-saturation').addEventListener('click', startEngagement);
}

// --- INITIALIZATION ---
function initAmmo() {
  THEATER_DATA.forEach(n => {
    if (n.type === 'BASE' || n.type === 'HVA') {
      ammo[n.id] = n.sam || 0;
      baseHealth[n.id] = 100;
    }
  });
  destroyedBases.clear();
  // Re-render map to restore any destroyed-base visuals
  if (baseIconsG) renderMap();
}

function restockAmmo() {
  Object.keys(BASES).forEach(id => {
    if (destroyedBases.has(id)) return; // Cannot restock a destroyed base
    const cap = BASES[id].sam || 0;
    if (cap <= 0) return;
    ammo[id] = Math.min(cap, (ammo[id] || 0) + Math.ceil(cap * 0.5));
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

  if (n1) n1.innerText = destroyedBases.has(b1) ? '⚠ DESTROYED' : (ammo[b1] || 0);
  if (n2) n2.innerText = destroyedBases.has(b2) ? '⚠ DESTROYED' : (ammo[b2] || 0);
  if (n1Lbl) n1Lbl.innerText = displayNames[b1] || b1;
  if (n2Lbl) n2Lbl.innerText = displayNames[b2] || b2;
  if (res) res.innerText = total;

  // Full theater inventory grid (dashboard only)
  updateTheaterInventory();
}

// Full per-base theater inventory grid — writes to #theater-inventory-grid
function updateTheaterInventory() {
  const grid = document.getElementById('theater-inventory-grid');
  if (!grid) return;
  const nodes = Object.values(BASES);
  if (!nodes.length) return;
  grid.innerHTML = nodes.map(b => {
    const destroyed = destroyedBases.has(b.id);
    const hp = destroyed ? 0 : (baseHealth[b.id] ?? 100);
    const sam = destroyed ? 0 : (ammo[b.id] ?? 0);
    const cap = b.sam || 0;
    const samPct = cap > 0 ? Math.round((sam / cap) * 100) : 0;
    const hpCol = destroyed ? '#555' : hp > 60 ? '#00ff88' : hp > 30 ? '#ffcc00' : '#ff3e3e';
    const samCol = destroyed ? '#555' : samPct > 60 ? '#00f2ff' : samPct > 25 ? '#ffcc00' : '#ff3e3e';
    const typeIcon = b.type === 'HVA' ? '⬟' : '▣';
    const statusTxt = destroyed ? '<span style="color:#ff3e3e;font-weight:bold;">DESTROYED</span>' :
      `<span style="color:${samCol}">${sam}/${cap} SAM</span>`;
    return `<div class="tinv-row${destroyed ? ' tinv-destroyed' : ''}">
      <span class="tinv-id">${typeIcon} ${b.id}</span>
      <span class="tinv-name">${b.name}</span>
      <div class="tinv-bars">
        <div class="tinv-bar-wrap" title="Structural Integrity: ${hp}%">
          <div class="tinv-bar" style="width:${hp}%;background:${hpCol}"></div>
        </div>
        <div class="tinv-bar-wrap" title="SAM: ${sam}/${cap}">
          <div class="tinv-bar" style="width:${samPct}%;background:${samCol}"></div>
        </div>
      </div>
      <span class="tinv-stat">${statusTxt}</span>
    </div>`;
  }).join('');

  // Broadcast inventory to 3D simulator
  const totalSAM = Object.values(ammo).reduce((a, b) => a + b, 0);
  SAAB_CH.postMessage({ type: 'INVENTORY_SYNC', totalSAM, impacts: stats.impacts, kills: stats.intercepted });
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
    // Draw a border polygon connecting all boreal nodes (exclude TERRAIN — no x/y coords)
    const baseNodes = THEATER_DATA.filter(n => n.type === 'BASE' || n.type === 'HVA' || n.type === 'ZONE');
    const sorted = [...baseNodes].sort((a, b) => Math.atan2(a.y - 650, a.x - 800) - Math.atan2(b.y - 650, b.x - 800));
    const pts = sorted.map(n => `${toSvgX(n.x)},${toSvgY(n.y)}`).join(' L');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M${pts} Z`);
    path.setAttribute('fill', 'rgba(0, 242, 255, 0.03)');
    path.setAttribute('stroke', 'rgba(0, 242, 255, 0.5)');
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-dasharray', '8 4');
    mapGeometry.appendChild(path);

    // Render Terrain Polygons
    THEATER_DATA.forEach(n => {
      if (n.type === 'TERRAIN' && n.poly) {
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        const pts = n.poly.map(pt => `${toSvgX(pt[0])},${toSvgY(pt[1])}`).join(' ');
        p.setAttribute('points', pts);
        p.setAttribute('fill', n.side === 'north' ? 'rgba(0, 242, 255, 0.08)' : 'rgba(255, 62, 62, 0.08)');
        p.setAttribute('stroke', n.side === 'north' ? 'rgba(0, 242, 255, 0.2)' : 'rgba(255, 62, 62, 0.2)');
        p.setAttribute('stroke-width', '1');
        mapGeometry.appendChild(p);
      }
    });

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

  // Skip TERRAIN nodes here — they are rendered as polygons above, they have no x/y point
  THEATER_DATA.filter(node => node.type !== 'TERRAIN').forEach(node => {
    const sx = toSvgX(node.x), sy = toSvgY(node.y);
    const isZone = node.type === 'ZONE';
    const col = node.type === 'HVA' ? '#00ff88' : (isZone ? 'rgba(0,242,255,0.4)' : '#00f2ff');
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');

    if (isZone) {
      // Draw tactical crosshair for terrain nodes
      const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line1.setAttribute('x1', sx - 5); line1.setAttribute('y1', sy); line1.setAttribute('x2', sx + 5); line1.setAttribute('y2', sy);
      line1.setAttribute('stroke', col); line1.setAttribute('stroke-width', '1');
      g.appendChild(line1);
      const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line2.setAttribute('x1', sx); line2.setAttribute('y1', sy - 5); line2.setAttribute('x2', sx); line2.setAttribute('y2', sy + 5);
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
  renderThreatVectors();
}

// ── JS-driven MARV threat track animation with PAC-3 intercept events ───────
// Replaces declarative SVG animateMotion so we can show actual intercept:
//  • MARV travels along track → PAC-3 rises from the base → explosion at 75% → repeat
//  • Clicking MARV label opens kinetic_chase.html pre-loaded with that engagement
// ── Quadratic bezier helper ──────────────────────────────────────────────────
function _qbez(t, x1, y1, cx, cy, x2, y2) {
  const mt = 1 - t;
  return {
    x: mt * mt * x1 + 2 * mt * t * cx + t * t * x2,
    y: mt * mt * y1 + 2 * mt * t * cy + t * t * y2
  };
}

function renderThreatVectors() {
  if (!threatLayerG) return;
  const svgNS = 'http://www.w3.org/2000/svg';
  Array.from(threatLayerG.querySelectorAll('.threat-track')).forEach(el => el.remove());
  if (window._marvAnimId) cancelAnimationFrame(window._marvAnimId);

  // intercept fraction = where PAC-3 kills the MARV (0–1 along track)
  const INTERCEPT_FRAC = 0.72;

  let tracks;
  if (MODE === 'sweden') {
    tracks = [
      { x1: 1000, y1: 270, x2: 545, y2: 530, bx: 545, by: 530, label: 'MARV-α', dur: 5.5, delay: 0, kIdx: null },
      { x1: 1000, y1: 460, x2: 472, y2: 699, bx: 472, by: 699, label: 'MARV-β', dur: 6.5, delay: 2, kIdx: null },
      { x1: 1000, y1: 150, x2: 553, y2: 619, bx: 553, by: 619, label: 'MARV-γ', dur: 7.5, delay: 3.8, kIdx: null },
    ];
  } else {
    tracks = [
      { x1: 185, y1: 10, x2: 58, y2: 690, bx: 58, by: 690, label: 'MARV-1', dur: 5.5, delay: 0, kIdx: 10 },
      { x1: 430, y1: 5, x2: 346, y2: 742, bx: 346, by: 742, label: 'MARV-2', dur: 6.5, delay: 2.2, kIdx: 11 },
      { x1: 765, y1: 10, x2: 735, y2: 725, bx: 735, by: 725, label: 'MARV-3', dur: 7.5, delay: 4.0, kIdx: 9 },
    ];
  }

  const PAUSE = 2.2;

  tracks.forEach(tr => {
    tr.ix = tr.x1 + (tr.x2 - tr.x1) * INTERCEPT_FRAC;
    tr.iy = tr.y1 + (tr.y2 - tr.y1) * INTERCEPT_FRAC;
    tr.period = tr.dur + PAUSE;

    // ── Bezier control points ────────────────────────────────────────────
    // MARV track: offset the midpoint perpendicular to track direction (ballistic arc)
    const trkDx = tr.ix - tr.x1, trkDy = tr.iy - tr.y1;
    const trkLen = Math.hypot(trkDx, trkDy) || 1;
    // Perpendicular unit vector (CCW)
    const perpX = -trkDy / trkLen, perpY = trkDx / trkLen;
    const CURVE_FRAC = 0.14;  // 14% of track length as lateral bulge
    tr.cpx = (tr.x1 + tr.ix) / 2 + perpX * trkLen * CURVE_FRAC;
    tr.cpy = (tr.y1 + tr.iy) / 2 + perpY * trkLen * CURVE_FRAC;

    // PAC-3 arc: rises steeply from city then arcs toward intercept
    //   → control point above the midpoint (up in SVG = smaller y)
    const pacDx = tr.ix - tr.bx, pacDy = tr.iy - tr.by;
    const pacLen = Math.hypot(pacDx, pacDy) || 1;
    tr.pacCpx = (tr.bx + tr.ix) / 2 - pacDy * 0.3;    // slight lateral
    tr.pacCpy = (tr.by + tr.iy) / 2 - pacLen * 0.55;  // big upward arc

    // ── Perpendicular direction for terminal MARV jink ───────────────────
    tr.jinkPX = -trkDy / trkLen;
    tr.jinkPY = trkDx / trkLen;

    const g = document.createElementNS(svgNS, 'g');
    g.setAttribute('class', 'threat-track');

    // Dashed bezier track line (full path preview)
    const trackPath = document.createElementNS(svgNS, 'path');
    trackPath.setAttribute('d', `M${tr.x1},${tr.y1} Q${tr.cpx},${tr.cpy} ${tr.ix},${tr.iy}`);
    trackPath.setAttribute('stroke', '#ff3e3e');
    trackPath.setAttribute('stroke-width', '1');
    trackPath.setAttribute('stroke-dasharray', '8 5');
    trackPath.setAttribute('fill', 'none');
    trackPath.setAttribute('opacity', '0.28');
    g.appendChild(trackPath);

    // PAC-3 interceptor dot (cyan)
    const pac3 = document.createElementNS(svgNS, 'circle');
    pac3.setAttribute('r', '3');
    pac3.setAttribute('fill', '#00f2ff');
    pac3.setAttribute('opacity', '0');
    g.appendChild(pac3);
    tr.pac3El = pac3;

    // MARV dot (red/orange)
    const marv = document.createElementNS(svgNS, 'circle');
    marv.setAttribute('r', '4.5');
    marv.setAttribute('fill', '#ff6600');
    marv.setAttribute('opacity', '0');
    g.appendChild(marv);
    tr.marvEl = marv;

    // Explosion flash
    const expl = document.createElementNS(svgNS, 'circle');
    expl.setAttribute('cx', tr.ix); expl.setAttribute('cy', tr.iy);
    expl.setAttribute('r', '0'); expl.setAttribute('fill', '#ffcc00'); expl.setAttribute('opacity', '0');
    g.appendChild(expl); tr.explEl = expl;

    // Explosion ring
    const ring = document.createElementNS(svgNS, 'circle');
    ring.setAttribute('cx', tr.ix); ring.setAttribute('cy', tr.iy);
    ring.setAttribute('r', '0'); ring.setAttribute('fill', 'none');
    ring.setAttribute('stroke', '#ff8800'); ring.setAttribute('stroke-width', '1.5');
    ring.setAttribute('opacity', '0');
    g.appendChild(ring); tr.ringEl = ring;

    // Clickable MARV label
    const kHref = `kinetic_chase.html?base=${tr.kIdx !== null ? tr.kIdx : tr.label}&threat=marv&dir=north&autorun=1`;
    const anchor = document.createElementNS(svgNS, 'a');
    anchor.setAttributeNS('http://www.w3.org/1999/xlink', 'href', kHref);
    anchor.setAttribute('target', '_blank');
    const earlyPos = _qbez(0.1, tr.x1, tr.y1, tr.cpx, tr.cpy, tr.ix, tr.iy);
    const lbl = document.createElementNS(svgNS, 'text');
    lbl.setAttribute('x', earlyPos.x + 7); lbl.setAttribute('y', earlyPos.y - 4);
    lbl.setAttribute('fill', '#ff6600'); lbl.setAttribute('font-size', '7');
    lbl.setAttribute('font-family', 'Orbitron, monospace'); lbl.setAttribute('opacity', '0.9');
    lbl.textContent = `${tr.label} ↗`;
    anchor.appendChild(lbl); g.appendChild(anchor);

    threatLayerG.appendChild(g);
  });

  const startEpoch = performance.now();

  function animTick() {
    const now = performance.now();
    const globalElapsed = (now - startEpoch) / 1000;

    tracks.forEach(tr => {
      const cycleT = (globalElapsed - tr.delay) % tr.period;
      if (globalElapsed < tr.delay || cycleT < 0) {
        tr.marvEl.setAttribute('opacity', '0');
        tr.pac3El.setAttribute('opacity', '0');
        tr.explEl.setAttribute('r', '0'); tr.explEl.setAttribute('opacity', '0');
        tr.ringEl.setAttribute('r', '0'); tr.ringEl.setAttribute('opacity', '0');
        return;
      }

      const travelDur = tr.dur * INTERCEPT_FRAC;
      const pac3StartT = travelDur * 0.28;
      const pac3Dur = travelDur * 0.72;
      const explDur = 0.55;

      if (cycleT < travelDur) {
        const t = cycleT / travelDur;

        // ── MARV: follows bezier curve + sinusoidal terminal jink ────────
        const bp = _qbez(t, tr.x1, tr.y1, tr.cpx, tr.cpy, tr.ix, tr.iy);
        // Terminal jink grows in last 40% of the approach (MARV evades)
        let jx = 0, jy = 0;
        if (t > 0.60) {
          const jt = (t - 0.60) / 0.40;           // 0→1 in terminal phase
          const jAmp = 11 * jt;                     // grows to 11px lateral
          const jinkHz = 2.8;
          const sineVal = Math.sin(jinkHz * cycleT);
          jx = tr.jinkPX * jAmp * sineVal;
          jy = tr.jinkPY * jAmp * sineVal;
        }
        tr.marvEl.setAttribute('cx', bp.x + jx);
        tr.marvEl.setAttribute('cy', bp.y + jy);
        tr.marvEl.setAttribute('opacity', '1');

        // ── PAC-3: arcs upward from base, curves to intercept ────────────
        if (cycleT >= pac3StartT) {
          const p = Math.min((cycleT - pac3StartT) / pac3Dur, 1.0);
          const pp = _qbez(p, tr.bx, tr.by, tr.pacCpx, tr.pacCpy, tr.ix, tr.iy);
          tr.pac3El.setAttribute('cx', pp.x);
          tr.pac3El.setAttribute('cy', pp.y);
          tr.pac3El.setAttribute('opacity', '1');
        } else {
          tr.pac3El.setAttribute('opacity', '0');
        }

        tr.explEl.setAttribute('r', '0'); tr.explEl.setAttribute('opacity', '0');
        tr.ringEl.setAttribute('r', '0'); tr.ringEl.setAttribute('opacity', '0');

      } else if (cycleT < travelDur + explDur) {
        const et = (cycleT - travelDur) / explDur;
        const er = et * 16;
        const op = Math.max(0, 1.0 - et);
        tr.marvEl.setAttribute('opacity', '0');
        tr.pac3El.setAttribute('opacity', '0');
        tr.explEl.setAttribute('r', er);
        tr.explEl.setAttribute('opacity', String(op * 0.95));
        tr.ringEl.setAttribute('r', er * 2.2);
        tr.ringEl.setAttribute('opacity', String(op * 0.65));

      } else {
        tr.marvEl.setAttribute('opacity', '0');
        tr.pac3El.setAttribute('opacity', '0');
        tr.explEl.setAttribute('r', '0'); tr.explEl.setAttribute('opacity', '0');
        tr.ringEl.setAttribute('r', '0'); tr.ringEl.setAttribute('opacity', '0');
      }
    });

    window._marvAnimId = requestAnimationFrame(animTick);
  }
  window._marvAnimId = requestAnimationFrame(animTick);
}

function blastSvg(wx, wy, col) {
  if (!threatLayerG) return;
  const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  c.setAttribute('cx', toSvgX(wx)); c.setAttribute('cy', toSvgY(wy));
  c.setAttribute('r', '2'); c.setAttribute('fill', col); c.setAttribute('opacity', '1');
  threatLayerG.appendChild(c);
  let s = 1;
  const iv = setInterval(() => {
    s += 3; c.setAttribute('r', s); c.setAttribute('opacity', String(1 - s / 30));
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
  l1.setAttribute('x1', sx - sz); l1.setAttribute('y1', sy - sz);
  l1.setAttribute('x2', sx + sz); l1.setAttribute('y2', sy + sz);
  l1.setAttribute('stroke', '#ff3e3e'); l1.setAttribute('stroke-width', '2');
  const l2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  l2.setAttribute('x1', sx + sz); l2.setAttribute('y1', sy - sz);
  l2.setAttribute('x2', sx - sz); l2.setAttribute('y2', sy + sz);
  l2.setAttribute('stroke', '#ff3e3e'); l2.setAttribute('stroke-width', '2');
  g.appendChild(l1); g.appendChild(l2);
  threatLayerG.appendChild(g);
  // Fade out after 4s
  let op = 1;
  const iv = setInterval(() => { op -= 0.05; g.setAttribute('opacity', op); if (op <= 0) { clearInterval(iv); g.remove(); } }, 200);
  setTimeout(() => { clearInterval(iv); g.remove(); }, 4500);
}

// --- BASE DAMAGE / DESTRUCTION VISUALS ---
// Change base dot color to reflect damage level; add destroyed overlay on SVG map
function _getBaseCircle(nodeId) {
  if (!baseIconsG) return null;
  const gs = baseIconsG.querySelectorAll('g');
  for (const g of gs) {
    const txt = g.querySelector('text');
    if (txt && txt.textContent === nodeId) return g.querySelector('circle');
  }
  return null;
}

function markBaseDamaged(nodeId, hpPct) {
  const dot = _getBaseCircle(nodeId);
  if (!dot) return;
  const col = hpPct > 60 ? '#00f2ff' : hpPct > 30 ? '#ffcc00' : '#ff3e3e';
  dot.setAttribute('fill', col);
  dot.setAttribute('filter', `drop-shadow(0 0 4px ${col})`);
}

function markBaseDestroyed(nodeId) {
  const dot = _getBaseCircle(nodeId);
  if (!dot) return;
  // Grey-out the dot and add an X overlay
  dot.setAttribute('fill', '#333');
  dot.setAttribute('filter', 'none');
  dot.setAttribute('stroke', '#ff3e3e');
  dot.setAttribute('stroke-width', '2');
  // Draw an X at the base location
  const node = BASES[nodeId];
  if (!node || !baseIconsG) return;
  const sx = toSvgX(node.x), sy = toSvgY(node.y);
  const sz = 7;
  const gx = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  gx.id = `destroyed-${nodeId}`;
  ['opacity', '0.85'].forEach((a, i, arr) => i % 2 === 0 && gx.setAttribute(a, arr[i + 1]));
  [[sx - sz, sy - sz, sx + sz, sy + sz], [sx + sz, sy - sz, sx - sz, sy + sz]].forEach(coords => {
    const ln = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    ['x1', 'y1', 'x2', 'y2'].forEach((a, i) => ln.setAttribute(a, coords[i]));
    ln.setAttribute('stroke', '#ff3e3e'); ln.setAttribute('stroke-width', '2.5');
    gx.appendChild(ln);
  });
  baseIconsG.appendChild(gx);
  updateInventoryDisplay();
}

// --- BENCHMARK REPLAY ---
// Takes a precomputed scenario (from ground_truth_scenarios.json) and runs it live,
// then compares live engine output vs MC ground truth
let benchGroundTruth = null;

function runBenchmarkScenario(scenarioThreats, groundTruth) {
  threats.forEach(t => t.dispose()); threats = [];
  isSimulating = true; waveTransitioning = false;
  cityHealth = 100; if (healthFill) healthFill.style.width = '100%';
  stats = { fired: 0, intercepted: 0, missed: 0, impacts: 0, totalThreats: 0, kills: 0 };
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
      'bomber': 'CRUISE', 'fast-mover': 'HYPERSONIC', 'drone': 'LOITER',
      'hypersonic': 'HYPERSONIC', 'fighter': 'CRUISE', 'decoy': 'LOITER'
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
  const liveTac = stats.fired > 0 ? (stats.intercepted / stats.fired * 100).toFixed(1) : '0.0';
  const liveStr = stats.totalThreats > 0 ? ((stats.totalThreats - stats.impacts) / stats.totalThreats * 100).toFixed(1) : '0.0';
  const mcTac = (gt.expected_kills / Math.max(1, gt.n_assigned) * 100).toFixed(1);
  const mcStr = ((gt.n_assigned) / Math.max(1, stats.totalThreats) * 100).toFixed(1);

  addCoT('══ BENCHMARK COMPARISON REPORT ══', 'success');
  addCoT(`TACTICAL  :: LIVE ${liveTac}%  vs  MC TRUTH ${mcTac}%  (Δ ${(liveTac - mcTac).toFixed(1)}%)`, liveTac >= mcTac ? 'success' : 'alert');
  addCoT(`STRATEGIC :: LIVE ${liveStr}%  vs  MC TRUTH ${mcStr}%  (Δ ${(liveStr - mcStr).toFixed(1)}%)`, liveStr >= mcStr ? 'success' : 'alert');
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
    this._effKey = effectorKey;

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
      this.done = true; // Mark as finished regardless of hit/miss
      const pk = getWeatherAdjustedPk(this._threatType, this._effKey);
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
    this.pos = new THREE.Vector3(600000 + idx * 20000, 5000, tz + (Math.random() - 0.5) * 200000);
    this.vel = new THREE.Vector3(tx, 5000, tz).sub(this.pos).normalize().multiplyScalar(this.wdef.speed);
    this.interceptors = [];

    // ── Advanced trajectory state ─────────────────────────────────────
    this.marvActive = false;
    this.mirvReleased = false;
    this.dogOutcome = null;   // null | 'KILL' | 'RTB' | 'ENEMY_WIN'
    this.rtbActive = false;
    this._spawnPos = this.pos.clone(); // for RTB direction
    this._frame = 0;
    this._totalFrames = 300;
    this.jinkPhase = Math.random() * Math.PI * 2;
    this.jinkV = { x: 0, z: 0 };

    this.path = []; // Temporal data buffer

    // 2D SVG components
    this.circle2D = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    this.circle2D.setAttribute('r', this.wdef.r2d);
    this.circle2D.setAttribute('fill', this.wdef.color3);
    this.circle2D.style.cursor = 'pointer';

    // Path trail (Temporal Visualisation)
    this.trail2D = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    this.trail2D.setAttribute('fill', 'none');
    this.trail2D.setAttribute('stroke', this.wdef.color3);
    this.trail2D.setAttribute('stroke-width', '1');
    this.trail2D.setAttribute('stroke-dasharray', '2 2');
    this.trail2D.setAttribute('opacity', '0.4');
    threatLayerG?.appendChild(this.trail2D);

    // Specialized marker for MARV/MIRV
    if (this.wdef.isMarv || this.wdef.isMirv) {
      this.marker2D = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const d = this.wdef.isMarv ? "M-6,0 L0,-10 L6,0 L0,4 Z" : "M-5,-5 L5,-5 L5,5 L-5,5 Z"; // Diamond vs Square
      this.marker2D.setAttribute('d', d);
      this.marker2D.setAttribute('fill', 'none');
      this.marker2D.setAttribute('stroke', this.wdef.color3);
      this.marker2D.setAttribute('stroke-width', '1.5');
      threatLayerG?.appendChild(this.marker2D);
    }

    // Deep link into kinetic chase physics with live geometry + history
    this.circle2D.onclick = () => {
      // Find assigned base if it exists, else default to Arktholm (x=251, y=57 in Boreal)
      const effBaseId = this.interceptors.length > 0 ? Object.keys(BASES).find(k => BASES[k].name === this.interceptors[0].eff.name) || 'ARK' : 'ARK';
      const effBase = BASES[effBaseId] || BASES['ARK'];

      const isMarv = this.wdef.isMarv ? 'True' : 'False';
      const hist = JSON.stringify(this.path.slice(-20).map(p => ({ x: p.x / 1666, y: p.z / 1666 })));
      const qs = `?tx=${this.pos.x / 1666}&ty=${this.pos.z / 1666}&destx=${this.targetNode.x}&desty=${this.targetNode.y}&mx=${effBase.x}&my=${effBase.y}&is_marv=${isMarv}&history=${encodeURIComponent(hist)}`;
      window.open(`kinetic_chase.html${qs}`, '_blank');
    };

    threatLayerG?.appendChild(this.circle2D);

    if (scene && !balticMap) {
      const geo = new THREE.SphereGeometry(10000, 16, 16);
      this.mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: this.wdef.hex3 }));
      scene.add(this.mesh);
    }
  }
  update() {
    if (this._disposed) return;
    this._frame++;
    const tgtPos = new THREE.Vector3(to3X(this.targetNode.x), 5000, to3Z(this.targetNode.y));

    // ── MARV: terminal jink once inside trigger range ─────────────────
    if (this.wdef.isMarv) {
      const distToTgt = this.pos.distanceTo(tgtPos);
      const trigM = (this.wdef.marvTriggerKm || 100) * 1000;
      if (distToTgt <= trigM && !this.marvActive) {
        this.marvActive = true;
        addCoT(`⚡ MARV TERMINAL JINK — ${this.id} (${(distToTgt / 1000).toFixed(0)}km out)`, 'alert');
      }
      if (this.marvActive) {
        // Persistent Sinusoidal Jink (Aligned with Backend Physics: 3.8s period)
        // 750 m/s amplitude at 1666 m/unit -> ~0.45 units/sec. 
        // At 60FPS simulation speed, we tune for visual parity.
        const jinkMag = (this.wdef.marvJinkFrac || 0.4) * 8000;
        const jinkAccel = jinkMag * 0.15;
        this.jinkPhase += 0.035; // ~3.6s period at 50Hz update rate

        this.jinkV.x += Math.sin(this.jinkPhase) * jinkAccel + (Math.random() - 0.5) * jinkAccel * 0.5;
        this.jinkV.z += Math.cos(this.jinkPhase + 1.1) * jinkAccel + (Math.random() - 0.5) * jinkAccel * 0.5;

        const speed = Math.hypot(this.jinkV.x, this.jinkV.z);
        if (speed > jinkMag) {
          this.jinkV.x = (this.jinkV.x / speed) * jinkMag;
          this.jinkV.z = (this.jinkV.z / speed) * jinkMag;
        }

        this.pos.x += this.jinkV.x * 0.05;
        this.pos.z += this.jinkV.z * 0.05;
      }
    }

    // ── MIRV: bus separation at release fraction ──────────────────────
    if (this.wdef.isMirv && !this.mirvReleased) {
      const totalDist = this._spawnPos.distanceTo(tgtPos);
      const travelDist = this.pos.distanceTo(this._spawnPos);
      const frac = totalDist > 0 ? travelDist / totalDist : 0;
      if (frac >= (this.wdef.mirvReleaseFrac || 0.45)) {
        this.mirvReleased = true;
        const count = this.wdef.mirvCount || 3;
        addCoT(`💥 MIRV BUS SEPARATION — ${count} WARHEADS | ${this.id}`, 'alert');
        const baseIds = Object.keys(BASES).slice(0, count);
        baseIds.forEach((bid, ci) => {
          const childNode = BASES[bid] || this.targetNode;
          const child = new Threat(`${this.id}-MRV${ci}`, 'BALLISTIC', childNode, ci + 100);
          child.pos.copy(this.pos); // spawn from bus position
          child.vel = new THREE.Vector3(to3X(childNode.x), 5000, to3Z(childNode.y)).sub(child.pos).normalize().multiplyScalar(1600);
          threats.push(child);
          stats.totalThreats++;
          addCoT(`  MRV-${ci} → ${childNode.name}`, 'info');
        });
        // MIRV-FIX: Dispose of the parent bus after warheads are released
        this.dispose();
        return;
      }
    }

    // ── DOGFIGHT: resolve once at 30% of travel ───────────────────────
    if (this.wdef.isDogfight && !this.dogOutcome) {
      const totalDist = this._spawnPos.distanceTo(tgtPos);
      const travelDist = this.pos.distanceTo(this._spawnPos);
      if (totalDist > 0 && travelDist / totalDist >= 0.30) {
        const r = Math.random();
        const wp = this.wdef.dogWinProb || 0.30;
        if (r < wp) {
          this.dogOutcome = 'ENEMY_WIN';
          addCoT(`✈ DOGFIGHT [${this.id}] — ENEMY WINS · OUR INTERCEPTOR LOST`, 'alert');
          // threat continues inbound
        } else if (this.wdef.canRtb && r < wp + 0.35) {
          this.dogOutcome = 'RTB';
          this.rtbActive = true;
          // RTB: reverse velocity direction
          const awayDir = this.pos.clone().sub(tgtPos).normalize();
          this.vel = awayDir.multiplyScalar(this.wdef.speed * 1.2);
          addCoT(`✈ DOGFIGHT [${this.id}] — ENEMY BREAKS OFF · RTB`, 'info');
        } else {
          this.dogOutcome = 'KILL';
          addCoT(`✈ DOGFIGHT [${this.id}] — FIGHTER KILLED IN MERGE`, 'success');
          if (!this._disposed) {
            createBlast(this.pos, 0x00ccff);
            blastSvg(this.pos.x / 1666, this.pos.z / 1666, '#00ccff');
            stats.intercepted++;
            updateAccuracyDisplay();
            this.dispose();
          }
          return;
        }
      }
    }

    // ── RTB: retreating — check if it has left the theatre ───────────
    if (this.rtbActive) {
      this.pos.add(this.vel);
      this.circle2D?.setAttribute('cx', toSvgX(this.pos.x / 1666));
      this.circle2D?.setAttribute('cy', toSvgY(this.pos.z / 1666));
      if (this.mesh) this.mesh.position.copy(this.pos);
      const distFromSpawn = this.pos.distanceTo(this._spawnPos);
      if (distFromSpawn > this._spawnPos.distanceTo(new THREE.Vector3(to3X(this.targetNode.x), 5000, to3Z(this.targetNode.y))) * 1.2) {
        addCoT(`✈ RTB COMPLETE — ${this.id} CLEARED THEATRE`, 'info');
        this.dispose();
      }
      return; // skip normal engagement
    }

    this.pos.add(this.vel);

    // Store temporal data (every 5 frames to keep buffer small)
    if (this._frame % 5 === 0) {
      this.path.push(this.pos.clone());
      if (this.path.length > 100) this.path.shift();
    }

    const sx = toSvgX(this.pos.x / 1666), sy = toSvgY(this.pos.z / 1666);
    this.circle2D?.setAttribute('cx', sx);
    this.circle2D?.setAttribute('cy', sy);

    if (this.marker2D) {
      this.marker2D.setAttribute('transform', `translate(${sx},${sy}) rotate(${this.wdef.isMarv ? (Math.sin(Date.now() / 200) * 20) : 0})`);
      if (this.wdef.isMirv) {
        this.marker2D.setAttribute('stroke-width', 1 + Math.sin(Date.now() / 100)); // Pulsing for MIRV
      }
    }

    if (this.trail2D && this.path.length > 1) {
      const pts = this.path.map(p => `${toSvgX(p.x / 1666)},${toSvgY(p.z / 1666)}`).join(' ');
      this.trail2D.setAttribute('points', pts);
    }

    if (this.mesh) this.mesh.position.copy(this.pos);
  }
  dispose() {
    if (this._disposed) return;
    this._disposed = true; this.hit = true;
    this.circle2D?.remove();
    this.trail2D?.remove();
    this.marker2D?.remove();
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
  const typeMap = { CRUISE: 'cruise-missile', HYPERSONIC: 'hypersonic-pgm', LOITER: 'drone', BALLISTIC: 'ballistic' };
  const valMap = { HYPERSONIC: 90, BALLISTIC: 80, CRUISE: 60, LOITER: 40 };
  // BUG-FIX UI-1: Boreal THEATER_DATA uses SVG units (1 unit = 1.667 km).
  // Backend engine expects km for all range-gate comparisons.
  // Sweden THEATER_DATA is already in km (offsets from Stockholm), no conversion needed.
  const kmFactor = (MODE === 'boreal') ? UNIT_TO_KM : 1.0;
  // BUG-FIX UI-3: Send full theater-correct inventory instead of only patriot+nasams.
  const swedenInv = { 'patriot-pac3': 100, 'iris-t-sls': 200, 'saab-nimbrix': 1000, 'meteor': 40, 'nasams': 20 };
  const borealInv = { 'patriot-pac3': 60, 'nasams': 100, 'coyote-block2': 200, 'merops-interceptor': 200 };
  const theaterInv = MODE === 'sweden' ? swedenInv : borealInv;
  const stateBasesPayload = Object.values(BASES).map(b => ({
    name: b.name,
    x: b.x * kmFactor,
    y: b.y * kmFactor,
    inventory: theaterInv
  }));
  try {
    const r = await fetch('http://localhost:8000/evaluate_advanced', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        state: { bases: stateBasesPayload },
        threats: threatList.map(t => ({
          id: t.id,
          x: (t.pos.x / 1666) * kmFactor,
          y: (t.pos.z / 1666) * kmFactor,
          speed_kmh: t.wdef.speed,
          estimated_type: typeMap[t.wdef.type] || 'cruise-missile',
          threat_value: valMap[t.wdef.type] || 50,
          interceptors_assigned: t.interceptors.length,
          is_marv: !!t.marvActive,
          is_mirv: !!t.wdef.isMirv && !t.mirvReleased
        })),
        weather: document.getElementById('sel-weather')?.value || 'clear',
        doctrine_primary: window._ACTIVE_DOCTRINE || 'balanced',
        use_rl: true
      }),
      signal: AbortSignal.timeout(5000)
    });
    return r.ok ? await r.json() : (() => {
      addCoT(`ENGINE HTTP ERROR — ${r.status} ${r.statusText}`, 'error');
      if (window._setEngineStatus) window._setEngineStatus(false, 'HTTP ' + r.status);
      return null;
    })();
  } catch (e) {
    const reason = e.name === 'TimeoutError' ? 'REQUEST TIMEOUT (5s)' :
      (e.name === 'TypeError' ? 'NETWORK ERROR — ENGINE OFFLINE' : (e.message || 'UNKNOWN'));
    addCoT(`ENGINE LINK FAILURE — ${reason}`, 'error');
    if (window._setEngineStatus) window._setEngineStatus(false, reason);
    return null;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// DYNAMIC SALVO MODE — Neural Autonomy
//
// Elite V3.5 treats salvo_ratio as a MINIMUM, not a cap.
// Even under "single-fire" doctrine the Elite neural model autonomously
// escalates to double-tap for mission-critical threats (HYPERSONIC / BALLISTIC).
// All other models respect doctrine restrictions.
// ─────────────────────────────────────────────────────────────────────────────
function getSalvoCount(threat) {
  const type = threat.wdef.type;
  const isElite = ACTIVE_MODEL.brain === 'TRANSFORMER-RESNET'; // Elite V3.5 only

  if (isElite) {
    // Neural Autonomy: escalate regardless of doctrine
    if (type === 'HYPERSONIC' || type === 'BALLISTIC') {
      window._lastNeuralAutonomy = { threat: threat.id, type, ts: Date.now() };
      addCoT(`⚡ NEURAL AUTONOMY: SALVO ESCALATION → ${threat.id} [${type}] — DOCTRINE OVERRIDE`, 'alert');
      const el = document.getElementById('neural-autonomy-badge');
      if (el) { el.style.display = 'inline-block'; clearTimeout(el._hide); el._hide = setTimeout(() => { el.style.display = 'none'; }, 5000); }
      return 2;
    }
  }

  // Non-elite or lower-value threats: respect doctrine
  const doctrine = window._ACTIVE_DOCTRINE || 'balanced';
  if (doctrine === 'aggressive') return (type === 'HYPERSONIC') ? 2 : 1;
  if (doctrine === 'fortress') return (type === 'HYPERSONIC' || type === 'BALLISTIC') ? 2 : 1;
  return 1; // balanced / single-fire
}

/**
 * Get weather-adjusted Pk for a given threat and effector
 */
function getWeatherAdjustedPk(threatType, effKey) {
  const eff = EFFECTORS[MODE][effKey];
  if (!eff) return 0.5;
  const basePk = eff.pk[threatType] || 0.5;
  const weather = document.getElementById('sel-weather')?.value || 'clear';
  const weatherMod = { clear: 1.0, storm: 0.6, fog: 0.5 }[weather] || 1.0;
  return basePk * weatherMod;
}

function startEngagement() {
  threats.forEach(t => t.dispose()); threats = [];
  isSimulating = true; currentWaveIdx = 0; waveTransitioning = false;
  window.waveTransitionStartedAt = 0;
  if (window.waveTransitionTimer) clearTimeout(window.waveTransitionTimer);
  window.waveTransitionTimer = null;
  cityHealth = 100; if (healthFill) healthFill.style.width = '100%';
  stats = { fired: 0, intercepted: 0, missed: 0, impacts: 0, totalThreats: 0, kills: 0 };
  pendingApprovals.clear(); rejectedThreats.clear();
  safeSetStorage(SESSION_ACTIVE_KEY, '1');
  updateAccuracyDisplay();
  initAmmo(); updateInventoryDisplay();
  if (balticMap) SAAB_CH.postMessage({ type: 'LAUNCH' });
  saveSessionSnapshot();
  launchWave();
}

function launchWave(retries) {
  retries = retries || 0;
  if (!groundTruthData) {
    if (retries >= 30) {
      addCoT("GROUND TRUTH DATA NOT LOADED :: ABORTING", "error");
      return;
    }
    if (retries === 0) addCoT("AWAITING GROUND TRUTH DATA...", "info");
    setTimeout(() => launchWave(retries + 1), 300);
    return;
  }

  const scenario = groundTruthData[currentScenarioIdx.toString()];
  if (!scenario) {
    addCoT(`SCENARIO ${currentScenarioIdx} NOT FOUND :: RESETTING`, "alert");
    currentScenarioIdx = 0;
    return;
  }

  addCoT(`INBOUND SCENARIO ${currentScenarioIdx + 1}: MC-GROUND TRUTH ACTIVE`, 'alert');
  addCoT(`ACTIVE NEURAL CORE: ${ACTIVE_MODEL.name} | Pk: ${(ACTIVE_MODEL.pk * 100).toFixed(1)}%`, 'info');

  const incomingThreats = scenario.threats || [];
  incomingThreats.forEach((tData, i) => {
    // Map scenario weapon types to visualization keys
    let wkey = 'BALLISTIC';
    if (tData.type === 'fast-mover') wkey = 'HYPERSONIC';
    if (tData.type === 'drone') wkey = 'LOITER';
    if (tData.type === 'fighter') wkey = 'CRUISE';

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
  const liveThreats = threats.filter(t => !t.hit);
  if (liveThreats.length > 0) {
    callEngine(liveThreats).then(result => {
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
  saveSessionSnapshot();
}

// --- NEURAL MODEL ROSTER (Multi-Theater Audited) ---
const MODEL_PROFILES = {
  elite: { name: "ELITE V3.5 (Final Boss) 👑", brain: "TRANSFORMER-RESNET", logic: "DIRECT ACTION", pkBoreal: 0.978, pkSweden: 0.982, speed: 1.2 },
  supreme3: { name: "SUPREME V3.1 (Chronos) 👁️", brain: "CHRONOS GRU", logic: "SEQUENCE", pkBoreal: 0.942, pkSweden: 0.951, speed: 1.05 },
  supreme2: { name: "SUPREME V2 (Legacy) 🏛️", brain: "RESNET-64", logic: "HYBRID", pkBoreal: 0.891, pkSweden: 0.902, speed: 1.0 },
  titan: { name: "TITAN TRANSFORMER 🌪️", brain: "SELF-ATTENTION", logic: "MULTI-VECTOR", pkBoreal: 0.908, pkSweden: 0.916, speed: 1.1 },
  hybrid: { name: "HYBRID RL V8.4 🛡️", brain: "RESNET-128", logic: "HUNGARIAN", pkBoreal: 0.875, pkSweden: 0.885, speed: 1.0 },
  genE10: { name: "GENERALIST E10 🧬", brain: "POLICY-ONLY", logic: "DIRECT ACTION", pkBoreal: 0.930, pkSweden: 0.930, speed: 1.0 },
  heuristic: { name: "HEURISTIC (Triage-Aware) ⚙️", brain: "CLASS-AWARE LOGIC", logic: "TRIAGE-AWARE", pkBoreal: 0.738, pkSweden: 0.752, speed: 0.9 },
  hBase: { name: "HEURISTIC V2 (Base) 📜", brain: "STATIC LOGIC", logic: "HUNGARIAN", pkBoreal: 0.575, pkSweden: 0.584, speed: 0.85 },
  random: { name: "RANDOM ASSIGNMENT 🎲", brain: "STOCHASTIC", logic: "RANDOM", pkBoreal: 0.501, pkSweden: 0.502, speed: 0.8 }
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
    int.baseId = baseId;
    int._effKey = effector;
    int._threatType = t.wdef.type;
    t.interceptors.push(int);  // FIX: was t.interceptor= (singular), never updated in sim loop
    stats.fired++;
    const effName = EFFECTORS[MODE][effector]?.name || effector;
    addCoT(`MANUAL OVERRIDE: ${effName} LAUNCHED FROM ${BASES[baseId].name}`, 'success');

    if (!window.isMirror) {
      SAAB_CH.postMessage({ type: 'INTERCEPT', threatId, baseId, effector });
    }
    saveSessionSnapshot();
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
    int.baseId = defId;
    int._effKey = effKey;
    int._threatType = t.wdef.type;
    t.interceptors.push(int);  // FIX: was t.interceptor= (singular), never updated in sim loop
    stats.fired++;
    addCoT(`HITL APPROVED: ${EFFECTORS[MODE][effKey].name} INTERCEPTING ${t.id}`, 'success');

    if (!window.isMirror) {
      SAAB_CH.postMessage({ type: 'INTERCEPT', threatId, baseId: defId, effector: effKey });
    }
  }
  pendingApprovals.delete(threatId);
  saveSessionSnapshot();
};

function updateSimulation() {
  if (!isSimulating) return;

  // CLEANUP: Purge dead threats every 30 frames to keep the telemetry and loop efficient
  if (typeof simFrames === 'undefined') window.simFrames = 0;
  window.simFrames++;
  if (window.simFrames % 30 === 0) {
    threats = threats.filter(t => !t.hit);
  }

  const isDecisionPending = (ENGINE_MODE === 'hitl' && pendingApprovals.size > 0);
  // Manual mode: sim runs freely — operator fires via dashboard manual panel (no freeze)
  const isManualPlanning = false;
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
    // FIX: Re-engage if salvo count requirement increases (e.g. jink start)
    if (t.interceptors.length < getSalvoCount(t)) {
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
            const pk = getWeatherAdjustedPk(t.wdef.type, effKey);
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
        const salvoCount = getSalvoCount(t);
        // Fire salvoCount interceptors (consuming top candidates; skip destroyed/empty bases)
        const usedThisTick = {}; // extra spend this tick before ammo[] is decremented
        let fired = 0;
        for (const cand of candidates) {
          if (fired >= salvoCount) break;
          const pending = usedThisTick[cand.baseId] || 0;
          if ((ammo[cand.baseId] - pending) <= 0) continue;
          if (destroyedBases.has(cand.baseId)) continue;
          usedThisTick[cand.baseId] = pending + 1;
          ammo[cand.baseId]--; updateInventoryDisplay();
          const int = new Interceptor(BASES[cand.baseId], cand.effKey);
          int.baseId = cand.baseId;
          int._effKey = cand.effKey;
          int._threatType = t.wdef.type;
          t.interceptors.push(int);
          stats.fired++; fired++;
          if (fired === 1) {
            addCoT(`AUTO-ENGAGED ${t.id} → ${EFFECTORS[MODE][cand.effKey].name} from ${BASES[cand.baseId].name} (${(cand.dToBase / 1000).toFixed(0)}km)`, 'success');
          } else {
            addCoT(`⚡ SALVO +${fired} ${t.id} → ${EFFECTORS[MODE][cand.effKey].name} from ${BASES[cand.baseId].name}`, 'success');
          }
        }
        if (fired > 0) saveSessionSnapshot();
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

              const pk = getWeatherAdjustedPk(t.wdef.type, effKey);

              hitlCands.push({ baseId, effKey, d, utility: (pk * 100) - (d / 100000) });
            });
          });
          hitlCands.sort((a, b) => b.utility - a.utility);
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
      return !int.done;
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
      stats.impacts++;

      const nodeId = t.targetNode.id;
      const nodeType = t.targetNode.type;

      if (nodeType === 'BASE') {
        // Structural damage to military base — can be destroyed
        const dmgTable = { HYPERSONIC: 60, BALLISTIC: 50, CRUISE: 35, LOITER: 20, FIGHTER: 40 };
        const dmg = dmgTable[t.wdef.type] || 30;
        baseHealth[nodeId] = Math.max(0, (baseHealth[nodeId] ?? 100) - dmg);
        if (baseHealth[nodeId] === 0 && !destroyedBases.has(nodeId)) {
          destroyedBases.add(nodeId);
          ammo[nodeId] = 0;
          addCoT(`⚠ BASE DESTROYED: ${t.targetNode.name} — ALL SAM CAPACITY LOST`, 'error');
          markBaseDestroyed(nodeId);
        } else if (!destroyedBases.has(nodeId)) {
          addCoT(`IMPACT AT ${t.targetNode.name} — BASE DAMAGED (${baseHealth[nodeId]}% integrity)`, 'alert');
          markBaseDamaged(nodeId, baseHealth[nodeId]);
        }
        cityHealth -= 8; // Bases count more toward capital health
      } else {
        // HVA capital impact — direct capital integrity damage
        cityHealth -= 15;
        addCoT(`IMPACT AT ${t.targetNode.name} — DEFENSE BREACH`, 'alert');
      }

      if (healthFill) healthFill.style.width = `${Math.max(0, cityHealth)}%`;
      t.dispose();
      updateAccuracyDisplay();
      updateInventoryDisplay();
    }
  });

  if (!anyAlive && !waveTransitioning && threats.length > 0) {
    waveTransitioning = true;
    window.waveTransitionStartedAt = Date.now();
    threats = threats.filter(t => !t.hit);
    // If this was a benchmark scenario (single wave), print comparison and stop
    if (benchGroundTruth) {
      printBenchmarkComparison();
      isSimulating = false;
      waveTransitioning = false;
      window.waveTransitionStartedAt = 0;
      if (window.waveTransitionTimer) clearTimeout(window.waveTransitionTimer);
      window.waveTransitionTimer = null;
      safeSetStorage(SESSION_ACTIVE_KEY, '0');
      saveSessionSnapshot();
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
      window.waveTransitionStartedAt = 0;
      if (window.waveTransitionTimer) clearTimeout(window.waveTransitionTimer);
      window.waveTransitionTimer = null;
      safeSetStorage(SESSION_ACTIVE_KEY, '0');
      saveSessionSnapshot();
    }
    if (!benchGroundTruth && currentWaveIdx < WAVE_SEQ.length) saveSessionSnapshot();
  }

  // --- SOURCE OF TRUTH BROADCAST ---
  // Periodically stream the entire theater state to secondary views (Kinetic 3D, Chase)
  if (!window.isMirror) {
    broadcastState();
    saveSessionSnapshot();
  }
}

function broadcastState() {
  // 1. Send Inventory/Stats
  const inventorySync = {
    type: 'INVENTORY_SYNC',
    totalSAM: stats.fired,
    kills: stats.intercepted, // intercepted is the live kill counter; stats.kills is only set on restore
    impacts: stats.impacts
  };
  cacheInventorySync(inventorySync);
  SAAB_CH.postMessage(inventorySync);

  // 2. Send Active Theater State
  const syncData = {
    type: 'STATE_SYNC',
    ts: Date.now(),
    mode: MODE,
    threats: threats.filter(t => !t.hit).map(t => ({
      id: t.id,
      x: t.pos.x, y: t.pos.y, z: t.pos.z,
      wkey: t.wdef.type,
      isMarv: !!t.marvActive,
      isMirv: !!t.wdef.isMirv && !t.mirvReleased,
      interceptors: t.interceptors.map(i => ({
        pos: { x: i.pos.x, y: i.pos.y, z: i.pos.z },
        eff: i.eff.name,
        color: i.eff.color
      }))
    }))
  };
  cacheStateSync(syncData);
  SAAB_CH.postMessage(syncData);
}

// --- 3D ENGINE ---
let scene, camera, renderer, orbitControls;
function init3D() {
  const container = document.getElementById('canvas-container');
  if (!container) { setInterval(updateSimulation, 16); return; }

  // Use offsetWidth/Height which forces layout reflow; fall back to window dims
  const W = container.offsetWidth || (window.innerWidth - 240);
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
    const w = container.offsetWidth || window.innerWidth;
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

  // Skip TERRAIN/ZONE nodes — they have no x/y point coords suitable for 3D placement
  THEATER_DATA.filter(n => n.type === 'BASE' || n.type === 'HVA').forEach(n => {
    const col = n.type === 'HVA' ? 0x00ff88 : 0x00f2ff;
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(15000, 20000, 40000, 6), new THREE.MeshBasicMaterial({ color: col, wireframe: true }));
    mesh.position.set(to3X(n.x), 20000, to3Z(n.y));
    mesh.userData = { id: n.id };
    scene.add(mesh);
  });

  renderer.domElement.addEventListener('click', e => {
    const rect = renderer.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    const ray = new THREE.Raycaster(); ray.setFromCamera(mouse, camera);
    const hits = ray.intersectObjects(scene.children);
    if (hits[0]?.object.userData.id) triggerDemo(hits[0].object.userData.id);
  });

  // Decouple physics/sync from rendering so it runs when tab is inactive
  setInterval(updateSimulation, 16);
  (function loop() { requestAnimationFrame(loop); orbitControls.update(); renderer.render(scene, camera); })();
}

function createBlast(pos, col) {
  // 3D Effect
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(20000, 16, 16), new THREE.MeshBasicMaterial({ color: col, wireframe: true, transparent: true }));
  mesh.position.copy(pos); scene?.add(mesh);

  // 2D SVG Effect
  const circ = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  circ.setAttribute('r', '2');
  circ.setAttribute('fill', 'none');
  circ.setAttribute('stroke', '#' + col.toString(16).padStart(6, '0'));
  circ.setAttribute('stroke-width', '4');
  circ.setAttribute('cx', toSvgX(pos.x / 1666));
  circ.setAttribute('cy', toSvgY(pos.z / 1666));
  threatLayerG?.appendChild(circ);

  let s = 1;
  let op = 1.0;
  const iv = setInterval(() => {
    s += 2;
    op -= 0.05;
    mesh.scale.setScalar(s);
    mesh.material.opacity = op;

    circ.setAttribute('r', (s * 5).toString());
    circ.setAttribute('opacity', op.toString());

    if (op <= 0) {
      clearInterval(iv);
      scene?.remove(mesh);
      circ.remove();
    }
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
  stats = { fired: 0, intercepted: 0, missed: 0, impacts: 0, totalThreats: 1 };
  // Use weapon selector if present (live_view.html), else random
  const WKEYS = ['CRUISE', 'HYPERSONIC', 'LOITER', 'BALLISTIC', 'MARV', 'MIRV', 'FIGHTER_DOG'];
  const wEl = document.getElementById('lv-sel-weapon');
  const wkey = (wEl && wEl.value) ? wEl.value : WKEYS[Math.floor(Math.random() * WKEYS.length)];
  const t = new Threat(`DEMO-${id}`, wkey, n, 0);
  threats.push(t);
  addCoT(`DEMO: ${WEAPONS[wkey].label} INBOUND → ${n.name}`, 'alert');
  if (camera) {
    camera.position.set(to3X(n.x), 400000, to3Z(n.y) + 400000);
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
  stats = { fired: 0, intercepted: 0, missed: 0, impacts: 0, totalThreats: 0, kills: 0 };
  pendingApprovals.clear(); rejectedThreats.clear();
  initAmmo(); updateInventoryDisplay();
  const WKEYS = ['CRUISE', 'HYPERSONIC', 'LOITER', 'BALLISTIC', 'MARV', 'MIRV', 'FIGHTER_DOG', 'CRUISE'];
  const tgtPool = THEATER_DATA.filter(n => n.type === 'HVA' || n.type === 'BASE');
  addCoT('STANDALONE SATURATION WAVE — 8 THREATS (MARV/MIRV/DOGFIGHT INCLUDED)', 'alert');
  addCoT(`ACTIVE MODEL: ${ACTIVE_MODEL.name} | Pk: ${(ACTIVE_MODEL.pk * 100).toFixed(1)}%`, 'info');
  // Set wave index past WAVE_SEQ boundary so updateSimulation() stops cleanly
  // instead of transitioning to ground-truth launchWave() after this wave ends
  currentWaveIdx = WAVE_SEQ.length;
  const newThreats = WKEYS.map((wkey, i) => {
    const tgt = tgtPool[Math.floor(Math.random() * tgtPool.length)];
    const t = new Threat(`WAVE-${i}`, wkey, tgt, i);
    threats.push(t);
    stats.totalThreats++;
    addCoT(`THREAT ${i + 1}: ${WEAPONS[wkey].label} → ${tgt.name}`, 'alert');
    return t;
  });
  if (typeof camera !== 'undefined' && typeof orbitControls !== 'undefined') {
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
    _engWs.onopen = () => {
      addCoT('CORTEX-1 NEURAL UPLINK ESTABLISHED — ENGINE ONLINE', 'success');
      if (window._setEngineStatus) window._setEngineStatus(true, '');
    };
    _engWs.onmessage = e => {
      if (e.data === '[HEARTBEAT]') return;
      addCoT(e.data.replace(/^\[(STRAT|LOG|SYS)\] ?/, '').substring(0, 100), 'info');
    };
    _engWs.onerror = () => {
      addCoT('NEURAL ENGINE UPLINK OFFLINE — STANDALONE MODE ACTIVE', 'alert');
      if (window._setEngineStatus) window._setEngineStatus(false, 'UPLINK ERROR');
    };
    _engWs.onclose = (e) => {
      if (!e.wasClean) {
        addCoT(`NEURAL UPLINK DROPPED (code ${e.code}) — STANDALONE MODE ACTIVE`, 'alert');
        if (window._setEngineStatus) window._setEngineStatus(false, 'DISCONNECTED');
      }
    };
  } catch (_) { }

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
      // Only dashboard re-launches on reload — mirrors receive state via BroadcastChannel
      if (!window.isMirror && safeGetStorage(SESSION_ACTIVE_KEY) === '1' && !isSimulating) {
        setTimeout(() => startEngagement(), 0);
      }
    })
    .catch(e => console.error("GROUND TRUTH FETCH FAILED", e));

  renderMap(); init3D(); initAmmo(); updateInventoryDisplay();
  const restoredSession = restoreSessionSnapshot();
  if (restoredSession && !window.isMirror) {
    broadcastState();
  }
  const cachedInventory = getCachedInventorySync();
  const cachedState = getCachedStateSync();
  if (!restoredSession && cachedInventory) SAAB_CH.postMessage(cachedInventory);
  if (!restoredSession && cachedState) SAAB_CH.postMessage(cachedState);
  // Initialize live_view model display (no-op if element absent on dashboard)
  const lvModel = document.getElementById('lv-active-model');
  if (lvModel) lvModel.innerText = ACTIVE_MODEL.name;

  if (!window.isMirror && !restoredSession && safeGetStorage(SESSION_ACTIVE_KEY) === '1') {
    // Dashboard only: restart simulation if session was active but not yet restored
    setTimeout(() => {
      if (!isSimulating && groundTruthData && !threats.length) {
        startEngagement();
      }
    }, 0);
  }

  if (window.isMirror) {
    // Mirror pages (live_view, kinetic_chase): request fresh state from dashboard
    setTimeout(() => SAAB_CH.postMessage({ type: 'STATE_REQUEST' }), 600);
  }

}

setInterval(() => {
  consumeLaunchRequest();
}, 250);

wireDashboardControls();
boot();

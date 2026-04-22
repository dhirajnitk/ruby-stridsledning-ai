// ==========================================
// BOREAL ADVANCED KINETIC ENGINE (V4.0)
// ==========================================

const PT_POWER = 100e3;
const RADAR_GAIN_DB = 30;
const RADAR_GAIN = Math.pow(10, RADAR_GAIN_DB / 10);
const WAVELENGTH = 0.03;
const P_MIN_DETECT = 1e-14;
const MISSILE_SPEED = 800;
const N_CONST = 4.0;
const DT = 0.05;

let scene, camera, renderer, controls;
let threats = [];
let interceptors = [];
let isSimulating = false;
let cityHealth = 100;

// --- UI REGISTRY ---
const threatList = document.getElementById('threat-list');
const cotFeed = document.getElementById('cot-feed');
const healthFill = document.getElementById('city-health');
const threatCount = document.getElementById('threat-count');

// ==========================================
// 1. CORE PHYSICS PORT
// ==========================================

function getRadarReturn(range, rcs) {
    if (range <= 0) return 0;
    return (PT_POWER * Math.pow(RADAR_GAIN, 2) * Math.pow(WAVELENGTH, 2) * rcs) / (Math.pow(4 * Math.PI, 3) * Math.pow(range, 4));
}

class Interceptor {
    constructor(startPos, color, targetId) {
        this.pos = new THREE.Vector3().copy(startPos);
        this.vel = new THREE.Vector3(0, 0, 0);
        this.active = true;
        this.targetId = targetId;
        
        const geometry = new THREE.SphereGeometry(30, 8, 8);
        const material = new THREE.MeshBasicMaterial({ color: color });
        this.mesh = new THREE.Mesh(geometry, material);
        scene.add(this.mesh);

        this.trailPoints = [];
        const trailGeom = new THREE.BufferGeometry();
        const trailMat = new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: 0.6 });
        this.trail = new THREE.Line(trailGeom, trailMat);
        scene.add(this.trail);
    }

    update(targetPos, targetVel) {
        if (!this.active) return;
        const r_tm = new THREE.Vector3().subVectors(targetPos, this.pos);
        const dist = r_tm.length();
        
        if (dist < 40) {
            this.active = false;
            addCoT(`T-ID [${this.targetId}] NEUTRALIZED. Intercept Proximity: ${dist.toFixed(1)}m`, "success");
            removeThreatUI(this.targetId);
            return true;
        }

        const p_r = getRadarReturn(targetPos.length(), 0.5);
        if (p_r > P_MIN_DETECT) {
            const v_tm = new THREE.Vector3().subVectors(targetVel, this.vel);
            const omega = new THREE.Vector3().crossVectors(r_tm, v_tm).divideScalar(dist * dist);
            const v_closing = -r_tm.dot(v_tm) / dist;
            const unit_los = r_tm.clone().normalize();
            const a_c = new THREE.Vector3().crossVectors(omega, unit_los).multiplyScalar(N_CONST * v_closing);
            this.vel.add(a_c.multiplyScalar(DT));
            this.vel.normalize().multiplyScalar(MISSILE_SPEED);
        }

        this.pos.add(this.vel.clone().multiplyScalar(DT));
        this.mesh.position.copy(this.pos);
        this.trailPoints.push(this.pos.clone());
        if (this.trailPoints.length > 50) this.trailPoints.shift();
        this.trail.geometry.setFromPoints(this.trailPoints);
        return false;
    }
}

// ==========================================
// 2. DASHBOARD & UI LOGIC
// ==========================================

function addCoT(text, type = '') {
    const div = document.createElement('div');
    div.style.marginBottom = '0.5rem';
    div.style.color = type === 'success' ? '#00ff88' : (type === 'alert' ? '#ff3e3e' : '#888');
    div.innerText = `> ${text}`;
    cotFeed.prepend(div);
}

function addThreatUI(id, type, dist) {
    const item = document.createElement('div');
    item.className = `threat-item ${dist < 20000 ? 'high-risk' : ''}`;
    item.id = `ui-${id}`;
    item.innerHTML = `<span>[!]</span><span>${type}</span><span>${(dist/1000).toFixed(1)}km</span>`;
    threatList.prepend(item);
}

function removeThreatUI(id) {
    const el = document.getElementById(`ui-${id}`);
    if (el) el.style.opacity = '0.3';
}

function updateDashboard() {
    threatCount.innerText = `${threats.filter(t => !t.hit).length} ACTIVE`;
}

// ==========================================
// 3. THREE.JS SCENE
// ==========================================

function init() {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 10, 500000);
    camera.position.set(40000, 20000, 40000);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('canvas-container').appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    scene.add(new THREE.GridHelper(100000, 20, 0x00f2ff, 0x112233));

    // Capital City (The HVA)
    const capital = new THREE.Mesh(new THREE.OctahedronGeometry(500), new THREE.MeshBasicMaterial({ color: 0x00ff88, wireframe: true }));
    scene.add(capital);

    animate();
}

function animate() {
    requestAnimationFrame(animate);
    if (isSimulating) updateSimulation();
    renderer.render(scene, camera);
}

function updateSimulation() {
    threats.forEach((t, i) => {
        if (t.hit) return;
        t.pos.add(t.vel.clone().multiplyScalar(DT));
        t.mesh.position.copy(t.pos);
        
        const distToCity = t.pos.length();
        if (distToCity < 500) {
            t.hit = true;
            cityHealth -= 10;
            healthFill.style.width = `${cityHealth}%`;
            addCoT("IMPACT DETECTED. City Integrity Compromised.", "alert");
            return;
        }

        const intercepted = interceptors[i].update(t.pos, t.vel);
        if (intercepted) t.hit = true;
    });
    updateDashboard();
}

function startEngagement() {
    isSimulating = true;
    threatList.innerHTML = '';
    addCoT("THREAT SPEAR DETECTED. Multi-Domain Saturation Confirmed.", "alert");
    
    const scenario = [
        { id: "S-01", type: "STEALTH", pos: [80000, 10000, 5000], vel: [-350, 0, 0], rcs: 0.005 },
        { id: "C-02", type: "CRUISE", pos: [40000, 200, 0], vel: [-250, 0, 0], rcs: 0.5 },
        { id: "L-03", type: "LOITER", pos: [30000, 100, -5000], vel: [-80, 0, 0], rcs: 0.1 }
    ];

    scenario.forEach(data => {
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(300, 150, 150), new THREE.MeshBasicMaterial({ color: 0xff3e3e }));
        const pos = new THREE.Vector3(...data.pos);
        mesh.position.copy(pos);
        scene.add(mesh);
        
        threats.push({ ...data, pos, vel: new THREE.Vector3(...data.vel), mesh, hit: false });
        interceptors.push(new Interceptor(new THREE.Vector3(0,0,0), 0x00f2ff, data.id));
        addThreatUI(data.id, data.type, pos.length());
    });
}

document.getElementById('btn-launch').addEventListener('click', startEngagement);
document.getElementById('btn-reset').addEventListener('click', () => location.reload());

init();

// BOREAL BASIC THEATRE ENGINE (V3.7 LEGACY)
const MISSILE_SPEED = 800;
const N_CONST = 4.0;
const DT = 0.05;

let scene, camera, renderer;
let threats = [];
let interceptors = [];

function init() {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 1, 100000);
    camera.position.set(20000, 10000, 20000);
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('canvas-container').appendChild(renderer.domElement);
    scene.add(new THREE.GridHelper(50000, 10, 0x00f2ff, 0x222222));
    animate();
}

function animate() {
    requestAnimationFrame(animate);
    threats.forEach((t, i) => {
        t.position.x -= 200 * DT;
        // Simple tracking logic for legacy version
    });
    renderer.render(scene, camera);
}

document.getElementById('btn-launch').addEventListener('click', () => {
    const geom = new THREE.BoxGeometry(200, 100, 100);
    const mesh = new THREE.Mesh(geom, new THREE.MeshBasicMaterial({ color: 0xff3e3e }));
    mesh.position.set(30000, 5000, 0);
    scene.add(mesh);
    threats.push(mesh);
    console.log("Legacy Sim Started.");
});

init();

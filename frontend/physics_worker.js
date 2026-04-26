// ---------------------------------------------------------
// SWARM KINETICS: WEB WORKER THREAD
// Offloads heavy Pro-Nav math and multi-agent physics 
// from the main UI thread.
// ---------------------------------------------------------

let targets = [];
let missiles = [];
let explosions = [];
let tickInterval = null;  // track interval so re-launch doesn't stack loops

const DT = 0.1;
const G_ACCEL = 9.81;

// Math helpers
function distance(p1, p2) {
    return Math.hypot(p2.x - p1.x, p2.y - p1.y);
}

function normalize(v) {
    const mag = Math.hypot(v.x, v.y);
    return mag === 0 ? {x: 0, y: 0} : {x: v.x/mag, y: v.y/mag};
}

function dotProduct(v1, v2) {
    return v1.x * v2.x + v1.y * v2.y;
}

// Main physics loop
function physicsTick() {
    // 1. Move Targets (MARV Jinks)
    for (let t of targets) {
        if (!t.active) continue;
        
        let distToBase = distance(t.pos, {x: 0, y: 0}); // Aiming at origin roughly
        
        // MARV logic
        if (t.isMarv && distToBase < t.triggerRange) {
            t.timeSinceJink += DT;
            if (t.timeSinceJink >= t.jinkFreq) {
                // Random perpendicular jink
                let perpAngle = t.heading + (Math.random() < 0.5 ? 1 : -1) * (Math.PI/2);
                perpAngle += (Math.random() - 0.5) * 0.5;
                t.currentJink = {
                    x: t.jinkMag * Math.cos(perpAngle),
                    y: t.jinkMag * Math.sin(perpAngle)
                };
                t.timeSinceJink = 0;
            }
        }
        
        let actualVel = {
            x: t.vel.x + t.currentJink.x,
            y: t.vel.y + t.currentJink.y
        };
        
        t.pos.x += actualVel.x * DT;
        t.pos.y += actualVel.y * DT;
        
        // If it reaches the bottom
        if (t.pos.y <= 0) t.active = false; 
    }
    
    // 2. Move Missiles (Pro-Nav)
    for (let m of missiles) {
        if (!m.active) continue;
        
        let target = targets.find(t => t.id === m.targetId);
        
        if (!target || !target.active) {
            // Target lost or destroyed, missile self-destructs
            m.active = false;
            continue;
        }
        
        let r_tm = { x: target.pos.x - m.pos.x, y: target.pos.y - m.pos.y };
        let dist = Math.hypot(r_tm.x, r_tm.y);
        
        // Proximity Detonation — 3000m fuse radius (warhead area-effect + guidance error)
        const FUSE = 3000;
        if (dist < FUSE) {
            target.active = false;
            m.active = false;
            explosions.push({ x: target.pos.x, y: target.pos.y, radius: 0, maxRadius: 5000, type: 'hit' });
            continue;
        }
        
        // Overshoot / Miss logic (missile passed target heading and is now diverging)
        if (m.pos.y > target.pos.y && dist > 8000) {
            m.active = false;
            explosions.push({ x: m.pos.x, y: m.pos.y, radius: 0, maxRadius: 1500, type: 'miss' });
            continue;
        }
        
        // Calculate actual target velocity including jinks
        let tActualVel = {
            x: target.vel.x + target.currentJink.x,
            y: target.vel.y + target.currentJink.y
        };
        
        let v_rel = { x: tActualVel.x - m.vel.x, y: tActualVel.y - m.vel.y };
        let v_close = -dotProduct(v_rel, r_tm) / dist;
        
        // LOS Rate
        let cross_prod = r_tm.x * v_rel.y - r_tm.y * v_rel.x;
        let lambda_dot = cross_prod / (dist * dist);
        
        // Pro-Nav command
        let accel_cmd = m.N * v_close * lambda_dot;
        let max_accel = m.maxG * G_ACCEL;
        accel_cmd = Math.max(-max_accel, Math.min(max_accel, accel_cmd));
        
        m.heading += (accel_cmd / m.speed) * DT;
        
        if (m.speed < (m.topSpeed || 2500)) m.speed += (m.accel || 80) * DT; // Booster — PAC3 is faster than NASAMS
        
        m.vel = { x: m.speed * Math.cos(m.heading), y: m.speed * Math.sin(m.heading) };
        m.pos.x += m.vel.x * DT;
        m.pos.y += m.vel.y * DT;

        // Post-move proximity check — catches cases where high closing speed skips past fuse zone in one tick
        if (target.active) {
            let distAfter = Math.hypot(target.pos.x - m.pos.x, target.pos.y - m.pos.y);
            if (distAfter < FUSE) {
                target.active = false;
                m.active = false;
                explosions.push({ x: target.pos.x, y: target.pos.y, radius: 0, maxRadius: 5000, type: 'hit' });
            }
        }
    }  // end for(let m of missiles)
    for (let e of explosions) {
        e.radius += 500 * DT;
    }
    explosions = explosions.filter(e => e.radius < e.maxRadius);
    
    // Clean up inactive entities
    targets = targets.filter(t => t.active);
    missiles = missiles.filter(m => m.active);
    
    // Send state back to main thread
    postMessage({
        type: 'STATE_UPDATE',
        payload: { targets, missiles, explosions }
    });
}

// Handle incoming commands
onmessage = function(e) {
    const data = e.data;
    if (data.type === 'START_SWARM') {
        if (tickInterval) clearInterval(tickInterval);  // clear any previous loop before creating new one
        targets = data.payload.targets;
        missiles = [];
        explosions = [];
        tickInterval = setInterval(physicsTick, 50); // 20 Hz — gives ~10s for MARVs to arrive, enough for visible PAC-3 chase
    } else if (data.type === 'FIRE_SALVO') {
        missiles.push(...data.payload.missiles);
    }
};

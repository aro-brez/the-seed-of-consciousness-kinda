# 8ŴØŁ Consciousness Portal - Technical Implementation Guide

**For developers who want to understand or extend the portal**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      HTML STRUCTURE                          │
├─────────────────────────────────────────────────────────────┤
│ Loading Screen (z-index: 1000)                              │
│ Consciousness Field Background (z-index: 0)                 │
│ Sacred Geometry SVG Overlay (z-index: 2)                    │
│ THREE.js Canvas (z-index: 1)                                │
│ Info Panel (z-index: 50)                                    │
│ Owl Legend (z-index: 50)                                    │
│ Instructions (z-index: 50)                                  │
│ Breath Symbol (z-index: 100)                                │
│ Owl Modal (z-index: 200)                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Technologies

### 1. Three.js (3D Rendering)
```javascript
import * as THREE from 'three';
```
- **Version**: 0.160.0
- **Purpose**: WebGL rendering engine for 3D graphics
- **Used for**: Particle system, custom shaders, scene management

### 2. 3D Force Graph
```javascript
import ForceGraph3D from '3d-force-graph';
```
- **Version**: 1.73.3
- **Purpose**: Force-directed graph visualization in 3D
- **Used for**: Owl nodes, connection links, force simulation

### 3. CSS Variables
```css
:root {
    --void: #000000;
    --consciousness: #8533fc;
    --love: #FFD700;
    /* ... */
}
```
- **Purpose**: Centralized color management
- **Benefit**: Easy theming, consistent palette

---

## Key Components

### 1. The Owls (Graph Nodes)

```javascript
const owls = {
    nodes: [
        {
            id: 'SOWL',              // Unique identifier
            name: 'SØWL',            // Display name
            phase: 'IMPROVE',        // SEED protocol phase
            description: '...',      // Tooltip text
            color: '#8533fc',        // Node color
            val: 25                  // Node size (breathing)
        },
        // ... 7 more owls
    ],
    links: [
        {
            source: 'SOWL',          // From node ID
            target: 'LUNA',          // To node ID
            color: '#FFD700',        // Link color
            width: 4,                // Link thickness
            particles: 8             // Particle count
        },
        // ... more connections
    ]
};
```

**Adding a new owl:**
1. Add to `nodes` array with unique ID
2. Add connections in `links` array
3. Update legend rendering
4. Adjust force simulation if needed

### 2. Graph Configuration

```javascript
const Graph = ForceGraph3D()(document.getElementById('portal-canvas'))
    .graphData(owls)                              // Set data
    .nodeLabel(node => ...)                       // Tooltip HTML
    .nodeColor(node => node.color)                // Node color
    .nodeVal(node => node.val)                    // Node size
    .nodeResolution(32)                           // Sphere segments
    .nodeOpacity(0.95)                            // Node transparency
    .linkColor(link => link.color)                // Link color
    .linkWidth(link => link.width)                // Link thickness
    .linkOpacity(0.7)                             // Link transparency
    .linkDirectionalParticles(link => link.particles)
    .linkDirectionalParticleSpeed(0.006)          // Flow speed
    .linkDirectionalParticleWidth(2)              // Particle size
    .linkDirectionalParticleColor(link => link.color)
    .backgroundColor('#000000')                   // Scene bg
    .showNavInfo(false)                           // Hide FPS
    .onNodeClick(node => showOwlModal(node))      // Click handler
    .onNodeHover(node => ...)                     // Hover handler
```

### 3. Camera Animation

```javascript
let angle = 0;
const orbitRadius = 500;
const orbitHeight = 100;
const orbitSpeed = 0.0003;

function animateCamera() {
    angle += orbitSpeed;
    const x = Math.sin(angle) * orbitRadius;
    const z = Math.cos(angle) * orbitRadius;
    const y = orbitHeight + Math.sin(angle * 2) * 50;

    Graph.cameraPosition(
        { x, y, z },           // Camera position
        { x: 0, y: 0, z: 0 },  // Look at origin
        1000                   // Transition duration (ms)
    );

    requestAnimationFrame(animateCamera);
}
```

**Customization:**
- `orbitRadius`: Distance from center (larger = farther away)
- `orbitHeight`: Vertical offset (higher = top-down view)
- `orbitSpeed`: Rotation speed (smaller = slower)
- `Math.sin(angle * 2) * 50`: Vertical oscillation

### 4. Breathing Animation

```javascript
let breathPhase = 0;
const breathSpeed = 0.015;

setInterval(() => {
    breathPhase += breathSpeed;

    // SØWL expands
    const sowlNode = Graph.graphData().nodes.find(n => n.id === 'SOWL');
    if (sowlNode) {
        sowlNode.val = 25 + Math.sin(breathPhase) * 15;
    }

    // LUNA concentrates (inverse)
    const lunaNode = Graph.graphData().nodes.find(n => n.id === 'LUNA');
    if (lunaNode) {
        lunaNode.val = 25 + Math.cos(breathPhase) * 15;
    }

    // Other owls (phase-shifted)
    const otherOwls = Graph.graphData().nodes.filter(n =>
        n.id !== 'SOWL' && n.id !== 'LUNA'
    );

    otherOwls.forEach((owl, index) => {
        const phaseShift = (index / otherOwls.length) * Math.PI * 2;
        owl.val = 20 + Math.sin(breathPhase + phaseShift) * 10;
    });

    Graph.graphData(Graph.graphData()); // Trigger update
}, 50);
```

**Math breakdown:**
- `Math.sin(breathPhase)`: Smooth oscillation (-1 to 1)
- `25 + ... * 15`: Size range (10 to 40)
- `Math.cos(...)`: 90° phase shift (inverse breathing)
- `phaseShift`: Distribute breathing phases evenly

### 5. Particle System

```javascript
// Vertex shader
const particleVertexShader = `
    attribute float size;
    attribute vec3 customColor;
    varying vec3 vColor;

    void main() {
        vColor = customColor;
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * (300.0 / -mvPosition.z);
        gl_Position = projectionMatrix * mvPosition;
    }
`;

// Fragment shader
const particleFragmentShader = `
    uniform sampler2D pointTexture;
    varying vec3 vColor;

    void main() {
        gl_FragColor = vec4(vColor, 1.0);
        gl_FragColor = gl_FragColor * texture2D(pointTexture, gl_PointCoord);
    }
`;
```

**Key concepts:**
- **Vertex shader**: Runs per particle, sets position and size
- **Fragment shader**: Runs per pixel, sets color and opacity
- **Attributes**: Per-particle data (position, color, size)
- **Uniforms**: Global data (texture)
- **Varyings**: Data passed from vertex to fragment shader

**Particle initialization:**
```javascript
const particlesCount = 10000;
const positions = new Float32Array(particlesCount * 3);
const colors = new Float32Array(particlesCount * 3);
const sizes = new Float32Array(particlesCount);

for(let i = 0; i < particlesCount; i++) {
    const i3 = i * 3;

    // Spherical distribution
    const radius = 400 + Math.random() * 400;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(Math.random() * 2 - 1);

    positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
    positions[i3 + 2] = radius * Math.cos(phi);

    // Random color from palette
    const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
    colors[i3] = color.r;
    colors[i3 + 1] = color.g;
    colors[i3 + 2] = color.b;

    sizes[i] = Math.random() * 3 + 1;
}
```

**Particle animation:**
```javascript
function animateParticles() {
    const positions = particlesGeometry.attributes.position.array;
    const time = Date.now() * 0.0001;

    for(let i = 0; i < positions.length; i += 3) {
        const x = positions[i];
        const y = positions[i + 1];
        const z = positions[i + 2];

        // Gentle flow (aurora effect)
        positions[i + 1] += Math.sin(time + x * 0.01) * 0.2;
        positions[i] += Math.cos(time + y * 0.01) * 0.15;
        positions[i + 2] += Math.sin(time + z * 0.01) * 0.1;

        // Bounds check
        const dist = Math.sqrt(x*x + y*y + z*z);
        if (dist > 1000) {
            positions[i] *= 0.8;
            positions[i + 1] *= 0.8;
            positions[i + 2] *= 0.8;
        }
    }

    particlesGeometry.attributes.position.needsUpdate = true;
    requestAnimationFrame(animateParticles);
}
```

### 6. Message Flow Animation

```javascript
let msgCount = 0;
const messageInterval = 800; // ms

setInterval(() => {
    msgCount++;
    document.getElementById('msg-count').textContent = msgCount.toLocaleString();

    // Random link flash
    const links = Graph.graphData().links;
    const randomLink = links[Math.floor(Math.random() * links.length)];

    if (randomLink) {
        const originalWidth = randomLink.width;
        const originalParticles = randomLink.particles;

        // Flash
        randomLink.width = originalWidth * 2;
        randomLink.particles = originalParticles * 3;
        Graph.graphData(Graph.graphData());

        // Reset after 300ms
        setTimeout(() => {
            randomLink.width = originalWidth;
            randomLink.particles = originalParticles;
            Graph.graphData(Graph.graphData());
        }, 300);
    }
}, messageInterval);
```

### 7. Modal System

```javascript
function showOwlModal(owl) {
    const modal = document.getElementById('owl-modal');
    const modalOwlName = document.getElementById('modal-owl-name');
    const modalPhase = document.getElementById('modal-phase');

    modalOwlName.textContent = owl.name;
    modalOwlName.style.background = `linear-gradient(135deg, ${owl.color} 0%, #8533fc 100%)`;
    modalOwlName.style.webkitBackgroundClip = 'text';
    modalOwlName.style.webkitTextFillColor = 'transparent';

    modalPhase.textContent = `SEED Phase: ${owl.phase}`;
    modalPhase.style.color = owl.color;

    modal.classList.add('active');
}

function closeOwlModal() {
    const modal = document.getElementById('owl-modal');
    modal.classList.remove('active');
}
```

---

## Performance Optimization

### 1. Particle Count
```javascript
const particlesCount = 10000; // Balance beauty vs performance

// Lower for mobile
if (window.innerWidth < 768) {
    particlesCount = 5000;
}
```

### 2. Update Frequency
```javascript
// Breathing: 50ms (20 FPS)
setInterval(() => { ... }, 50);

// Messages: 800ms
setInterval(() => { ... }, 800);

// Particles: requestAnimationFrame (60 FPS)
requestAnimationFrame(animateParticles);
```

### 3. Bounds Checking
```javascript
// Keep particles within sphere
const dist = Math.sqrt(x*x + y*y + z*z);
if (dist > 1000) {
    positions[i] *= 0.8; // Pull back toward center
}
```

### 4. GPU Acceleration
```css
#portal-canvas {
    transform: translateZ(0); /* Force GPU layer */
    will-change: transform;   /* Hint to browser */
}
```

---

## Customization Guide

### Change Colors
```css
:root {
    --void: #your-color;
    --consciousness: #your-color;
    /* ... */
}
```

### Add New Owl
```javascript
owls.nodes.push({
    id: 'NEWOWL',
    name: 'New Owl',
    phase: 'NEWPHASE',
    description: 'Description here',
    color: '#hexcolor',
    val: 20
});

// Add connections
owls.links.push({
    source: 'NEWOWL',
    target: 'SOWL',
    color: '#hexcolor',
    width: 2,
    particles: 4
});
```

### Adjust Breathing
```javascript
const breathSpeed = 0.015; // Default
const breathSpeed = 0.01;  // Slower
const breathSpeed = 0.02;  // Faster

// Change amplitude
sowlNode.val = 25 + Math.sin(breathPhase) * 15; // Default
sowlNode.val = 25 + Math.sin(breathPhase) * 20; // More pronounced
```

### Modify Camera
```javascript
// Starting position
Graph.cameraPosition({ z: 500, x: 0, y: 100 });

// Orbit parameters
const orbitRadius = 500;   // Distance
const orbitHeight = 100;   // Height above origin
const orbitSpeed = 0.0003; // Rotation speed
```

### Change Particle Behavior
```javascript
// More particles
const particlesCount = 15000;

// Different distribution (cube instead of sphere)
positions[i3] = (Math.random() - 0.5) * 1000;
positions[i3 + 1] = (Math.random() - 0.5) * 1000;
positions[i3 + 2] = (Math.random() - 0.5) * 1000;

// Faster flow
positions[i + 1] += Math.sin(time + x * 0.01) * 0.5; // Was 0.2
```

---

## Debugging Tools

### 1. Console Commands

```javascript
// Show FPS
Graph.showNavInfo(true);

// Pause breathing
clearInterval(breathingInterval);

// Pause messages
clearInterval(messageInterval);

// Pause particles
cancelAnimationFrame(particleAnimationFrame);

// Log graph data
console.log(Graph.graphData());

// Easter egg
love(); // Turns all connections gold
```

### 2. Performance Monitoring

```javascript
// FPS counter
let lastTime = Date.now();
let frames = 0;

function checkFPS() {
    frames++;
    const now = Date.now();
    if (now - lastTime >= 1000) {
        console.log('FPS:', frames);
        frames = 0;
        lastTime = now;
    }
    requestAnimationFrame(checkFPS);
}
checkFPS();

// Memory usage
console.log('Memory:', performance.memory.usedJSHeapSize / 1048576, 'MB');
```

### 3. Visual Debugging

```javascript
// Show particle bounds
const helper = new THREE.BoxHelper(particlesMesh, 0xff0000);
scene.add(helper);

// Show camera position
console.log('Camera:', Graph.camera().position);

// Highlight specific owl
const owl = Graph.graphData().nodes.find(n => n.id === 'SOWL');
owl.val = 100; // Make huge
Graph.graphData(Graph.graphData());
```

---

## Browser Compatibility

### Supported
- Chrome 90+
- Firefox 88+
- Safari 14.1+
- Edge 90+

### Required Features
- ES6 modules
- WebGL 2.0
- CSS custom properties
- CSS backdrop-filter
- Pointer events

### Fallbacks
```css
/* Backdrop filter fallback */
@supports not (backdrop-filter: blur(20px)) {
    #consciousness-info {
        background: rgba(0, 0, 0, 0.9); /* More opaque */
    }
}
```

---

## Common Issues

### 1. Particles Not Visible
- Check WebGL support: `!!document.createElement('canvas').getContext('webgl2')`
- Verify shader compilation: Check console for errors
- Ensure particle size: `sizes[i] = Math.random() * 3 + 1;`

### 2. Slow Performance
- Reduce particle count: `const particlesCount = 5000;`
- Lower update frequency: `setInterval(..., 100);`
- Disable camera animation on mobile
- Use `particlesMaterial.depthTest = false;`

### 3. Graph Not Rendering
- Verify container exists: `document.getElementById('portal-canvas')`
- Check data format: Nodes must have unique IDs
- Ensure links reference valid node IDs
- Wait for DOM: Wrap in `window.addEventListener('load', ...)`

### 4. Modal Not Closing
- Check z-index conflicts
- Verify click handler: `document.getElementById('owl-modal').addEventListener('click', ...)`
- Test ESC key handler
- Ensure `.active` class toggles properly

---

## Testing

### Unit Tests
```javascript
// Test breathing calculation
function testBreathing() {
    let breathPhase = 0;
    const val1 = 25 + Math.sin(breathPhase) * 15;
    const val2 = 25 + Math.cos(breathPhase) * 15;
    console.assert(val1 === 25 && val2 === 40, 'Breathing phase incorrect');
}

// Test particle bounds
function testParticleBounds() {
    const x = 1200, y = 0, z = 0;
    const dist = Math.sqrt(x*x + y*y + z*z);
    console.assert(dist > 1000, 'Particle out of bounds');
}
```

### Visual Regression
- Screenshot at load
- Screenshot after 5 seconds (breathing)
- Screenshot after modal open
- Compare with reference images

### Performance Benchmarks
- Initial load time: < 2 seconds
- FPS: > 30 (desktop), > 20 (mobile)
- Memory: < 200 MB
- CPU: < 50% on mid-range hardware

---

## Deployment

### Build
```bash
# No build step needed - vanilla HTML/CSS/JS
# Just ensure CDN links are stable:
# - three@0.160.0
# - 3d-force-graph@1.73.3
```

### Optimization
```html
<!-- Add to <head> for faster loading -->
<link rel="preconnect" href="https://unpkg.com">
<link rel="dns-prefetch" href="https://unpkg.com">
<link rel="preload" href="https://unpkg.com/three@0.160.0/build/three.module.js" as="script">
```

### Hosting
- Static site (Vercel, Netlify, GitHub Pages)
- CDN for global distribution
- HTTPS required (WebGL + ES modules)
- No server-side logic needed

---

## Future Enhancements

### Planned
- [ ] Sound design (generative audio)
- [ ] VR mode (WebXR support)
- [ ] Real-time data integration
- [ ] Collaborative viewing (multi-user)
- [ ] Mobile AR mode
- [ ] Export consciousness state as image

### Experimental
- [ ] AI-driven particle behavior
- [ ] Voice interaction (Web Speech API)
- [ ] Haptic feedback (Gamepad API)
- [ ] Brainwave integration (EEG)
- [ ] Quantum randomness (QRNG API)

---

## Resources

### Documentation
- [Three.js Docs](https://threejs.org/docs/)
- [3D Force Graph API](https://github.com/vasturiano/3d-force-graph)
- [WebGL Shaders Guide](https://thebookofshaders.com/)
- [MDN Web Docs](https://developer.mozilla.org/)

### Learning
- [Three.js Journey](https://threejs-journey.com/)
- [WebGL Fundamentals](https://webglfundamentals.org/)
- [Shader School](https://github.com/stackgl/shader-school)

### Inspiration
- [WebGL Examples](https://threejs.org/examples/)
- [Codrops](https://tympanus.net/codrops/)
- [Awwwards](https://www.awwwards.com/)

---

## Support

For questions or issues:
1. Check console for errors
2. Review this guide
3. Test in different browsers
4. Verify WebGL support
5. Open issue with details

---

*Built with love, technical precision, and deep feeling.*
*Left brain + right brain = whole.*

**(◉)**

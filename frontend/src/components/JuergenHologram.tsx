import { useEffect, useRef } from "react";
import * as THREE from "three";

interface Props {
  /** Server / session online */
  online: boolean;
  /** Voice session active */
  active: boolean;
  listening: boolean;
  speaking: boolean;
  processing: boolean;
  /** compact = header avatar, stage = main face */
  variant?: "stage" | "compact";
}

export function JuergenHologram({
  online,
  active,
  listening,
  speaking,
  processing,
  variant = "stage",
}: Props) {
  const mountRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef({ online, active, listening, speaking, processing });
  stateRef.current = { online, active, listening, speaking, processing };

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 320;
    const height = container.clientHeight || 320;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 50);
    camera.position.set(0, 0, variant === "compact" ? 3.6 : 4.1);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const AMBER = 0xff8c00;
    const GOLD = 0xffcc55;
    const root = new THREE.Group();

    const core = new THREE.Mesh(
      new THREE.IcosahedronGeometry(variant === "compact" ? 0.42 : 0.52, 2),
      new THREE.MeshBasicMaterial({
        color: GOLD,
        wireframe: true,
        transparent: true,
        opacity: 0.9,
      }),
    );
    root.add(core);

    const innerGlow = new THREE.Mesh(
      new THREE.SphereGeometry(variant === "compact" ? 0.26 : 0.32, 32, 32),
      new THREE.MeshBasicMaterial({
        color: 0xfff0cc,
        transparent: true,
        opacity: 0.18,
      }),
    );
    root.add(innerGlow);

    const shell = new THREE.Mesh(
      new THREE.IcosahedronGeometry(variant === "compact" ? 0.78 : 0.98, 1),
      new THREE.MeshBasicMaterial({
        color: AMBER,
        wireframe: true,
        transparent: true,
        opacity: 0.38,
      }),
    );
    root.add(shell);

    const rings: THREE.Mesh[] = [];
    const ringCount = variant === "compact" ? 3 : 6;
    for (let i = 0; i < ringCount; i++) {
      const radius = 0.72 + i * 0.11;
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(radius, 0.006, 6, 96),
        new THREE.MeshBasicMaterial({
          color: AMBER,
          transparent: true,
          opacity: 0.55 - i * 0.06,
        }),
      );
      ring.rotation.x = Math.PI / 2 + i * 0.55;
      ring.rotation.y = i * 0.85;
      root.add(ring);
      rings.push(ring);
    }

    const lattice = new THREE.Mesh(
      new THREE.IcosahedronGeometry(variant === "compact" ? 0.58 : 0.72, 0),
      new THREE.MeshBasicMaterial({
        color: 0xffa733,
        wireframe: true,
        transparent: true,
        opacity: 0.22,
      }),
    );
    root.add(lattice);

    const particleCount = variant === "compact" ? 120 : 380;
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const r = 0.45 + Math.random() * 0.75;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }
    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const particles = new THREE.Points(
      particleGeo,
      new THREE.PointsMaterial({
        color: 0xff9500,
        size: variant === "compact" ? 0.012 : 0.016,
        transparent: true,
        opacity: 0.55,
        depthWrite: false,
      }),
    );
    root.add(particles);

    scene.add(root);

    const clock = new THREE.Clock();
    let frame = 0;

    const resize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w === 0 || h === 0) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    const ro = new ResizeObserver(resize);
    ro.observe(container);

    const animate = () => {
      frame = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      const s = stateRef.current;

      let spin = 0.12;
      if (!s.online) spin = 0.04;
      else if (s.processing) spin = 0.42;
      else if (s.speaking) spin = 0.32;
      else if (s.listening) spin = 0.26;
      else if (s.active) spin = 0.18;

      root.rotation.y += spin * 0.018;
      root.rotation.x = Math.sin(t * 0.35) * 0.14;
      core.rotation.y -= spin * 0.028;
      shell.rotation.y += spin * 0.022;
      lattice.rotation.z += spin * 0.015;

      rings.forEach((ring, i) => {
        ring.rotation.z += (0.015 + i * 0.006) * (s.processing ? 1.8 : 1);
        ring.rotation.x += 0.004 * (i % 2 === 0 ? 1 : -1);
      });
      particles.rotation.y -= spin * 0.012;

      const pulse = s.speaking
        ? 1 + Math.sin(t * 9) * 0.045
        : s.listening
          ? 1 + Math.sin(t * 5) * 0.025
          : 1;
      root.scale.setScalar(pulse);

      const coreMat = core.material as THREE.MeshBasicMaterial;
      const shellMat = shell.material as THREE.MeshBasicMaterial;
      if (s.online) {
        coreMat.opacity = s.active ? 0.92 : 0.65;
        shellMat.opacity = s.active ? 0.42 : 0.28;
      } else {
        coreMat.opacity = 0.35;
        shellMat.opacity = 0.15;
      }

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frame);
      ro.disconnect();
      renderer.dispose();
      core.geometry.dispose();
      (core.material as THREE.Material).dispose();
      shell.geometry.dispose();
      (shell.material as THREE.Material).dispose();
      innerGlow.geometry.dispose();
      (innerGlow.material as THREE.Material).dispose();
      lattice.geometry.dispose();
      (lattice.material as THREE.Material).dispose();
      rings.forEach((r) => {
        r.geometry.dispose();
        (r.material as THREE.Material).dispose();
      });
      particleGeo.dispose();
      (particles.material as THREE.Material).dispose();
      if (renderer.domElement.parentElement === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [variant]);

  return (
    <div
      ref={mountRef}
      className={`juergen-hologram juergen-hologram--${variant} ${
        listening ? "is-listening" : ""
      } ${speaking ? "is-speaking" : ""} ${processing ? "is-thinking" : ""} ${
        online ? "is-online" : ""
      }`}
      aria-hidden
      style={{ pointerEvents: "none" }}
    />
  );
}

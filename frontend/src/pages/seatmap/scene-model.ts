import {
  BoxGeometry,
  Color,
  DataTexture,
  LinearFilter,
  LinearMipmapLinearFilter,
  RepeatWrapping,
  CylinderGeometry,
  ExtrudeGeometry,
  Group,
  InstancedMesh,
  Matrix4,
  Mesh,
  MeshStandardMaterial,
  PerspectiveCamera,
  PlaneGeometry,
  Shape,
  SpotLight,
  Vector3,
} from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import type { StaticSeat } from "./types";

export type VenueView = "interior" | "overview";
const hall = { halfWidth: 10, front: -4, rear: 16, height: 5.8 };
type XYZ = [number, number, number];

function curtainGeometry() {
  const geometry = new PlaneGeometry(2.2, 4.5, 64, 8);
  const positions = geometry.attributes.position;
  for (let i = 0; i < positions.count; i++) {
    const x = positions.getX(i);
    const y = positions.getY(i);
    positions.setXYZ(
      i,
      x * (1 - 0.04 * (y + 2.25)),
      y,
      0.16 * Math.cos(x * 16 + 0.12 * y),
    );
  }
  geometry.computeVertexNormals();
  return geometry;
}

function pianoGeometry() {
  const outline = new Shape();
  outline.moveTo(-0.75, 0.62);
  outline.lineTo(0.75, 0.62);
  outline.lineTo(0.75, -0.15);
  outline.bezierCurveTo(0.72, -0.68, 0.14, -0.48, 0.04, -1.22);
  outline.bezierCurveTo(-0.08, -1.86, -0.74, -1.76, -0.75, -1.34);
  outline.closePath();
  return new ExtrudeGeometry(outline, {
    depth: 0.27,
    bevelThickness: 0.02,
    bevelSize: 0.025,
    bevelSegments: 2,
  }).rotateX(-Math.PI / 2);
}

// Small, repeatable material tiles keep the hall independent of image downloads.
function surfaceTile(sample: (u: number, v: number) => number) {
  const size = 128;
  const pixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const value = Math.round(255 * sample(x / size, y / size));
      pixels.set([value, value, value, 255], (y * size + x) * 4);
    }
  }
  const texture = new DataTexture(pixels, size, size);
  texture.wrapS = texture.wrapT = RepeatWrapping;
  texture.generateMipmaps = true;
  texture.minFilter = LinearMipmapLinearFilter;
  texture.magFilter = LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

export function createVenueResources() {
  const wood = surfaceTile((u, v) => {
    const grain =
      2 * Math.PI * u * 18 +
      Math.sin(2 * Math.PI * v + 4 * Math.sin(2 * Math.PI * u));
    return 0.82 + 0.11 * Math.sin(grain) + 0.06 * Math.cos(3 * grain);
  });
  const weave = surfaceTile(
    (u, v) =>
      0.83 +
      0.08 * Math.cos(72 * Math.PI * u) +
      0.08 * Math.sin(64 * Math.PI * v),
  );
  weave.repeat.set(3, 4);
  const geometries = {
    box: new BoxGeometry(1, 1, 1),
    cushion: new RoundedBoxGeometry(0.75, 0.18, 0.72, 2, 0.075),
    shell: new RoundedBoxGeometry(0.71, 0.47, 0.07, 2, 0.03),
    back: new RoundedBoxGeometry(0.75, 0.76, 0.19, 2, 0.09),
    arm: new RoundedBoxGeometry(0.095, 0.1, 0.57, 1, 0.04),
    support: new CylinderGeometry(0.16, 0.22, 0.44, 8),
    curtain: curtainGeometry(),
    piano: pianoGeometry(),
  };
  const finish = (color: string, roughness = 0.8, metalness = 0) =>
    new MeshStandardMaterial({ color, roughness, metalness });
  const materials = {
    carpet: finish("#45424b"),
    runner: finish("#633844"),
    velvet: finish("#813345"),
    walnut: finish("#664634", 0.55),
    oak: finish("#bc8656", 0.64),
    paleOak: finish("#deaa75"),
    wall: finish("#514850"),
    felt: finish("#3e3942"),
    ceiling: finish("#514a4e"),
    brass: finish("#bd915d", 0.36, 0.42),
    metal: finish("#302c32", 0.48, 0.25),
    drape: finish("#853345"),
    piano: finish("#202025", 0.24),
    ivory: finish("#f2e5d1"),
    lamp: new MeshStandardMaterial({
      color: "#fff2cc",
      emissive: "#ffcc84",
      emissiveIntensity: 2.3,
    }),
    exit: new MeshStandardMaterial({
      color: "#d6ffeb",
      emissive: "#57bd98",
      emissiveIntensity: 1.3,
    }),
  };
  for (const material of [materials.walnut, materials.oak, materials.paleOak])
    material.map = wood;
  for (const material of [materials.carpet, materials.runner, materials.velvet])
    material.map = weave;
  return {
    geometries,
    materials,
    dispose() {
      wood.dispose();
      weave.dispose();
      for (const geometry of Object.values(geometries)) geometry.dispose();
      for (const material of Object.values(materials)) material.dispose();
    },
  };
}

export type VenueResources = ReturnType<typeof createVenueResources>;

export function createSeatObject(
  seat: StaticSeat,
  resources: VenueResources,
): Group {
  const group = new Group();
  group.name = `seat-${seat.id}`;
  group.position.set(seat.x, seat.y, seat.z);
  group.userData = {
    seatId: seat.id,
    row: seat.row,
    number: seat.number,
    label: seat.label,
  };
  const { geometries: g, materials: m } = resources;
  const cushion = new Mesh(g.cushion, m.velvet);
  cushion.position.y = 0.53;
  const back = new Mesh(g.back, m.velvet);
  back.position.set(0, 0.89, 0.28);
  back.rotation.x = 0.1;
  back.castShadow = true;
  const pedestal = new Mesh(g.support, m.metal);
  pedestal.position.y = 0.22;
  const shell = new Mesh(g.shell, m.walnut);
  shell.position.set(0, 0.79, 0.377);
  shell.rotation.x = back.rotation.x;
  group.add(cushion, back, pedestal, shell);
  cushion.castShadow = true;
  cushion.receiveShadow = true;
  for (const x of [-0.42, 0.42]) {
    const arm = new Mesh(g.arm, m.walnut);
    arm.position.set(x, 0.68, 0.02);
    const bracket = new Mesh(g.box, m.metal);
    bracket.position.set(x, 0.46, 0.16);
    bracket.scale.set(0.065, 0.38, 0.15);
    group.add(arm, bracket);
  }
  return group;
}

// Room, sconce spacing, stage-edge and instanced aisle lights adapted from Codrops
// CinemaSeatPreview/js/room.js. See public/licenses/codrops-cinema-seat-preview.txt.
export function createVenueStructure({
  geometries: g,
  materials: m,
}: VenueResources): Group {
  const room = new Group();
  room.name = "fixed-venue";
  function section(name: string) {
    const group = new Group();
    group.name = name;
    room.add(group);
    return group;
  }
  function box(
    parent: Group,
    name: string,
    size: XYZ,
    at: XYZ,
    mat: MeshStandardMaterial,
  ) {
    const mesh = new Mesh(g.box, mat);
    mesh.name = name;
    mesh.position.set(...at);
    mesh.scale.set(...size);
    mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  }
  function repeat(
    parent: Group,
    at: XYZ[],
    size: XYZ,
    mat: MeshStandardMaterial,
  ) {
    const mesh = new InstancedMesh(g.box, mat, at.length);
    const matrix = new Matrix4().makeScale(...size);
    at.forEach(([x, y, z], index) =>
      mesh.setMatrixAt(index, matrix.setPosition(x, y, z)),
    );
    parent.add(mesh);
    return mesh;
  }
  const { height: h, halfWidth: w, front, rear } = hall;
  const mid = (front + rear) / 2;
  box(room, "floor", [20, 0.3, 20], [0, -0.15, mid], m.carpet);
  box(room, "aisle", [2.2, 0.024, 14], [0, 0.012, 8], m.runner);
  const markers: XYZ[] = [];
  for (let row = 0; row < 10; row++) {
    for (const x of [-1.03, 1.03]) markers.push([x, 0.03, 1.8 + row * 1.2]);
  }
  repeat(room, markers, [0.065, 0.014, 0.26], m.lamp);
  box(room, "stage", [15.6, 0.72, 4.2], [0, 0.36, -1.65], m.oak);
  box(room, "stage-step", [5.4, 0.3, 0.55], [0, 0.15, 0.72], m.walnut);
  box(room, "apron-light", [15.3, 0.035, 0.025], [0, 0.62, 0.47], m.lamp);

  const frontWall = section("front-wall");
  box(frontWall, "stage-wall", [20.36, h, 0.18], [0, h / 2, front], m.wall);
  // A faceted timber acoustic shell behind the concert platform.
  for (let bay = -3; bay <= 3; bay++) {
    const panel = box(
      frontWall,
      "reflector",
      [1.56, 3.8, 0.22],
      [bay * 1.61, 2.82, -3.54 + Math.abs(bay) * 0.13],
      bay % 2 ? m.oak : m.paleOak,
    );
    panel.rotation.y = -bay * 0.055;
  }
  for (const x of [-6.55, 6.55]) {
    const drape = new Mesh(g.curtain, m.drape);
    drape.position.set(x, 3.02, -2.3);
    drape.castShadow = true;
    frontWall.add(drape);
  }
  box(frontWall, "proscenium", [16, 0.34, 1.2], [0, 5.3, -2.6], m.walnut);
  const rearWall = section("rear-wall");
  box(rearWall, "rear-shell", [20.36, h, 0.18], [0, h / 2, rear], m.wall);
  for (const x of [-0.57, 0.57]) {
    box(rearWall, "door-leaf", [1.1, 2.45, 0.09], [x, 1.225, 15.85], m.walnut);
    box(rearWall, "push-bar", [0.78, 0.045, 0.08], [x, 1.1, 15.77], m.brass);
  }
  box(rearWall, "exit-lamp", [0.76, 0.16, 0.12], [0, 2.68, 15.82], m.exit);
  for (const side of [-1, 1]) {
    const wall = section(side < 0 ? "left-wall" : "right-wall");
    box(wall, "side-shell", [0.18, h, 20], [side * w, h / 2, mid], m.wall);
    box(wall, "wainscot", [0.11, 1.08, 20], [side * 9.85, 0.54, mid], m.walnut);
    box(wall, "chair-rail", [0.13, 0.055, 20], [side * 9.8, 1.1, mid], m.brass);
    const battens: XYZ[] = [];
    for (let bay = 0; bay < 5; bay++) {
      const z = -2 + bay * 4;
      box(
        wall,
        "acoustic-panel",
        [0.12, 3.45, 3.68],
        [side * 9.84, 3.08, z],
        m.felt,
      );
      for (let slat = 0; slat < 8; slat++)
        battens.push([side * 9.74, 3.1, z - 1.55 + slat * 0.44]);
      box(
        wall,
        "sconce-base",
        [0.18, 0.57, 0.32],
        [side * 9.65, 2.55, z],
        m.brass,
      );
      box(
        wall,
        "sconce-diffuser",
        [0.12, 0.43, 0.2],
        [side * 9.52, 2.55, z],
        m.lamp,
      );
    }
    repeat(wall, battens, [0.07, 3.35, 0.058], m.oak);
  }
  const lid = section("ceiling");
  box(lid, "roof", [20.36, 0.22, 20.18], [0, h + 0.11, mid], m.ceiling);
  for (const z of [-1.6, 2.2, 6, 9.8, 13.6]) {
    box(lid, "coffer-beam", [20, 0.28, 0.3], [0, h - 0.14, z], m.walnut);
    for (const x of [-5, 5]) {
      box(lid, "light-housing", [4.5, 0.085, 0.32], [x, h - 0.315, z], m.metal);
      box(
        lid,
        "ceiling-diffuser",
        [4.25, 0.025, 0.18],
        [x, h - 0.37, z],
        m.lamp,
      );
    }
  }
  // A concert grand with a raised lid, a keyboard and a separate bench.
  const piano = section("grand-piano");
  piano.position.set(-0.8, 0.72, -1.65);
  piano.rotation.y = -1.27;
  const body = new Mesh(g.piano, m.piano);
  body.position.y = 0.8;
  const cover = new Mesh(g.piano, m.piano);
  cover.scale.y = 0.18;
  cover.rotation.z = 0.6;
  cover.position.set(-0.12, 1.5, 0);
  const soundboard = new Mesh(g.piano, m.brass);
  soundboard.scale.set(0.93, 0.03, 0.93);
  soundboard.position.y = 1.09;
  piano.add(body, soundboard, cover);
  for (const [x, z] of [
    [-0.57, -0.4],
    [0.57, -0.4],
    [-0.45, 1.22],
  ]) {
    box(piano, "piano-leg", [0.11, 0.78, 0.11], [x, 0.41, z], m.piano);
    box(piano, "caster", [0.14, 0.07, 0.14], [x, 0.05, z], m.brass);
  }
  box(piano, "lid-prop", [0.024, 0.74, 0.024], [0.42, 1.44, 0.27], m.brass);
  box(piano, "keyboard", [1.42, 0.1, 0.25], [0, 0.87, -0.7], m.ivory);
  const keys: XYZ[] = [];
  for (let i = 0; i < 35; i++)
    if (i % 7 !== 2 && i % 7 !== 6) keys.push([-0.68 + i * 0.039, 0.94, -0.66]);
  repeat(piano, keys, [0.023, 0.04, 0.13], m.piano);
  box(piano, "bench-seat", [0.86, 0.13, 0.43], [0, 0.5, -1.14], m.piano);
  for (const x of [-0.32, 0.32])
    box(piano, "bench-leg", [0.09, 0.47, 0.26], [x, 0.235, -1.14], m.walnut);
  piano.traverse((object) => {
    if (object instanceof Mesh) object.castShadow = true;
  });
  for (const [x, z] of [
    [-5, 6],
    [5, 9.8],
  ]) {
    const houseLight = new SpotLight("#ffe6bf", 130, 18, 1.04, 0.77, 2);
    houseLight.position.set(x, h - 0.41, z);
    houseLight.target.position.set(x * 0.4, 0, z - 1);
    room.add(houseLight, houseLight.target);
  }
  // Both stage spots belong to the lighting rig even when the roof is cut away.
  for (const x of [-4.3, 4.3]) {
    const spot = new SpotLight(new Color("#ffdda8"), 210, 22, 0.63, 0.72, 2);
    spot.position.set(x, 5.2, 1.3);
    spot.target.position.set(x * 0.32, 1.5, -2.7);
    const fixture = box(
      lid,
      "stage-spot",
      [0.34, 0.32, 0.47],
      spot.position.toArray(),
      m.metal,
    );
    fixture.lookAt(spot.target.position);
    room.add(spot, spot.target);
  }
  return room;
}

// A cutaway hides the whole near-side assembly, including its trim and fixtures.
export function updateVenueShell(
  room: Group,
  camera: Vector3,
  view: VenueView,
) {
  const interior = view === "interior";
  for (const group of room.children) {
    switch (group.name) {
      case "ceiling":
        group.visible = interior;
        break;
      case "front-wall":
        group.visible = interior || camera.z >= hall.front;
        break;
      case "rear-wall":
        group.visible = interior || camera.z <= hall.rear;
        break;
      case "left-wall":
        group.visible = interior || camera.x >= -hall.halfWidth;
        break;
      case "right-wall":
        group.visible = interior || camera.x <= hall.halfWidth;
        break;
    }
  }
}
/** 用固定场馆（含标识）的八个角适配画幅；同一计算用于初始、重置和 resize。 */
export function frameVenueCamera(aspect: number, view: VenueView = "overview") {
  const safeAspect = Number.isFinite(aspect) && aspect > 0 ? aspect : 1;
  if (view === "interior") {
    // At the rear cross-aisle. Keep the stage in frame on a portrait screen.
    const fov = Math.max(
      56,
      (2 * Math.atan(0.54 / safeAspect) * 180) / Math.PI,
    );
    const camera = new PerspectiveCamera(fov, safeAspect, 0.08, 100);
    const target = new Vector3(0, 2.0, 2.4);
    camera.position.set(0.8, 3.1, 15.25);
    camera.lookAt(target);
    return { camera, target, distance: camera.position.distanceTo(target) };
  }
  const camera = new PerspectiveCamera(42, safeAspect, 0.1, 250);
  const target = new Vector3(0, 2.1, 6);
  const backward = new Vector3(15, 22, 26).normalize();
  const right = new Vector3(0, 1, 0).cross(backward).normalize();
  const up = backward.clone().cross(right);
  const tangent = Math.tan((camera.fov * Math.PI) / 360);
  let distance = 0;
  for (const x of [-10.5, 10.5]) {
    for (const y of [-0.3, hall.height + 0.24]) {
      for (const z of [-4.5, 16.5]) {
        const offset = new Vector3(x, y, z).sub(target);
        distance = Math.max(
          distance,
          offset.dot(backward) +
            Math.max(
              Math.abs(offset.dot(right)) / (tangent * safeAspect),
              Math.abs(offset.dot(up)) / tangent,
            ),
        );
      }
    }
  }
  camera.position.copy(target).addScaledVector(backward, distance * 1.1);
  camera.lookAt(target);
  return { camera, target, distance: camera.position.distanceTo(target) };
}

import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { URL } from "node:url";
import { Box3, Raycaster, Vector2, Vector3 } from "three";
import ts from "typescript";

async function loadModule(path) {
  const source = await readFile(new URL(path, import.meta.url), "utf8");
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2023,
    },
  });
  const code = outputText.replace(
    /from "(three(?:\/[^"]*)?)"/g,
    (_, path) => `from "${import.meta.resolve(path)}"`,
  );
  return import(
    `data:text/javascript;base64,${Buffer.from(code).toString("base64")}`
  );
}

const { mockSeats } = await loadModule("../src/pages/seatmap/mock-data.ts");
const {
  createVenueResources,
  createSeatObject,
  createVenueStructure,
  frameVenueCamera,
  updateVenueShell,
} = await loadModule("../src/pages/seatmap/scene-model.ts");
const resources = createVenueResources();
const seats = mockSeats.map((seat) => createSeatObject(seat, resources));
const structure = createVenueStructure(resources);

test("120 个真实座椅模型保留业务编号、排座与原始坐标", () => {
  assert.equal(seats.length, 120);
  for (const [index, object] of seats.entries()) {
    const seat = mockSeats[index];
    assert.deepEqual(object.position.toArray(), [seat.x, seat.y, seat.z]);
    assert.equal(object.userData.seatId, seat.id);
    assert.equal(object.userData.row, seat.row);
    assert.equal(object.userData.number, seat.number);
    assert.equal(object.userData.label, seat.label);
    assert.ok(!new Box3().setFromObject(object).isEmpty());
  }
});

test("全部座椅互不重叠，落在地面内并避开中央过道及前方舞台", () => {
  const boxes = seats.map((object) => new Box3().setFromObject(object));
  const floor = new Box3().setFromObject(structure.getObjectByName("floor"));
  const stage = new Box3().setFromObject(structure.getObjectByName("stage"));
  const aisle = new Box3().setFromObject(structure.getObjectByName("aisle"));
  for (const [index, box] of boxes.entries()) {
    assert.ok(box.min.x > floor.min.x && box.max.x < floor.max.x);
    assert.ok(box.min.z > floor.min.z && box.max.z < floor.max.z);
    assert.ok(box.min.y >= -0.001);
    assert.ok(stage.max.z < box.min.z, "舞台应在全部座位前方");
    assert.equal(box.intersectsBox(aisle), false, "中央过道保持畅通");
    for (const other of boxes.slice(index + 1))
      assert.equal(box.intersectsBox(other), false);
  }
});

for (const [name, aspect] of [
  ["桌面", 760 / 520],
  ["窄屏", 340 / 420],
  ["宽屏", 1200 / 460],
]) {
  test(`${name}初始与重置镜头完整覆盖实际场馆和 120 座`, () => {
    const { camera, target } = frameVenueCamera(aspect);
    camera.lookAt(target);
    camera.updateMatrixWorld();
    const bounds = new Box3().setFromObject(structure);
    for (const object of seats) bounds.union(new Box3().setFromObject(object));
    for (const x of [bounds.min.x, bounds.max.x]) {
      for (const y of [bounds.min.y, bounds.max.y]) {
        for (const z of [bounds.min.z, bounds.max.z]) {
          const point = new Vector3(x, y, z).project(camera);
          assert.ok(
            Math.abs(point.x) < 0.96 && Math.abs(point.y) < 0.96,
            `${point.toArray()}`,
          );
          assert.ok(point.z > -1 && point.z < 1);
        }
      }
    }
  });
}

test("全景视角下每个座椅均能被射线命中并追溯到正确编号", () => {
  const { camera } = frameVenueCamera(760 / 520);
  camera.updateMatrixWorld();
  for (const seat of seats) seat.updateMatrixWorld(true);
  updateVenueShell(structure, camera.position, "overview");
  structure.updateMatrixWorld(true);
  const targets = [...seats];
  structure.traverseVisible((object) => {
    if (object.isMesh) targets.push(object);
  });
  const raycaster = new Raycaster();
  for (const seat of mockSeats) {
    const point = new Vector3(seat.x, seat.y + 0.6, seat.z).project(camera);
    raycaster.setFromCamera(new Vector2(point.x, point.y), camera);
    const hit = raycaster.intersectObjects(targets, true)[0];
    assert.ok(hit, `${seat.label} 应可命中`);
    let object = hit.object;
    while (object.parent && object.userData.seatId === undefined)
      object = object.parent;
    assert.equal(
      object.userData.seatId,
      seat.id,
      `${seat.label} 不应被其他座椅遮挡`,
    );
  }
});

test("馆内镜头被四面墙和顶棚围合，俯瞰时遮挡相机的一侧随旋转切换", () => {
  const { camera } = frameVenueCamera(1.5, "interior");
  updateVenueShell(structure, camera.position, "interior");
  structure.updateMatrixWorld(true);
  for (const [wall, direction] of [
    ["front-wall", [0, 0, -1]],
    ["rear-wall", [0, 0, 1]],
    ["left-wall", [-1, 0, 0]],
    ["right-wall", [1, 0, 0]],
    ["ceiling", [0, 1, 0]],
  ]) {
    const surface = structure.getObjectByName(wall);
    assert.equal(surface.visible, true);
    const ray = new Raycaster(camera.position, new Vector3(...direction));
    assert.ok(ray.intersectObject(surface, true).length > 0, wall);
  }
  for (const sign of [-1, 1]) {
    updateVenueShell(
      structure,
      new Vector3(sign * 22, 18, 6 + sign * 25),
      "overview",
    );
    assert.equal(structure.getObjectByName("ceiling").visible, false);
    assert.equal(structure.getObjectByName("right-wall").visible, sign < 0);
    assert.equal(structure.getObjectByName("left-wall").visible, sign > 0);
    assert.equal(structure.getObjectByName("rear-wall").visible, sign < 0);
    assert.equal(structure.getObjectByName("front-wall").visible, sign > 0);
  }
});

test.after(() => resources.dispose());

import assert from "node:assert/strict";
import { test } from "node:test";
import { URL } from "node:url";
import { Group, Vector2, Vector3 } from "three";
import { loadTypeScript } from "./helpers/load-typescript.mjs";

const load = (file) =>
  loadTypeScript(
    new URL("../src/pages/seatmap/" + file + ".ts", import.meta.url),
  );
const { mockSeats } = await load("mock-data");
const {
  createVenueResources,
  createSeatObject,
  createVenueStructure,
  frameVenueCamera,
  updateVenueShell,
  setSeatAppearance,
  setSeatPalette,
} = await load("scene-model");

test("三态只替换目标座位材质，取消后恢复且不改变任何座位坐标", () => {
  const resources = createVenueResources();
  try {
    const selected = createSeatObject(mockSeats[0], resources);
    const other = createSeatObject(mockSeats[1], resources);
    const before = selected.position.toArray();
    const otherMaterial = other.getObjectByName("seat-cushion").material;
    setSeatPalette(resources, {
      available: "#248372",
      sold: "#737582",
      selected: "#efb747",
      unavailable: "#938ba0",
    });
    setSeatAppearance(selected, resources, "selected");
    assert.notEqual(
      selected.getObjectByName("seat-cushion").material,
      otherMaterial,
    );
    assert.equal(other.getObjectByName("seat-cushion").material, otherMaterial);
    assert.equal(otherMaterial.color.getHexString(), "248372");
    assert.equal(
      selected.getObjectByName("seat-cushion").material.color.getHexString(),
      "efb747",
    );
    setSeatAppearance(selected, resources, "sold");
    assert.equal(
      selected.getObjectByName("seat-cushion").material.color.getHexString(),
      "737582",
    );
    setSeatAppearance(selected, resources, "available");
    assert.equal(
      selected.getObjectByName("seat-cushion").material,
      otherMaterial,
    );
    assert.deepEqual(selected.position.toArray(), before);
  } finally {
    resources.dispose();
  }
});

test("平面坐标、真实 3D 模型和点击命中使用相同的 120 个编号与位置", async () => {
  const { projectSeatToPlan, venueLayout } = await load("seat-layout");
  const { pickSeat } = await load("seat-interaction");
  const resources = createVenueResources();
  try {
    const group = new Group();
    for (const seat of mockSeats) group.add(createSeatObject(seat, resources));
    const structure = createVenueStructure(resources);
    const { camera } = frameVenueCamera(760 / 520);
    updateVenueShell(structure, camera.position, "overview");
    camera.updateMatrixWorld();
    for (const seat of mockSeats) {
      const { left, top } = projectSeatToPlan(seat);
      const object = group.getObjectByName("seat-" + seat.id);
      assert.ok(
        Math.abs(
          object.position.x - ((left / 100) * 20 - venueLayout.halfWidth),
        ) < 1e-10,
      );
      assert.ok(
        Math.abs(object.position.z - ((top / 100) * 20 + venueLayout.front)) <
          1e-10,
      );
      const point = new Vector3(seat.x, seat.y + 0.6, seat.z).project(camera);
      assert.equal(
        pickSeat(new Vector2(point.x, point.y), camera, group, structure),
        seat.id,
        seat.label,
      );
    }
  } finally {
    resources.dispose();
  }
});

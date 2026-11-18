import assert from "node:assert/strict";
import { test } from "node:test";
import { URL } from "node:url";
import {
  BoxGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  PerspectiveCamera,
  Vector2,
} from "three";
import { loadTypeScript } from "./helpers/load-typescript.mjs";

const { SeatPointerGesture, pickSeat } = await loadTypeScript(
  new URL("../src/pages/seatmap/seat-interaction.ts", import.meta.url),
);
const pointer = (overrides = {}) => ({
  pointerId: 1,
  clientX: 100,
  clientY: 100,
  button: 0,
  isPrimary: true,
  ...overrides,
});

test("轻点选择，拖动旋转及拖出后返回原点不触发选座", () => {
  const gesture = new SeatPointerGesture();
  gesture.down(pointer());
  assert.equal(gesture.up(pointer({ clientX: 102 })), true);
  gesture.down(pointer());
  gesture.move(pointer({ clientX: 120 }));
  assert.equal(gesture.up(pointer({ clientX: 120 })), false);
  gesture.down(pointer());
  gesture.move(pointer({ clientX: 150 }));
  gesture.move(pointer());
  assert.equal(gesture.up(pointer()), false);
});

test("右键、双指缩放、指针取消和不匹配的抬起都不触发选座", () => {
  const gesture = new SeatPointerGesture();
  gesture.down(pointer({ button: 2 }));
  assert.equal(gesture.up(pointer({ button: 2 })), false);
  gesture.down(pointer());
  gesture.down(pointer({ pointerId: 2, isPrimary: false }));
  assert.equal(gesture.up(pointer({ pointerId: 2, isPrimary: false })), false);
  assert.equal(gesture.up(pointer()), false);
  gesture.down(pointer());
  gesture.cancel();
  assert.equal(gesture.up(pointer()), false);
  gesture.down(pointer());
  assert.equal(gesture.up(pointer({ pointerId: 2 })), false);
});

test("只选中射线首先命中的可见座位，不穿过围墙或选中空白", () => {
  const geometry = new BoxGeometry(1, 1, 1);
  const material = new MeshBasicMaterial();
  const seats = new Group();
  const seat = new Group();
  seat.userData.seatId = 47;
  seat.add(new Mesh(geometry, material));
  seats.add(seat);
  const room = new Group();
  const wall = new Mesh(geometry, material);
  wall.scale.set(10, 10, 1);
  wall.position.z = 5;
  room.add(wall);
  const camera = new PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.set(0, 0, 10);
  camera.lookAt(0, 0, 0);
  assert.equal(pickSeat(new Vector2(), camera, seats, room), null);
  room.visible = false;
  assert.equal(pickSeat(new Vector2(), camera, seats, room), 47);
  seat.visible = false;
  assert.equal(pickSeat(new Vector2(), camera, seats, room), null);
  seat.visible = true;
  assert.equal(pickSeat(new Vector2(0.95, 0.95), camera, seats, room), null);
  geometry.dispose();
  material.dispose();
});

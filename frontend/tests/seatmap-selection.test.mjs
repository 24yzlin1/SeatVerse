import assert from "node:assert/strict";
import { test } from "node:test";
import { URL } from "node:url";
import { loadTypeScript } from "./helpers/load-typescript.mjs";

const { mockSeats, getMockEvent } = await loadTypeScript(
  new URL("../src/pages/seatmap/mock-data.ts", import.meta.url),
);
const {
  toggleSeatSelection,
  filterSelection,
  clearSelection,
  seatVisualState,
} = await loadTypeScript(
  new URL("../src/pages/seatmap/selection.ts", import.meta.url),
);
const { projectSeatToPlan, venueLayout } = await loadTypeScript(
  new URL("../src/pages/seatmap/seat-layout.ts", import.meta.url),
);
const states = new Map(
  getMockEvent(1001).seatStates.map((s) => [s.seatId, s.status]),
);

test("可选座位可选中，再次点击取消，输入集合与服务端状态不变", () => {
  const empty = new Set();
  const selected = toggleSeatSelection(empty, 1, mockSeats, states);
  assert.deepEqual([...selected], [1]);
  assert.equal(seatVisualState(1, states, selected), "selected");
  assert.equal(empty.size, 0);
  assert.equal(states.get(1), "available");
  const cancelled = toggleSeatSelection(selected, 1, mockSeats, states);
  assert.equal(cancelled.size, 0);
  assert.equal(seatVisualState(1, states, cancelled), "available");
  assert.deepEqual([...selected], [1]);
});

test("重复切换保持唯一编号，不影响其他已选座位", () => {
  let selected = new Set([2]);
  for (let i = 0; i < 101; i++)
    selected = toggleSeatSelection(selected, 1, mockSeats, states);
  assert.deepEqual([...selected].sort(), [1, 2]);
  assert.equal(selected.size, 2);
});

test("已预约、锁定、缺失和非法状态及场馆外编号均不可选择", () => {
  for (const status of ["sold", "locked", undefined, "unexpected"]) {
    const current = new Map(states);
    if (status === undefined) current.delete(1);
    else current.set(1, status);
    assert.equal(toggleSeatSelection(new Set(), 1, mockSeats, current).size, 0);
    assert.equal(
      seatVisualState(1, current, new Set([1])),
      status === "sold" ? "sold" : "unavailable",
    );
  }
  const extraneous = new Map(states).set(99999, "available");
  assert.equal(
    toggleSeatSelection(new Set(), 99999, mockSeats, extraneous).size,
    0,
  );
});

test("清空得到独立空集合，旧选择仍保持不变", () => {
  const before = new Set([1, 2]);
  const cleared = clearSelection();
  assert.equal(cleared.size, 0);
  assert.deepEqual([...before], [1, 2]);
  assert.notEqual(cleared, clearSelection());
});

test("刷新后删除失效、缺失、锁定和场馆外编号，保留仍可选座位", () => {
  const previous = new Set([1, 2, 3, 4, 5, 6, 99999]);
  const refreshed = new Map(states).set(1, "sold").set(2, "locked");
  refreshed.delete(5);
  refreshed.set(99999, "available");
  assert.deepEqual([...filterSelection(previous, mockSeats, refreshed)], [6]);
  assert.equal(previous.size, 7);
});

test("同一座位切换活动时按对应活动状态判定，不写入模拟数据", () => {
  const other = new Map(
    getMockEvent(1002).seatStates.map((s) => [s.seatId, s.status]),
  );
  const selected = toggleSeatSelection(new Set(), 1, mockSeats, states);
  assert.equal(filterSelection(selected, mockSeats, other).size, 0);
  assert.equal(toggleSeatSelection(new Set(), 1, mockSeats, other).size, 0);
  assert.equal(states.get(1), "available");
  assert.equal(other.get(1), "sold");
});

test("平面图按 X 向右、Z 向后直接投影，120 个座位坐标可还原", () => {
  for (const seat of mockSeats) {
    const { left, top } = projectSeatToPlan(seat);
    const x =
      (left / 100) * (venueLayout.halfWidth * 2) - venueLayout.halfWidth;
    const z =
      (top / 100) * (venueLayout.rear - venueLayout.front) + venueLayout.front;
    assert.ok(Math.abs(x - seat.x) < 1e-10, seat.label);
    assert.ok(Math.abs(z - seat.z) < 1e-10, seat.label);
    assert.ok(left > 0 && left < 100 && top > 0 && top < 100);
  }
  const first = projectSeatToPlan(mockSeats[0]);
  const next = projectSeatToPlan(mockSeats[1]);
  const rear = projectSeatToPlan(mockSeats[12]);
  assert.ok(first.left < next.left);
  assert.ok(first.top < rear.top);
});

test("平面位置不从排号、座号或数组顺序重新计算", () => {
  const seat = {
    ...mockSeats[0],
    id: 900,
    row: 31,
    number: 74,
    x: 5.4,
    z: 12.1,
  };
  const result = projectSeatToPlan(seat);
  assert.ok(Math.abs(result.left - 77) < 1e-10);
  assert.ok(Math.abs(result.top - 80.5) < 1e-10);
});

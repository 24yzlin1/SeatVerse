import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { URL } from "node:url";
import ts from "typescript";

// 复用工程已有 TypeScript 编译器，测试仍可运行于团队约定的 Node 20+。
const source = await readFile(
  new URL("../src/pages/seatmap/mock-data.ts", import.meta.url),
  "utf8",
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
  },
});
const { mockVenue, mockSeats, mockEvents, getMockEvent } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);

test("固定场馆包含 120 个唯一座位、排座和有效坐标", () => {
  assert.equal(mockSeats.length, 120);
  assert.equal(new Set(mockSeats.map((seat) => seat.id)).size, 120);
  assert.equal(
    new Set(mockSeats.map((seat) => `${seat.row}-${seat.number}`)).size,
    120,
  );
  assert.equal(
    new Set(mockSeats.map((seat) => `${seat.x},${seat.y},${seat.z}`)).size,
    120,
  );
  assert.deepEqual(
    [...new Set(mockSeats.map((seat) => seat.row))],
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  );
  for (const seat of mockSeats) {
    assert.ok(Number.isSafeInteger(seat.id) && seat.id > 0);
    assert.ok(seat.number >= 1 && seat.number <= 12);
    assert.equal(seat.label, `${seat.row}排${seat.number}号`);
    assert.equal(seat.seatType, "standard");
    assert.ok([seat.x, seat.y, seat.z].every(Number.isFinite));
  }
});

test("两场活动分别完整覆盖同一组座位，包含可选和已预约", () => {
  assert.equal(mockEvents.length, 2);
  assert.equal(new Set(mockEvents.map((event) => event.id)).size, 2);
  const expectedIds = mockSeats.map((seat) => seat.id).sort((a, b) => a - b);
  for (const event of mockEvents) {
    assert.ok(Number.isSafeInteger(event.id) && event.id > 0);
    assert.equal(event.venue.id, mockVenue.id);
    assert.equal(event.status, "published");
    assert.ok(Date.parse(event.endTime) > Date.parse(event.startTime));
    const fixture = getMockEvent(event.id);
    assert.equal(fixture.event.id, event.id);
    assert.equal(fixture.seatStates.length, 120);
    assert.deepEqual(
      fixture.seatStates.map((seat) => seat.seatId).sort((a, b) => a - b),
      expectedIds,
    );
    assert.deepEqual(
      new Set(fixture.seatStates.map((seat) => seat.status)),
      new Set(["available", "sold"]),
    );
    assert.ok(
      fixture.seatStates.every((seat) => !("x" in seat) && !("row" in seat)),
    );
  }
});

test("同一座位的两场状态不同，返回数据不可相互污染", () => {
  const first = getMockEvent(mockEvents[0].id);
  const second = getMockEvent(mockEvents[1].id);
  const differingSeat = first.seatStates.find((seat) =>
    second.seatStates.some(
      (other) => other.seatId === seat.seatId && other.status !== seat.status,
    ),
  );
  assert.ok(differingSeat);
  assert.notEqual(first.seatStates, second.seatStates);
  const target = first.seatStates.find(
    (seat) => seat.seatId === differingSeat.seatId,
  );
  assert.throws(() => {
    target.status = "locked";
  }, TypeError);
  assert.equal(
    getMockEvent(first.event.id).seatStates.find(
      (seat) => seat.seatId === target.seatId,
    ).status,
    differingSeat.status,
  );
});

test("未知或无效活动编号不默认为演示活动", () => {
  for (const id of [0, -1, 1.5, 99999, NaN, Infinity]) {
    assert.equal(getMockEvent(id), undefined);
  }
});

import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { URL } from "node:url";
import ts from "typescript";

const source = await readFile(
  new URL("../src/common/utils/groupBookings.ts", import.meta.url),
  "utf8",
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
  },
});
const { BOOKING_TABS, STATUS_LABEL, countBookings, groupBookings } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);

const items = [
  { id: 1, status: "reserved" },
  { id: 2, status: "reserved" },
  { id: 3, status: "cancelled" },
  { id: 4, status: "used" },
];

test("按状态统计条数", () => {
  assert.deepEqual(countBookings(items), {
    all: 4,
    reserved: 2,
    cancelled: 1,
    used: 1,
  });
});

test("按状态筛选列表", () => {
  assert.deepEqual(
    groupBookings(items, "all").map((item) => item.id),
    [1, 2, 3, 4],
  );
  assert.deepEqual(
    groupBookings(items, "reserved").map((item) => item.id),
    [1, 2],
  );
  assert.deepEqual(
    groupBookings(items, "cancelled").map((item) => item.id),
    [3],
  );
  assert.deepEqual(
    groupBookings(items, "used").map((item) => item.id),
    [4],
  );
});

test("各状态条数之和等于全部", () => {
  const counts = countBookings(items);
  assert.equal(counts.reserved + counts.cancelled + counts.used, counts.all);
});

test("空列表在每个 tab 下都返回空数组", () => {
  for (const tab of BOOKING_TABS) {
    assert.deepEqual(groupBookings([], tab.key), []);
  }
});

test("tab 顺序与状态标签一致", () => {
  assert.deepEqual(
    BOOKING_TABS.map((tab) => tab.key),
    ["all", "reserved", "cancelled", "used"],
  );
  assert.deepEqual(STATUS_LABEL, {
    reserved: "待参加",
    cancelled: "已取消",
    used: "已签到",
  });
});

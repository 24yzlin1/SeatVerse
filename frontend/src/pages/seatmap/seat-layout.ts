import type { StaticSeat } from "./types";

/** 米制右手系：X 向右，Y 向上，Z 从舞台向后；两视图共享同一场馆边界。 */
export const venueLayout = Object.freeze({
  halfWidth: 10,
  front: -4,
  rear: 16,
  height: 5.8,
  stage: Object.freeze({ width: 15.6, depth: 4.2, x: 0, z: -1.65 }),
  aisle: Object.freeze({ width: 2.2, depth: 14, x: 0, z: 8 }),
});

/** 平面图只投影原始 X/Z，绝不根据排座或数组下标重建坐标。 */
export function projectSeatToPlan(seat: Pick<StaticSeat, "x" | "z">) {
  return {
    left:
      ((seat.x + venueLayout.halfWidth) / (venueLayout.halfWidth * 2)) * 100,
    top:
      ((seat.z - venueLayout.front) / (venueLayout.rear - venueLayout.front)) *
      100,
  };
}

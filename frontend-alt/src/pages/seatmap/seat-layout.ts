import type { StaticSeat } from "./types";

// Metric right-handed system: X points right, Y points up, Z points from the
// stage towards the rear; both views share the same venue boundary.
export const venueLayout = Object.freeze({
  halfWidth: 10,
  front: -4,
  rear: 16,
  height: 5.8,
  stage: Object.freeze({ width: 15.6, depth: 4.2, x: 0, z: -1.65 }),
  aisle: Object.freeze({ width: 2.2, depth: 14, x: 0, z: 8 }),
});

// The plan projection only uses the raw X/Z values; coordinates are never
// rebuilt from row numbers or array indexes.
export function projectSeatToPlan(seat: Pick<StaticSeat, "x" | "z">) {
  return {
    left:
      ((seat.x + venueLayout.halfWidth) / (venueLayout.halfWidth * 2)) * 100,
    top:
      ((seat.z - venueLayout.front) / (venueLayout.rear - venueLayout.front)) *
      100,
  };
}

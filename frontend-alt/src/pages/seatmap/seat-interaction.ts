import {
  Mesh,
  Raycaster,
  type Camera,
  type Object3D,
  type Vector2,
} from "three";
import type { SeatId } from "./types";

type Pointer = Pick<
  PointerEvent,
  "pointerId" | "clientX" | "clientY" | "button" | "isPrimary"
>;

/** Track the whole gesture so a drag back to the origin or a two-finger zoom
 * is never mistaken for a click. */
export class SeatPointerGesture {
  private active = new Set<number>();
  private start: Pointer | null = null;

  down(event: Pointer) {
    this.active.add(event.pointerId);
    this.start =
      this.active.size === 1 && event.isPrimary && event.button === 0
        ? {
            ...event,
            pointerId: event.pointerId,
            clientX: event.clientX,
            clientY: event.clientY,
            button: event.button,
            isPrimary: event.isPrimary,
          }
        : null;
  }

  move(event: Pointer) {
    if (this.start?.pointerId === event.pointerId && this.distance(event) > 6) {
      this.start = null;
    }
  }

  up(event: Pointer) {
    this.active.delete(event.pointerId);
    const clicked =
      this.active.size === 0 &&
      this.start?.pointerId === event.pointerId &&
      event.button === 0 &&
      this.distance(event) <= 6;
    this.start = null;
    return clicked;
  }

  cancel() {
    this.active.clear();
    this.start = null;
  }

  private distance(event: Pointer) {
    return this.start
      ? Math.hypot(
          event.clientX - this.start.clientX,
          event.clientY - this.start.clientY,
        )
      : Infinity;
  }
}

/** Intersect with the visible meshes only, so a wall hit never selects a seat
 * hidden behind it. */
export function pickSeat(
  point: Vector2,
  camera: Camera,
  seats: Object3D,
  room: Object3D,
  raycaster = new Raycaster(),
): SeatId | null {
  camera.updateMatrixWorld();
  const meshes: Object3D[] = [];
  for (const root of [seats, room]) {
    root.updateMatrixWorld(true);
    root.traverseVisible((object) => {
      if (object instanceof Mesh) {
        meshes.push(object);
      }
    });
  }
  raycaster.setFromCamera(point, camera);
  let object: Object3D | null =
    raycaster.intersectObjects(meshes, false)[0]?.object ?? null;
  while (object && object.userData.seatId === undefined) {
    object = object.parent;
  }
  const id: unknown = object?.userData.seatId;
  return typeof id === "number" ? id : null;
}

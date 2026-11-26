<script lang="ts">
  import { T, useThrelte } from "@threlte/core";
  import { onDestroy, onMount } from "svelte";
  import {
    Group,
    InstancedMesh,
    PerspectiveCamera,
    Raycaster,
    SpotLight,
    Vector2,
  } from "three";
  import { OrbitControls } from "three/addons/controls/OrbitControls.js";
  import SceneLabel from "./SceneLabel.svelte";
  import SeatMesh from "./SeatMesh.svelte";
  import {
    createVenueResources,
    createVenueStructure,
    frameVenueCamera,
    setSeatPalette,
    updateVenueShell,
  } from "./scene-model";
  import {
    SeatPointerGesture,
    pickSeat,
  } from "./seat-interaction";
  import { seatVisualState } from "@/common/utils/seatSelection";
  import type { SeatSceneProps } from "./types";

  // Only the full-venue panorama view is kept; the cutaway shells follow the
  // orbit camera so the hall always reads as an open model.
  const props: SeatSceneProps = $props();
  const { canvas, size, invalidate } = useThrelte();
  const viewCamera = new PerspectiveCamera(42, 1, 0.1, 250);
  const resources = createVenueResources();
  const structure = createVenueStructure(resources);
  const seatGroup = new Group();
  const rows = $derived(props.seats.filter((seat) => seat.number === 1));
  let controls = $state.raw<OrbitControls>();

  onMount(() => {
    const orbit = new OrbitControls(viewCamera, canvas);
    orbit.enablePan = false;
    orbit.enableDamping = false;
    function updateView() {
      props.onSeatHover?.(null);
      canvas.style.cursor = "grab";
      updateVenueShell(structure, viewCamera.position);
      invalidate();
    }
    orbit.addEventListener("change", updateView);
    const gesture = new SeatPointerGesture();
    const raycaster = new Raycaster();
    const point = new Vector2();
    let hoverFrame = 0;
    const previousCursor = canvas.style.cursor;
    const seatAt = (event: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      if (
        rect.width <= 0 ||
        rect.height <= 0 ||
        event.clientX < rect.left ||
        event.clientX > rect.right ||
        event.clientY < rect.top ||
        event.clientY > rect.bottom
      ) {
        return null;
      }
      point.set(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1,
      );
      return pickSeat(point, viewCamera, seatGroup, structure, raycaster);
    };
    const hover = (id: number | null) => {
      props.onSeatHover?.(id);
      canvas.style.cursor =
        id === null
          ? "grab"
          : !props.disabled && props.seatStates.get(id) === "available"
            ? "pointer"
            : "not-allowed";
    };
    const resetPointer = () => {
      gesture.cancel();
      cancelAnimationFrame(hoverFrame);
      hover(null);
    };
    const pointerDown = (event: PointerEvent) => {
      gesture.down(event);
      cancelAnimationFrame(hoverFrame);
      hover(null);
    };
    const pointerMove = (event: PointerEvent) => {
      gesture.move(event);
      cancelAnimationFrame(hoverFrame);
      if (event.buttons === 0 && event.pointerType === "mouse") {
        hoverFrame = requestAnimationFrame(() => hover(seatAt(event)));
      }
    };
    const pointerUp = (event: PointerEvent) => {
      if (!gesture.up(event)) {
        return;
      }
      const id = seatAt(event);
      if (id !== null && !props.disabled) {
        props.onSeatToggle(id);
      }
      hover(id);
    };
    canvas.addEventListener("pointerdown", pointerDown);
    canvas.addEventListener("pointermove", pointerMove);
    canvas.addEventListener("pointerup", pointerUp);
    canvas.addEventListener("pointercancel", resetPointer);
    canvas.addEventListener("pointerleave", resetPointer);
    const applyTheme = () => {
      const style = getComputedStyle(canvas);
      setSeatPalette(resources, {
        available: style.getPropertyValue("--seat-available").trim(),
        sold: style.getPropertyValue("--seat-sold").trim(),
        selected: style.getPropertyValue("--seat-selected").trim(),
        unavailable: style.getPropertyValue("--seat-unavailable").trim(),
      });
      invalidate();
    };
    applyTheme();
    const themeObserver = new MutationObserver(applyTheme);
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class", "style"],
    });
    canvas.setAttribute("role", "img");
    canvas.setAttribute(
      "aria-label",
      `${props.seats.length} 座礼堂全馆 3D 选座，前方为舞台，中央为过道。拖动旋转，滚轮或双指缩放。点击座位即可选中或取消。`,
    );
    controls = orbit;
    return () => {
      orbit.removeEventListener("change", updateView);
      orbit.dispose();
      canvas.removeEventListener("pointerdown", pointerDown);
      canvas.removeEventListener("pointermove", pointerMove);
      canvas.removeEventListener("pointerup", pointerUp);
      canvas.removeEventListener("pointercancel", resetPointer);
      canvas.removeEventListener("pointerleave", resetPointer);
      cancelAnimationFrame(hoverFrame);
      themeObserver.disconnect();
      canvas.style.cursor = previousCursor;
    };
  });
  onDestroy(() => {
    structure.traverse((object) => {
      if (object instanceof InstancedMesh || object instanceof SpotLight) {
        object.dispose();
      }
    });
    resources.dispose();
  });

  $effect(() => {
    const { width, height } = $size;
    if (!controls || width <= 0 || height <= 0) {
      return;
    }
    const frame = frameVenueCamera(width / height);
    controls.minPolarAngle = 0.15;
    controls.maxPolarAngle = Math.PI / 2 - 0.15;
    controls.minAzimuthAngle = -Infinity;
    controls.maxAzimuthAngle = Infinity;
    controls.minDistance = 8;
    viewCamera.aspect = width / height;
    viewCamera.position.copy(frame.camera.position);
    viewCamera.updateProjectionMatrix();
    controls.target.copy(frame.target);
    controls.maxDistance = frame.distance * 1.8;
    controls.update();
    controls.saveState();
    updateVenueShell(structure, viewCamera.position);
    invalidate();
  });

  $effect(() => {
    const version = props.resetVersion;
    if (!controls || version === undefined) {
      return;
    }
    controls.reset();
    updateVenueShell(structure, viewCamera.position);
    invalidate();
  });
</script>

<T is={viewCamera} makeDefault manual />
<T.HemisphereLight args={["#fff0df", "#a18d92", 1.35]} />
<T.DirectionalLight
  position={[5, 8, 11]}
  intensity={1.1}
  color="#fff1dd"
  castShadow
  oncreate={(light) => {
    Object.assign(light.shadow.camera, {
      left: -13,
      right: 13,
      top: 12,
      bottom: -12,
      near: 0.1,
      far: 42,
    });
    light.shadow.camera.updateProjectionMatrix();
    light.shadow.mapSize.set(1024, 1024);
    light.shadow.normalBias = 0.018;
    light.shadow.bias = -0.0002;
  }}
/>
<T is={structure} dispose={false} />
<T is={seatGroup} dispose={false}>
  {#each props.seats as seat (seat.id)}
    <SeatMesh
      {seat}
      {resources}
      visualState={seatVisualState(
        seat.id,
        props.seatStates,
        props.selectedSeatIds,
      )}
    />
  {/each}
</T>
<SceneLabel
  text="舞台 · STAGE"
  color="#fff4da"
  background="#433239"
  position={[0, 1.25, -1.2]}
  width={5}
/>
<SceneLabel
  text="入口 / 后排"
  color="#fff4da"
  position={[0, 0.5, 15]}
  width={3.6}
/>
{#each rows as seat (seat.id)}
  <SceneLabel
    text={`${seat.row}排`}
    color="#fff4da"
    position={[-8.6, 0.5, seat.z]}
    width={1.6}
  />
{/each}

<script lang="ts">
  import { T, useThrelte } from "@threlte/core";
  import { onDestroy, onMount } from "svelte";
  import { InstancedMesh, PerspectiveCamera, SpotLight, Vector3 } from "three";
  import { OrbitControls } from "three/addons/controls/OrbitControls.js";

  import { venueLayout } from "./seat-layout";
  import {
    createSeatObject,
    createVenueResources,
    createVenueStructure,
    updateVenueShell,
  } from "./scene-model";
  import type { StaticSeat } from "@/common/api";

  // Read-only seat perspective world: the camera sits at eye height above
  // one fixed seat looking at the stage. Every seat keeps the shared velvet
  // finish of the hall's ordinary seats and nothing in this scene is
  // selectable; dragging orbits and the wheel zooms.
  const props: {
    seats: readonly StaticSeat[];
    focusSeat: StaticSeat;
  } = $props();

  const { canvas, size, invalidate } = useThrelte();
  const viewCamera = new PerspectiveCamera(50, 1, 0.1, 250);
  const resources = createVenueResources();
  const structure = createVenueStructure(resources);
  // No state materials here: every seat is built from the default velvet,
  // so the preview always reads as a full wine-red house.
  const seatObjects = $derived(
    props.seats.map((seat) => createSeatObject(seat, resources)),
  );
  let controls = $state.raw<OrbitControls>();

  onMount(() => {
    const orbit = new OrbitControls(viewCamera, canvas);
    orbit.enablePan = false;
    orbit.enableDamping = false;
    orbit.minDistance = 1.5;
    orbit.maxDistance = 14;
    orbit.minPolarAngle = 0.15;
    orbit.maxPolarAngle = Math.PI / 2 - 0.15;
    orbit.minAzimuthAngle = -Infinity;
    orbit.maxAzimuthAngle = Infinity;
    // Eye height above the seat, a touch behind its back so the seat edge
    // reads at the bottom of the frame.
    viewCamera.position.set(
      props.focusSeat.x,
      props.focusSeat.y + 1.45,
      props.focusSeat.z + 0.35,
    );
    const target = new Vector3(
      props.focusSeat.x * 0.6,
      props.focusSeat.y + 1.1,
      Math.max(props.focusSeat.z - 6, venueLayout.stage.z + 1),
    );
    orbit.target.copy(target);
    viewCamera.lookAt(target);
    viewCamera.updateProjectionMatrix();
    orbit.update();
    orbit.saveState();
    canvas.style.cursor = "grab";
    const updateView = () => {
      updateVenueShell(structure, viewCamera.position);
      invalidate();
    };
    orbit.addEventListener("change", updateView);
    // The theme palette is deliberately not applied here: the shared CSS
    // variables tint available seats teal, while this preview must show the
    // venue's native wine-red velvet across the whole house.
    canvas.setAttribute("role", "img");
    canvas.setAttribute(
      "aria-label",
      `${props.focusSeat.label} 座位视角预览：正对舞台，拖动环视，滚轮缩放。`,
    );
    controls = orbit;
    return () => {
      orbit.removeEventListener("change", updateView);
      orbit.dispose();
      canvas.style.cursor = "";
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
    viewCamera.aspect = width / height;
    viewCamera.updateProjectionMatrix();
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
{#each seatObjects as seatObject (seatObject.name)}
  <T is={seatObject} dispose={false} />
{/each}

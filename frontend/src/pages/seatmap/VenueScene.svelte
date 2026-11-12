<script lang="ts">
  import { T, useThrelte } from "@threlte/core";
  import { onDestroy, onMount, untrack } from "svelte";
  import { InstancedMesh, PerspectiveCamera, SpotLight, Vector3 } from "three";
  import { OrbitControls } from "three/addons/controls/OrbitControls.js";
  import SceneLabel from "./SceneLabel.svelte";
  import SeatMesh from "./SeatMesh.svelte";
  import {
    createVenueResources,
    createVenueStructure,
    frameVenueCamera,
    updateVenueShell,
    type VenueView,
  } from "./scene-model";
  import type { StaticSeat } from "./types";

  interface Props {
    seats: readonly StaticSeat[];
    view: VenueView;
    command: {
      action: "reset" | "left" | "right" | "in" | "out";
      revision: number;
    };
    onReady: () => void;
  }
  const props: Props = $props();
  const { canvas, size, invalidate } = useThrelte();
  const viewCamera = new PerspectiveCamera(42, 1, 0.1, 250);
  const resources = createVenueResources();
  const structure = createVenueStructure(resources);
  const rows = $derived(props.seats.filter((seat) => seat.number === 1));
  let controls = $state.raw<OrbitControls>();

  onMount(() => {
    const orbit = new OrbitControls(viewCamera, canvas);
    orbit.enablePan = false;
    orbit.enableDamping = false;
    function updateView() {
      updateVenueShell(
        structure,
        viewCamera.position,
        untrack(() => props.view),
      );
      invalidate();
    }
    orbit.addEventListener("change", updateView);
    canvas.setAttribute("role", "img");
    canvas.setAttribute(
      "aria-label",
      "120 座礼堂 3D 预览，前方为舞台，中央为过道。可使用上方按钮调整视角。",
    );
    controls = orbit;
    props.onReady();
    return () => {
      orbit.removeEventListener("change", updateView);
      orbit.dispose();
    };
  });
  onDestroy(() => {
    structure.traverse((object) => {
      if (object instanceof InstancedMesh || object instanceof SpotLight)
        object.dispose();
    });
    resources.dispose();
  });

  $effect(() => {
    const { width, height } = $size;
    if (!controls || width <= 0 || height <= 0) return;
    const interior = props.view === "interior";
    const frame = frameVenueCamera(width / height, props.view);
    viewCamera.fov = frame.camera.fov;
    controls.minPolarAngle = interior ? 1.34 : 0.15;
    controls.maxPolarAngle = interior ? 1.57 : Math.PI / 2 - 0.15;
    controls.minAzimuthAngle = interior ? -0.52 : -Infinity;
    controls.maxAzimuthAngle = interior ? 0.52 : Infinity;
    controls.minDistance = interior ? 7 : 8;
    viewCamera.aspect = width / height;
    viewCamera.position.copy(frame.camera.position);
    viewCamera.updateProjectionMatrix();
    controls.target.copy(frame.target);
    controls.maxDistance = interior ? 13.2 : frame.distance * 1.8;
    controls.update();
    controls.saveState();
    updateVenueShell(structure, viewCamera.position, props.view);
    invalidate();
  });

  $effect(() => {
    const command = props.command;
    if (!controls) return;
    if (command.action === "reset") {
      controls.reset();
    } else {
      const offset = viewCamera.position.clone().sub(controls.target);
      if (command.action === "left" || command.action === "right") {
        offset.applyAxisAngle(
          new Vector3(0, 1, 0),
          command.action === "left" ? -Math.PI / 9 : Math.PI / 9,
        );
      } else {
        offset.multiplyScalar(command.action === "in" ? 0.85 : 1 / 0.85);
      }
      viewCamera.position.copy(controls.target).add(offset);
      controls.update();
    }
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
{#each props.seats as seat (seat.id)}
  <SeatMesh {seat} {resources} />
{/each}
{#if props.view === "overview"}
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
{/if}

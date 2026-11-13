<script lang="ts">
  import { Canvas } from "@threlte/core";
  import { AgXToneMapping, PCFShadowMap } from "three";
  import VenueScene from "./VenueScene.svelte";
  import type { VenueView } from "./scene-model";
  import type { StaticSeat } from "./types";

  const props: { seats: readonly StaticSeat[] } = $props();
  let view = $state<VenueView>("interior");
  let ready = $state(false);
  let sceneFailed = $state(false);
  let command = $state({
    action: "reset" as "reset" | "left" | "right" | "in" | "out",
    revision: 0,
  });

  function move(action: typeof command.action) {
    command = { action, revision: command.revision + 1 };
  }
</script>

<div class="scene-toolbar" aria-label="场馆视角控制">
  <div class="view-modes" role="group" aria-label="场馆视图">
    <button
      type="button"
      aria-pressed={view === "interior"}
      onclick={() => (view = "interior")}>馆内视角</button
    >
    <button
      type="button"
      aria-pressed={view === "overview"}
      onclick={() => (view = "overview")}>全馆俯瞰</button
    >
  </div>
  <div class="view-buttons">
    <button
      type="button"
      aria-label="向左旋转视角"
      disabled={!ready}
      onclick={() => move("left")}>↶</button
    >
    <button
      type="button"
      aria-label="向右旋转视角"
      disabled={!ready}
      onclick={() => move("right")}>↷</button
    >
    <button
      type="button"
      aria-label="放大场馆"
      disabled={!ready}
      onclick={() => move("in")}>＋</button
    >
    <button
      type="button"
      aria-label="缩小场馆"
      disabled={!ready}
      onclick={() => move("out")}>−</button
    >
    <button
      type="button"
      class="reset"
      disabled={!ready}
      onclick={() => move("reset")}>重置视角</button
    >
  </div>
</div>
<div class="scene-viewport">
  <svelte:boundary
    onerror={() => {
      ready = false;
      sceneFailed = true;
    }}
  >
    <Canvas
      renderMode="on-demand"
      shadows={PCFShadowMap}
      dpr={[1, 1.75]}
      toneMapping={AgXToneMapping}
    >
      <VenueScene
        seats={props.seats}
        {view}
        {command}
        onReady={() => {
          ready = true;
        }}
      />
    </Canvas>
    {#snippet failed(error, reset)}
      <div class="scene-error" role="alert">
        <strong>3D 场馆暂时无法显示</strong>
        <p>
          {error instanceof Error && /WebGL/i.test(error.message)
            ? "请确认浏览器支持 WebGL 2。"
            : "请尝试重新加载场景。"}你仍可展开下方平面图查看座位。
        </p>
        <button
          type="button"
          onclick={() => {
            sceneFailed = false;
            reset();
          }}>重新加载场景</button
        >
      </div>
    {/snippet}
  </svelte:boundary>
  {#if !ready && !sceneFailed}
    <p class="loading" role="status">正在准备场馆…</p>
  {/if}
</div>
<p class="scene-caption">拖动旋转视角，滚轮或双指缩放。</p>

<style>
  .scene-toolbar,
  .view-buttons {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .scene-toolbar {
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
  }
  .view-modes {
    display: flex;
    gap: 2px;
    padding: 3px;
    border-radius: var(--radius-sm);
    background: var(--secondary);
  }
  .view-modes button {
    font-size: 13px;
    padding: 0 12px;
    border: none;
    background: transparent;
  }
  .view-modes button[aria-pressed="true"] {
    background: var(--primary);
    color: var(--primary-foreground);
  }
  button {
    min-width: 36px;
    min-height: 36px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--background);
    color: var(--foreground);
    cursor: pointer;
    font-size: 18px;
  }
  button:hover:enabled {
    background: var(--secondary);
  }
  button:disabled {
    opacity: 0.45;
    cursor: wait;
  }
  button:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 3px;
  }
  button.reset {
    padding: 0 12px;
    font-size: 12px;
    margin-left: 4px;
  }
  .scene-viewport {
    height: clamp(420px, 46vw, 540px);
    width: 100%;
    position: relative;
    background: var(--background);
    cursor: grab;
  }
  .scene-viewport:active {
    cursor: grabbing;
  }
  .scene-caption {
    border-top: 1px solid var(--border);
    padding: 12px 20px;
    font-size: 11px;
    color: var(--muted-foreground);
    text-align: center;
  }
  .scene-error {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 24px;
    text-align: center;
    background: var(--background);
    cursor: auto;
    z-index: 2;
  }
  .scene-error p {
    font-size: 13px;
    line-height: 1.8;
    color: var(--muted-foreground);
  }
  .scene-error button {
    font-size: 13px;
    padding: 0 16px;
  }
  .loading {
    position: absolute;
    inset: 50% 0 auto;
    text-align: center;
    font-size: 13px;
    color: var(--muted-foreground);
    pointer-events: none;
  }
  @media (max-width: 480px) {
    .scene-toolbar {
      padding: 12px 16px;
    }
    .scene-viewport {
      height: 420px;
    }
  }
</style>

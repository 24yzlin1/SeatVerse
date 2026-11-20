<script lang="ts">
  import SeatLegend from "./SeatLegend.svelte";
  import SeatPlan from "./SeatPlan.svelte";
  import SelectedSeatPanel from "./SelectedSeatPanel.svelte";
  import { seatVisualState } from "./selection";
  import { eventStatusLabel } from "@/common/utils/eventAvailability";
  import type { SeatId, SeatMapData, SelectedSeatIds } from "./types";
  interface Props {
    data: SeatMapData;
    selectedSeatIds: SelectedSeatIds;
    selectionDisabled: boolean;
    disabledReason: string;
    submitting: boolean;
    refreshing: boolean;
    loggedIn: boolean;
    feedback: string;
    onSeatToggle: (id: SeatId) => void;
    onClear: () => void;
    onSubmit: () => void;
    onRefresh: () => void;
  }
  const props: Props = $props();
  const sceneModule = import("./SeatScene.svelte");
  const event = $derived(props.data.event);
  const seats = $derived(props.data.seats);
  const states = $derived(props.data.seatStates);
  let hoveredSeatId = $state<SeatId | null>(null);
  const hoveredSeat = $derived(seats.find((seat) => seat.id === hoveredSeatId));
  const selectedSeats = $derived(
    seats.filter((seat) => props.selectedSeatIds.has(seat.id)),
  );
  const availableCount = $derived(
    [...states.values()].filter((state) => state === "available").length,
  );
  const soldCount = $derived(
    [...states.values()].filter((state) => state === "sold").length,
  );
  const labels = {
    available: "可选",
    sold: "已预约",
    selected: "本地已选",
    unavailable: "锁定或状态未知，不可选",
  };
  const format = new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
</script>

<main class="seatmap-page">
  <header class="page-header">
    <p class="brand">SEATVERSE <span>/ 场馆选座</span></p>
    <nav aria-label="活动导航">
      <a href={`#/events/${event.id}`}>返回活动详情</a><a href="#/events"
        >活动列表</a
      >
    </nav>
  </header>
  <section class="event-header" aria-labelledby="event-title">
    <p class="eyebrow">{event.venue.name}</p>
    <h1 id="event-title">{event.title}</h1>
    <p class="event-time">
      <time datetime={event.startTime}
        >{format.format(new Date(event.startTime))}</time
      ><span>—</span><time datetime={event.endTime}
        >{format.format(new Date(event.endTime))}</time
      ><span>{eventStatusLabel(event)}</span>
    </p>
    {#if event.description}<p class="description">{event.description}</p>{/if}
  </section>
  <div class="preview-layout">
    <section class="venue-card" aria-labelledby="preview-title">
      <div class="card-heading">
        <div>
          <h2 id="preview-title">3D 场馆选座</h2>
          <p>{seats.length} 座 · 可选 {availableCount} · 已预约 {soldCount}</p>
        </div>
        <button
          type="button"
          disabled={props.submitting || props.refreshing}
          onclick={props.onRefresh}
          >{props.refreshing ? "更新中…" : "刷新座位"}</button
        >
      </div>
      <SeatLegend />
      {#if seats.length === 0}
        <p class="scene-loading" role="status">
          该场馆尚未配置座位，请联系活动主办方。
        </p>
      {:else}
        {#await sceneModule}
          <p class="scene-loading" role="status">正在加载 3D 场馆…</p>
        {:then scene}
          {#key event.venue.id}
            <scene.default
              {seats}
              seatStates={states}
              selectedSeatIds={props.selectedSeatIds}
              disabled={props.selectionDisabled}
              onSeatToggle={props.onSeatToggle}
              onSeatHover={(id) => (hoveredSeatId = id)}
            />
          {/key}
        {:catch}<p class="scene-loading" role="alert">
            3D 场馆加载失败，可继续使用下方平面图选座。
          </p>{/await}
        <p class="seat-inspection">
          {#if hoveredSeat}<strong>{hoveredSeat.label}</strong> · {labels[
              seatVisualState(hoveredSeat.id, states, props.selectedSeatIds)
            ]}{:else}指向 3D 或平面座位，查看排号、座号和状态。{/if}
        </p>
        <details class="flat-preview" open>
          <summary>平面选座 <span>与 3D 同步 · 舞台在上方</span></summary>
          <SeatPlan
            {seats}
            seatStates={states}
            selectedSeatIds={props.selectedSeatIds}
            disabled={props.selectionDisabled}
            onSeatToggle={props.onSeatToggle}
            onSeatHover={(id) => (hoveredSeatId = id)}
          />
        </details>
      {/if}
    </section>
    <SelectedSeatPanel
      seats={selectedSeats}
      submitting={props.submitting}
      disabledReason={props.disabledReason}
      feedback={props.feedback}
      loggedIn={props.loggedIn}
      onSeatToggle={props.onSeatToggle}
      onClear={props.onClear}
      onSubmit={props.onSubmit}
    />
  </div>
  <details class="data-details">
    <summary>查看场馆座位数据 <span>后端编号、坐标与本场状态</span></summary>
    <p>
      坐标单位：米。X 向右、Y 向上、Z 从舞台指向后排；平面与 3D
      使用同一份后端坐标。
    </p>
    <div class="table-scroll" role="group" aria-label="场馆座位数据，可滚动">
      <table>
        <caption
          >活动 {event.id} · 场馆 {event.venue.id} · {seats.length} 座</caption
        ><thead
          ><tr
            ><th scope="col">编号</th><th scope="col">座位</th><th scope="col"
              >X</th
            ><th scope="col">Y</th><th scope="col">Z</th><th scope="col"
              >本场状态</th
            ></tr
          ></thead
        >
        <tbody
          >{#each seats as seat (seat.id)}<tr
              ><td>{seat.id}</td><td>{seat.label}</td><td>{seat.x}</td><td
                >{seat.y}</td
              ><td>{seat.z}</td><td
                >{labels[
                  seatVisualState(seat.id, states, props.selectedSeatIds)
                ]}</td
              ></tr
            >{/each}</tbody
        >
      </table>
    </div>
  </details>
</main>

<style>
  .seatmap-page {
    max-width: 1120px;
    margin: 0 auto;
    padding: 32px 24px 48px;
  }
  .page-header,
  .card-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }
  .page-header {
    margin-bottom: 32px;
  }
  .brand {
    font-size: 14px;
    font-weight: 750;
    letter-spacing: 0.08em;
  }
  .brand span {
    margin-left: 8px;
    font-weight: 400;
    letter-spacing: 0;
    color: var(--muted-foreground);
  }
  nav {
    display: flex;
    gap: 16px;
    font-size: 12px;
  }
  a {
    text-decoration: underline;
    text-underline-offset: 3px;
  }
  .event-header {
    margin: 28px 0;
  }
  .eyebrow {
    color: var(--muted-foreground);
    font-size: 13px;
    margin-bottom: 10px;
  }
  h1 {
    font-size: clamp(24px, 3.5vw, 36px);
    font-weight: 650;
    letter-spacing: -0.04em;
    line-height: 1.3;
    margin-bottom: 14px;
  }
  .event-time {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    color: var(--muted-foreground);
    font-size: 13px;
  }
  .description {
    margin-top: 14px;
    font-size: 13px;
    line-height: 1.8;
    white-space: pre-line;
  }
  .preview-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 280px;
    gap: 20px;
    align-items: start;
  }
  .venue-card {
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    background: var(--card);
    overflow: hidden;
  }
  .card-heading {
    padding: 20px;
    border-bottom: 1px solid var(--border);
  }
  .card-heading h2 {
    font-size: 15px;
    font-weight: 600;
  }
  .card-heading p {
    margin-top: 6px;
    color: var(--muted-foreground);
    font-size: 12px;
  }
  button {
    flex-shrink: 0;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 8px 12px;
    font-size: 12px;
    cursor: pointer;
  }
  button:disabled {
    opacity: 0.5;
    cursor: wait;
  }
  button:focus-visible,
  a:focus-visible,
  summary:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 3px;
  }
  .scene-loading {
    min-height: 280px;
    padding: 40px 24px;
    color: var(--muted-foreground);
    font-size: 13px;
  }
  .seat-inspection {
    min-height: 48px;
    padding: 14px 20px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    color: var(--muted-foreground);
  }
  .seat-inspection strong {
    color: var(--foreground);
  }
  .flat-preview {
    border-top: 1px solid var(--border);
  }
  .flat-preview > summary {
    padding: 16px 20px;
  }
  .data-details {
    margin-top: 24px;
    padding: 18px 24px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
  summary {
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
  }
  summary span {
    margin-left: 12px;
    font-size: 12px;
    color: var(--muted-foreground);
    font-weight: 400;
  }
  .data-details > p {
    margin: 16px 0;
    font-size: 12px;
    color: var(--muted-foreground);
  }
  .table-scroll {
    overflow: auto;
    max-height: 320px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    white-space: nowrap;
    text-align: left;
  }
  caption {
    text-align: left;
    padding-bottom: 12px;
    color: var(--muted-foreground);
  }
  th,
  td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
  }
  th {
    background: var(--muted);
    font-weight: 500;
  }
  @media (max-width: 800px) {
    .preview-layout {
      grid-template-columns: minmax(0, 1fr);
    }
  }
  @media (max-width: 480px) {
    .seatmap-page {
      padding: 20px 16px 32px;
    }
    .page-header {
      align-items: start;
    }
    .brand span {
      display: block;
      margin: 4px 0 0;
    }
    nav {
      gap: 10px;
    }
    .card-heading {
      padding: 16px;
    }
    summary span {
      display: block;
      margin: 6px 0 0;
    }
  }
</style>

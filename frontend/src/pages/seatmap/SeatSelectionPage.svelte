<script lang="ts">
  import { getMockEvent, mockEvents, mockSeats } from "./mock-data";
  import type { EventId, EventSeatStatus } from "./types";

  interface Props {
    eventId: EventId;
    onEventChange: (eventId: EventId) => void;
  }

  const props: Props = $props();
  // 只在进入选座页时加载 Three.js，避免其他业务页面承担 3D 包的首屏开销。
  const sceneModule = import("./SeatScene.svelte");
  const fixture = $derived(getMockEvent(props.eventId));
  const states = $derived(
    new Map(fixture?.seatStates.map((seat) => [seat.seatId, seat.status])),
  );
  const availableCount = $derived(
    fixture?.seatStates.filter((seat) => seat.status === "available").length ??
      0,
  );
  const soldCount = $derived(
    fixture?.seatStates.filter((seat) => seat.status === "sold").length ?? 0,
  );
  const rows = Array.from({ length: 10 }, (_, index) => ({
    row: index + 1,
    seats: mockSeats.filter((seat) => seat.row === index + 1),
  }));
  const statusLabels: Record<EventSeatStatus | "unknown", string> = {
    available: "可选",
    sold: "已预约",
    locked: "锁定，不可选",
    unknown: "状态未知，不可选",
  };
  const dateFormat = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Singapore",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
</script>

<main class="seatmap-page">
  <header class="page-header">
    <p class="brand">SEATVERSE <span>/ 场馆预览</span></p>
    <span class="demo-badge">模拟演示 · C-02</span>
  </header>

  <nav class="event-nav" aria-label="切换模拟活动">
    {#each mockEvents as event (event.id)}
      <button
        type="button"
        aria-current={props.eventId === event.id ? "page" : undefined}
        onclick={() => props.onEventChange(event.id)}
      >
        <span>活动 {event.id}</span>
        {event.title}
      </button>
    {/each}
  </nav>

  {#if fixture}
    <section class="event-header" aria-labelledby="event-title">
      <p class="eyebrow">{fixture.event.venue.name}</p>
      <h1 id="event-title">{fixture.event.title}</h1>
      <p class="event-time">
        <time datetime={fixture.event.startTime}>
          {dateFormat.format(new Date(fixture.event.startTime))}
        </time>
        <span>—</span>
        <time datetime={fixture.event.endTime}>
          {dateFormat.format(new Date(fixture.event.endTime))}
        </time>
        <span>UTC+8</span>
      </p>
    </section>

    <div class="preview-layout">
      <section class="venue-card" aria-labelledby="preview-title">
        <div class="card-heading">
          <h2 id="preview-title">3D 场馆</h2>
          <span>10 排 × 12 座</span>
        </div>
        {#await sceneModule}
          <p class="scene-loading" role="status">正在加载 3D 场馆…</p>
        {:then scene}
          <scene.default seats={mockSeats} />
        {:catch}
          <p class="scene-loading" role="alert">
            场馆加载失败，请刷新重试，或展开下方平面图查看座位。
          </p>
        {/await}
        <details class="flat-preview">
          <summary>查看平面座位状态 <span>可选 / 已预约</span></summary>
          <div
            class="map-scroll"
            role="group"
            aria-label="120 座平面预览，可横向滚动"
          >
            <div class="seat-plan">
              <div class="stage">舞 台 <span>STAGE</span></div>
              <div class="seat-rows" role="group" aria-label="座位状态预览">
                {#each rows as row (row.row)}
                  <div class="seat-row">
                    <span class="row-label">{row.row}排</span>
                    {#each row.seats as seat (seat.id)}
                      {@const state = states.get(seat.id) ?? "unknown"}
                      <span
                        class="seat"
                        data-state={state}
                        class:aisle={seat.number === 7}
                        title={`${seat.label} · ${statusLabels[state]}`}
                        aria-label={`${seat.label}，${statusLabels[state]}`}
                        >{seat.number}</span
                      >
                    {/each}
                  </div>
                {/each}
              </div>
              <p class="orientation">后排 / 入场方向</p>
            </div>
          </div>
          <div class="legend" aria-label="座位图例">
            <span><i class="swatch available"></i>可选</span>
            <span><i class="swatch sold"></i>已预约</span>
            <span class="legend-note">平面数据预览</span>
          </div>
        </details>
      </section>

      <aside class="summary-card" aria-labelledby="summary-title">
        <p class="eyebrow">本场座位概览</p>
        <h2 id="summary-title">同一场馆，不同场次。</h2>
        <p class="summary-copy">切换活动，查看这一场的座位占用情况。</p>
        <dl class="seat-counts" aria-live="polite" aria-atomic="true">
          <div>
            <dt>可选座位</dt>
            <dd>{availableCount}<small> 座</small></dd>
          </div>
          <div>
            <dt>已预约</dt>
            <dd>{soldCount}<small> 座</small></dd>
          </div>
          <div>
            <dt>场馆总座位</dt>
            <dd>{mockSeats.length}<small> 座</small></dd>
          </div>
        </dl>
        <p class="demo-note">
          当前为场馆空间预览，可旋转、缩放和重置视角。展开平面图查看本场座位状态；点击选座将在下一阶段开放。
        </p>
      </aside>
    </div>

    <details class="data-details">
      <summary>查看模拟座位数据 <span>编号、坐标与本场状态</span></summary>
      <p>坐标单位：米。X 向右、Y 向上、Z 从舞台指向后排；舞台位于座位前方。</p>
      <div class="table-scroll" role="group" aria-label="模拟座位数据，可滚动">
        <table>
          <caption
            >活动 {fixture.event.id} · 120 座静态坐标与动态状态关联</caption
          >
          <thead
            ><tr
              ><th scope="col">编号</th><th scope="col">座位</th><th scope="col"
                >X</th
              ><th scope="col">Y</th><th scope="col">Z</th><th scope="col"
                >类型</th
              ><th scope="col">本场状态</th></tr
            ></thead
          >
          <tbody>
            {#each mockSeats as seat (seat.id)}
              <tr>
                <td>{seat.id}</td><td>{seat.label}</td><td>{seat.x}</td><td
                  >{seat.y}</td
                ><td>{seat.z}</td><td>普通座</td><td
                  >{statusLabels[states.get(seat.id) ?? "unknown"]}</td
                >
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </details>
  {:else}
    <section class="empty-state" role="status">
      <p class="eyebrow">模拟演示</p>
      <h1>未找到模拟活动</h1>
      <p>当前提供 1001、1002 两场模拟活动，请从上方选择一场继续预览。</p>
    </section>
  {/if}
</main>

<style>
  .seatmap-page {
    max-width: 1120px;
    margin: 0 auto;
    padding: 32px 24px 48px;
  }
  .page-header,
  .card-heading,
  .legend {
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
  .demo-badge {
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 6px 12px;
    font-size: 12px;
    white-space: nowrap;
  }
  .event-nav {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  .event-nav button {
    text-align: left;
    padding: 12px 18px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--background);
    cursor: pointer;
    font-size: 14px;
  }
  .event-nav button span {
    display: block;
    margin-bottom: 4px;
    font-size: 11px;
    color: var(--muted-foreground);
  }
  .event-nav button[aria-current="page"] {
    background: var(--primary);
    color: var(--primary-foreground);
    border-color: var(--primary);
  }
  .event-nav button[aria-current="page"] span {
    color: inherit;
  }
  button:focus-visible,
  summary:focus-visible,
  .map-scroll:focus-visible,
  .table-scroll:focus-visible {
    outline: 2px solid var(--ring);
    outline-offset: 4px;
  }
  .event-header {
    margin: 36px 0 28px;
  }
  .eyebrow {
    color: var(--muted-foreground);
    font-size: 13px;
    margin: 0 0 10px;
  }
  h1 {
    font-size: clamp(24px, 3.5vw, 36px);
    font-weight: 650;
    letter-spacing: -0.04em;
    line-height: 1.3;
    margin: 0 0 14px;
  }
  .event-time {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 13px;
    color: var(--muted-foreground);
  }
  .preview-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 280px;
    gap: 20px;
    align-items: start;
  }
  .venue-card,
  .summary-card {
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    background: var(--card);
  }
  .venue-card {
    overflow: hidden;
  }
  .flat-preview {
    border-top: 1px solid var(--border);
  }
  .flat-preview > summary {
    padding: 16px 24px;
  }
  .scene-loading {
    min-height: 420px;
    padding: 40px 24px;
    color: var(--muted-foreground);
    font-size: 13px;
  }
  .card-heading {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
  }
  .card-heading h2 {
    font-weight: 600;
    font-size: 15px;
  }
  .card-heading > span {
    font-size: 12px;
    color: var(--muted-foreground);
  }
  .map-scroll {
    overflow-x: auto;
    padding: 28px 20px 0;
  }
  .seat-plan {
    min-width: 440px;
    max-width: 560px;
    margin: 0 auto;
  }
  .stage {
    text-align: center;
    background: var(--muted);
    color: var(--muted-foreground);
    border-radius: 4px 4px 50% 50% / 4px 4px 14px 14px;
    padding: 12px;
    margin: 0 48px 28px;
    font-size: 13px;
  }
  .stage span {
    margin-left: 10px;
    font-size: 9px;
    letter-spacing: 0.15em;
  }
  .seat-rows {
    display: grid;
    gap: 9px;
  }
  .seat-row {
    display: grid;
    grid-template-columns:
      28px repeat(6, minmax(0, 1fr)) minmax(0, 1.8fr)
      repeat(5, minmax(0, 1fr));
    align-items: center;
    gap: 6px;
  }
  .row-label {
    font-size: 10px;
    color: var(--muted-foreground);
  }
  .seat {
    display: grid;
    place-items: center;
    height: 27px;
    border: 1px solid var(--border);
    border-radius: 6px 6px 3px 3px;
    background: var(--secondary);
    color: var(--secondary-foreground);
    font-size: 10px;
    font-variant-numeric: tabular-nums;
  }
  .seat.aisle {
    margin-left: 18px;
  }
  .seat[data-state="available"],
  .swatch.available {
    background: var(--primary);
    border-color: var(--primary);
    color: var(--primary-foreground);
  }
  .seat[data-state="sold"],
  .swatch.sold {
    background: var(--muted);
    border-color: var(--border);
    color: var(--muted-foreground);
  }
  .seat[data-state="sold"] {
    text-decoration: line-through;
  }
  .seat[data-state="locked"],
  .seat[data-state="unknown"] {
    border-style: dashed;
  }
  .orientation {
    font-size: 10px;
    text-align: center;
    color: var(--muted-foreground);
    margin: 22px 0;
    letter-spacing: 0.12em;
  }
  .legend {
    justify-content: start;
    padding: 16px 24px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    flex-wrap: wrap;
  }
  .legend > span {
    display: flex;
    align-items: center;
    gap: 7px;
  }
  .swatch {
    width: 12px;
    height: 12px;
    border: 1px solid;
    border-radius: 3px;
  }
  .legend-note {
    color: var(--muted-foreground);
    margin-left: auto;
  }
  .summary-card {
    padding: 24px;
  }
  .summary-card h2 {
    font-size: 20px;
    font-weight: 600;
    line-height: 1.4;
  }
  .summary-copy {
    font-size: 13px;
    line-height: 1.8;
    color: var(--muted-foreground);
    margin-top: 12px;
  }
  .seat-counts {
    margin-top: 24px;
  }
  .seat-counts > div {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid var(--border);
  }
  .seat-counts dt {
    font-size: 13px;
    color: var(--muted-foreground);
  }
  .seat-counts dd {
    font-size: 24px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
  .seat-counts small {
    font-size: 11px;
    font-weight: 400;
  }
  .demo-note {
    font-size: 12px;
    line-height: 1.9;
    color: var(--muted-foreground);
    padding-top: 20px;
  }
  .data-details {
    margin-top: 24px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 24px;
  }
  summary {
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
  }
  summary span {
    font-weight: 400;
    color: var(--muted-foreground);
    font-size: 12px;
    margin-left: 12px;
  }
  .data-details > p {
    color: var(--muted-foreground);
    margin: 16px 0;
    font-size: 12px;
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
    color: var(--muted-foreground);
    padding-bottom: 12px;
  }
  th,
  td {
    border-bottom: 1px solid var(--border);
    padding: 10px 12px;
  }
  th {
    background: var(--muted);
    font-weight: 500;
  }
  .empty-state {
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 40px;
    margin-top: 32px;
  }
  .empty-state > p:last-child {
    color: var(--muted-foreground);
    font-size: 14px;
    line-height: 1.8;
  }
  @media (max-width: 800px) {
    .preview-layout {
      grid-template-columns: minmax(0, 1fr);
    }
    .seat-counts {
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
    }
    .seat-counts > div {
      gap: 16px;
    }
  }
  @media (max-width: 480px) {
    .seatmap-page {
      padding: 20px 16px 32px;
    }
    .page-header {
      align-items: start;
      margin-bottom: 24px;
    }
    .brand span {
      display: block;
      margin: 4px 0 0;
    }
    .event-nav {
      flex-direction: column;
    }
    .event-header {
      margin-top: 28px;
    }
    .card-heading,
    .legend {
      padding: 16px;
    }
    .data-details {
      padding: 16px;
    }
    summary span {
      display: block;
      margin: 6px 0 0;
    }
    .empty-state {
      padding: 24px;
    }
  }
</style>

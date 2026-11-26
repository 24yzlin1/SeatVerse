<!-- 
  COPYRIGHT (C) PRINCE_CJH

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at https://mozilla.org/MPL/2.0/.
 -->

<script lang="ts">
  import type { Component } from "svelte";
  import { RiCircleLine } from "remixicon-svelte";
  import { PieChart, Text, Tooltip } from "layerchart";

  import { Badge } from "$lib/components/ui/badge";
  import * as Item from "$lib/components/ui/item";

  const {
    icon,
    title,
    type = "text",
    data,
    options = {},
  }: {
    icon?: Component;
    title?: string;
    type: "text" | "badge" | "pie" | "bar" | "line";
    data:
      | string
      | string[]
      | {
          label: string;
          value: number;
        }[];
    options?: { note?: string | number; noteDescription?: string };
  } = $props();

  function countTop(
    data: {
      label: string;
      value: number;
    }[],
  ): {
    label: string;
    value: number;
  }[] {
    const counter = data.reduce(
      (acc, x) => {
        acc[x.label] = (acc[x.label] || 0) + x.value;
        return acc;
      },
      {} as Record<string, number>,
    );

    const counterTop = Object.entries(counter)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4);

    const sum = Object.entries(counter).reduce((acc, x) => acc + x[1], 0);
    const remains = sum - counterTop.reduce((acc, x) => acc + x[1], 0);
    if (remains !== 0) {
      counterTop.push(["其他", remains]);
    }

    return counterTop.map(([k, v]) => {
      return {
        label: k,
        value: v,
      };
    });
  }

  type ChartData = {
    key: string;
    value: number;
    label: string;
    color: string;
  };

  function buildChart(
    raw: {
      label: string;
      value: number;
    }[],
  ): ChartData[] {
    return countTop(raw).map(({ label, value }, i) => {
      return {
        key: i.toString(),
        value,
        label,
        color: `var(--chart-${i + 1})`,
      };
    });
  }
</script>

<Item.Root variant="muted">
  <div
    class={[
      "w-full",
      "py-4",
      "flex",
      "flex-col",
      "gap-4",
      "items-start",
      "overflow-hidden",
    ]}
  >
    <Item.Root class={["p-0"]}>
      <Item.Media class={["size-8"]} variant="icon">
        {@const Icon = icon || RiCircleLine}
        <Icon />
      </Item.Media>
      <Item.Content>
        <Item.Title>{title}</Item.Title>
      </Item.Content>
    </Item.Root>
    {#if type === "text"}
      <Item.Content class={["pl-12", "pr-4"]}>{data}</Item.Content>
    {/if}
    {#if type === "badge"}
      <Item.Content class={["pl-12", "pr-4"]}>
        {#each data as string[] as x, i (i)}
          <Badge>{x}</Badge>
        {/each}
      </Item.Content>
    {/if}
    {#if type === "pie" || type === "bar" || type === "line"}
      {@const chart = buildChart(
        data as {
          label: string;
          value: number;
        }[],
      )}
      <div class={["w-full"]}>
        <div class={["p-6", "flex", "justify-center"]}>
          <div class={["size-48"]}>
            <PieChart
              data={chart}
              label="label"
              c="color"
              cornerRadius={5}
              innerRadius={-20}
              padAngle={0.05}
              props={{ pie: { motion: "tween" } }}
            >
              {#snippet aboveMarks()}
                {#if options.note}
                  <Text
                    value={options.note}
                    textAnchor="middle"
                    verticalAnchor="middle"
                    class="fill-foreground text-3xl! font-bold"
                  />
                {/if}
                {#if options.noteDescription}
                  <Text
                    value={options.noteDescription}
                    textAnchor="middle"
                    verticalAnchor="middle"
                    class="fill-muted-foreground! text-muted-foreground"
                    dy={20}
                  />
                {/if}
              {/snippet}
              {#snippet tooltip()}
                <Tooltip.Root variant="none">
                  {#snippet children({ data }: { data: ChartData })}
                    {@render hoverNote(data.label, data.value, data.color)}
                  {/snippet}
                </Tooltip.Root>
              {/snippet}
            </PieChart>
          </div>
        </div>
        <div class={["pl-12", "pr-4", "pt-4", "flex", "flex-col", "gap-2"]}>
          {#each chart as x (x.key)}
            <div class={["flex", "gap-2", "text-xs"]}>
              <div class={["flex", "items-center", "gap-2"]}>
                <div
                  style:--color-bg={x.color}
                  style:--color-border={x.color}
                  class={[
                    "shrink-0",
                    "rounded-xs",
                    "border-(--color-border)",
                    "bg-(--color-bg)",
                    "h-full",
                    "w-1",
                  ]}
                ></div>
                <p>{x.label}</p>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</Item.Root>

{#snippet hoverNote(label: string, value: number, color: string)}
  <div
    class={[
      "border",
      "border-border/50",
      "bg-background/80",
      "backdrop-blur-xs",
      "flex",
      "flex-col",
      "min-w-36",
      "gap-2",
      "rounded-lg",
      "px-3",
      "py-2",
      "text-xs",
      "shadow-xl",
    ]}
  >
    <p class={["font-medium"]}>{label}</p>
    <div class={["flex", "gap-2"]}>
      <div class={["flex", "items-center", "gap-2"]}>
        <div
          style:--color-bg={color}
          style:--color-border={color}
          class={[
            "shrink-0",
            "rounded-xs",
            "border-(--color-border)",
            "bg-(--color-bg)",
            "h-full",
            "w-1",
          ]}
        ></div>
        <p>{value}</p>
      </div>
    </div>
  </div>
{/snippet}

<script lang="ts">
  import { CalendarDate, type DateValue } from "@internationalized/date";
  import { RiCalendarLine } from "remixicon-svelte";

  import { Button } from "$lib/components/ui/button";
  import { Calendar } from "$lib/components/ui/calendar";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import * as Popover from "$lib/components/ui/popover";

  // Date picker per shadcn-svelte docs, extended with a time field because
  // events start and end at specific moments. `value` is an ISO string
  // ("" when unset), so callers keep plain string state.
  let {
    id,
    placeholder = "选择日期与时间",
    value = $bindable(""),
    disabled = false,
  }: {
    id?: string;
    placeholder?: string;
    value?: string;
    disabled?: boolean;
  } = $props();

  let open = $state(false);

  // Time-of-day text edited in the popover; persists across selections.
  let timeText = $state("19:00");

  const selected = $derived.by(() => {
    if (value.length === 0) {
      return null;
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return null;
    }
    const pad = (part: number) => part.toString().padStart(2, "0");
    return {
      date: new CalendarDate(
        date.getFullYear(),
        date.getMonth() + 1,
        date.getDate(),
      ),
      time: `${pad(date.getHours())}:${pad(date.getMinutes())}`,
    };
  });

  // Keep the time field in sync when the value changes from outside
  // (e.g. the create form resets after submit).
  $effect(() => {
    if (selected) {
      timeText = selected.time;
    }
  });

  const label = $derived(
    selected === null
      ? placeholder
      : `${selected.date.year}年${selected.date.month}月${selected.date.day}日 ${selected.time}`,
  );

  function commit(nextDate: CalendarDate, nextTime: string) {
    const [hours, minutes] = nextTime.split(":").map((part) =>
      Number.parseInt(part, 10),
    );
    if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
      return;
    }
    const date = new Date(
      nextDate.year,
      nextDate.month - 1,
      nextDate.day,
      hours,
      minutes,
    );
    value = date.toISOString();
  }

  function onValueChange(next: DateValue | undefined) {
    if (!next) {
      return;
    }
    const date =
      next instanceof CalendarDate
        ? next
        : new CalendarDate(next.year, next.month, next.day);
    open = false;
    commit(date, timeText);
  }

  function onTimeInput(event: Event) {
    const target = event.currentTarget as HTMLInputElement;
    timeText = target.value;
    if (selected) {
      commit(selected.date, timeText);
    }
  }
</script>

<Popover.Root bind:open>
  <Popover.Trigger>
    {#snippet child({ props })}
      <Button
        {...props}
        {id}
        type="button"
        variant="outline"
        disabled={disabled}
        class={[
          "w-full",
          "justify-start",
          "text-left",
          "font-normal",
          ...(selected === null ? (["text-muted-foreground"] as const) : []),
        ]}
      >
        <RiCalendarLine data-icon="inline-start" />
        {label}
      </Button>
    {/snippet}
  </Popover.Trigger>
  <Popover.Content align="start" class={["w-auto", "p-0"]}>
    <Calendar
      type="single"
      locale="zh-CN"
      value={selected?.date}
      onValueChange={onValueChange}
      disabled={disabled}
    />
    <div class={["border-t", "border-border", "p-3", "flex", "items-center", "gap-2"]}>
      <Label for={id === undefined ? undefined : `${id}-time`}>时间</Label>
      <Input
        id={id === undefined ? undefined : `${id}-time`}
        type="time"
        step={300}
        value={timeText}
        disabled={disabled}
        oninput={onTimeInput}
      />
    </div>
  </Popover.Content>
</Popover.Root>

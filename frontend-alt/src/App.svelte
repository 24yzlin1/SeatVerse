<script lang="ts">
  import { ModeWatcher } from "mode-watcher";
  import { onMount, type Component } from "svelte";
  import Router, {
    pop,
    push,
    router,
    type WrappedComponent,
  } from "svelte-spa-router";
  import { wrap } from "svelte-spa-router/wrap";
  import { RiArrowLeftLine, RiCircleLine, RiMenu2Line } from "remixicon-svelte";
  import { toast } from "svelte-sonner";

  import * as Avatar from "$lib/components/ui/avatar";
  import { Button } from "$lib/components/ui/button";
  import * as ButtonGroup from "$lib/components/ui/button-group";
  import * as Drawer from "$lib/components/ui/drawer";
  import { Toaster } from "$lib/components/ui/sonner";

  import Authorize from "@/common/Authorize.svelte";
  import Error from "@/common/Error.svelte";
  import Identify from "@/common/Identify.svelte";
  import RequireAuthorize from "@/common/RequireAuthorize.svelte";
  import { endpoints, request } from "@/common/api";
  import type { LoginResponse, User } from "@/common/api";
  import {
    authentication,
    setAuthenticationApi,
  } from "@/common/stores/authentication.svelte";
  import type { Role } from "@/common/api";

  import Home from "@/pages/Home.svelte";
  import Events from "@/pages/events/Events.svelte";
  import EventDetail from "@/pages/events/EventDetail.svelte";
  import SeatMap from "@/pages/seatmap/SeatMap.svelte";
  import Bookings from "@/pages/bookings/Bookings.svelte";
  import Ticket from "@/pages/tickets/Ticket.svelte";
  import TicketByCode from "@/pages/tickets/TicketByCode.svelte";
  import OrganizerEvents from "@/pages/organizer/Events.svelte";
  import OrganizerBookings from "@/pages/organizer/Bookings.svelte";
  import Verify from "@/pages/organizer/Verify.svelte";

  let isShowMenu = $state(false);
  let isShowUser = $state(false);

  let headerHeight = $state(0);
  let bodyHeight = $state(0);
  let footerHeight = $state(0);
  let screenHeight = $state(window.innerHeight);

  window.addEventListener("resize", () => (screenHeight = window.innerHeight));
  let footerMargin = $derived(
    Math.max(0, screenHeight - headerHeight - bodyHeight - footerHeight),
  );

  const menu = $derived<[string, [string, string][]][]>([
    [
      "浏览",
      [
        ["首页", "/"],
        ["活动列表", "/events"],
        ["我的预约", "/bookings"],
      ],
    ],
    ...(authentication.role === "organizer"
      ? [
          [
            "主办方",
            [
              ["后台活动", "/organizer/events"],
              ["签到核验", "/organizer/verify"],
            ],
          ] as [string, [string, string][]],
        ]
      : []),
  ]);

  // Restore the session from the stored token on startup; without a token
  // this only settles the status to signed out.
  onMount(() => {
    // Both authentication calls go through the request client, so token
    // injection and 401 handling only happen in one place.
    setAuthenticationApi({
      me: () => request<User>(endpoints.authenticationMe()),
      login: (payload) =>
        request<LoginResponse>(endpoints.authenticationLogin(), {
          method: "POST",
          body: payload,
        }),
    });
    void authentication.bootstrap();
  });

  // Pages behind the session guard open the user drawer when the guard
  // rejects access. Organizer pages additionally require the organizer role.
  function wrapRequireAuthorize(
    target: Component<any>,
    roles?: readonly Role[],
  ): WrappedComponent {
    return wrap({
      component: RequireAuthorize,
      props: {
        target,
        roles,
        showLoginCallback: (x: boolean) => (isShowUser = x),
      },
    });
  }
</script>

<ModeWatcher />
<Toaster position="top-center" />

{@render header()}
<main class={["max-w-211", "mx-auto"]} bind:clientHeight={bodyHeight}>
  <Router
    routes={{
      "/": Home,
      "/events": Events,
      "/events/:id": EventDetail,
      "/events/:id/seats": SeatMap,
      "/bookings": wrapRequireAuthorize(Bookings),
      "/bookings/:id/ticket": wrapRequireAuthorize(Ticket),
      "/tickets/:code": wrapRequireAuthorize(TicketByCode),
      "/organizer/events": wrapRequireAuthorize(OrganizerEvents, ["organizer"]),
      "/organizer/events/:id/bookings": wrapRequireAuthorize(
        OrganizerBookings,
        ["organizer"],
      ),
      "/organizer/verify": wrapRequireAuthorize(Verify, ["organizer"]),
      "*": Error,
    }}
  />
</main>
{@render footer()}

<Drawer.Root bind:open={isShowMenu}>
  <Drawer.Overlay
    class={["bg-background/80"]}
    onclick={() => (isShowMenu = !isShowMenu)}
  >
    <nav
      class={["flex", "flex-col", "gap-12", "overflow-auto", "px-8", "py-32"]}
    >
      {#each menu as [groupTitle, groupEntries] (groupTitle)}
        <div class={["flex", "flex-col", "gap-3"]}>
          <div class={["text-muted-foreground", "text-sm", "font-medium"]}>
            {groupTitle}
          </div>
          {#each groupEntries as [entryLabel, entryPath] (entryPath)}
            <button
              onclick={() => push(entryPath)}
              class={["click-link", "text-2xl", "font-medium", "text-start"]}
            >
              {entryLabel}
            </button>
          {/each}
        </div>
      {/each}
    </nav>
  </Drawer.Overlay>
</Drawer.Root>

<Drawer.Root bind:open={isShowUser}>
  <Drawer.Content class={["px-8", "h-[67vh]"]}>
    {#if authentication.isLoggedIn}
      <Identify
        succeedCallback={() => {
          isShowUser = false;
          toast.success("");
        }}
      />
    {:else}
      <Authorize
        succeedCallback={() => {
          isShowUser = false;
          toast.success("");
        }}
      />
    {/if}
  </Drawer.Content>
</Drawer.Root>

{#snippet header()}
  <header
    bind:clientHeight={headerHeight}
    class={[
      "h-14",
      "px-6",
      "sticky",
      "z-9",
      "top-0",
      "bg-background",
      "flex",
      "items-center",
      "justify-between",
      "bg-background/80",
      "backdrop-blur-xs",
    ]}
  >
    <div>
      <ButtonGroup.Root>
        {#if !(router.location === "/")}
          <Button onclick={pop} variant="secondary">
            <RiArrowLeftLine />
          </Button>
        {/if}
        <Button onclick={() => (isShowMenu = !isShowMenu)} variant="secondary">
          <RiMenu2Line />
          {#if router.location === "/"}
            SeatVerse
          {/if}
        </Button>
      </ButtonGroup.Root>
    </div>
    <div>
      <Button
        variant={authentication.isLoggedIn ? "ghost" : "secondary"}
        size={authentication.isLoggedIn ? "icon" : "default"}
        onclick={() => (isShowUser = !isShowUser)}
      >
        {#if authentication.isLoggedIn}
          <Avatar.Root class={["size-9"]}>
            <Avatar.Fallback>
              {authentication.user?.name.charAt(0).toUpperCase()}
            </Avatar.Fallback>
          </Avatar.Root>
        {:else}
          登录
        {/if}
      </Button>
    </div>
  </header>
{/snippet}

{#snippet footer()}
  <footer
    bind:clientHeight={footerHeight}
    class={["p-4", "flex", "items-center", "justify-center"]}
    style:margin-top={`${footerMargin}px`}
  >
    <div
      class={[
        "rounded-4xl",
        "text-sm",
        "font-medium",
        "flex",
        "items-center",
        "justify-center",
        "bg-secondary",
        "h-9",
        "gap-1.5",
        "px-3",
        "opacity-50",
      ]}
    >
      <RiCircleLine class={["size-4"]} />
      SeatVerse · 座位预约与电子票
      <RiCircleLine class={["size-4"]} />
    </div>
  </footer>
{/snippet}

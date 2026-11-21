// API path constants.
//
// Paths follow the "route path" column of docs/contracts/api.md §3 and do NOT
// include the `/api` prefix: the request client's baseURL owns the prefix,
// and writing `/api` here would produce a doubled prefix.
//
// Path parameters are always passed through `encodeURIComponent` before being
// concatenated. Ticket codes are 20-character Crockford Base32 strings
// (ticket-qr.md §2.1) but are still encoded without assuming a safe charset.

// Encode a single path segment; ids may be numbers so callers can pass
// `booking.id` directly.
const encodePathSegment = (value: string | number): string =>
  encodeURIComponent(String(value));

export const endpoints = {
  authenticationLogin: () => "/authentication/login",
  authenticationRegister: () => "/authentication/register",
  authenticationMe: () => "/authentication/me",
  event: (id: string | number) => `/events/${encodePathSegment(id)}`,
  eventSeats: (id: string | number) => `/events/${encodePathSegment(id)}/seats`,
  eventSeatStatistics: (id: string | number) =>
    `/events/${encodePathSegment(id)}/seat-statistics`,
  venueSeats: (id: string | number) => `/venues/${encodePathSegment(id)}/seats`,
  bookingsCreate: () => "/bookings",
  events: () => "/events",
  eventCreate: () => "/events",
  eventDetail: (id: string | number) => `/events/${encodePathSegment(id)}`,
  eventStatus: (id: string | number) =>
    `/events/${encodePathSegment(id)}/status`,
  eventBookings: (id: string | number) =>
    `/events/${encodePathSegment(id)}/bookings`,
  bookingsMe: () => "/bookings/me",
  bookingCancel: (id: string | number) =>
    `/bookings/${encodePathSegment(id)}/cancel`,
  bookingTicket: (id: string | number) =>
    `/bookings/${encodePathSegment(id)}/ticket`,
  ticketByCode: (code: string) => `/tickets/${encodePathSegment(code)}`,
  ticketVerify: () => "/tickets/verify",
} as const;

// The single response envelope used by every REST endpoint.
// The business status lives at the top level, never inside payload.
export interface ResponseEnvelope<TPayload> {
  code: number;
  message: string;
  payload: TPayload | null;
}

// Shape check without assertions: narrow with `in` only.
function isEnvelopeShape(value: unknown): value is ResponseEnvelope<unknown> {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  if (!("code" in value && "message" in value && "payload" in value)) {
    return false;
  }
  return true;
}

// Guard an envelope together with its payload type. The payload guard decides
// the concrete payload type, so callers never cast the raw response.
export function isResponseEnvelope<TPayload>(
  value: unknown,
  guardPayload: (candidate: unknown) => candidate is TPayload,
): value is ResponseEnvelope<TPayload> {
  if (!isEnvelopeShape(value)) {
    return false;
  }
  if (typeof value.code !== "number") {
    return false;
  }
  if (typeof value.message !== "string") {
    return false;
  }
  if (value.payload !== null && !guardPayload(value.payload)) {
    return false;
  }
  return true;
}

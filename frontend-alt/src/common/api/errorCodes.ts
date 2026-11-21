// Error code constants shared with the backend. Keep this table in sync with
// the backend contract within the same commit.
//
// Every endpoint answers with HTTP 200 and carries the business result in the
// top-level `code` field of the response envelope. Branching on HTTP status
// codes is forbidden; success is exactly `code === 200`.
export const RESPONSE_CODE_SUCCESS = 200;

export const RESPONSE_CODE_BAD_REQUEST = 400;

export const RESPONSE_CODE_UNAUTHORIZED = 401;

export const RESPONSE_CODE_FORBIDDEN = 403;

export const RESPONSE_CODE_NOT_FOUND = 404;

export const RESPONSE_CODE_CONFLICT = 409;

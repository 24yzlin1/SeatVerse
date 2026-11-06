/**
 * 业务错误码常量。
 *
 * 与后端响应体顶层 `code` 字段逐字一致（02 号规范 §三 / 03 号规范 §六）：
 * 所有接口 HTTP 恒为 200，成败只看 `code === 200`，禁止依赖 HTTP 状态码分支。
 * 变更时必须与后端同一次提交内同步。
 */
export const CODE = {
  OK: 200,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
} as const;

export type ApiCode = (typeof CODE)[keyof typeof CODE];

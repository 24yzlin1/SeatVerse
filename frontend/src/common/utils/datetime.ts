/**
 * 时间展示工具。
 *
 * 接口时间是 ISO 8601 带时区偏移的字符串（api.md §4），前端只做本地化展示，
 * 不参与业务判断；解析失败时原样返回，避免出现 “Invalid Date”。
 */
export function formatDateTime(isoValue: string): string {
  const timestamp = Date.parse(isoValue);
  if (Number.isNaN(timestamp)) {
    return isoValue;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(timestamp);
}

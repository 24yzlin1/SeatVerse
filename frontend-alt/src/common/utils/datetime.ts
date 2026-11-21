// Time display helpers.
//
// API times are ISO 8601 strings with a timezone offset (api.md §4). The
// frontend only renders them in the local locale and never uses them for
// business decisions; unparseable values are returned as-is to avoid showing
// "Invalid Date".
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

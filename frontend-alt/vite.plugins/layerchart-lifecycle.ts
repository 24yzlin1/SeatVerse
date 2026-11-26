import type { Plugin } from "vite";

const constructor = "constructor(getSeries, getStackConfig) {";
const cleanup = "$effect.pre(() => () => this.#_syncSelectedFromProps());";

/**
 * LayerChart 2.0.0-next.48 creates a detached effect root for series selection
 * and retains its disposer, but never calls it. Attach that disposer to the
 * owning chart's effect lifecycle before Svelte compiles the dependency.
 */
export function patchLayerchartSeries(source: string): string {
  if (
    !source.includes("#_syncSelectedFromProps = $effect.root(") ||
    source.includes(cleanup)
  ) {
    return source;
  }
  if (!source.includes(constructor)) {
    throw new Error(
      "LayerChart SeriesState 结构已变化，请重新检查生命周期兼容修复。",
    );
  }
  return source.replace(constructor, `${constructor}\n        ${cleanup}`);
}

export function layerchartLifecycle(): Plugin {
  return {
    name: "seatverse-layerchart-lifecycle",
    enforce: "pre",
    transform(source, id) {
      const filename = id.split("?")[0]?.replaceAll("\\", "/");
      if (!filename?.endsWith("/layerchart/dist/states/series.svelte.js")) {
        return;
      }
      return { code: patchLayerchartSeries(source), map: null };
    },
  };
}

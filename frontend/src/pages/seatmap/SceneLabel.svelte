<script lang="ts">
  import { T } from "@threlte/core";
  import { onDestroy, untrack } from "svelte";
  import { CanvasTexture, SRGBColorSpace } from "three";

  interface Props {
    text: string;
    color: string;
    background?: string;
    position: [number, number, number];
    width?: number;
  }
  const props: Props = $props();
  // 父场景在主题变化时重新挂载；文字纹理不需要外部字体或图片请求。
  const texture = untrack(() => {
    const surface = document.createElement("canvas");
    surface.width = 512;
    surface.height = 128;
    const context = surface.getContext("2d");
    if (context) {
      if (props.background) {
        context.fillStyle = props.background;
        context.beginPath();
        context.roundRect(0, 0, 512, 128, 20);
        context.fill();
      }
      context.font = '600 54px "Inter Variable", sans-serif';
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillStyle = props.color;
      context.fillText(props.text, 256, 66);
    }
    const map = new CanvasTexture(surface);
    map.colorSpace = SRGBColorSpace;
    return map;
  });
  onDestroy(() => texture.dispose());
</script>

<T.Sprite
  position={props.position}
  scale={[props.width ?? 1, (props.width ?? 1) / 4, 1]}
>
  <T.SpriteMaterial
    map={texture}
    transparent
    depthWrite={false}
    depthTest={false}
    toneMapped={false}
  />
</T.Sprite>

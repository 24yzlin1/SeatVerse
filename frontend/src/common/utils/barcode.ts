/**
 * Barcode Detection API 的最小类型与能力探测。
 *
 * 该 API 只在部分 Chromium 内核浏览器提供，TypeScript 的 DOM 库尚未内置声明；
 * 核验页必须在运行时探测，不可用时降级为手动输入票号（ticket-qr.md §3.2）。
 * `window.BarcodeDetector` 的全局声明见 `src/types/barcode.d.ts`。
 */

export interface DetectedBarcode {
  readonly rawValue: string;
}

export interface BarcodeDetectorInstance {
  detect(source: CanvasImageSource): Promise<DetectedBarcode[]>;
}

export interface BarcodeDetectorConstructor {
  new (options?: { formats?: string[] }): BarcodeDetectorInstance;
}

/** 浏览器不支持时返回 `undefined`，调用方据此走手动通道。 */
export function getBarcodeDetectorConstructor():
  BarcodeDetectorConstructor | undefined {
  return window.BarcodeDetector;
}

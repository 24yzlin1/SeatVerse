// Minimal types and capability probe for the Barcode Detection API.
//
// The API is only available in some Chromium-based browsers and the
// TypeScript DOM library does not declare it yet. The verification page must
// probe at runtime and fall back to manual ticket code entry when the API is
// missing (ticket-qr.md §3.2). The `window.BarcodeDetector` global declaration
// lives in `src/types/barcode.d.ts`.
export interface DetectedBarcode {
  readonly rawValue: string;
}

export interface BarcodeDetectorInstance {
  detect(source: CanvasImageSource): Promise<DetectedBarcode[]>;
}

export interface BarcodeDetectorConstructor {
  new (options?: { formats?: string[] }): BarcodeDetectorInstance;
}

// Returns `undefined` when the browser does not support the API; callers use
// that to switch to the manual channel.
export function getBarcodeDetectorConstructor():
  BarcodeDetectorConstructor | undefined {
  return window.BarcodeDetector;
}

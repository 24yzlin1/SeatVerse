import type { BarcodeDetectorConstructor } from "@/common/utils/barcode";

declare global {
  interface Window {
    readonly BarcodeDetector?: BarcodeDetectorConstructor;
  }
}

export {};

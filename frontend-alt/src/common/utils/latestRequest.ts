/** Only the latest request owned by a mounted view may publish a result. */
export class LatestRequest {
  private version = 0;
  private controller: AbortController | null = null;

  cancel(): void {
    this.version++;
    this.controller?.abort();
  }

  async run<T>(
    load: (signal: AbortSignal) => Promise<T>,
    accept: (value: T) => void,
    reject: (error: unknown) => void,
  ): Promise<void> {
    this.cancel();
    const version = this.version;
    const controller = new AbortController();
    this.controller = controller;
    try {
      const result = await load(controller.signal);
      if (version === this.version && !controller.signal.aborted) {
        accept(result);
      }
    } catch (error) {
      if (version === this.version && !controller.signal.aborted) {
        reject(error);
      }
    }
  }
}

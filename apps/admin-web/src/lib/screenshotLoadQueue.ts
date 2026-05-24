const MAX_CONCURRENT = 5;
let active = 0;
const waitQueue: Array<() => void> = [];

export function acquireScreenshotSlot(): Promise<void> {
  if (active < MAX_CONCURRENT) {
    active += 1;
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    waitQueue.push(() => {
      active += 1;
      resolve();
    });
  });
}

export function releaseScreenshotSlot(): void {
  active = Math.max(0, active - 1);
  const next = waitQueue.shift();
  if (next) next();
}

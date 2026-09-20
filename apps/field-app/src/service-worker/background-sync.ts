/**
 * Background Sync Coordinator (Phase 24)
 * Provides capability detection and sync registration foundation for browser Background Sync.
 * Does NOT implement the Phase 25 sync protocol or server reconciliation.
 */

export const OUTBOX_SYNC_TAG = 'nexus-field-outbox-sync';

export interface BackgroundSyncCapability {
  isSupported: boolean;
  registeredTag: string | null;
  lastRegisteredAt?: string;
  error?: string;
}

export class BackgroundSyncManager {
  private static instance: BackgroundSyncManager | null = null;
  private lastRegistration: string | null = null;

  private constructor() {}

  public static getInstance(): BackgroundSyncManager {
    if (!this.instance) {
      this.instance = new BackgroundSyncManager();
    }
    return this.instance;
  }

  /**
   * Safe capability check. Detects whether Background Sync is supported by the user agent.
   */
  public isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      'SyncManager' in window
    );
  }

  /**
   * Registers a one-off Background Sync event with tag 'nexus-field-outbox-sync'.
   * Triggers when the device regains connectivity.
   */
  public async registerOutboxSync(): Promise<boolean> {
    if (!this.isSupported()) {
      return false;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      // Access SyncManager through type casting to support standard experimental spec
      const syncManager = (registration as any).sync;
      if (syncManager && typeof syncManager.register === 'function') {
        await syncManager.register(OUTBOX_SYNC_TAG);
        this.lastRegistration = new Date().toISOString();
        return true;
      }
      return false;
    } catch (err: any) {
      console.warn('Background sync registration failed:', err);
      return false;
    }
  }

  public getCapability(): BackgroundSyncCapability {
    return {
      isSupported: this.isSupported(),
      registeredTag: this.lastRegistration ? OUTBOX_SYNC_TAG : null,
      lastRegisteredAt: this.lastRegistration || undefined,
    };
  }
}

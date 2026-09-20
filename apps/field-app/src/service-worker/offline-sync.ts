/**
 * Service Worker Client Coordinator (Phase 24)
 * Handles client-side registration, lifecycle updates, and controlled message exchange
 * between the React application and the active Service Worker.
 */

export type ServiceWorkerState = 'ACTIVE' | 'INSTALLING' | 'WAITING' | 'UNAVAILABLE';

export interface ServiceWorkerInfo {
  status: ServiceWorkerState;
  hasUpdate: boolean;
  scope?: string;
  cacheVersion?: string;
}

export type OutboxSyncListener = () => void;

export class ServiceWorkerCoordinator {
  private static instance: ServiceWorkerCoordinator | null = null;
  private registration: ServiceWorkerRegistration | null = null;
  private syncListeners: Set<OutboxSyncListener> = new Set();
  private updateListeners: Set<(hasUpdate: boolean) => void> = new Set();
  private currentStatus: ServiceWorkerState = 'UNAVAILABLE';
  private hasUpdate: boolean = false;

  private constructor() {}

  public static getInstance(): ServiceWorkerCoordinator {
    if (!this.instance) {
      this.instance = new ServiceWorkerCoordinator();
    }
    return this.instance;
  }

  public isSupported(): boolean {
    return typeof window !== 'undefined' && 'serviceWorker' in navigator;
  }

  /**
   * Registers the root scope Service Worker /sw.js safely.
   */
  public async register(): Promise<ServiceWorkerRegistration | null> {
    if (!this.isSupported()) {
      this.currentStatus = 'UNAVAILABLE';
      return null;
    }

    try {
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });

      if (this.registration.installing) {
        this.currentStatus = 'INSTALLING';
      } else if (this.registration.waiting) {
        this.currentStatus = 'WAITING';
        this.hasUpdate = true;
        this.notifyUpdate();
      } else if (this.registration.active) {
        this.currentStatus = 'ACTIVE';
      }

      this.registration.onupdatefound = () => {
        const installingWorker = this.registration?.installing;
        if (installingWorker) {
          installingWorker.onstatechange = () => {
            if (installingWorker.state === 'installed' && navigator.serviceWorker.controller) {
              this.hasUpdate = true;
              this.currentStatus = 'WAITING';
              this.notifyUpdate();
            }
          };
        }
      };

      // Listen for broadcasts from Service Worker
      navigator.serviceWorker.addEventListener('message', (event) => {
        const data = event.data;
        if (data && data.type === 'OUTBOX_SYNC_TRIGGERED') {
          this.notifySync();
        }
      });

      return this.registration;
    } catch (err) {
      console.warn('Service Worker registration failed:', err);
      this.currentStatus = 'UNAVAILABLE';
      return null;
    }
  }

  /**
   * Prompts the waiting worker to activate immediately without page reload disruption.
   */
  public skipWaiting(): void {
    if (this.registration && this.registration.waiting) {
      this.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
    }
  }

  public getStatus(): ServiceWorkerInfo {
    return {
      status: this.currentStatus,
      hasUpdate: this.hasUpdate,
      scope: this.registration?.scope,
      cacheVersion: 'v1',
    };
  }

  public onOutboxSyncTriggered(listener: OutboxSyncListener): () => void {
    this.syncListeners.add(listener);
    return () => this.syncListeners.delete(listener);
  }

  public onUpdateFound(listener: (hasUpdate: boolean) => void): () => void {
    this.updateListeners.add(listener);
    listener(this.hasUpdate);
    return () => this.updateListeners.delete(listener);
  }

  private notifySync(): void {
    this.syncListeners.forEach((l) => l());
  }

  private notifyUpdate(): void {
    this.updateListeners.forEach((l) => l(this.hasUpdate));
  }
}

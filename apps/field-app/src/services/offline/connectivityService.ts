/**
 * Connectivity & Offline State Abstraction (Phase 22).
 * Distinguishes device network status from server reachability.
 */

import { ConnectionStatus, DataMode } from '../../types';

export interface ConnectivityState {
  status: ConnectionStatus;
  isDeviceOnline: boolean;
  isServerReachable: boolean;
  dataMode: DataMode;
  lastOnlineAt: string | null;
}

export class ConnectivityService {
  private static listeners: Set<(state: ConnectivityState) => void> = new Set();
  private static currentState: ConnectivityState = {
    status: typeof navigator !== 'undefined' && navigator.onLine ? 'ONLINE' : 'OFFLINE',
    isDeviceOnline: typeof navigator !== 'undefined' ? navigator.onLine : false,
    isServerReachable: typeof navigator !== 'undefined' ? navigator.onLine : false,
    dataMode: typeof navigator !== 'undefined' && navigator.onLine ? 'LIVE' : 'OFFLINE',
    lastOnlineAt: typeof navigator !== 'undefined' && navigator.onLine ? new Date().toISOString() : null,
  };

  public static initialize(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      this.updateState({
        isDeviceOnline: true,
        isServerReachable: true,
        status: 'ONLINE',
        dataMode: 'LIVE',
        lastOnlineAt: new Date().toISOString(),
      });
    });

    window.addEventListener('offline', () => {
      this.updateState({
        isDeviceOnline: false,
        isServerReachable: false,
        status: 'OFFLINE',
        dataMode: 'OFFLINE',
      });
    });
  }

  public static getState(): ConnectivityState {
    return { ...this.currentState };
  }

  public static setSimulatedStatus(status: ConnectionStatus): void {
    const isOnline = status === 'ONLINE';
    this.updateState({
      status,
      isDeviceOnline: isOnline,
      isServerReachable: isOnline,
      dataMode: isOnline ? 'LIVE' : 'OFFLINE',
      lastOnlineAt: isOnline ? new Date().toISOString() : this.currentState.lastOnlineAt,
    });
  }

  public static subscribe(listener: (state: ConnectivityState) => void): () => void {
    this.listeners.add(listener);
    listener(this.currentState);
    return () => this.listeners.delete(listener);
  }

  private static updateState(partial: Partial<ConnectivityState>): void {
    this.currentState = { ...this.currentState, ...partial };
    this.listeners.forEach((l) => l(this.currentState));
  }
}

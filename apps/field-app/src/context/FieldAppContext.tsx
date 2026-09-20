import React, { createContext, useContext, useEffect, useState } from 'react';
import { ConnectionStatus, DataMode, FieldAssignment, PendingSyncItem } from '../types';
import { ConnectivityService } from '../services/offline/connectivityService';
import { SyncQueueService } from '../services/sync/syncQueueService';
import { DEMO_ASSIGNMENT } from '../services/fixtures/demoData';
import { AssignmentRepository } from '../database/repositories/AssignmentRepository';
import { DurableAssignment } from '../database/types';
import {
  ServiceWorkerCoordinator,
  ServiceWorkerState,
} from '../service-worker/offline-sync';
import {
  BackgroundSyncManager,
  BackgroundSyncCapability,
} from '../service-worker/background-sync';

interface FieldAppContextType {
  connectionStatus: ConnectionStatus;
  dataMode: DataMode;
  currentAssignment: FieldAssignment | null;
  pendingSyncCount: number;
  pendingItems: PendingSyncItem[];
  setConnectionStatus: (status: ConnectionStatus) => void;
  updateAssignmentStatus: (status: FieldAssignment['status']) => void;
  isDbReady: boolean;
  swStatus: ServiceWorkerState;
  hasSwUpdate: boolean;
  applySwUpdate: () => void;
  bgSyncCapability: BackgroundSyncCapability;
}

const FieldAppContext = createContext<FieldAppContextType | undefined>(undefined);

export const FieldAppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connectionStatus, setConnectionStatusState] = useState<ConnectionStatus>(
    ConnectivityService.getState().status
  );
  const [dataMode, setDataMode] = useState<DataMode>(ConnectivityService.getState().dataMode);
  const [currentAssignment, setCurrentAssignment] = useState<FieldAssignment | null>(DEMO_ASSIGNMENT);
  const [pendingItems, setPendingItems] = useState<PendingSyncItem[]>(SyncQueueService.getPending());
  const [isDbReady, setIsDbReady] = useState<boolean>(false);
  const [swStatus, setSwStatus] = useState<ServiceWorkerState>('UNAVAILABLE');
  const [hasSwUpdate, setHasSwUpdate] = useState<boolean>(false);
  const [bgSyncCapability, setBgSyncCapability] = useState<BackgroundSyncCapability>(
    BackgroundSyncManager.getInstance().getCapability()
  );

  useEffect(() => {
    // 1. Initialize connectivity
    ConnectivityService.initialize();
    const unsubConn = ConnectivityService.subscribe((conn) => {
      setConnectionStatusState(conn.status);
      setDataMode(conn.dataMode);
    });

    // 2. Initialize sync queue from IndexedDB
    SyncQueueService.initialize().then(() => {
      setPendingItems(SyncQueueService.getPending());
      setIsDbReady(true);
    });

    const unsubSync = SyncQueueService.subscribe((items) => {
      setPendingItems(items);
    });

    // 3. Hydrate cached assignment from IndexedDB if available
    const assignmentRepo = new AssignmentRepository();
    assignmentRepo.getById(DEMO_ASSIGNMENT.assignment_id).then((cached) => {
      if (cached) {
        setCurrentAssignment(cached);
      } else {
        const durableDemo: DurableAssignment = {
          ...DEMO_ASSIGNMENT,
          cached_at: new Date().toISOString(),
          is_cached: true,
        };
        assignmentRepo.save(durableDemo).catch(() => {});
      }
    }).catch(() => {});

    // 4. Hook Service Worker coordinator & update listeners
    const swCoordinator = ServiceWorkerCoordinator.getInstance();
    setSwStatus(swCoordinator.getStatus().status);

    const unsubSwUpdate = swCoordinator.onUpdateFound((hasUpdate) => {
      setHasSwUpdate(hasUpdate);
      setSwStatus(swCoordinator.getStatus().status);
    });

    const unsubOutboxSync = swCoordinator.onOutboxSyncTriggered(() => {
      // Re-hydrate sync queue state when background sync fires
      setPendingItems(SyncQueueService.getPending());
      setBgSyncCapability(BackgroundSyncManager.getInstance().getCapability());
    });

    setBgSyncCapability(BackgroundSyncManager.getInstance().getCapability());

    return () => {
      unsubConn();
      unsubSync();
      unsubSwUpdate();
      unsubOutboxSync();
    };
  }, []);

  const setConnectionStatus = (status: ConnectionStatus) => {
    ConnectivityService.setSimulatedStatus(status);
  };

  const updateAssignmentStatus = (status: FieldAssignment['status']) => {
    if (currentAssignment) {
      const updated = { ...currentAssignment, status };
      setCurrentAssignment(updated);

      const durable: DurableAssignment = {
        ...updated,
        cached_at: new Date().toISOString(),
        is_cached: true,
        last_local_status_update: new Date().toISOString(),
      };
      new AssignmentRepository().save(durable).catch((err) => {
        console.warn('Failed to cache assignment update in IndexedDB:', err);
      });
    }
  };

  const applySwUpdate = () => {
    ServiceWorkerCoordinator.getInstance().skipWaiting();
    setHasSwUpdate(false);
  };

  return (
    <FieldAppContext.Provider
      value={{
        connectionStatus,
        dataMode,
        currentAssignment,
        pendingSyncCount: pendingItems.length,
        pendingItems,
        setConnectionStatus,
        updateAssignmentStatus,
        isDbReady,
        swStatus,
        hasSwUpdate,
        applySwUpdate,
        bgSyncCapability,
      }}
    >
      {children}
    </FieldAppContext.Provider>
  );
};

export const useFieldApp = (): FieldAppContextType => {
  const context = useContext(FieldAppContext);
  if (!context) {
    throw new Error('useFieldApp must be used within FieldAppProvider');
  }
  return context;
};

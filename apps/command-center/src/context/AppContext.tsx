/**
 * Global App Context for NEXUS Command Center
 * Manages Connection Status, Data Mode, Digital Twin State Version, and Session
 */

import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { ConnectionStatus, DataMode, EmergencyType, StateVersionInfo, UserSession } from '../types';
import { digitalTwinService } from '../services/endpoints';

interface AppContextValue {
  connectionStatus: ConnectionStatus;
  dataMode: DataMode;
  emergencyType: EmergencyType;
  districtId: string;
  stateVersionInfo: StateVersionInfo;
  currentUser: UserSession;
  lastSyncTime: Date | null;
  setDataMode: (mode: DataMode) => void;
  setEmergencyType: (type: EmergencyType) => void;
  setDistrictId: (districtId: string) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  resetOperationalContext: () => void;
  refreshStateVersion: () => Promise<void>;
}

const defaultSession: UserSession = {
  userId: 'USR-OP-01',
  name: 'Operations Commander',
  role: 'COMMANDER',
  jurisdiction: 'Zone 1 (HQ)',
};

const defaultVersionInfo: StateVersionInfo = {
  version: null,
  lastUpdated: null,
  authority: 'NEXUS Digital Twin Authority',
};

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('ONLINE');
  const [dataMode, setDataMode] = useState<DataMode>('REAL');

  // Load persisted emergencyType and districtId or default to FLOOD / chennai
  const [emergencyType, setEmergencyTypeState] = useState<EmergencyType>(() => {
    try {
      const saved = localStorage.getItem('nexus_emergency_type');
      return (saved as EmergencyType) || 'FLOOD';
    } catch {
      return 'FLOOD';
    }
  });

  const [districtId, setDistrictIdState] = useState<string>(() => {
    try {
      const saved = localStorage.getItem('nexus_district_id');
      return saved || 'chennai';
    } catch {
      return 'chennai';
    }
  });

  const setEmergencyType = (type: EmergencyType) => {
    setEmergencyTypeState(type);
    try {
      localStorage.setItem('nexus_emergency_type', type);
    } catch {
      // ignore storage failure
    }
  };

  const setDistrictId = (id: string) => {
    const cleanId = id.toLowerCase();
    setDistrictIdState(cleanId);
    try {
      localStorage.setItem('nexus_district_id', cleanId);
    } catch {
      // ignore storage failure
    }
  };

  const resetOperationalContext = () => {
    setEmergencyType('FLOOD');
    setDistrictId('chennai');
  };

  const [stateVersionInfo, setStateVersionInfo] = useState<StateVersionInfo>(defaultVersionInfo);
  const [currentUser] = useState<UserSession>(defaultSession);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  // Monitor browser network status
  useEffect(() => {
    const handleOnline = () => setConnectionStatus('ONLINE');
    const handleOffline = () => setConnectionStatus('OFFLINE');

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    if (!navigator.onLine) {
      setConnectionStatus('OFFLINE');
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const refreshStateVersion = async () => {
    try {
      const info = await digitalTwinService.getStateVersion();
      if (info && info.version !== undefined) {
        setStateVersionInfo(info);
        setLastSyncTime(new Date());
        setConnectionStatus('ONLINE');
      }
    } catch (err) {
      // Degraded or offline connection to backend
      setConnectionStatus((prev) => (prev === 'OFFLINE' ? 'OFFLINE' : 'DEGRADED'));
    }
  };

  useEffect(() => {
    refreshStateVersion();
  }, []);

  const value = useMemo(
    () => ({
      connectionStatus,
      dataMode,
      emergencyType,
      districtId,
      stateVersionInfo,
      currentUser,
      lastSyncTime,
      setDataMode,
      setEmergencyType,
      setDistrictId,
      setConnectionStatus,
      resetOperationalContext,
      refreshStateVersion,
    }),
    [connectionStatus, dataMode, emergencyType, districtId, stateVersionInfo, currentUser, lastSyncTime]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = (): AppContextValue => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

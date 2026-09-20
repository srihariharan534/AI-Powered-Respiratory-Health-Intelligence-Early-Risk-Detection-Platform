import React from 'react';
import { useApp } from '../../context/AppContext';
import { StatusIndicator, DataModeBadge, DigitalTwinBadge } from '../ui';
import { DISTRICT_REGISTRY } from '../../services/districtRegistry';

export const Header: React.FC = () => {
  const {
    connectionStatus,
    dataMode,
    emergencyType,
    districtId,
    stateVersionInfo,
    currentUser,
    setDataMode,
    setEmergencyType,
    setDistrictId,
    resetOperationalContext,
  } = useApp();

  const handleToggleDataMode = () => {
    // Cycle between REAL, SIMULATION, and DEMO for testing / operations
    const modes: ('REAL' | 'SIMULATION' | 'DEMO')[] = ['REAL', 'SIMULATION', 'DEMO'];
    const currentIndex = modes.indexOf(dataMode as any);
    const nextMode = modes[(currentIndex + 1) % modes.length];
    setDataMode(nextMode);
  };

  return (
    <header className="header-container" role="banner">
      {/* Left: Brand / Platform Identity */}
      <div className="header-brand">
        <div className="header-brand-logo">
          <span style={{ fontSize: '1.25rem', color: '#3b82f6' }}>⬡</span>
          <span>NEXUS</span>
        </div>
        <div style={{ height: '16px', width: '1px', backgroundColor: 'var(--border-subtle)' }} />
        <div className="header-brand-title">Emergency Decision Platform</div>
      </div>

      {/* Center: Hazard Domain & District Operational Selectors */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
        {/* 1. Emergency Hazard Selector */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.2rem 0.5rem',
            backgroundColor: 'var(--bg-base)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            fontSize: '0.72rem',
          }}
        >
          <span style={{ color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.04em' }}>EMERGENCY:</span>
          <select
            value={emergencyType}
            onChange={(e) => setEmergencyType(e.target.value as any)}
            aria-label="Emergency Type Selector"
            style={{
              backgroundColor: 'transparent',
              color: '#60a5fa',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.75rem',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="FLOOD" style={{ background: '#0e131f', color: '#f8fafc' }}>🌊 Flood (Validated)</option>
            <option value="CYCLONE" style={{ background: '#0e131f', color: '#f8fafc' }}>🌀 Cyclone</option>
            <option value="LANDSLIDE" style={{ background: '#0e131f', color: '#f8fafc' }}>⛰ Landslide</option>
            <option value="WILDFIRE" style={{ background: '#0e131f', color: '#f8fafc' }}>🔥 Wildfire</option>
            <option value="EXTREME_HEAT" style={{ background: '#0e131f', color: '#f8fafc' }}>☀️ Extreme Heat</option>
            <option value="TORNADO" style={{ background: '#0e131f', color: '#f8fafc' }}>🌪 Tornado / Severe Storm</option>
            <option value="INDUSTRIAL_ACCIDENT" style={{ background: '#0e131f', color: '#f8fafc' }}>🏭 Industrial Accident</option>
            <option value="CHEMICAL_INCIDENT" style={{ background: '#0e131f', color: '#f8fafc' }}>☣ Chemical Incident</option>
            <option value="URBAN_INFRASTRUCTURE_FAILURE" style={{ background: '#0e131f', color: '#f8fafc' }}>🏗 Urban Infrastructure Failure</option>
            <option value="PUBLIC_HEALTH_EMERGENCY" style={{ background: '#0e131f', color: '#f8fafc' }}>🏥 Public-Health Emergency</option>
            <option value="MAJOR_TRANSPORT_INCIDENT" style={{ background: '#0e131f', color: '#f8fafc' }}>🚆 Major Transport Incident</option>
            <option value="EARTHQUAKE" style={{ background: '#0e131f', color: '#f8fafc' }}>🌋 Earthquake</option>
          </select>
        </div>

        {/* 2. District Operational Area Selector */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.2rem 0.5rem',
            backgroundColor: 'var(--bg-base)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            fontSize: '0.72rem',
          }}
        >
          <span style={{ color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.04em' }}>DISTRICT:</span>
          <select
            value={districtId}
            onChange={(e) => setDistrictId(e.target.value)}
            aria-label="District Selector"
            style={{
              backgroundColor: 'transparent',
              color: '#34d399',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.75rem',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            {Object.values(DISTRICT_REGISTRY).map((dist) => (
              <option key={dist.id} value={dist.id} style={{ background: '#0e131f', color: '#f8fafc' }}>
                📍 {dist.name} ({dist.region})
              </option>
            ))}
          </select>
        </div>

        {/* 3. Reset Operational Context */}
        <button
          type="button"
          onClick={resetOperationalContext}
          title="Reset Operational Context to Default (Chennai + Flood)"
          style={{
            padding: '0.2rem 0.45rem',
            fontSize: '0.68rem',
            fontWeight: 600,
            backgroundColor: 'var(--bg-surface-raised)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-muted)',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          ↺ Reset
        </button>
      </div>

      {/* Right: Operational Status, Authority, and Session Telemetry */}
      <div className="header-metrics">
        {/* Connection Status Indicator */}
        <StatusIndicator status={connectionStatus} />

        {/* Data Mode with interactive toggle */}
        <DataModeBadge mode={dataMode} onToggle={handleToggleDataMode} />

        {/* Data Trust Freshness Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.2rem 0.5rem',
            backgroundColor: 'var(--bg-base)',
            borderRadius: '4px',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.7rem',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <span style={{ color: 'var(--text-muted)' }}>DATA:</span>
          <span style={{ color: 'var(--color-online)', fontWeight: 600 }}>● FRESH</span>
        </div>

        {/* Digital Twin State Version Authority */}
        <DigitalTwinBadge versionInfo={stateVersionInfo} />

        {/* Current Officer / Session Role */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.2rem 0.5rem',
            backgroundColor: 'var(--bg-surface-raised)',
            borderRadius: '4px',
            fontSize: '0.72rem',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <span style={{ color: 'var(--text-muted)' }}>Role:</span>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{currentUser.role}</span>
        </div>
      </div>
    </header>
  );
};

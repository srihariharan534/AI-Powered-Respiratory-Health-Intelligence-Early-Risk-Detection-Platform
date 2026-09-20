/**
 * Live GIS Dashboard - Phase 13 Primary Operational Surface
 * Integrates:
 * - Phase 05/08: Roads & Bridges with Dynamic Operational State
 * - Phase 07/08: Dynamic Rerouting Engine Visualization
 * - Phase 09: Digital Twin State Authority
 * - Phase 10: Flood Inundation Simulation
 * - Phase 11: Counterfactual Scenario Transitions
 * - Phase 20: Dedicated Operational Recommendation & Human Approval Strip
 */

import React, { useState, useMemo } from 'react';
import {
  Card,
  Button,
  DataModeBadge,
  SeverityBadge,
  RecommendationCard,
} from '../components/ui';
import {
  CommandMap,
  MapControls,
  MapLegend,
  DetailPanel,
} from '../components/command-map';
import { useApp } from '../context/AppContext';
import { getDistrictOperationalData } from '../services/districtRegistry';
import {
  GisSelectedEntity,
} from '../types';

export const DashboardPage: React.FC = () => {
  const { dataMode, emergencyType, districtId, stateVersionInfo, refreshStateVersion, setDataMode } = useApp();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Authoritative dynamic district + emergency operational data
  const operationalData = useMemo(() => {
    return getDistrictOperationalData(districtId, emergencyType);
  }, [districtId, emergencyType]);

  const {
    district,
    incidents,
    hospitals,
    shelters,
    criticalZones,
    roadFeatures,
    bridgeFeatures,
    routes,
    floodFeatures,
    recommendation,
  } = operationalData;

  const hazardName =
    emergencyType === 'FLOOD'
      ? 'Flood'
      : emergencyType === 'WILDFIRE'
      ? 'Wildfire'
      : emergencyType === 'CYCLONE'
      ? 'Cyclone'
      : emergencyType === 'LANDSLIDE'
      ? 'Landslide'
      : emergencyType === 'EXTREME_HEAT'
      ? 'Extreme Heat'
      : emergencyType === 'EARTHQUAKE'
      ? 'Earthquake'
      : emergencyType.replace(/_/g, ' ');

  // Layer filter toggles
  const [visibleLayers, setVisibleLayers] = useState({
    flood: true,
    roads: true,
    bridges: true,
    incidents: true,
    facilities: true,
    routes: true,
  });

  // Selected feature
  const [selectedEntity, setSelectedEntity] = useState<GisSelectedEntity>(null);

  // Scenario toggle state (BASELINE vs SIMULATED SCENARIO)
  const [scenarioActive, setScenarioActive] = useState<boolean>(true);

  // Primary operational recommendation state
  const [recStatus, setRecStatus] = useState<'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');

  const handleToggleLayer = (layerName: keyof typeof visibleLayers) => {
    setVisibleLayers((prev) => ({ ...prev, [layerName]: !prev[layerName] }));
  };

  const handleResetCenter = () => {
    // Center is dynamically updated via district.center
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshStateVersion();
    setIsRefreshing(false);
  };

  const handleToggleScenario = () => {
    if (scenarioActive) {
      setScenarioActive(false);
      setDataMode('REAL');
    } else {
      setScenarioActive(true);
      setDataMode('SIMULATION');
    }
  };

  const activeReroute = routes.find((r) => r.properties.status === 'REROUTED');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Top Banner / Operational Command Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.75rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h1 style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '0.02em', color: 'var(--text-primary)' }}>
              {district.eocName}
            </h1>
            <DataModeBadge mode={dataMode === 'SIMULATION' ? 'SIMULATION' : district.id === 'chennai' ? 'REAL' : 'DEMO'} />
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
            {district.name} • {district.operationalArea} • Active Domain: <strong style={{ color: '#60a5fa' }}>{hazardName.toUpperCase()}</strong> • Mission Control Surface
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <Button
            variant={scenarioActive ? 'primary' : 'outline'}
            size="sm"
            onClick={handleToggleScenario}
          >
            {scenarioActive ? 'Scenario: Flood +1.0m (Simulated)' : 'Switch to Scenario Preview'}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            isLoading={isRefreshing}
          >
            Sync State
          </Button>
        </div>
      </div>

      {/* Top Operational KPI Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          gap: '0.75rem',
        }}
      >
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            padding: '0.75rem 1rem',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            ACTIVE INCIDENTS
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.2rem' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
              {incidents.length}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--color-critical)' }}>
              {incidents.filter((i) => i.severity === 'CRITICAL').length} Critical
            </span>
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            padding: '0.75rem 1rem',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            CRITICAL ZONES
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.2rem' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-severe)' }}>
              {criticalZones.length}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>High Exposure</span>
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            padding: '0.75rem 1rem',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            HOSPITALS & SHELTERS
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.2rem' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-online)' }}>
              {hospitals.length + shelters.length}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {hospitals.length} Hosp / {shelters.length} Shelt
            </span>
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            padding: '0.75rem 1rem',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            DYNAMIC REROUTES
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.2rem' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#60a5fa' }}>
              {activeReroute ? '1 Active' : '0 Active'}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {activeReroute ? `+${activeReroute.properties.deltaDistanceKm || 1.4} km detour` : 'Normal Flow'}
            </span>
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            padding: '0.75rem 1rem',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            PENDING APPROVALS
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.2rem' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: recStatus === 'PENDING' ? '#f59e0b' : '#10b981' }}>
              {recStatus === 'PENDING' ? '01' : '00'}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Action Required</span>
          </div>
        </div>
      </div>

      {/* Main HERO GIS MAP Surface */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 340px',
          gap: '1rem',
          minHeight: '520px',
        }}
      >
        {/* Left Column: Command Map & Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          <MapControls
            layers={visibleLayers}
            onToggleLayer={handleToggleLayer}
            onResetView={handleResetCenter}
          />

          <div
            style={{
              position: 'relative',
              flex: 1,
              minHeight: '460px',
              borderRadius: '8px',
              border: '1px solid var(--border-strong)',
              overflow: 'hidden',
            }}
          >
            <CommandMap
              center={district.center}
              zoom={district.defaultZoom}
              floodFeatures={scenarioActive ? floodFeatures : []}
              roadFeatures={roadFeatures}
              bridgeFeatures={bridgeFeatures}
              incidents={incidents}
              hospitals={hospitals}
              shelters={shelters}
              routes={routes}
              visibleLayers={visibleLayers}
              selectedEntity={selectedEntity}
              onSelectEntity={setSelectedEntity}
            />

            {/* Overlaid Map Legend */}
            <div style={{ position: 'absolute', bottom: '16px', right: '16px', zIndex: 1000 }}>
              <MapLegend visibleLayers={visibleLayers} />
            </div>

            {/* Simulation Mode Indicator Watermark */}
            {dataMode === 'SIMULATION' && (
              <div
                style={{
                  position: 'absolute',
                  top: '12px',
                  left: '52px',
                  zIndex: 1000,
                  padding: '0.25rem 0.6rem',
                  backgroundColor: 'rgba(139, 92, 246, 0.9)',
                  color: '#ffffff',
                  fontSize: '0.72rem',
                  fontWeight: 800,
                  borderRadius: '4px',
                  letterSpacing: '0.06em',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
                }}
              >
                ⚠ SIMULATION MODE • {hazardName.toUpperCase()} IN {district.name.toUpperCase()} • LIVE STATE UNMODIFIED
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Context Panels (Detail Panel + Critical Zones + Dynamic Reroute Alert) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {/* 1. Feature Inspector */}
          <DetailPanel
            selectedEntity={selectedEntity}
            onClose={() => setSelectedEntity(null)}
          />

          {/* 2. Dynamic Rerouting Engine Card */}
          {activeReroute && (
            <Card
              title="Dynamic Rerouting Advisory"
              subtitle={`${district.name} State Invalidation Overlay Trigger`}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.76rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-critical)' }}>
                  <span>Invalidated Corridor:</span>
                  <span style={{ fontWeight: 600 }}>{activeReroute.properties.name}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#60a5fa' }}>
                  <span>Active Diversion:</span>
                  <span style={{ fontWeight: 600 }}>{district.name} Northern Bypass</span>
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '0.5rem',
                    backgroundColor: 'var(--bg-surface-raised)',
                    padding: '0.5rem',
                    borderRadius: '4px',
                  }}
                >
                  <div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>Detour Distance:</div>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>+{activeReroute.properties.deltaDistanceKm || 1.4} km ({activeReroute.properties.distanceKm} km total)</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>Travel Delay:</div>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>+{activeReroute.properties.deltaTravelTimeMin || 2.7} min ({activeReroute.properties.travelTimeMin} min total)</div>
                  </div>
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                  {activeReroute.properties.changeExplanation}
                </p>
              </div>
            </Card>
          )}

          {/* 3. Critical Zones Panel */}
          <Card title={`Critical Sectors (${district.name})`} subtitle={`${hazardName} exposure summary`}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {criticalZones.map((zone) => (
                <div
                  key={zone.id}
                  style={{
                    padding: '0.55rem 0.7rem',
                    backgroundColor: 'var(--bg-surface-raised)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.25rem',
                    fontSize: '0.74rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{zone.name}</span>
                    <SeverityBadge level={zone.severity} />
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>
                    Severity: {zone.severity} • Affected Roads: {zone.affectedRoadsCount}
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>
                    Triage Receiving: {zone.nearestHospital}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Bottom Operational Action & Governance Strip: Dedicated Recommendation Engine Card */}
      <RecommendationCard
        id={recommendation.id}
        action={recommendation.action}
        target={recommendation.target}
        priority={recommendation.priority}
        reasoning={recommendation.reasoning}
        score={recommendation.score}
        status={recStatus}
        dataFreshness={recommendation.dataFreshness}
        stateVersion={stateVersionInfo.version ? `v${stateVersionInfo.version}` : 'v104'}
        factors={recommendation.factors}
        onApprove={() => setRecStatus('APPROVED')}
        onReject={() => setRecStatus('REJECTED')}
        canApprove={true}
      />
    </div>
  );
};

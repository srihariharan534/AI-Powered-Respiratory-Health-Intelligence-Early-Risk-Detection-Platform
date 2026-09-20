import React, { useState } from 'react';
import { Card, Button, DataModeBadge } from '../components/ui';
import { useApp } from '../context/AppContext';
import { DISTRICT_REGISTRY, getDistrictOperationalData } from '../services/districtRegistry';

export const SimulationPage: React.FC = () => {
  const { districtId, emergencyType } = useApp();
  const district = DISTRICT_REGISTRY[districtId.toLowerCase()] || DISTRICT_REGISTRY['chennai'];
  const data = getDistrictOperationalData(districtId as any, emergencyType as any);

  // Build district-specific bridge options from operational data
  const bridgeOptions = data.bridgeFeatures.map((b, idx) => ({
    id: b.properties?.bridgeId || `B-${String(idx + 1).padStart(3, '0')}`,
    label: `${b.properties?.bridgeId || `B-${String(idx + 1).padStart(3, '0')}`} (${b.properties?.name || `${district.name} Bridge ${idx + 1}`})`,
  }));

  const [rainfallMm, setRainfallMm] = useState<number>(100);
  const [surgeM, setSurgeM] = useState<number>(1.5);
  const [selectedBridge, setSelectedBridge] = useState<string>('none');
  const [simulationResult, setSimulationResult] = useState<any | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const hazardName = emergencyType.replace(/_/g, ' ');

  const handleRunSimulation = () => {
    setIsRunning(true);
    setTimeout(() => {
      setSimulationResult({
        scenarioId: 'SIM-SCENARIO-' + Date.now().toString().slice(-4),
        timestamp: new Date().toISOString(),
        isolatedStateVersion: 104,
        district: district.name,
        emergencyType: hazardName,
        rainfallMm,
        surgeM,
        failedBridges: selectedBridge !== 'none' ? [selectedBridge] : [],
        affectedRoadSegments: Math.floor(rainfallMm * 0.4 + surgeM * 12),
        facilitiesAtRisk: Math.floor(surgeM * 2),
        evacuationRequired: surgeM > 2.5 || rainfallMm > 200,
      });
      setIsRunning(false);
    }, 600);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {district.name} — What-If Counterfactual Scenario Launcher
            </h1>
            <DataModeBadge mode="SIMULATION" />
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            {district.operationalArea} • {hazardName} scenario • Sandbox state evaluation — Does not modify authoritative Digital Twin production state
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '1.5rem' }}>
        {/* Scenario Parameters Form */}
        <Card title="Scenario Parameter Config">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.85rem' }}>
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                Simulated Rainfall: <strong>{rainfallMm} mm / 24h</strong>
              </label>
              <input
                type="range"
                min="0"
                max="350"
                value={rainfallMm}
                onChange={(e) => setRainfallMm(Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                River / Coastal Surge: <strong>{surgeM.toFixed(1)} meters</strong>
              </label>
              <input
                type="range"
                min="0"
                max="5"
                step="0.1"
                value={surgeM}
                onChange={(e) => setSurgeM(Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                Simulated Bridge Failure — {district.name}:
              </label>
              <select
                value={selectedBridge}
                onChange={(e) => setSelectedBridge(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  backgroundColor: 'var(--bg-surface-raised)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  color: 'var(--text-primary)',
                }}
              >
                <option value="none">No Structural Failures</option>
                {bridgeOptions.map((b) => (
                  <option key={b.id} value={b.id}>{b.label}</option>
                ))}
              </select>
            </div>

            <Button
              variant="primary"
              onClick={handleRunSimulation}
              isLoading={isRunning}
              style={{ marginTop: '0.5rem' }}
            >
              Execute Scenario Simulation
            </Button>
          </div>
        </Card>

        {/* Output Evaluation */}
        <Card title="Counterfactual Impact Evaluation">
          {!simulationResult && (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Configure parameters and launch simulation to inspect isolated {district.name} network impacts.
            </div>
          )}

          {simulationResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.85rem' }}>
              <div
                style={{
                  padding: '0.75rem',
                  backgroundColor: 'rgba(139, 92, 246, 0.1)',
                  border: '1px solid rgba(139, 92, 246, 0.3)',
                  borderRadius: '6px',
                  color: '#c4b5fd',
                  fontSize: '0.75rem',
                }}
              >
                Executed in isolated sandbox for <strong>{simulationResult.district}</strong> ({simulationResult.emergencyType}). Authority state version untouched.
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '6px' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Affected Road Segments</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.25rem', color: 'var(--color-severe)' }}>
                    {simulationResult.affectedRoadSegments}
                  </div>
                </div>

                <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '6px' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Facilities At Risk</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.25rem', color: 'var(--color-critical)' }}>
                    {simulationResult.facilitiesAtRisk}
                  </div>
                </div>

                {simulationResult.evacuationRequired && (
                  <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.3)', gridColumn: '1/-1' }}>
                    <div style={{ color: '#ef4444', fontWeight: 700, fontSize: '0.8rem' }}>⚠ MASS EVACUATION THRESHOLD EXCEEDED — {district.name}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.2rem' }}>Immediate district-wide evacuation protocol recommended for {district.operationalArea}.</div>
                  </div>
                )}
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Scenario Hash: {simulationResult.scenarioId} • Timestamp: {simulationResult.timestamp}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

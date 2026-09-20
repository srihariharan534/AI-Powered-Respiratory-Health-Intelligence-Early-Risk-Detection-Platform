/**
 * Judge Mode Demonstration Layout & Experience
 * Walkthrough of:
 * Baseline → Flood Simulation → Bridge Failure → Dynamic Rerouting
 * → Field Offline → Local Queuing → Sync → Digital Twin Update → What-If
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  DataModeBadge,
} from '../components/ui';
import {
  CommandMap,
  MapLegend,
} from '../components/command-map';
import {
  JudgeModeManager,
  JudgeStep,
  JUDGE_SCENARIO,
} from '../services/judgeModeManager';
import {
  DEMO_OPERATIONAL_AREA,
  DEMO_FLOOD_FEATURES,
  DEMO_ROAD_FEATURES,
  DEMO_BRIDGE_FEATURES,
  DEMO_INCIDENTS,
  DEMO_HOSPITALS,
  DEMO_SHELTERS,
  DEMO_ROUTES,
} from '../services/gisDemoData';
import {
  GisSelectedEntity,
  RoadFeature,
  BridgeFeature,
  RouteFeature,
  IncidentSummary,
} from '../types';

export const JudgeModePage: React.FC = () => {
  const [manager] = useState(() => new JudgeModeManager());
  const [currentStep, setCurrentStep] = useState<JudgeStep>(() => manager.getCurrentStep());
  const [selectedEntity, setSelectedEntity] = useState<GisSelectedEntity>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Keyboard navigation support: Right Arrow -> Next, Left Arrow -> Prev, R -> Reset
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') {
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        handlePrev();
      } else if (e.key === 'r' || e.key === 'R') {
        handleReset();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleNext = () => {
    setCurrentStep(manager.nextStep());
    setSelectedEntity(null);
  };

  const handlePrev = () => {
    setCurrentStep(manager.previousStep());
    setSelectedEntity(null);
  };

  const handleReset = () => {
    setCurrentStep(manager.reset());
    setSelectedEntity(null);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  // Derive dynamic map elements from currentStep
  const isFloodActive = currentStep.flood_extent_active;
  const isBridgeFailed = currentStep.bridge_status === 'FAILED';
  const isRoadBlocked = currentStep.road_status === 'BLOCKED';
  const isRerouted = currentStep.route_status === 'REROUTED';

  // Dynamic roads
  const dynamicRoads: RoadFeature[] = DEMO_ROAD_FEATURES.map((road) => {
    if (road.properties.roadId === 'R-101') {
      return {
        ...road,
        properties: {
          ...road.properties,
          status: isRoadBlocked ? 'BLOCKED' : 'OPEN',
          floodDepthCm: isRoadBlocked ? 95 : 0,
        },
      };
    }
    return road;
  });

  // Dynamic bridges
  const dynamicBridges: BridgeFeature[] = DEMO_BRIDGE_FEATURES.map((b) => {
    if (b.properties.bridgeId === 'B-001') {
      return {
        ...b,
        properties: {
          ...b.properties,
          status: isBridgeFailed ? 'FAILED' : 'OPEN',
        },
      };
    }
    return b;
  });

  // Dynamic routes
  const dynamicRoutes: RouteFeature[] = DEMO_ROUTES.map((r) => {
    if (r.properties.status === 'REROUTED') {
      return {
        ...r,
        properties: {
          ...r.properties,
          status: isRerouted ? 'REROUTED' : 'ACTIVE',
        },
      };
    }
    if (r.properties.status === 'BLOCKED') {
      return {
        ...r,
        properties: {
          ...r.properties,
          status: isRoadBlocked ? 'BLOCKED' : 'ACTIVE',
        },
      };
    }
    return r;
  });

  // Dynamic incidents (only shows offline queued incident when step reaches OFFLINE_INCIDENT or beyond)
  const dynamicIncidents: IncidentSummary[] =
    currentStep.step_index >= 6
      ? DEMO_INCIDENTS
      : DEMO_INCIDENTS.filter((i) => i.id !== 'INC-001');

  const visibleLayers = {
    flood: isFloodActive,
    roads: true,
    bridges: true,
    incidents: true,
    facilities: true,
    routes: true,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* 1. Header Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.8rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{ fontWeight: 800, color: '#60a5fa', fontSize: '1.1rem' }}>⬡ JUDGE MODE</span>
              <DataModeBadge mode={currentStep.data_mode} />
              <span
                style={{
                  fontSize: '0.7rem',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '4px',
                  backgroundColor: 'rgba(59, 130, 246, 0.15)',
                  color: '#93c5fd',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                }}
              >
                Step {currentStep.step_index} / {manager.getTotalSteps()}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              {JUDGE_SCENARIO.name} • Controlled Demo Environment
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.25rem 0.6rem',
              backgroundColor: 'var(--bg-surface-raised)',
              borderRadius: '4px',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <span style={{ color: 'var(--text-muted)' }}>Twin State:</span>
            <span style={{ color: '#60a5fa', fontWeight: 700 }}>v{currentStep.digital_twin_version}</span>
          </div>

          <Button variant="outline" size="sm" onClick={toggleFullscreen}>
            {isFullscreen ? 'Exit Fullscreen' : '⛶ Fullscreen'}
          </Button>

          <Button variant="danger" size="sm" onClick={handleReset}>
            Reset Demo (R)
          </Button>
        </div>
      </div>

      {/* 2. Main Visual Surface: Map + Presentation Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.8fr 1.2fr',
          gap: '1.25rem',
          minHeight: '520px',
        }}
      >
        {/* Left: GIS Map with dynamic scenario overlay */}
        <div
          style={{
            position: 'relative',
            borderRadius: '8px',
            border: '1px solid var(--border-strong)',
            overflow: 'hidden',
            minHeight: '480px',
          }}
        >
          <CommandMap
            center={DEMO_OPERATIONAL_AREA.center}
            zoom={DEMO_OPERATIONAL_AREA.defaultZoom}
            floodFeatures={isFloodActive ? DEMO_FLOOD_FEATURES : []}
            roadFeatures={dynamicRoads}
            bridgeFeatures={dynamicBridges}
            incidents={dynamicIncidents}
            hospitals={DEMO_HOSPITALS}
            shelters={DEMO_SHELTERS}
            routes={dynamicRoutes}
            visibleLayers={visibleLayers}
            selectedEntity={selectedEntity}
            onSelectEntity={setSelectedEntity}
          />

          {/* Mode Watermark */}
          <div
            style={{
              position: 'absolute',
              top: '12px',
              left: '52px',
              zIndex: 1000,
              padding: '0.25rem 0.6rem',
              backgroundColor:
                currentStep.data_mode === 'SIMULATION'
                  ? 'rgba(139, 92, 246, 0.9)'
                  : 'rgba(245, 158, 11, 0.9)',
              color: '#ffffff',
              fontSize: '0.72rem',
              fontWeight: 700,
              borderRadius: '4px',
              letterSpacing: '0.05em',
            }}
          >
            DEMO SCENARIO: {currentStep.state_id}
          </div>

          <div style={{ position: 'absolute', bottom: '16px', right: '16px', zIndex: 1000 }}>
            <MapLegend visibleLayers={visibleLayers} />
          </div>
        </div>

        {/* Right: Presentation Narrative & System Response */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Active Step Card */}
          <Card
            title={currentStep.title}
            subtitle={`Phase Integration: ${currentStep.event_source}`}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', fontSize: '0.85rem' }}>
              <p style={{ color: 'var(--text-primary)', lineHeight: 1.5, fontWeight: 500 }}>
                {currentStep.narration}
              </p>

              {/* Status Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '0.5rem',
                  fontSize: '0.75rem',
                  backgroundColor: 'var(--bg-surface-raised)',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Bridge B-001: </span>
                  <span
                    style={{
                      fontWeight: 700,
                      color: isBridgeFailed ? 'var(--color-critical)' : 'var(--color-online)',
                    }}
                  >
                    {currentStep.bridge_status}
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Corridor R-101: </span>
                  <span
                    style={{
                      fontWeight: 700,
                      color: isRoadBlocked ? 'var(--color-critical)' : 'var(--color-online)',
                    }}
                  >
                    {currentStep.road_status}
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Emergency Route: </span>
                  <span
                    style={{
                      fontWeight: 700,
                      color: isRerouted ? '#60a5fa' : isRoadBlocked ? 'var(--color-critical)' : 'var(--color-online)',
                    }}
                  >
                    {currentStep.route_status}
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Field App Net: </span>
                  <span
                    style={{
                      fontWeight: 700,
                      color:
                        currentStep.field_connectivity === 'ONLINE'
                          ? 'var(--color-online)'
                          : 'var(--color-critical)',
                    }}
                  >
                    {currentStep.field_connectivity}
                  </span>
                </div>
              </div>

              {/* Dynamic Rerouting Box */}
              {isRerouted && (
                <div
                  style={{
                    padding: '0.6rem',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ fontWeight: 700, color: '#93c5fd' }}>Phase 08 Dynamic Rerouting</div>
                  <div>Diversion: +{currentStep.route_detour_km} km • Delay: +{currentStep.route_delay_min} min</div>
                  <div style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Causeway Bridge B-001 submerged → Invalidation triggered → Alternative computed via Northern Flyover.
                  </div>
                </div>
              )}

              {/* Offline Field Incident Box */}
              {currentStep.offline_queue_count > 0 && (
                <div
                  style={{
                    padding: '0.6rem',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ fontWeight: 700, color: '#fcd34d' }}>Field Device Offline Queue</div>
                  <div>1 Pending Incident (INC-001) stored locally in IndexedDB</div>
                  <div style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Zero data loss while disconnected. Ready for central reconciliation upon network recovery.
                  </div>
                </div>
              )}

              {/* Sync Success Box */}
              {currentStep.state_id === 'NETWORK_RESTORED_SYNC' && (
                <div
                  style={{
                    padding: '0.6rem',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ fontWeight: 700, color: '#6ee7b7' }}>Reconciliation Complete</div>
                  <div>Field event synced → Digital Twin bumped from v43 to v44</div>
                  <div style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Deterministic Merkle audit hash generated. Incident dispatched to RESCUE-UNIT-03.
                  </div>
                </div>
              )}

              {/* What-If Counterfactual Box */}
              {currentStep.state_id === 'WHAT_IF_EVALUATION' && (
                <div
                  style={{
                    padding: '0.6rem',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ fontWeight: 700, color: '#c4b5fd' }}>Phase 11 Counterfactual Evaluation</div>
                  <div>Tested Hospital H-002 zero-capacity scenario in forked sandbox state.</div>
                  <div style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Authoritative Twin state remains clean and unmutated at v44.
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Causal Chain Display */}
          <Card title="Causal Chain Synthesizer" subtitle="Deterministic cause-and-effect progression">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ color: isFloodActive ? 'var(--color-critical)' : 'var(--text-muted)' }}>●</span>
                <span>Flood Surge (+1.0m Inundation)</span>
              </div>
              <div style={{ paddingLeft: '0.4rem', color: 'var(--text-muted)' }}>↓</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ color: isBridgeFailed ? 'var(--color-critical)' : 'var(--text-muted)' }}>●</span>
                <span>Bridge B-001 Clearance Breach (Structural Closure)</span>
              </div>
              <div style={{ paddingLeft: '0.4rem', color: 'var(--text-muted)' }}>↓</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ color: isRoadBlocked ? 'var(--color-critical)' : 'var(--text-muted)' }}>●</span>
                <span>Corridor R-101 Impassable</span>
              </div>
              <div style={{ paddingLeft: '0.4rem', color: 'var(--text-muted)' }}>↓</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ color: isRerouted ? '#60a5fa' : 'var(--text-muted)' }}>●</span>
                <span>Dynamic Reroute via Northern Flyover Computed</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* 3. Timeline & Scenario Stepper Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.8rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrev}
            disabled={manager.isFirstStep()}
          >
            ◀ Previous (←)
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleNext}
            disabled={manager.isLastStep()}
          >
            {manager.isLastStep() ? 'Scenario Finished' : 'Next Event (→)'}
          </Button>
        </div>

        {/* Stepper Dots */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {JUDGE_SCENARIO.steps.map((step) => (
            <div
              key={step.step_index}
              title={`${step.step_index}. ${step.title}`}
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor:
                  step.step_index === currentStep.step_index
                    ? '#3b82f6'
                    : step.step_index < currentStep.step_index
                    ? 'var(--color-online)'
                    : 'var(--border-strong)',
                boxShadow:
                  step.step_index === currentStep.step_index
                    ? '0 0 6px #3b82f6'
                    : 'none',
              }}
            />
          ))}
        </div>

        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Tip: Use <kbd style={{ padding: '0.1rem 0.3rem', background: 'var(--bg-surface-raised)', borderRadius: '3px' }}>←</kbd> and <kbd style={{ padding: '0.1rem 0.3rem', background: 'var(--bg-surface-raised)', borderRadius: '3px' }}>→</kbd> keys to step through presentation.
        </div>
      </div>
    </div>
  );
};

/**
 * Operational Incident Management Page - Phase 15
 * Complete incident lifecycle management:
 * Table, Filter bar, Detail inspector, Status actions (Acknowledge, Start, Resolve, Cancel),
 * Create form with validation, and Audit Timeline.
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  SeverityBadge,
} from '../components/ui';
import {
  IncidentSummary,
  SeverityLevel,
} from '../types';
import { DEMO_INCIDENTS } from '../services/gisDemoData';
import { getDistrictOperationalData, DISTRICT_REGISTRY } from '../services/districtRegistry';
import { useApp } from '../context/AppContext';

interface IncidentItem extends IncidentSummary {
  priority?: number;
  state_version?: number;
  allowed_transitions?: string[];
  history?: {
    action: string;
    timestamp: string;
    actor: string;
    details?: string;
  }[];
}

function buildIncidents(districtId: string, emergencyType: string): IncidentItem[] {
  // For Chennai (default), use the canonical DEMO data to preserve test compatibility
  const rawIncidents = districtId.toLowerCase() === 'chennai'
    ? DEMO_INCIDENTS
    : getDistrictOperationalData(districtId as any, emergencyType as any).incidents;
  return rawIncidents.map((inc) => ({
    ...inc,
    priority: inc.severity === 'CRITICAL' ? 1 : inc.severity === 'HIGH' ? 2 : 3,
    state_version: 1,
    allowed_transitions: inc.status === 'REPORTED' ? ['ACKNOWLEDGED', 'CANCELLED'] : ['RESOLVED', 'CANCELLED'],
    history: [
      {
        action: 'CREATED',
        timestamp: inc.reportedAt,
        actor: inc.source || 'FIELD_OFFICER',
        details: 'Incident ingested into operational twin',
      },
    ],
  }));
}

export const IncidentsPage: React.FC = () => {
  const { districtId, emergencyType } = useApp();
  const district = DISTRICT_REGISTRY[districtId.toLowerCase()] || DISTRICT_REGISTRY['chennai'];
  const hazardName = emergencyType.replace(/_/g, ' ');

  const [incidents, setIncidents] = useState<IncidentItem[]>(() => buildIncidents(districtId, emergencyType));
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);

  // Re-sync incidents when district or emergency changes
  useEffect(() => {
    setIncidents(buildIncidents(districtId, emergencyType));
    setSelectedIncident(null);
  }, [districtId, emergencyType]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  // Create Form State
  const [isCreating, setIsCreating] = useState(false);
  const [newId, setNewId] = useState(`INC-${Date.now().toString().slice(-4)}`);
  const [newType, setNewType] = useState('FLOOD_INUNDATION');
  const [newSeverity, setNewSeverity] = useState<SeverityLevel>('HIGH');
  const [newPriority, setNewPriority] = useState<number>(2);
  const [newLon, setNewLon] = useState<number>(80.2707);
  const [newLat, setNewLat] = useState<number>(13.0827);
  const [newDesc, setNewDesc] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  // Filter logic
  const filteredIncidents = incidents.filter((inc) => {
    if (statusFilter !== 'ALL' && inc.status !== statusFilter) return false;
    if (severityFilter !== 'ALL' && inc.severity !== severityFilter) return false;
    return true;
  });

  const handleSelectIncident = (inc: IncidentItem) => {
    setSelectedIncident(inc);
    setIsCreating(false);
  };

  const handleStatusTransition = (targetStatus: 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'RESOLVED' | 'CANCELLED') => {
    if (!selectedIncident) return;

    const currentVersion = selectedIncident.state_version || 1;
    const now = new Date().toLocaleTimeString();

    const allowedNext: Record<string, string[]> = {
      ACKNOWLEDGED: ['IN_PROGRESS', 'CANCELLED'],
      IN_PROGRESS: ['RESOLVED', 'CANCELLED'],
      RESOLVED: [],
      CANCELLED: [],
    };

    const updated: IncidentItem = {
      ...selectedIncident,
      status: targetStatus as any,
      state_version: currentVersion + 1,
      allowed_transitions: allowedNext[targetStatus] || [],
      history: [
        ...(selectedIncident.history || []),
        {
          action: `STATUS_${targetStatus}`,
          timestamp: now,
          actor: 'COORDINATOR',
          details: `Transitioned status to ${targetStatus}`,
        },
      ],
    };

    setIncidents((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    setSelectedIncident(updated);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!newDesc.trim()) {
      setFormError('Situational description is required.');
      return;
    }

    if (newLon < -180 || newLon > 180 || newLat < -90 || newLat > 90) {
      setFormError('Invalid coordinate boundaries (WGS84 lon: [-180, 180], lat: [-90, 90]).');
      return;
    }

    const now = new Date().toLocaleTimeString();
    const created: IncidentItem = {
      id: newId,
      type: newType,
      severity: newSeverity,
      status: 'REPORTED',
      description: newDesc,
      latitude: newLat,
      longitude: newLon,
      reportedAt: now,
      source: 'COMMAND_CENTER',
      priority: newPriority,
      state_version: 1,
      allowed_transitions: ['ACKNOWLEDGED', 'CANCELLED'],
      history: [
        {
          action: 'CREATED',
          timestamp: now,
          actor: 'COMMAND_CENTER_OPERATOR',
          details: 'Manual dispatch creation via Command Center',
        },
      ],
    };

    setIncidents([created, ...incidents]);
    setSelectedIncident(created);
    setIsCreating(false);
    setNewDesc('');
    setNewId(`INC-${Date.now().toString().slice(-4)}`);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.9rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Operational Incident Management
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
            {district.name} • {district.operationalArea} • {hazardName} • Lifecycle State Machine • Digital Twin Versioning • Audit Trail
          </p>
        </div>

        <Button
          variant={isCreating ? 'outline' : 'primary'}
          size="sm"
          onClick={() => {
            setIsCreating(!isCreating);
            if (!isCreating) setSelectedIncident(null);
          }}
        >
          {isCreating ? 'Cancel Creation' : '＋ Report Incident'}
        </Button>
      </div>

      {/* Main Grid: List/Form on Left, Detail/Timeline on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1.25rem' }}>
        {/* Left Column: Create Form or Incidents Table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isCreating ? (
            <Card title="Register New Emergency Incident" subtitle="Canonical Phase 04 schema validation">
              <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                {formError && (
                  <div style={{ color: 'var(--color-critical)', fontSize: '0.78rem', fontWeight: 600 }}>
                    {formError}
                  </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                      Incident ID
                    </label>
                    <input
                      type="text"
                      value={newId}
                      readOnly
                      style={{
                        width: '100%',
                        padding: '0.4rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-muted)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.8rem',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                      Event Category
                    </label>
                    <select
                      value={newType}
                      onChange={(e) => setNewType(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.4rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontSize: '0.8rem',
                      }}
                    >
                      <option value="FLOOD_INUNDATION">FLOOD_INUNDATION</option>
                      <option value="ROAD_BLOCKED">ROAD_BLOCKED</option>
                      <option value="BRIDGE_FAILURE">BRIDGE_FAILURE</option>
                      <option value="MEDICAL_EMERGENCY">MEDICAL_EMERGENCY</option>
                      <option value="TRAPPED_PERSONS">TRAPPED_PERSONS</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                      Severity
                    </label>
                    <select
                      value={newSeverity}
                      onChange={(e) => setNewSeverity(e.target.value as SeverityLevel)}
                      style={{
                        width: '100%',
                        padding: '0.4rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontSize: '0.8rem',
                      }}
                    >
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                      <option value="CRITICAL">CRITICAL</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                      Priority (1 highest - 5 lowest)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="5"
                      value={newPriority}
                      onChange={(e) => setNewPriority(Number(e.target.value))}
                      style={{
                        width: '100%',
                        padding: '0.4rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontSize: '0.8rem',
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                      Longitude (WGS84)
                    </label>
                    <input
                      type="number"
                      step="0.0001"
                      value={newLon}
                      onChange={(e) => setNewLon(parseFloat(e.target.value))}
                      style={{
                        width: '100%',
                        padding: '0.4rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontSize: '0.8rem',
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                      Latitude (WGS84)
                    </label>
                    <input
                      type="number"
                      step="0.0001"
                      value={newLat}
                      onChange={(e) => setNewLat(parseFloat(e.target.value))}
                      style={{
                        width: '100%',
                        padding: '0.4rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontSize: '0.8rem',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                    Situational Description
                  </label>
                  <textarea
                    rows={3}
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    placeholder="Describe emergency conditions, water level, trapped victims..."
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      backgroundColor: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: 'var(--text-primary)',
                      fontSize: '0.8rem',
                    }}
                  />
                </div>

                <Button variant="primary" type="submit" style={{ marginTop: '0.4rem' }}>
                  Submit Operational Report
                </Button>
              </form>
            </Card>
          ) : (
            <Card title="Incident Dispatch Roster">
              {/* Filter Bar */}
              <div
                style={{
                  display: 'flex',
                  gap: '1rem',
                  marginBottom: '1rem',
                  paddingBottom: '0.75rem',
                  borderBottom: '1px solid var(--border-subtle)',
                  fontSize: '0.75rem',
                }}
              >
                <div>
                  <label style={{ color: 'var(--text-muted)', marginRight: '0.4rem' }}>Status:</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    style={{
                      padding: '0.25rem 0.5rem',
                      backgroundColor: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: 'var(--text-primary)',
                    }}
                  >
                    <option value="ALL">ALL STATUSES</option>
                    <option value="REPORTED">REPORTED / OPEN</option>
                    <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                    <option value="IN_PROGRESS">IN_PROGRESS</option>
                    <option value="RESOLVED">RESOLVED</option>
                    <option value="CANCELLED">CANCELLED</option>
                  </select>
                </div>

                <div>
                  <label style={{ color: 'var(--text-muted)', marginRight: '0.4rem' }}>Severity:</label>
                  <select
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value)}
                    style={{
                      padding: '0.25rem 0.5rem',
                      backgroundColor: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: 'var(--text-primary)',
                    }}
                  >
                    <option value="ALL">ALL SEVERITIES</option>
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              {/* Table */}
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.78rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-strong)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '0.5rem' }}>ID</th>
                    <th style={{ padding: '0.5rem' }}>Type</th>
                    <th style={{ padding: '0.5rem' }}>Severity</th>
                    <th style={{ padding: '0.5rem' }}>Status</th>
                    <th style={{ padding: '0.5rem' }}>Reported</th>
                    <th style={{ padding: '0.5rem' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIncidents.map((inc) => {
                    const isSelected = selectedIncident?.id === inc.id;
                    return (
                      <tr
                        key={inc.id}
                        onClick={() => handleSelectIncident(inc)}
                        style={{
                          borderBottom: '1px solid var(--border-subtle)',
                          backgroundColor: isSelected ? 'var(--bg-surface-raised)' : 'transparent',
                          cursor: 'pointer',
                        }}
                      >
                        <td style={{ padding: '0.5rem', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          {inc.id}
                        </td>
                        <td style={{ padding: '0.5rem' }}>{inc.type}</td>
                        <td style={{ padding: '0.5rem' }}>
                          <SeverityBadge level={inc.severity} />
                        </td>
                        <td style={{ padding: '0.5rem' }}>
                          <span
                            style={{
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              color:
                                inc.status === 'RESOLVED'
                                  ? 'var(--color-online)'
                                  : inc.status === 'CANCELLED'
                                  ? 'var(--text-muted)'
                                  : 'var(--color-severe)',
                            }}
                          >
                            {inc.status}
                          </span>
                        </td>
                        <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>{inc.reportedAt}</td>
                        <td style={{ padding: '0.5rem' }}>
                          <Button variant="outline" size="sm" onClick={() => handleSelectIncident(inc)}>
                            Inspect
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          )}
        </div>

        {/* Right Column: Selected Incident Lifecycle & Audit Trail */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {selectedIncident ? (
            <>
              <Card
                title={`Incident: ${selectedIncident.id}`}
                subtitle={`Twin Version: v${selectedIncident.state_version || 1} • Priority: ${selectedIncident.priority || 1}`}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Severity Level:</span>
                    <SeverityBadge level={selectedIncident.severity} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Operational Status:</span>
                    <span style={{ fontWeight: 700, color: '#60a5fa' }}>{selectedIncident.status}</span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Coordinates:</span>
                    <span style={{ fontFamily: 'var(--font-mono)' }}>
                      [{selectedIncident.longitude.toFixed(4)}, {selectedIncident.latitude.toFixed(4)}]
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Assigned Unit:</span>
                    <span style={{ fontWeight: 600 }}>{selectedIncident.assignedUnit || 'Unassigned'}</span>
                  </div>

                  <div style={{ padding: '0.6rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '4px' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: '0.2rem' }}>
                      Situation Report:
                    </div>
                    <p style={{ lineHeight: 1.4 }}>{selectedIncident.description}</p>
                  </div>

                  {/* Valid Lifecycle Actions (Enforcing State Machine) */}
                  <div style={{ marginTop: '0.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>
                      PERMITTED LIFECYCLE ACTIONS:
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {selectedIncident.status === 'REPORTED' && (
                        <>
                          <Button variant="primary" size="sm" onClick={() => handleStatusTransition('ACKNOWLEDGED')}>
                            ✓ Acknowledge
                          </Button>
                          <Button variant="danger" size="sm" onClick={() => handleStatusTransition('CANCELLED')}>
                            ✕ Cancel
                          </Button>
                        </>
                      )}

                      {selectedIncident.status === 'ACKNOWLEDGED' && (
                        <>
                          <Button variant="primary" size="sm" onClick={() => handleStatusTransition('IN_PROGRESS')}>
                            ▶ Start Response
                          </Button>
                          <Button variant="danger" size="sm" onClick={() => handleStatusTransition('CANCELLED')}>
                            ✕ Cancel
                          </Button>
                        </>
                      )}

                      {selectedIncident.status === 'IN_PROGRESS' && (
                        <>
                          <Button variant="primary" size="sm" onClick={() => handleStatusTransition('RESOLVED')}>
                            ★ Resolve Incident
                          </Button>
                          <Button variant="danger" size="sm" onClick={() => handleStatusTransition('CANCELLED')}>
                            ✕ Cancel
                          </Button>
                        </>
                      )}

                      {(selectedIncident.status === 'RESOLVED' || selectedIncident.status === 'CANCELLED') && (
                        <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.75rem' }}>
                          Incident is in terminal state ({selectedIncident.status}).
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Audit History Card */}
              <Card title="Audit & State History" subtitle="Immutable state transition log">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.75rem' }}>
                  {(selectedIncident.history || []).map((h, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '0.4rem 0.6rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        borderRadius: '4px',
                        borderLeft: '3px solid #3b82f6',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-primary)', fontWeight: 600 }}>
                        <span>{h.action}</span>
                        <span style={{ color: 'var(--text-muted)' }}>{h.timestamp}</span>
                      </div>
                      <div style={{ color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                        By {h.actor} — {h.details}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          ) : (
            <div
              style={{
                padding: '2rem',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.8rem',
              }}
            >
              Select an incident from the dispatch roster to inspect telemetry, execute validated lifecycle transitions, and view the audit log.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

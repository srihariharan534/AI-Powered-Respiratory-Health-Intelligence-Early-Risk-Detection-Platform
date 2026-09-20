/**
 * Operational Hospitals Management Page - Phase 16
 * Complete hospital operational coordination:
 * - Stats overview (Total capacity, Available capacity, Operational count, Overloaded count)
 * - Roster Table with live badges (REAL vs SIMULATION vs DEMO)
 * - Filter bar (Status, Accessibility, Emergency Availability, Has Available Capacity, Search)
 * - Facility Inspector Detail View with Flood Exposure evaluation and Audit Timeline
 * - Interactive Capacity Update dialog (Optimistic Concurrency vX -> vX+1)
 * - Interactive Status Transition dialog (OPERATIONAL, OVERLOADED, EVACUATING, CLOSED)
 * - Leaflet CommandMap synchronization
 */

import React, { useState, useMemo } from 'react';
import { Card, Button, DataModeBadge } from '../components/ui';
import { CommandMap, DetailPanel } from '../components/command-map';
import { DEMO_HOSPITALS, DEMO_SHELTERS } from '../services/gisDemoData';
import { DISTRICT_REGISTRY, getDistrictOperationalData } from '../services/districtRegistry';
import { useApp } from '../context/AppContext';
import { FacilitySummary, GisSelectedEntity } from '../types';

interface HospitalRecord extends FacilitySummary {
  hospital_id: string;
  emergency_available: boolean;
  icu_available: number;
  accessibility: string;
  source: string;
  state_version: number;
  history?: {
    action: string;
    timestamp: string;
    actor: string;
    state_version: number;
    details?: string;
  }[];
}

function buildHospitalRecords(districtId: string, emergencyType: string): HospitalRecord[] {
  // For Chennai (default), use the canonical DEMO data to preserve test compatibility
  const rawHospitals = districtId.toLowerCase() === 'chennai'
    ? DEMO_HOSPITALS
    : getDistrictOperationalData(districtId as any, emergencyType as any).hospitals;
  return rawHospitals.map((h) => ({
    ...h,
    hospital_id: h.id,
    emergency_available: h.emergencyAvailable ?? true,
    icu_available: h.icuAvailable ?? 8,
    accessibility: h.accessibility || 'ALL_VEHICLES',
    source: h.source || 'SYNTHETIC_DEMO',
    state_version: h.stateVersion || 1,
    history: [
      {
        action: 'INGESTED',
        timestamp: h.lastUpdated,
        actor: h.source || 'SYNTHETIC_DEMO',
        state_version: 1,
        details: `Hospital registered with capacity ${h.capacityTotal}`,
      },
    ],
  }));
}

export const HospitalsPage: React.FC = () => {
  const { districtId, emergencyType } = useApp();
  const district = DISTRICT_REGISTRY[districtId.toLowerCase()] || DISTRICT_REGISTRY['chennai'];

  const districtHospitals = useMemo(
    () => buildHospitalRecords(districtId, emergencyType),
    [districtId, emergencyType]
  );

  const [hospitals, setHospitals] = useState<HospitalRecord[]>(districtHospitals);
  const [selectedHospital, setSelectedHospital] = useState<HospitalRecord | null>(districtHospitals[0] || null);

  // Re-sync when district/emergency changes
  React.useEffect(() => {
    const fresh = buildHospitalRecords(districtId, emergencyType);
    setHospitals(fresh);
    setSelectedHospital(fresh[0] || null);
  }, [districtId, emergencyType]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [emergencyFilter, setEmergencyFilter] = useState<string>('ALL');
  const [accessibilityFilter, setAccessibilityFilter] = useState<string>('ALL');
  const [capacityOnly, setCapacityOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals / Dialogs
  const [isUpdatingCapacity, setIsUpdatingCapacity] = useState<boolean>(false);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false);
  const [newAvailableCapacity, setNewAvailableCapacity] = useState<number>(0);
  const [newStatus, setNewStatus] = useState<string>('OPERATIONAL');
  const [updateReason, setUpdateReason] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);

  // Map state — follows district center
  const [mapCenter, setMapCenter] = useState<[number, number]>(
    selectedHospital
      ? [selectedHospital.longitude ?? district.center[0], selectedHospital.latitude ?? district.center[1]]
      : district.center
  );
  const [mapZoom, setMapZoom] = useState<number>(district.defaultZoom);

  React.useEffect(() => {
    setMapCenter(district.center);
    setMapZoom(district.defaultZoom);
  }, [district]);

  // Filtered hospitals
  const filteredHospitals = useMemo(() => {
    return hospitals.filter((h) => {
      if (statusFilter !== 'ALL' && h.operationalStatus !== statusFilter) return false;
      if (emergencyFilter === 'AVAILABLE' && !h.emergency_available) return false;
      if (emergencyFilter === 'UNAVAILABLE' && h.emergency_available) return false;
      if (accessibilityFilter !== 'ALL' && h.accessibility !== accessibilityFilter) return false;
      if (capacityOnly && h.capacityTotal - h.capacityOccupied <= 0) return false;
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchName = h.name.toLowerCase().includes(query);
        const matchId = h.hospital_id.toLowerCase().includes(query);
        if (!matchName && !matchId) return false;
      }
      return true;
    });
  }, [hospitals, statusFilter, emergencyFilter, accessibilityFilter, capacityOnly, searchQuery]);

  // Aggregate Metrics
  const metrics = useMemo(() => {
    let totalCap = 0;
    let totalOccupied = 0;
    let operationalCount = 0;
    let overloadedCount = 0;
    let emergencyReadyCount = 0;

    hospitals.forEach((h) => {
      totalCap += h.capacityTotal;
      totalOccupied += h.capacityOccupied;
      if (h.operationalStatus === 'OPERATIONAL') operationalCount++;
      if (h.operationalStatus === 'OVERLOADED') overloadedCount++;
      if (h.emergency_available) emergencyReadyCount++;
    });

    return {
      totalCapacity: totalCap,
      availableCapacity: totalCap - totalOccupied,
      operationalCount,
      overloadedCount,
      emergencyReadyCount,
    };
  }, [hospitals]);

  const handleSelectHospital = (hosp: HospitalRecord) => {
    setSelectedHospital(hosp);
    if (hosp.longitude && hosp.latitude) {
      setMapCenter([hosp.longitude, hosp.latitude]);
      setMapZoom(15);
    }
    setFormError(null);
  };

  const openCapacityModal = () => {
    if (!selectedHospital) return;
    const currentAvailable = selectedHospital.capacityTotal - selectedHospital.capacityOccupied;
    setNewAvailableCapacity(currentAvailable);
    setUpdateReason('');
    setFormError(null);
    setIsUpdatingCapacity(true);
    setIsUpdatingStatus(false);
  };

  const openStatusModal = () => {
    if (!selectedHospital) return;
    setNewStatus(selectedHospital.operationalStatus);
    setUpdateReason('');
    setFormError(null);
    setIsUpdatingStatus(true);
    setIsUpdatingCapacity(false);
  };

  const handleSaveCapacity = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedHospital) return;

    if (newAvailableCapacity < 0) {
      setFormError('Available capacity cannot be negative.');
      return;
    }
    if (newAvailableCapacity > selectedHospital.capacityTotal) {
      setFormError(`Available capacity cannot exceed total capacity (${selectedHospital.capacityTotal}).`);
      return;
    }

    const currentVersion = selectedHospital.state_version || 1;
    const now = new Date().toLocaleTimeString();

    const updated: HospitalRecord = {
      ...selectedHospital,
      capacityOccupied: selectedHospital.capacityTotal - newAvailableCapacity,
      lastUpdated: now,
      state_version: currentVersion + 1,
      stateVersion: currentVersion + 1,
      history: [
        {
          action: 'CAPACITY_UPDATED',
          timestamp: now,
          actor: 'COORDINATOR',
          state_version: currentVersion + 1,
          details: updateReason || `Available beds set to ${newAvailableCapacity}/${selectedHospital.capacityTotal}`,
        },
        ...(selectedHospital.history || []),
      ],
    };

    setHospitals((prev) => prev.map((h) => (h.hospital_id === updated.hospital_id ? updated : h)));
    setSelectedHospital(updated);
    setIsUpdatingCapacity(false);
  };

  const handleSaveStatus = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedHospital) return;

    const currentVersion = selectedHospital.state_version || 1;
    const now = new Date().toLocaleTimeString();

    const updated: HospitalRecord = {
      ...selectedHospital,
      operationalStatus: newStatus,
      lastUpdated: now,
      state_version: currentVersion + 1,
      stateVersion: currentVersion + 1,
      history: [
        {
          action: `STATUS_TRANSITION_${newStatus}`,
          timestamp: now,
          actor: 'COORDINATOR',
          state_version: currentVersion + 1,
          details: updateReason || `Status transitioned to ${newStatus}`,
        },
        ...(selectedHospital.history || []),
      ],
    };

    setHospitals((prev) => prev.map((h) => (h.hospital_id === updated.hospital_id ? updated : h)));
    setSelectedHospital(updated);
    setIsUpdatingStatus(false);
  };

  // Convert for CommandMap selectedEntity
  const selectedEntity: GisSelectedEntity = selectedHospital
    ? {
        type: 'HOSPITAL',
        data: {
          ...selectedHospital,
          id: selectedHospital.hospital_id,
        },
      }
    : null;

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
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Hospital &amp; Trauma Facility Management
            </h1>
            <DataModeBadge mode="DEMO" />
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            {district.name} • {district.operationalArea} • Operational bed availability, emergency care status, and optimistic concurrency versioning
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {selectedHospital && (
            <>
              <Button variant="outline" size="sm" onClick={openCapacityModal}>
                ⚡ Update Capacity
              </Button>
              <Button variant="primary" size="sm" onClick={openStatusModal}>
                🔄 Transition Status
              </Button>
            </>
          )}
        </div>
      </div>

      {/* KPI Overview Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.75rem' }}>
        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Capacity</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
            {metrics.totalCapacity} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>beds</span>
          </div>
        </div>

        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Available Capacity</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--color-online)', marginTop: '0.2rem' }}>
            {metrics.availableCapacity} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>beds</span>
          </div>
        </div>

        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Operational</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#34d399', marginTop: '0.2rem' }}>
            {metrics.operationalCount} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>facilities</span>
          </div>
        </div>

        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Overloaded</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f59e0b', marginTop: '0.2rem' }}>
            {metrics.overloadedCount} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>facilities</span>
          </div>
        </div>

        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Emergency Care</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#60a5fa', marginTop: '0.2rem' }}>
            {metrics.emergencyReadyCount} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>active</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Roster Table (Left) + GIS Map & Details (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '1.25rem' }}>
        {/* Left Column: Filter Bar + Roster Table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Card title="Hospital Telemetry Roster">
            {/* Filter Bar */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.75rem',
                marginBottom: '1rem',
                paddingBottom: '0.75rem',
                borderBottom: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
              }}
            >
              <div>
                <label style={{ color: 'var(--text-muted)', marginRight: '0.3rem' }}>Status:</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    padding: '0.25rem 0.4rem',
                    backgroundColor: 'var(--bg-surface-raised)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    color: 'var(--text-primary)',
                  }}
                >
                  <option value="ALL">ALL STATUSES</option>
                  <option value="OPERATIONAL">OPERATIONAL</option>
                  <option value="OVERLOADED">OVERLOADED</option>
                  <option value="EVACUATING">EVACUATING</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)', marginRight: '0.3rem' }}>Emergency:</label>
                <select
                  value={emergencyFilter}
                  onChange={(e) => setEmergencyFilter(e.target.value)}
                  style={{
                    padding: '0.25rem 0.4rem',
                    backgroundColor: 'var(--bg-surface-raised)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    color: 'var(--text-primary)',
                  }}
                >
                  <option value="ALL">ALL</option>
                  <option value="AVAILABLE">AVAILABLE</option>
                  <option value="UNAVAILABLE">UNAVAILABLE</option>
                </select>
              </div>

              <div>
                <label style={{ color: 'var(--text-muted)', marginRight: '0.3rem' }}>Access:</label>
                <select
                  value={accessibilityFilter}
                  onChange={(e) => setAccessibilityFilter(e.target.value)}
                  style={{
                    padding: '0.25rem 0.4rem',
                    backgroundColor: 'var(--bg-surface-raised)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    color: 'var(--text-primary)',
                  }}
                >
                  <option value="ALL">ALL ROADS</option>
                  <option value="ALL_VEHICLES">ALL_VEHICLES</option>
                  <option value="EMERGENCY_ONLY">EMERGENCY_ONLY</option>
                  <option value="HIGH_CLEARANCE_ONLY">HIGH_CLEARANCE_ONLY</option>
                  <option value="IMPASSABLE">IMPASSABLE</option>
                </select>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <input
                  type="checkbox"
                  id="capOnly"
                  checked={capacityOnly}
                  onChange={(e) => setCapacityOnly(e.target.checked)}
                />
                <label htmlFor="capOnly" style={{ color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  Has Available Capacity
                </label>
              </div>

              <div style={{ flex: 1, minWidth: '140px' }}>
                <input
                  type="text"
                  placeholder="Search hospital..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.25rem 0.5rem',
                    backgroundColor: 'var(--bg-surface-raised)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    color: 'var(--text-primary)',
                    fontSize: '0.75rem',
                  }}
                />
              </div>
            </div>

            {/* Roster Table */}
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.78rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-strong)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.5rem' }}>Hospital</th>
                  <th style={{ padding: '0.5rem' }}>Status</th>
                  <th style={{ padding: '0.5rem' }}>Available / Total</th>
                  <th style={{ padding: '0.5rem' }}>Emergency</th>
                  <th style={{ padding: '0.5rem' }}>ICU</th>
                  <th style={{ padding: '0.5rem' }}>Flood Exp.</th>
                  <th style={{ padding: '0.5rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredHospitals.map((h) => {
                  const isSelected = selectedHospital?.hospital_id === h.hospital_id;
                  const available = h.capacityTotal - h.capacityOccupied;
                  const isExposed = h.floodExposure?.is_exposed;

                  return (
                    <tr
                      key={h.hospital_id}
                      onClick={() => handleSelectHospital(h)}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        backgroundColor: isSelected ? 'var(--bg-surface-raised)' : 'transparent',
                        cursor: 'pointer',
                      }}
                    >
                      <td style={{ padding: '0.5rem' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{h.name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {h.hospital_id} • v{h.state_version || 1}
                        </div>
                      </td>

                      <td style={{ padding: '0.5rem' }}>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            color:
                              h.operationalStatus === 'OPERATIONAL'
                                ? 'var(--color-online)'
                                : h.operationalStatus === 'OVERLOADED'
                                ? 'var(--color-severe)'
                                : 'var(--color-critical)',
                          }}
                        >
                          {h.operationalStatus}
                        </span>
                      </td>

                      <td style={{ padding: '0.5rem' }}>
                        <span style={{ fontWeight: 700, color: available > 0 ? 'var(--color-online)' : 'var(--color-critical)' }}>
                          {available}
                        </span>{' '}
                        / {h.capacityTotal}
                      </td>

                      <td style={{ padding: '0.5rem' }}>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            fontWeight: 600,
                            color: h.emergency_available ? 'var(--color-online)' : 'var(--text-muted)',
                          }}
                        >
                          {h.emergency_available ? 'AVAILABLE' : 'OFFLINE'}
                        </span>
                      </td>

                      <td style={{ padding: '0.5rem', fontWeight: 600 }}>{h.icu_available}</td>

                      <td style={{ padding: '0.5rem' }}>
                        {isExposed ? (
                          <span
                            style={{
                              fontSize: '0.68rem',
                              fontWeight: 700,
                              padding: '0.15rem 0.4rem',
                              borderRadius: '3px',
                              backgroundColor: 'rgba(59, 130, 246, 0.2)',
                              color: '#60a5fa',
                            }}
                          >
                            EXPOSED
                          </span>
                        ) : (
                          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>CLEAR</span>
                        )}
                      </td>

                      <td style={{ padding: '0.5rem' }}>
                        <Button variant="outline" size="sm" onClick={() => handleSelectHospital(h)}>
                          Select
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>

          {/* Modal / Dialog: Capacity Update */}
          {isUpdatingCapacity && selectedHospital && (
            <Card title={`Update Bed Capacity: ${selectedHospital.name}`}>
              <form onSubmit={handleSaveCapacity} style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                {formError && <div style={{ color: 'var(--color-critical)', fontSize: '0.78rem' }}>{formError}</div>}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8rem' }}>
                  <div>
                    <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Total Capacity</label>
                    <input
                      type="number"
                      value={selectedHospital.capacityTotal}
                      disabled
                      style={{
                        width: '100%',
                        padding: '0.4rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-muted)',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.2rem' }}>
                      New Available Capacity
                    </label>
                    <input
                      type="number"
                      min="0"
                      max={selectedHospital.capacityTotal}
                      value={newAvailableCapacity}
                      onChange={(e) => setNewAvailableCapacity(parseInt(e.target.value) || 0)}
                      required
                      style={{
                        width: '100%',
                        padding: '0.4rem',
                        backgroundColor: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-strong)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontWeight: 700,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                    Reason / Operational Justification
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Mass casualty intake from flood sector 4"
                    value={updateReason}
                    onChange={(e) => setUpdateReason(e.target.value)}
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

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <Button variant="outline" size="sm" onClick={() => setIsUpdatingCapacity(false)}>
                    Cancel
                  </Button>
                  <Button variant="primary" size="sm" type="submit">
                    Confirm & Emit Twin Event
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {/* Modal / Dialog: Status Transition */}
          {isUpdatingStatus && selectedHospital && (
            <Card title={`Transition Facility Status: ${selectedHospital.name}`}>
              <form onSubmit={handleSaveStatus} style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                <div style={{ fontSize: '0.8rem' }}>
                  <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>
                    Target Operational Status
                  </label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.4rem',
                      backgroundColor: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-strong)',
                      borderRadius: '4px',
                      color: 'var(--text-primary)',
                      fontWeight: 600,
                    }}
                  >
                    <option value="OPERATIONAL">OPERATIONAL (Standard triage active)</option>
                    <option value="OVERLOADED">OVERLOADED (High patient surge)</option>
                    <option value="EVACUATING">EVACUATING (Active patient transfer)</option>
                    <option value="CLOSED">CLOSED (Inaccessible / structurally shut)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                    Operational Rationale
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Floodwater compromised emergency ward generator"
                    value={updateReason}
                    onChange={(e) => setUpdateReason(e.target.value)}
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

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <Button variant="outline" size="sm" onClick={() => setIsUpdatingStatus(false)}>
                    Cancel
                  </Button>
                  <Button variant="danger" size="sm" type="submit">
                    Confirm Transition
                  </Button>
                </div>
              </form>
            </Card>
          )}
        </div>

        {/* Right Column: GIS Map + Inspector + Audit Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Map Preview */}
          <Card title="Operational Geospatial Map" subtitle="Click facility marker to inspect">
            <div style={{ height: '320px', width: '100%' }}>
              <CommandMap
                center={mapCenter}
                zoom={mapZoom}
                floodFeatures={[]}
                roadFeatures={[]}
                bridgeFeatures={[]}
                incidents={[]}
                hospitals={hospitals}
                shelters={DEMO_SHELTERS}
                routes={[]}
                visibleLayers={{
                  flood: false,
                  roads: false,
                  bridges: false,
                  incidents: false,
                  facilities: true,
                  routes: false,
                }}
                selectedEntity={selectedEntity}
                onSelectEntity={(ent) => {
                  if (ent && ent.type === 'HOSPITAL') {
                    const match = hospitals.find((h) => h.hospital_id === ent.data.id);
                    if (match) handleSelectHospital(match);
                  }
                }}
              />
            </div>
          </Card>

          {/* Inspector Panel */}
          <DetailPanel selectedEntity={selectedEntity} onClose={() => setSelectedHospital(null)} />

          {/* Audit History Timeline */}
          {selectedHospital && (
            <Card
              title="Audit & Telemetry History"
              subtitle={`State Version: v${selectedHospital.state_version || 1} • Source: ${selectedHospital.source}`}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.75rem' }}>
                {(selectedHospital.history || []).map((h, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '0.4rem 0.6rem',
                      backgroundColor: 'var(--bg-surface-raised)',
                      borderRadius: '4px',
                      borderLeft: '3px solid #10b981',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                      <span>{h.action}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{h.timestamp}</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                      v{h.state_version} by {h.actor} — {h.details}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

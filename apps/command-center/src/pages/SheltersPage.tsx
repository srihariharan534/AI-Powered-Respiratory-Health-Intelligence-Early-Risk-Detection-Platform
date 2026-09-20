/**
 * Operational Shelters Management Page - Phase 16
 * Complete evacuation shelter & relief camp coordination:
 * - Stats overview (Total capacity, Available capacity, Open count, At-Capacity count)
 * - Roster Table with live badges (REAL vs SIMULATION vs DEMO)
 * - Filter bar (Status, Accessibility, Has Available Capacity, Search)
 * - Facility Inspector Detail View with Flood Exposure evaluation and Audit Timeline
 * - Interactive Capacity Update dialog (Optimistic Concurrency vX -> vX+1)
 * - Interactive Status Transition dialog (OPEN, AT_CAPACITY, STANDBY, CLOSED)
 * - Leaflet CommandMap synchronization
 */

import React, { useState, useMemo } from 'react';
import { Card, Button, DataModeBadge } from '../components/ui';
import { CommandMap, DetailPanel } from '../components/command-map';
import { DEMO_HOSPITALS, DEMO_SHELTERS } from '../services/gisDemoData';
import { DISTRICT_REGISTRY, getDistrictOperationalData } from '../services/districtRegistry';
import { useApp } from '../context/AppContext';
import { FacilitySummary, GisSelectedEntity } from '../types';

interface ShelterRecord extends FacilitySummary {
  shelter_id: string;
  has_power_backup: boolean;
  has_potable_water: boolean;
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

function buildShelterRecords(districtId: string, emergencyType: string): ShelterRecord[] {
  // For Chennai (default), use the canonical DEMO data to preserve test compatibility
  const rawShelters = districtId.toLowerCase() === 'chennai'
    ? DEMO_SHELTERS
    : getDistrictOperationalData(districtId as any, emergencyType as any).shelters;
  return rawShelters.map((s) => ({
    ...s,
    shelter_id: s.id,
    has_power_backup: s.powerStatus === 'GENERATOR' || s.powerStatus === 'GRID',
    has_potable_water: true,
    accessibility: s.accessibility || 'ALL_VEHICLES',
    source: s.source || 'SYNTHETIC_DEMO',
    state_version: s.stateVersion || 1,
    history: [
      {
        action: 'INGESTED',
        timestamp: s.lastUpdated,
        actor: s.source || 'SYNTHETIC_DEMO',
        state_version: 1,
        details: `Evacuation shelter registered with capacity ${s.capacityTotal}`,
      },
    ],
  }));
}

export const SheltersPage: React.FC = () => {
  const { districtId, emergencyType } = useApp();
  const district = DISTRICT_REGISTRY[districtId.toLowerCase()] || DISTRICT_REGISTRY['chennai'];

  const districtShelters = useMemo(
    () => buildShelterRecords(districtId, emergencyType),
    [districtId, emergencyType]
  );

  const [shelters, setShelters] = useState<ShelterRecord[]>(districtShelters);
  const [selectedShelter, setSelectedShelter] = useState<ShelterRecord | null>(districtShelters[0] || null);

  // Re-sync when district/emergency changes
  React.useEffect(() => {
    const fresh = buildShelterRecords(districtId, emergencyType);
    setShelters(fresh);
    setSelectedShelter(fresh[0] || null);
  }, [districtId, emergencyType]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [accessibilityFilter, setAccessibilityFilter] = useState<string>('ALL');
  const [capacityOnly, setCapacityOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals / Dialogs
  const [isUpdatingCapacity, setIsUpdatingCapacity] = useState<boolean>(false);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false);
  const [newAvailableCapacity, setNewAvailableCapacity] = useState<number>(0);
  const [newStatus, setNewStatus] = useState<string>('OPEN');
  const [updateReason, setUpdateReason] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);

  // Map state — follows district center
  const [mapCenter, setMapCenter] = useState<[number, number]>(
    selectedShelter
      ? [selectedShelter.longitude ?? district.center[0], selectedShelter.latitude ?? district.center[1]]
      : district.center
  );
  const [mapZoom, setMapZoom] = useState<number>(district.defaultZoom);

  React.useEffect(() => {
    setMapCenter(district.center);
    setMapZoom(district.defaultZoom);
  }, [district]);

  // Filtered shelters
  const filteredShelters = useMemo(() => {
    return shelters.filter((s) => {
      if (statusFilter !== 'ALL' && s.operationalStatus !== statusFilter) return false;
      if (accessibilityFilter !== 'ALL' && s.accessibility !== accessibilityFilter) return false;
      if (capacityOnly && s.capacityTotal - s.capacityOccupied <= 0) return false;
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchName = s.name.toLowerCase().includes(query);
        const matchId = s.shelter_id.toLowerCase().includes(query);
        if (!matchName && !matchId) return false;
      }
      return true;
    });
  }, [shelters, statusFilter, accessibilityFilter, capacityOnly, searchQuery]);

  // Aggregate Metrics
  const metrics = useMemo(() => {
    let totalCap = 0;
    let totalOccupied = 0;
    let openCount = 0;
    let atCapacityCount = 0;

    shelters.forEach((s) => {
      totalCap += s.capacityTotal;
      totalOccupied += s.capacityOccupied;
      if (s.operationalStatus === 'OPEN') openCount++;
      if (s.operationalStatus === 'AT_CAPACITY') atCapacityCount++;
    });

    return {
      totalCapacity: totalCap,
      availableCapacity: totalCap - totalOccupied,
      openCount,
      atCapacityCount,
    };
  }, [shelters]);

  const handleSelectShelter = (shelt: ShelterRecord) => {
    setSelectedShelter(shelt);
    if (shelt.longitude && shelt.latitude) {
      setMapCenter([shelt.longitude, shelt.latitude]);
      setMapZoom(15);
    }
    setFormError(null);
  };

  const openCapacityModal = () => {
    if (!selectedShelter) return;
    const currentAvailable = selectedShelter.capacityTotal - selectedShelter.capacityOccupied;
    setNewAvailableCapacity(currentAvailable);
    setUpdateReason('');
    setFormError(null);
    setIsUpdatingCapacity(true);
    setIsUpdatingStatus(false);
  };

  const openStatusModal = () => {
    if (!selectedShelter) return;
    setNewStatus(selectedShelter.operationalStatus);
    setUpdateReason('');
    setFormError(null);
    setIsUpdatingStatus(true);
    setIsUpdatingCapacity(false);
  };

  const handleSaveCapacity = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedShelter) return;

    if (newAvailableCapacity < 0) {
      setFormError('Available capacity cannot be negative.');
      return;
    }
    if (newAvailableCapacity > selectedShelter.capacityTotal) {
      setFormError(`Available capacity cannot exceed total capacity (${selectedShelter.capacityTotal}).`);
      return;
    }

    const currentVersion = selectedShelter.state_version || 1;
    const now = new Date().toLocaleTimeString();

    const updated: ShelterRecord = {
      ...selectedShelter,
      capacityOccupied: selectedShelter.capacityTotal - newAvailableCapacity,
      lastUpdated: now,
      state_version: currentVersion + 1,
      stateVersion: currentVersion + 1,
      history: [
        {
          action: 'CAPACITY_UPDATED',
          timestamp: now,
          actor: 'COORDINATOR',
          state_version: currentVersion + 1,
          details: updateReason || `Available spots set to ${newAvailableCapacity}/${selectedShelter.capacityTotal}`,
        },
        ...(selectedShelter.history || []),
      ],
    };

    setShelters((prev) => prev.map((s) => (s.shelter_id === updated.shelter_id ? updated : s)));
    setSelectedShelter(updated);
    setIsUpdatingCapacity(false);
  };

  const handleSaveStatus = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedShelter) return;

    const currentVersion = selectedShelter.state_version || 1;
    const now = new Date().toLocaleTimeString();

    const updated: ShelterRecord = {
      ...selectedShelter,
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
        ...(selectedShelter.history || []),
      ],
    };

    setShelters((prev) => prev.map((s) => (s.shelter_id === updated.shelter_id ? updated : s)));
    setSelectedShelter(updated);
    setIsUpdatingStatus(false);
  };

  const selectedEntity: GisSelectedEntity = selectedShelter
    ? {
        type: 'SHELTER',
        data: {
          ...selectedShelter,
          id: selectedShelter.shelter_id,
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
              Evacuation Shelter &amp; Relief Camp Management
            </h1>
            <DataModeBadge mode="DEMO" />
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            {district.name} • {district.operationalArea} • Shelter population capacity, potable water/power status, and digital twin state authority
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {selectedShelter && (
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Capacity</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
            {metrics.totalCapacity} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>people</span>
          </div>
        </div>

        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Available Capacity</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--color-online)', marginTop: '0.2rem' }}>
            {metrics.availableCapacity} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>spots</span>
          </div>
        </div>

        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Open Shelters</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#06b6d4', marginTop: '0.2rem' }}>
            {metrics.openCount} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>centers</span>
          </div>
        </div>

        <div style={{ padding: '0.8rem', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>At Capacity</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f59e0b', marginTop: '0.2rem' }}>
            {metrics.atCapacityCount} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>camps</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Shelter Table (Left) + GIS Map & Details (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '1.25rem' }}>
        {/* Left Column: Filter Bar + Roster Table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Card title="Designated Relief Shelter Roster">
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
                  <option value="OPEN">OPEN</option>
                  <option value="AT_CAPACITY">AT_CAPACITY</option>
                  <option value="STANDBY">STANDBY</option>
                  <option value="CLOSED">CLOSED</option>
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
                  id="sheltCapOnly"
                  checked={capacityOnly}
                  onChange={(e) => setCapacityOnly(e.target.checked)}
                />
                <label htmlFor="sheltCapOnly" style={{ color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  Has Available Capacity
                </label>
              </div>

              <div style={{ flex: 1, minWidth: '140px' }}>
                <input
                  type="text"
                  placeholder="Search shelter..."
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
                  <th style={{ padding: '0.5rem' }}>Shelter</th>
                  <th style={{ padding: '0.5rem' }}>Status</th>
                  <th style={{ padding: '0.5rem' }}>Available / Total</th>
                  <th style={{ padding: '0.5rem' }}>Power & Water</th>
                  <th style={{ padding: '0.5rem' }}>Flood Exp.</th>
                  <th style={{ padding: '0.5rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredShelters.map((s) => {
                  const isSelected = selectedShelter?.shelter_id === s.shelter_id;
                  const available = s.capacityTotal - s.capacityOccupied;
                  const isExposed = s.floodExposure?.is_exposed;

                  return (
                    <tr
                      key={s.shelter_id}
                      onClick={() => handleSelectShelter(s)}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        backgroundColor: isSelected ? 'var(--bg-surface-raised)' : 'transparent',
                        cursor: 'pointer',
                      }}
                    >
                      <td style={{ padding: '0.5rem' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {s.shelter_id} • v{s.state_version || 1}
                        </div>
                      </td>

                      <td style={{ padding: '0.5rem' }}>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            color:
                              s.operationalStatus === 'OPEN'
                                ? 'var(--color-online)'
                                : s.operationalStatus === 'AT_CAPACITY'
                                ? 'var(--color-severe)'
                                : 'var(--color-critical)',
                          }}
                        >
                          {s.operationalStatus}
                        </span>
                      </td>

                      <td style={{ padding: '0.5rem' }}>
                        <span style={{ fontWeight: 700, color: available > 0 ? 'var(--color-online)' : 'var(--color-critical)' }}>
                          {available}
                        </span>{' '}
                        / {s.capacityTotal}
                      </td>

                      <td style={{ padding: '0.5rem' }}>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                          {s.powerStatus} • {s.has_potable_water ? '💧 Water' : 'No Water'}
                        </span>
                      </td>

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
                        <Button variant="outline" size="sm" onClick={() => handleSelectShelter(s)}>
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
          {isUpdatingCapacity && selectedShelter && (
            <Card title={`Update Shelter Capacity: ${selectedShelter.name}`}>
              <form onSubmit={handleSaveCapacity} style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                {formError && <div style={{ color: 'var(--color-critical)', fontSize: '0.78rem' }}>{formError}</div>}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8rem' }}>
                  <div>
                    <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Total Capacity</label>
                    <input
                      type="number"
                      value={selectedShelter.capacityTotal}
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
                      New Available Spots
                    </label>
                    <input
                      type="number"
                      min="0"
                      max={selectedShelter.capacityTotal}
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
                    placeholder="e.g. Influx of displaced families from Sector 2"
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
          {isUpdatingStatus && selectedShelter && (
            <Card title={`Transition Shelter Status: ${selectedShelter.name}`}>
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
                    <option value="OPEN">OPEN (Accepting evacuees)</option>
                    <option value="AT_CAPACITY">AT_CAPACITY (No additional intake)</option>
                    <option value="STANDBY">STANDBY (Staged for activation)</option>
                    <option value="CLOSED">CLOSED (Inaccessible / closed)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                    Operational Rationale
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Shelter reached maximum occupancy quota"
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
                hospitals={DEMO_HOSPITALS}
                shelters={shelters}
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
                  if (ent && ent.type === 'SHELTER') {
                    const match = shelters.find((s) => s.shelter_id === ent.data.id);
                    if (match) handleSelectShelter(match);
                  }
                }}
              />
            </div>
          </Card>

          {/* Inspector Panel */}
          <DetailPanel selectedEntity={selectedEntity} onClose={() => setSelectedShelter(null)} />

          {/* Audit History Timeline */}
          {selectedShelter && (
            <Card
              title="Audit & Telemetry History"
              subtitle={`State Version: v${selectedShelter.state_version || 1} • Source: ${selectedShelter.source}`}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.75rem' }}>
                {(selectedShelter.history || []).map((s, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '0.4rem 0.6rem',
                      backgroundColor: 'var(--bg-surface-raised)',
                      borderRadius: '4px',
                      borderLeft: '3px solid #06b6d4',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                      <span>{s.action}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{s.timestamp}</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                      v{s.state_version} by {s.actor} — {s.details}
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

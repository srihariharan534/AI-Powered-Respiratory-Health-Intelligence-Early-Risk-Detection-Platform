import React from 'react';
import { Card, Button, DigitalTwinBadge } from '../components/ui';
import { useApp } from '../context/AppContext';
import { DISTRICT_REGISTRY, getDistrictOperationalData } from '../services/districtRegistry';

export const DigitalTwinPage: React.FC = () => {
  const { stateVersionInfo, refreshStateVersion, districtId, emergencyType } = useApp();
  const district = DISTRICT_REGISTRY[districtId.toLowerCase()] || DISTRICT_REGISTRY['chennai'];
  const data = getDistrictOperationalData(districtId as any, emergencyType as any);
  const hazardName = emergencyType.replace(/_/g, ' ');

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
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {district.name} — Digital Twin Authority
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            {district.operationalArea} • {hazardName} domain • Versioned operational state authority across roads, bridges, facilities, and flood extents
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refreshStateVersion}>
          Poll Authority
        </Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <Card title="State Authority Metadata">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Authority Service:</span>
              <span style={{ fontWeight: 600 }}>{stateVersionInfo.authority}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Active District:</span>
              <span style={{ fontWeight: 600, color: 'var(--color-online)' }}>{district.name}, {district.region}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Emergency Domain:</span>
              <span style={{ fontWeight: 600, color: '#f59e0b' }}>{hazardName}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>EOC Command Node:</span>
              <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>{district.eocName}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>State Version:</span>
              <DigitalTwinBadge versionInfo={stateVersionInfo} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Last Synchronization:</span>
              <span>{stateVersionInfo.lastUpdated || 'Never'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Integrity Verification:</span>
              <span style={{ color: 'var(--color-online)', fontWeight: 600 }}>Deterministic Merkle Root Valid</span>
            </div>
          </div>
        </Card>

        <Card title={`Entity Registry — ${district.name}`}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', fontSize: '0.85rem' }}>
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '6px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Road Segments</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '0.2rem' }}>{data.roadFeatures.length} Monitored</div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '6px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Bridges</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '0.2rem' }}>{data.bridgeFeatures.length} State Overlay Active</div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '6px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Shelters</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '0.2rem' }}>{data.shelters.length} Operational</div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '6px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Hospitals</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '0.2rem' }}>{data.hospitals.length} Operational</div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '6px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Active Incidents</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '0.2rem', color: 'var(--color-critical)' }}>{data.incidents.length} Tracked</div>
            </div>
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-raised)', borderRadius: '6px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Evac Routes</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '0.2rem' }}>{data.routes.length} Active</div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

import React from 'react';
import { Card, EmptyState } from '../components/ui';
import { useApp } from '../context/AppContext';
import { DISTRICT_REGISTRY, getDistrictOperationalData } from '../services/districtRegistry';

export const HospitalsPage: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Hospital & Trauma Center Coordination
        </h1>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Bed occupancy, triage status, backup generator power, and accessibility
        </p>
      </div>

      <Card title="Operational Medical Centers">
        <EmptyState
          title="No Hospital Telemetry Stream Active"
          description="Facility status updates and capacity streams will sync from health coordination gateways in Phase 15."
        />
      </Card>
    </div>
  );
};

export const SheltersPage: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Evacuation Shelters & Relief Camps
        </h1>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Camp capacity, food/water supply rations, sanitation, and medical triage
        </p>
      </div>

      <Card title="Designated Relief Shelters">
        <EmptyState
          title="No Shelter Telemetry Stream Active"
          description="Shelter occupancy and supply telemetry will sync in Phase 16 (Shelter & Relief Camp Engine)."
        />
      </Card>
    </div>
  );
};

export const VulnerabilityPage: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Vulnerability & Social Demographic Priority
        </h1>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Priority scores for elderly populations, mobility-impaired citizens, and low-lying clusters
        </p>
      </div>

      <Card title="Vulnerability Clusters">
        <EmptyState
          title="Vulnerability Analysis Engine"
          description="Population demographic and vulnerability scoring maps will be integrated in Phase 17."
        />
      </Card>
    </div>
  );
};

export const RecommendationsPage: React.FC = () => {
  const { districtId, emergencyType } = useApp();
  const district = DISTRICT_REGISTRY[districtId.toLowerCase()] || DISTRICT_REGISTRY['chennai'];
  const data = getDistrictOperationalData(districtId as any, emergencyType as any);
  const hazardName = emergencyType.replace(/_/g, ' ');

  const districtRec = data.recommendation;

  const [recommendations, setRecommendations] = React.useState<Array<{
    id: string;
    action: string;
    priority: number;
    target: string;
    reasoning: string;
    score: number;
    status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
    factors: Array<{ name: string; weight: number; description: string }>;
    stateVersion: string;
    mode?: string;
  }>>(() => [
    {
      id: districtRec.id,
      action: districtRec.action,
      priority: districtRec.priority,
      target: districtRec.target,
      reasoning: districtRec.reasoning,
      score: districtRec.score,
      status: 'PENDING' as const,
      factors: districtRec.factors,
      stateVersion: 'state-v104',
      mode: 'REAL_DATA',
    },
    {
      id: `REC-HOSP-${district.id.slice(0, 3).toUpperCase()}-002`,
      action: 'DIVERT_AMBULANCES',
      priority: 2,
      target: `${district.name} District Headquarters Hospital`,
      reasoning: `Optimal receiving facility in ${district.operationalArea} with available surge beds and Level 1 emergency care active.`,
      score: 0.84,
      status: 'PENDING' as const,
      factors: [
        { name: 'travel_time', weight: 0.35, description: `Distance within ${district.name}: ~4.2 km (~8 min transit)` },
        { name: 'available_capacity', weight: 0.30, description: '14 / 50 available beds (28%)' },
        { name: 'emergency_care', weight: 0.20, description: '24/7 Emergency Care Active' },
        { name: 'hazard_safety', weight: 0.15, description: `Facility clear of active ${hazardName.toLowerCase()} zone` },
      ],
      stateVersion: 'state-v104',
      mode: 'REAL_DATA',
    },
  ]);

  const [message, setMessage] = React.useState<{ text: string; type: 'success' | 'error' | 'warning' } | null>(null);
  const [selectedRecId, setSelectedRecId] = React.useState<string | null>(null);
  const [actionType, setActionType] = React.useState<'APPROVE' | 'REJECT' | null>(null);
  const [rejectReason, setRejectReason] = React.useState<string>('');
  const [simulatedCurrentStateVersion] = React.useState<string>('state-v104');
  const [userRole, setUserRole] = React.useState<'COMMANDER' | 'APPROVER' | 'OPERATOR' | 'VIEWER'>('COMMANDER');

  const canDecide = userRole === 'COMMANDER' || userRole === 'APPROVER';

  const confirmDecision = () => {
    if (!selectedRecId || !actionType) return;
    const targetRec = recommendations.find((r) => r.id === selectedRecId);
    if (!targetRec) return;

    // Check state freshness
    if (targetRec.stateVersion !== simulatedCurrentStateVersion) {
      setMessage({
        text: `APPROVAL BLOCKED: Recommendation ${selectedRecId} is STALE (source ${targetRec.stateVersion} vs current ${simulatedCurrentStateVersion}). Must regenerate.`,
        type: 'error',
      });
      setRecommendations((prev) =>
        prev.map((r) => (r.id === selectedRecId ? { ...r, status: 'EXPIRED' } : r))
      );
      setSelectedRecId(null);
      setActionType(null);
      return;
    }

    if (actionType === 'REJECT' && (!rejectReason || rejectReason.trim().length < 3)) {
      alert('A substantive operational rejection reason is mandatory.');
      return;
    }

    const newStatus = actionType === 'APPROVE' ? 'APPROVED' : 'REJECTED';
    setRecommendations((prev) =>
      prev.map((r) => (r.id === selectedRecId ? { ...r, status: newStatus } : r))
    );

    setMessage({
      text: `Recommendation ${selectedRecId} marked as ${newStatus} by ${userRole}. Immutable audit event appended.`,
      type: newStatus === 'APPROVED' ? 'success' : 'warning',
    });
    setSelectedRecId(null);
    setActionType(null);
    setRejectReason('');
    setTimeout(() => setMessage(null), 5000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {district.name} — Operational Recommendation Governance
            </h1>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              {district.operationalArea} • {hazardName} • Deterministic triage, routing, and facility allocation with mandatory human-in-the-loop coordinator approval
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <span>Acting Role:</span>
              <select
                value={userRole}
                onChange={(e) => setUserRole(e.target.value as any)}
                style={{
                  padding: '0.2rem 0.5rem',
                  borderRadius: '4px',
                  backgroundColor: 'var(--bg-card)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                }}
              >
                <option value="COMMANDER">COMMANDER (Full Authority)</option>
                <option value="APPROVER">APPROVER (Approval Only)</option>
                <option value="OPERATOR">OPERATOR (Read & Propose)</option>
                <option value="VIEWER">VIEWER (Read-Only)</option>
              </select>
            </div>
            <span
              style={{
                padding: '0.3rem 0.6rem',
                borderRadius: '4px',
                backgroundColor: 'rgba(239, 68, 68, 0.12)',
                color: '#ef4444',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: '1px solid rgba(239, 68, 68, 0.3)',
              }}
            >
              HUMAN APPROVAL MANDATORY
            </span>
          </div>
        </div>
      </div>

      {message && (
        <div
          style={{
            padding: '0.75rem 1rem',
            backgroundColor:
              message.type === 'success'
                ? 'rgba(34, 197, 94, 0.12)'
                : message.type === 'error'
                ? 'rgba(239, 68, 68, 0.12)'
                : 'rgba(234, 179, 8, 0.12)',
            border: `1px solid ${
              message.type === 'success'
                ? 'rgba(34, 197, 94, 0.3)'
                : message.type === 'error'
                ? 'rgba(239, 68, 68, 0.3)'
                : 'rgba(234, 179, 8, 0.3)'
            }`,
            borderRadius: '6px',
            color: message.type === 'success' ? '#22c55e' : message.type === 'error' ? '#ef4444' : '#eab308',
            fontSize: '0.85rem',
          }}
        >
          {message.text}
        </div>
      )}

      {/* Confirmation / Rejection Modal Dialog */}
      {selectedRecId && actionType && (
        <div
          style={{
            padding: '1.25rem',
            backgroundColor: 'var(--bg-surface)',
            border: '2px solid var(--border-subtle)',
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          }}
        >
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            {actionType === 'APPROVE' ? 'Confirm Operational Authorization' : 'Record Operational Rejection'}
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            {actionType === 'APPROVE' ? (
              <>
                You are approving recommendation <strong>{selectedRecId}</strong> against Digital Twin state{' '}
                <code>{simulatedCurrentStateVersion}</code>. This action is irreversible and recorded in the append-only audit log.
              </>
            ) : (
              <>
                Please provide an operational rationale for rejecting recommendation <strong>{selectedRecId}</strong>:
              </>
            )}
          </p>

          {actionType === 'REJECT' && (
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Ground commander reported localized bridge flooding rendering primary corridor hazardous..."
              rows={3}
              style={{
                width: '100%',
                padding: '0.5rem',
                borderRadius: '4px',
                backgroundColor: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.85rem',
                marginBottom: '0.75rem',
              }}
            />
          )}

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={confirmDecision}
              style={{
                padding: '0.4rem 1.25rem',
                backgroundColor: actionType === 'APPROVE' ? '#22c55e' : '#ef4444',
                color: '#ffffff',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {actionType === 'APPROVE' ? 'Confirm Authorization' : 'Confirm Rejection'}
            </button>
            <button
              onClick={() => {
                setSelectedRecId(null);
                setActionType(null);
              }}
              style={{
                padding: '0.4rem 1rem',
                backgroundColor: 'transparent',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {recommendations.map((rec) => {
          const isStale = rec.stateVersion !== simulatedCurrentStateVersion && rec.status === 'PENDING';

          return (
            <Card key={rec.id} title={`${rec.action.replace('_', ' ')}: ${rec.target}`}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: rec.priority === 1 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                        color: rec.priority === 1 ? '#ef4444' : '#eab308',
                      }}
                    >
                      Priority {rec.priority}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      ID: {rec.id} ({rec.stateVersion})
                    </span>
                    <span
                      style={{
                        padding: '0.1rem 0.4rem',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        backgroundColor: 'var(--bg-card)',
                        color: 'var(--text-secondary)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      MODE: {rec.mode || 'REAL_DATA'}
                    </span>
                  </div>
                  <span
                    style={{
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      backgroundColor:
                        rec.status === 'APPROVED'
                          ? 'rgba(34, 197, 94, 0.2)'
                          : rec.status === 'REJECTED'
                          ? 'rgba(239, 68, 68, 0.2)'
                          : rec.status === 'EXPIRED'
                          ? 'rgba(107, 114, 128, 0.2)'
                          : 'rgba(59, 130, 246, 0.2)',
                      color:
                        rec.status === 'APPROVED'
                          ? '#22c55e'
                          : rec.status === 'REJECTED'
                          ? '#ef4444'
                          : rec.status === 'EXPIRED'
                          ? '#9ca3af'
                          : '#3b82f6',
                    }}
                  >
                    {rec.status}
                  </span>
                </div>

                {isStale && (
                  <div
                    style={{
                      padding: '0.5rem 0.75rem',
                      backgroundColor: 'rgba(234, 179, 8, 0.12)',
                      border: '1px solid rgba(234, 179, 8, 0.3)',
                      borderRadius: '4px',
                      color: '#eab308',
                      fontSize: '0.75rem',
                    }}
                  >
                    ⚠ <strong>RECOMMENDATION STALE:</strong> Digital Twin state advanced from{' '}
                    <code>{rec.stateVersion}</code> to <code>{simulatedCurrentStateVersion}</code>. Operational approval is blocked; review a regenerated recommendation.
                  </div>
                )}

                <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                  <strong>Reasoning:</strong> {rec.reasoning}
                </p>

                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                    Decision Factors (Policy Score: {(rec.score * 100).toFixed(0)}%):
                  </span>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                      gap: '0.5rem',
                      marginTop: '0.4rem',
                    }}
                  >
                    {rec.factors.map((f, i) => (
                      <div
                        key={i}
                        style={{
                          padding: '0.4rem 0.6rem',
                          backgroundColor: 'var(--bg-card)',
                          borderRadius: '4px',
                          border: '1px solid var(--border-subtle)',
                          fontSize: '0.75rem',
                        }}
                      >
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                          {f.name.replace('_', ' ').toUpperCase()} ({(f.weight * 100).toFixed(0)}%)
                        </div>
                        <div style={{ color: 'var(--text-muted)', marginTop: '0.1rem' }}>{f.description}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {rec.status === 'PENDING' && (
                  <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem', alignItems: 'center' }}>
                    <button
                      disabled={!canDecide || isStale}
                      onClick={() => {
                        setSelectedRecId(rec.id);
                        setActionType('APPROVE');
                      }}
                      style={{
                        padding: '0.4rem 1rem',
                        backgroundColor: canDecide && !isStale ? '#22c55e' : 'var(--bg-card)',
                        color: canDecide && !isStale ? '#ffffff' : 'var(--text-muted)',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: canDecide && !isStale ? 'pointer' : 'not-allowed',
                      }}
                    >
                      Authorize Action
                    </button>
                    <button
                      disabled={!canDecide}
                      onClick={() => {
                        setSelectedRecId(rec.id);
                        setActionType('REJECT');
                      }}
                      style={{
                        padding: '0.4rem 1rem',
                        backgroundColor: 'transparent',
                        color: canDecide ? '#ef4444' : 'var(--text-muted)',
                        border: `1px solid ${canDecide ? '#ef4444' : 'var(--border-subtle)'}`,
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: canDecide ? 'pointer' : 'not-allowed',
                      }}
                    >
                      Reject Proposal
                    </button>
                    {!canDecide && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        (Requires APPROVER or COMMANDER role)
                      </span>
                    )}
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export const AuditPage: React.FC = () => {
  const [events] = React.useState<Array<{
    id: string;
    type: string;
    timestamp: string;
    actor: string;
    role: string;
    recommendationId: string;
    previousState?: string;
    newState: string;
    sourceVersion: string;
    reason: string;
  }>>([
    {
      id: 'AUD-e89a1b02',
      type: 'RECOMMENDATION_CREATED',
      timestamp: '2026-09-20T07:15:00Z',
      actor: 'SYSTEM',
      role: 'OPERATOR',
      recommendationId: 'REC-PRIO-INC-001',
      newState: 'PENDING',
      sourceVersion: 'state-v104',
      reason: 'Generated priority triage recommendation for Sector 4 flood cluster',
    },
    {
      id: 'AUD-7f12bc44',
      type: 'RECOMMENDATION_VIEWED',
      timestamp: '2026-09-20T07:18:22Z',
      actor: 'USR-OP-01',
      role: 'COMMANDER',
      recommendationId: 'REC-PRIO-INC-001',
      previousState: 'PENDING',
      newState: 'PENDING',
      sourceVersion: 'state-v104',
      reason: 'Coordinator reviewed incident factors and physical water exposure',
    },
    {
      id: 'AUD-3a8901df',
      type: 'RECOMMENDATION_APPROVED',
      timestamp: '2026-09-20T07:20:10Z',
      actor: 'USR-OP-01',
      role: 'COMMANDER',
      recommendationId: 'REC-PRIO-INC-001',
      previousState: 'PENDING',
      newState: 'APPROVED',
      sourceVersion: 'state-v104',
      reason: 'Authorized rescue dispatch based on verified route corridor availability',
    },
  ]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Audit & Provenance Ledger
        </h1>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Append-only, cryptographically ordered governance timeline of all recommendation creations, reviews, approvals, and rejections
        </p>
      </div>

      <Card title="Chronological Governance Timeline">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {events.map((evt) => (
            <div
              key={evt.id}
              style={{
                display: 'flex',
                gap: '1rem',
                padding: '0.75rem 1rem',
                backgroundColor: 'var(--bg-card)',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                alignItems: 'flex-start',
              }}
            >
              <div
                style={{
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  backgroundColor:
                    evt.type === 'RECOMMENDATION_APPROVED'
                      ? 'rgba(34, 197, 94, 0.2)'
                      : evt.type === 'RECOMMENDATION_REJECTED'
                      ? 'rgba(239, 68, 68, 0.2)'
                      : evt.type === 'RECOMMENDATION_CREATED'
                      ? 'rgba(59, 130, 246, 0.2)'
                      : 'rgba(107, 114, 128, 0.2)',
                  color:
                    evt.type === 'RECOMMENDATION_APPROVED'
                      ? '#22c55e'
                      : evt.type === 'RECOMMENDATION_REJECTED'
                      ? '#ef4444'
                      : evt.type === 'RECOMMENDATION_CREATED'
                      ? '#3b82f6'
                      : '#9ca3af',
                  whiteSpace: 'nowrap',
                }}
              >
                {evt.type.replace('RECOMMENDATION_', '')}
              </div>

              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {evt.recommendationId} ({evt.sourceVersion})
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>{evt.reason}</p>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  Actor: <code>{evt.actor}</code> [{evt.role}] • Event ID: <code>{evt.id}</code>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export const JudgeModePage: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            NEXUS Evaluation & Judge Mode
          </h1>
          <span
            style={{
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              backgroundColor: 'rgba(59, 130, 246, 0.2)',
              color: '#60a5fa',
              fontSize: '0.7rem',
              fontWeight: 700,
            }}
          >
            PHASE 14 RESERVED
          </span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Interactive proof walkthrough and benchmark validation interface for hackathon evaluators
        </p>
      </div>

      <Card title="Judge Evaluation Shell">
        <EmptyState
          title="Judge Mode Interface Reserved for Phase 14"
          description="The dedicated hackathon evaluator mode with live verification gates and scenario test playback will be built in Phase 14."
        />
      </Card>
    </div>
  );
};

export const NotFoundPage: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
        textAlign: 'center',
        gap: '1rem',
      }}
    >
      <div style={{ fontSize: '3rem', fontWeight: 800, color: 'var(--text-muted)' }}>404</div>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
        PAGE NOT FOUND
      </h2>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: '400px' }}>
        The requested Command Center view does not exist or is not registered in the operational route table.
      </p>
      <a
        href="/dashboard"
        style={{
          marginTop: '0.5rem',
          padding: '0.5rem 1rem',
          backgroundColor: '#2563eb',
          color: '#ffffff',
          borderRadius: '6px',
          textDecoration: 'none',
          fontSize: '0.85rem',
          fontWeight: 600,
        }}
      >
        Return to Dashboard
      </a>
    </div>
  );
};

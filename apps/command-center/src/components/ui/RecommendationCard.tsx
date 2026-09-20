import React from 'react';
import { Button } from './Button';

export interface DecisionFactor {
  name: string;
  weight: number;
  description: string;
}

export interface RecommendationCardProps {
  id: string;
  action: string;
  target: string;
  priority: number;
  reasoning: string;
  score: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
  factors: DecisionFactor[];
  dataFreshness?: 'FRESH' | 'STALE' | 'HISTORICAL' | 'SIMULATED';
  stateVersion: string;
  onApprove?: () => void;
  onReject?: () => void;
  canApprove?: boolean;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  id,
  action,
  target,
  priority,
  reasoning,
  score,
  status,
  factors,
  dataFreshness = 'FRESH',
  stateVersion,
  onApprove,
  onReject,
  canApprove = true,
}) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-strong)',
        borderRadius: '8px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.9rem',
        position: 'relative',
        boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
      }}
    >
      {/* Header Strip */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                fontSize: '0.68rem',
                fontWeight: 800,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                color: '#60a5fa',
              }}
            >
              ✦ NEXUS RECOMMENDATION
            </span>
            <span
              style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                backgroundColor: priority === 1 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                color: priority === 1 ? '#ef4444' : '#f59e0b',
                border: `1px solid ${priority === 1 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
              }}
            >
              PRIORITY {priority}
            </span>
          </div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
            {action.replace('_', ' ')}: {target}
          </h3>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              backgroundColor:
                status === 'APPROVED'
                  ? 'rgba(16, 185, 129, 0.15)'
                  : status === 'REJECTED'
                  ? 'rgba(239, 68, 68, 0.15)'
                  : 'rgba(59, 130, 246, 0.15)',
              color:
                status === 'APPROVED'
                  ? '#10b981'
                  : status === 'REJECTED'
                  ? '#ef4444'
                  : '#60a5fa',
              border: `1px solid ${
                status === 'APPROVED'
                  ? 'rgba(16, 185, 129, 0.4)'
                  : status === 'REJECTED'
                  ? 'rgba(239, 68, 68, 0.4)'
                  : 'rgba(59, 130, 246, 0.4)'
              }`,
            }}
          >
            {status}
          </span>
          <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            v{stateVersion}
          </span>
        </div>
      </div>

      {/* Operational Reasoning */}
      <div
        style={{
          padding: '0.75rem',
          backgroundColor: 'var(--bg-surface-raised)',
          borderRadius: '6px',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.82rem',
          color: 'var(--text-primary)',
          lineHeight: 1.5,
        }}
      >
        <span style={{ fontWeight: 700, color: '#93c5fd', marginRight: '0.35rem' }}>WHY:</span>
        {reasoning}
      </div>

      {/* Decision Factors Breakdown */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Decision Factors (Model Confidence {(score * 100).toFixed(0)}%)
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.7rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>DATA STATUS:</span>
            <span style={{ color: dataFreshness === 'FRESH' ? '#10b981' : '#f59e0b', fontWeight: 600 }}>
              ● {dataFreshness}
            </span>
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '0.4rem',
          }}
        >
          {factors.map((factor, index) => (
            <div
              key={index}
              style={{
                padding: '0.45rem 0.6rem',
                backgroundColor: 'var(--bg-base)',
                borderRadius: '4px',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.74rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontWeight: 600 }}>
                <span>{factor.name.replace('_', ' ').toUpperCase()}</span>
                <span style={{ color: '#60a5fa', fontFamily: 'var(--font-mono)' }}>{(factor.weight * 100).toFixed(0)}%</span>
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '0.15rem' }}>
                {factor.description}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Human Governance / Approval Strip */}
      {status === 'PENDING' && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '0.75rem',
            borderTop: '1px solid var(--border-subtle)',
            marginTop: '0.25rem',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            Human Approval Mandatory • Action ID: <code>{id}</code>
          </div>

          <div style={{ display: 'flex', gap: '0.6rem' }}>
            {onReject && (
              <Button
                variant="outline"
                size="sm"
                onClick={onReject}
                disabled={!canApprove}
                style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: '#ef4444' }}
              >
                Reject
              </Button>
            )}
            {onApprove && (
              <Button
                variant="primary"
                size="sm"
                onClick={onApprove}
                disabled={!canApprove}
                style={{ backgroundColor: '#10b981', borderColor: '#10b981' }}
              >
                Authorize Action
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

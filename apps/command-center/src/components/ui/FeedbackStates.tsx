import React from 'react';

interface LoadingStateProps {
  message?: string;
  description?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading operational data...',
  description = 'Connecting to authority state...',
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 1.5rem',
        textAlign: 'center',
        gap: '0.75rem',
      }}
    >
      <div
        style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          border: '3px solid var(--border-strong)',
          borderTopColor: '#3b82f6',
          animation: 'spin 1s linear infinite',
        }}
      />
      <div>
        <p style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {message}
        </p>
        {description && (
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            {description}
          </p>
        )}
      </div>
    </div>
  );
};

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, action }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 1.5rem',
        textAlign: 'center',
        backgroundColor: 'var(--bg-surface-raised)',
        border: '1px dashed var(--border-strong)',
        borderRadius: '8px',
        gap: '0.75rem',
      }}
    >
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '8px',
          backgroundColor: 'var(--bg-surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          fontSize: '1.25rem',
        }}
      >
        ℹ
      </div>
      <div>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {title}
        </h4>
        <p
          style={{
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            marginTop: '0.25rem',
            maxWidth: '420px',
          }}
        >
          {description}
        </p>
      </div>
      {action && <div style={{ marginTop: '0.5rem' }}>{action}</div>}
    </div>
  );
};

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'DATA UNAVAILABLE',
  message,
  onRetry,
}) => {
  return (
    <div
      role="alert"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 1.5rem',
        textAlign: 'center',
        backgroundColor: 'rgba(239, 68, 68, 0.05)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: '8px',
        gap: '0.75rem',
      }}
    >
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '8px',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-critical)',
          fontSize: '1.25rem',
          fontWeight: 'bold',
        }}
      >
        !
      </div>
      <div>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-critical)' }}>
          {title}
        </h4>
        <p
          style={{
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            marginTop: '0.25rem',
            maxWidth: '460px',
          }}
        >
          {message}
        </p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          style={{
            marginTop: '0.5rem',
            padding: '0.4rem 0.9rem',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-strong)',
            color: 'var(--text-primary)',
            borderRadius: '6px',
            fontSize: '0.8rem',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          Retry Connection
        </button>
      )}
    </div>
  );
};

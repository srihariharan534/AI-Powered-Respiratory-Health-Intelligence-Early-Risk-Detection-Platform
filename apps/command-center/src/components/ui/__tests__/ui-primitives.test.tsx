import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusIndicator } from '../StatusIndicator';
import { SeverityBadge } from '../SeverityBadge';
import { DataModeBadge } from '../DataModeBadge';
import { DigitalTwinBadge } from '../DigitalTwinBadge';

describe('UI Primitives', () => {
  it('renders StatusIndicator correctly for ONLINE and OFFLINE', () => {
    const { rerender } = render(<StatusIndicator status="ONLINE" />);
    expect(screen.getByRole('status')).toBeDefined();
    expect(screen.getByText('ONLINE')).toBeDefined();

    rerender(<StatusIndicator status="OFFLINE" />);
    expect(screen.getByText('OFFLINE')).toBeDefined();
  });

  it('renders SeverityBadge with accessible semantics', () => {
    render(<SeverityBadge level="CRITICAL" />);
    expect(screen.getByText('CRITICAL')).toBeDefined();
    expect(screen.getByRole('status').getAttribute('aria-label')).toBe('Severity level: CRITICAL');
  });

  it('renders DataModeBadge clearly distinguishing SIMULATION from REAL', () => {
    const { rerender } = render(<DataModeBadge mode="SIMULATION" />);
    expect(screen.getByText('SIMULATION')).toBeDefined();

    rerender(<DataModeBadge mode="REAL" />);
    expect(screen.getByText('REAL DATA')).toBeDefined();
  });

  it('renders DigitalTwinBadge with version number or dash', () => {
    const { rerender } = render(
      <DigitalTwinBadge versionInfo={{ version: 42, lastUpdated: 'now', authority: 'NEXUS' }} />
    );
    expect(screen.getByText('42')).toBeDefined();

    rerender(
      <DigitalTwinBadge versionInfo={{ version: null, lastUpdated: null, authority: 'NEXUS' }} />
    );
    expect(screen.getByText('—')).toBeDefined();
  });
});

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppProvider } from '../../../context/AppContext';
import { Sidebar } from '../Sidebar';
import { Header } from '../Header';

describe('Layout Components', () => {
  it('renders Header with NEXUS branding, status, and state version', () => {
    render(
      <AppProvider>
        <Header />
      </AppProvider>
    );

    expect(screen.getByText('NEXUS')).toBeDefined();
    expect(screen.getByText('Emergency Decision Platform')).toBeDefined();
    expect(screen.getByText('State Version:')).toBeDefined();
  });

  it('renders Sidebar with all operational navigation links', () => {
    render(
      <AppProvider>
        <MemoryRouter initialEntries={['/dashboard']}>
          <Sidebar />
        </MemoryRouter>
      </AppProvider>
    );

    expect(screen.getByText('Dashboard')).toBeDefined();
    expect(screen.getByText('Incidents')).toBeDefined();
    expect(screen.getByText('Hospitals')).toBeDefined();
    expect(screen.getByText('Shelters')).toBeDefined();
    expect(screen.getByText('Vulnerability')).toBeDefined();
    expect(screen.getByText('What-If Simulation')).toBeDefined();
    expect(screen.getByText('Digital Twin')).toBeDefined();
    expect(screen.getByText('Recommendations')).toBeDefined();
    expect(screen.getByText('Audit & Provenance')).toBeDefined();
    expect(screen.getByText('Judge Mode')).toBeDefined();
  });
});

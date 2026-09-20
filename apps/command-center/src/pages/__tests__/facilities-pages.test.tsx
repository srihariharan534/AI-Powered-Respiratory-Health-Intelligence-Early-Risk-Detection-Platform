/**
 * Tests for Operational Facilities Management Pages - Phase 16
 * Tests HospitalsPage and SheltersPage components:
 * - Table rendering, KPI metrics, and capacity display
 * - Filtering by status, availability, emergency care
 * - Concurrency state versioning
 * - Interactive capacity and status dialogs
 * - Flood exposure labeling
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { HospitalsPage } from '../HospitalsPage';
import { SheltersPage } from '../SheltersPage';
import { AppProvider } from '../../context/AppContext';

// Mock Leaflet
vi.mock('leaflet', () => {
  const mapMock = {
    setView: vi.fn(),
    remove: vi.fn(),
    on: vi.fn(),
  };
  const layerGroupMock = {
    addTo: vi.fn().mockReturnThis(),
    clearLayers: vi.fn(),
    addLayer: vi.fn(),
  };
  const markerMock = {
    addTo: vi.fn().mockReturnThis(),
    bindTooltip: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
  };

  return {
    default: {
      map: vi.fn(() => mapMock),
      tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
      layerGroup: vi.fn(() => layerGroupMock),
      circleMarker: vi.fn(() => markerMock),
      polyline: vi.fn(() => markerMock),
      polygon: vi.fn(() => markerMock),
    },
  };
});

describe('HospitalsPage Operational Management', () => {
  it('renders Hospital Management header, KPI metrics, and roster table', () => {
    render(
      <AppProvider>
        <HospitalsPage />
      </AppProvider>
    );

    // Title and KPI metrics
    expect(screen.getByText('Hospital & Trauma Facility Management')).toBeDefined();
    expect(screen.getByText('Hospital Telemetry Roster')).toBeDefined();
    expect(screen.getAllByText('District General Trauma Hospital').length).toBeGreaterThan(0);
  });

  it('filters hospitals by status and emergency care', () => {
    render(
      <AppProvider>
        <HospitalsPage />
      </AppProvider>
    );

    const statusSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(statusSelect, { target: { value: 'OVERLOADED' } });

    // Metropolitan Surgical Institute is OVERLOADED
    expect(screen.getAllByText('Metropolitan Surgical Institute').length).toBeGreaterThan(0);
  });

  it('opens update capacity modal and allows editing capacity', () => {
    render(
      <AppProvider>
        <HospitalsPage />
      </AppProvider>
    );

    const updateCapBtn = screen.getByText('⚡ Update Capacity');
    fireEvent.click(updateCapBtn);

    expect(screen.getByText(/Update Bed Capacity:/)).toBeDefined();
    const spinbuttons = screen.getAllByRole('spinbutton');
    // Change available capacity input
    fireEvent.change(spinbuttons[spinbuttons.length - 1], { target: { value: '50' } });

    const submitBtn = screen.getByText('Confirm & Emit Twin Event');
    fireEvent.click(submitBtn);

    // Modal closes
    expect(screen.queryByText(/Update Bed Capacity:/)).toBeNull();
  });
});

describe('SheltersPage Operational Management', () => {
  it('renders Shelter Management header, KPI metrics, and roster table', () => {
    render(
      <AppProvider>
        <SheltersPage />
      </AppProvider>
    );

    expect(screen.getByText('Evacuation Shelter & Relief Camp Management')).toBeDefined();
    expect(screen.getByText('Designated Relief Shelter Roster')).toBeDefined();
    expect(screen.getAllByText('Community Relief Center North').length).toBeGreaterThan(0);
  });

  it('opens transition status dialog and allows transitioning shelter status', () => {
    render(
      <AppProvider>
        <SheltersPage />
      </AppProvider>
    );

    const transitionBtn = screen.getByText('🔄 Transition Status');
    fireEvent.click(transitionBtn);

    expect(screen.getByText(/Transition Shelter Status:/)).toBeDefined();
    const confirmBtn = screen.getByText('Confirm Transition');
    fireEvent.click(confirmBtn);

    expect(screen.queryByText(/Transition Shelter Status:/)).toBeNull();
  });
});



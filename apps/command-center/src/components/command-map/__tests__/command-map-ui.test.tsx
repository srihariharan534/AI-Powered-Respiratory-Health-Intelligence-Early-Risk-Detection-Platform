import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MapControls } from '../MapControls';
import { MapLegend } from '../MapLegend';
import { DetailPanel } from '../DetailPanel';
import { GisSelectedEntity } from '../../../types';

describe('GIS Map UI Controls & Symbology', () => {
  it('renders MapControls and handles layer toggle callbacks', () => {
    const onToggleLayer = vi.fn();
    const onResetView = vi.fn();

    const layers = {
      flood: true,
      roads: true,
      bridges: false,
      incidents: true,
      facilities: true,
      routes: true,
    };

    render(
      <MapControls
        layers={layers}
        onToggleLayer={onToggleLayer}
        onResetView={onResetView}
      />
    );

    expect(screen.getByText(/Flood Hazard/i)).toBeDefined();
    expect(screen.getByText(/Dynamic Routes/i)).toBeDefined();

    // Toggle flood layer
    fireEvent.click(screen.getByText(/Flood Hazard/i));
    expect(onToggleLayer).toHaveBeenCalledWith('flood');

    // Reset center
    fireEvent.click(screen.getByText(/Reset Center/i));
    expect(onResetView).toHaveBeenCalled();
  });

  it('renders MapLegend with accessible textual labels', () => {
    const visibleLayers = {
      flood: true,
      roads: true,
      bridges: true,
      incidents: true,
      facilities: true,
      routes: true,
    };

    render(<MapLegend visibleLayers={visibleLayers} />);
    expect(screen.getByRole('region').getAttribute('aria-label')).toBe('Map Symbology Legend');
    expect(screen.getByText(/Flood Hazard/i)).toBeDefined();
    expect(screen.getByText(/Road \(Open\)/i)).toBeDefined();
    expect(screen.getByText(/Road \(Blocked \/ Flooded\)/i)).toBeDefined();
    expect(screen.getByText(/Active Detour Route/i)).toBeDefined();
    expect(screen.getByText(/Hospital \/ Trauma/i)).toBeDefined();
  });

  it('renders DetailPanel empty instruction when nothing selected', () => {
    render(<DetailPanel selectedEntity={null} onClose={vi.fn()} />);
    expect(screen.getByText(/Click any feature on the operational map/i)).toBeDefined();
  });

  it('renders DetailPanel correctly for a selected Flood feature', () => {
    const floodEntity: GisSelectedEntity = {
      type: 'FLOOD',
      data: {
        id: 'F-001',
        floodZoneId: 'F-001',
        name: 'Sector 4 Flash Inundation',
        severity: 'CRITICAL',
        waterDepthM: 1.25,
        mode: 'SIMULATION',
        scenarioId: 'SIM-101',
        source: 'NEXUS Elevation Model',
        updatedAt: '2026-09-19T14:30:00Z',
      },
    };

    render(<DetailPanel selectedEntity={floodEntity} onClose={vi.fn()} />);
    expect(screen.getByText('Sector 4 Flash Inundation')).toBeDefined();
    expect(screen.getByText('1.25 meters')).toBeDefined();
    expect(screen.getByText('SIMULATION')).toBeDefined();
  });

  it('renders DetailPanel with dynamic rerouting delta for a selected Route', () => {
    const routeEntity: GisSelectedEntity = {
      type: 'ROUTE',
      data: {
        id: 'ROUTE-01',
        routeId: 'R-DETOUR',
        name: 'Northern Flyover Detour',
        status: 'REROUTED',
        isCurrent: true,
        distanceKm: 4.6,
        travelTimeMin: 9.1,
        deltaDistanceKm: 1.4,
        deltaTravelTimeMin: 2.7,
        startNode: 'H-001',
        endNode: 'S-001',
        changeExplanation: 'Computed detour around flooded causeway bridge.',
      },
    };

    render(<DetailPanel selectedEntity={routeEntity} onClose={vi.fn()} />);
    expect(screen.getByText('Northern Flyover Detour')).toBeDefined();
    expect(screen.getByText(/Distance: \+1.4 km/i)).toBeDefined();
    expect(screen.getByText(/Travel Time: \+2.7 min/i)).toBeDefined();
    expect(screen.getByText(/Computed detour around flooded causeway bridge/i)).toBeDefined();
  });
});

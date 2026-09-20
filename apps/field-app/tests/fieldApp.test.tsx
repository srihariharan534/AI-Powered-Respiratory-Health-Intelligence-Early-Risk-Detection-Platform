import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { I18nProvider } from '../src/context/I18nContext';
import { FieldAppProvider } from '../src/context/FieldAppContext';
import { HomeScreen } from '../src/screens/home/HomeScreen';
import { IncidentReportScreen } from '../src/screens/incident-report/IncidentReportScreen';
import { SmsFallbackScreen } from '../src/screens/sms-fallback/SmsFallbackScreen';
import { SyncStatusScreen } from '../src/screens/sync-status/SyncStatusScreen';
import { CachedMapScreen } from '../src/screens/cached-map/CachedMapScreen';
import { ResourceRequestScreen } from '../src/screens/resource-request/ResourceRequestScreen';
import { AssignmentScreen } from '../src/screens/assignment/AssignmentScreen';
import { LocationService } from '../src/services/location/locationService';
import { SyncQueueService } from '../src/services/sync/syncQueueService';

describe('Phase 22 Field PWA Foundation', () => {
  beforeEach(() => {
    SyncQueueService.clearQueue();
    localStorage.clear();
    vi.restoreAllMocks();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <I18nProvider>
        <FieldAppProvider>
          <BrowserRouter>{component}</BrowserRouter>
        </FieldAppProvider>
      </I18nProvider>
    );
  };

  it('renders HomeScreen with tactical assignment and touch action tiles', () => {
    renderWithProviders(<HomeScreen />);

    expect(screen.getByText(/Sector 4 Embankment Breach Inspection/i)).toBeDefined();
    expect(screen.getByText(/Saidapet Bridge South Corridor/i)).toBeDefined();
    expect(screen.getByText(/Report Incident/i)).toBeDefined();
    expect(screen.getByText(/Capture Evidence/i)).toBeDefined();
    expect(screen.getByText(/SMS Fallback/i)).toBeDefined();
  });

  it('captures GPS coordinates or provides manual fallback in IncidentReportScreen', async () => {
    const mockGeo = {
      getCurrentPosition: vi.fn().mockImplementation((success) => {
        success({
          coords: {
            latitude: 13.0180,
            longitude: 80.2230,
            accuracy: 12.0,
          },
        });
      }),
    };
    (globalThis as any).navigator.geolocation = mockGeo;

    renderWithProviders(<IncidentReportScreen />);

    expect(screen.getByText(/Report Incident/i)).toBeDefined();

    const gpsBtn = screen.getByText(/Capture GPS/i);
    fireEvent.click(gpsBtn);

    await waitFor(() => {
      expect(screen.getByText(/GPS VERIFIED/i)).toBeDefined();
    });

    // Toggle manual override
    const manualBtn = screen.getByText(/Manual/i);
    fireEvent.click(manualBtn);
    expect(screen.getByPlaceholderText(/Lon \(80.223\)/i)).toBeDefined();
  });

  it('enqueues incident report into SyncQueueService compliant with Phase 04 schema', async () => {
    renderWithProviders(<IncidentReportScreen />);

    const descInput = screen.getByPlaceholderText(/Report ground depth, stranded count/i);
    fireEvent.change(descInput, { target: { value: 'Severe overflow near bridge piers' } });

    const submitBtn = screen.getByRole('button', { name: /Submit to Sync Queue/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/SAVED ON DEVICE/i)).toBeDefined();
      expect(SyncQueueService.getPending().length).toBe(1);
    });

    const items = SyncQueueService.getPending();
    expect(items.length).toBe(1);
    expect(items[0].entity_type).toBe('INCIDENT');
    expect(items[0].payload.event_type).toBe('FLOOD_INUNDATION');
    expect(items[0].payload.severity).toBe('HIGH');
  });

  it('generates deterministic Phase 04 SMS fallback string <= 160 characters', () => {
    renderWithProviders(<SmsFallbackScreen />);

    // Look for SMS payload format FLOOD <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>
    const payloadRegex = /FLOOD\s+[\w-]+\s+[A-Z_]+\s+[A-Z_]+\s+[-+]?[0-9]*\.?[0-9]+\s+[-+]?[0-9]*\.?[0-9]+/;
    const payloadElement = screen.getByText(payloadRegex);
    expect(payloadElement).toBeDefined();

    const text = payloadElement.textContent || '';
    expect(text.length).toBeLessThanOrEqual(160);
    expect(text.startsWith('FLOOD ')).toBe(true);
  });

  it('displays active assignment with interactive status transitions in AssignmentScreen', () => {
    renderWithProviders(<AssignmentScreen />);

    expect(screen.getByText(/Sector 4 Embankment Breach Inspection/i)).toBeDefined();
    expect(screen.getByText(/PRIORITY 1/i)).toBeDefined();

    const onSceneBtn = screen.getByRole('button', { name: /ON SCENE/i });
    fireEvent.click(onSceneBtn);

    expect(screen.getByRole('button', { name: /ON SCENE/i }).textContent).toContain('CURRENT');
  });

  it('enqueues tactical resource request into SyncQueueService', async () => {
    renderWithProviders(<ResourceRequestScreen />);

    const reasonInput = screen.getByPlaceholderText(/State why assets are required/i);
    fireEvent.change(reasonInput, { target: { value: 'Inflatable boat required for stranded family' } });

    const submitBtn = screen.getByRole('button', { name: /Submit to Sync Queue/i });
    const form = submitBtn.closest('form');
    if (form) {
      fireEvent.submit(form);
    } else {
      fireEvent.click(submitBtn);
    }

    await waitFor(() => {
      expect(SyncQueueService.getPending().length).toBe(1);
    });

    const items = SyncQueueService.getPending();
    expect(items.length).toBe(1);
    expect(items[0].entity_type).toBe('RESOURCE_REQUEST');
    expect(items[0].payload.resource_type).toBe('RESCUE_BOAT');
  });

  it('renders CachedMapScreen with disclaimer and mock vector grid', () => {
    renderWithProviders(<CachedMapScreen />);

    expect(screen.getByText(/OFFLINE MAP: Cached map tiles will be available when configured/i)).toBeDefined();
    expect(screen.getByText(/WGS84 EPSG:4326/i)).toBeDefined();
    expect(screen.getByText(/Tactical Map Layers/i)).toBeDefined();
  });

  it('renders SyncStatusScreen with queue counts and actions', () => {
    SyncQueueService.enqueue('INCIDENT', { test: 'data' });

    renderWithProviders(<SyncStatusScreen />);

    expect(screen.getByText(/Total Pending Operations/i)).toBeDefined();
    expect(screen.getAllByText(/INCIDENT/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Retry Sync/i)).toBeDefined();
  });

  it('validates manual location fallback works when GPS fails or is unavailable', async () => {
    (globalThis as any).navigator.geolocation = {
      getCurrentPosition: vi.fn().mockImplementation((_success, error) => {
        error({ code: 1, message: 'User denied Geolocation' });
      }),
    };

    await expect(LocationService.getCurrentPosition()).rejects.toThrow();

    const manualLocation = LocationService.createManualPosition(80.2230, 13.0180);
    expect(manualLocation.latitude).toBe(13.0180);
    expect(manualLocation.longitude).toBe(80.2230);
    expect(manualLocation.source).toBe('MANUAL');
  });
});

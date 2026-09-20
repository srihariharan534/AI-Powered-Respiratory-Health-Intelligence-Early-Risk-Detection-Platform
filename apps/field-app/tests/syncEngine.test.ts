import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ClientSyncEngine } from '../src/services/sync/clientSyncEngine';
import { OutboxRepository } from '../src/database/repositories/OutboxRepository';
import { IncidentRepository } from '../src/database/repositories/IncidentRepository';
import { DurableIncident } from '../src/database/types';

describe('Phase 25 Client Synchronization Engine', () => {
  let outboxRepo: OutboxRepository;
  let incidentRepo: IncidentRepository;
  let syncEngine: ClientSyncEngine;

  beforeEach(async () => {
    outboxRepo = new OutboxRepository();
    incidentRepo = new IncidentRepository();
    await outboxRepo.clearAll();
    syncEngine = ClientSyncEngine.getInstance();
    vi.restoreAllMocks();
  });

  it('reconciles ACCEPTED operation by marking local incident SYNCED and removing outbox entry', async () => {
    // 1. Seed incident in IndexedDB
    const localIncident: DurableIncident = {
      schema_version: '1.0.0',
      incident_id: 'INC-CLIENT-001',
      event_type: 'FLOOD_INUNDATION',
      severity: 'HIGH',
      status: 'OPEN',
      priority: 1,
      location: { type: 'Point', coordinates: [80.223, 13.018] },
      reported_at: '2026-09-20T08:00:00Z',
      reported_by: 'FIELD_OFFICER_01',
      description: 'Breach at canal',
      source: 'field_officer',
      local_record_id: 'LOCAL-INC-001',
      created_locally_at: new Date().toISOString(),
      updated_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };
    await incidentRepo.save(localIncident);

    // 2. Enqueue outbox operation
    const op = await outboxRepo.enqueue('INCIDENT', 'INC-CLIENT-001', 'CREATE', localIncident);

    // 3. Mock fetch to /api/v1/sync
    (globalThis as any).fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        batch_id: 'BATCH-TEST-001',
        total_operations: 1,
        accepted_count: 1,
        results: [
          {
            operation_id: op.operation_id,
            entity_id: 'INC-CLIENT-001',
            entity_type: 'INCIDENT',
            status: 'ACCEPTED',
            server_state_version: 15,
          },
        ],
      }),
    });

    // 4. Trigger sync
    const summary = await syncEngine.sync();
    expect(summary.total).toBe(1);
    expect(summary.accepted).toBe(1);

    // 5. Verify local incident state updated to SYNCED
    const updatedIncident = await incidentRepo.getById('INC-CLIENT-001');
    expect(updatedIncident?.sync_status).toBe('SYNCED');

    // 6. Verify outbox operation removed
    const remainingOps = await outboxRepo.getPending();
    expect(remainingOps.length).toBe(0);
  });

  it('reconciles CONFLICT operation by retaining outbox entry and marking local record SYNC_ERROR', async () => {
    const localIncident: DurableIncident = {
      schema_version: '1.0.0',
      incident_id: 'INC-CONFLICT-001',
      event_type: 'FLOOD_INUNDATION',
      severity: 'LOW',
      status: 'OPEN',
      priority: 3,
      location: { type: 'Point', coordinates: [80.223, 13.018] },
      reported_at: '2026-09-20T08:00:00Z',
      reported_by: 'FIELD_OFFICER_01',
      description: 'Stale report',
      source: 'field_officer',
      local_record_id: 'LOCAL-INC-002',
      created_locally_at: new Date().toISOString(),
      updated_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };
    await incidentRepo.save(localIncident);

    const op = await outboxRepo.enqueue('INCIDENT', 'INC-CONFLICT-001', 'UPDATE', { severity: 'MEDIUM' });

    (globalThis as any).fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        batch_id: 'BATCH-TEST-002',
        total_operations: 1,
        conflict_count: 1,
        results: [
          {
            operation_id: op.operation_id,
            entity_id: 'INC-CONFLICT-001',
            entity_type: 'INCIDENT',
            status: 'CONFLICT',
            conflict_type: 'STATE_VERSION_CONFLICT',
            message: 'State version mismatch with central twin',
            server_state: { server_current_version: 25 },
          },
        ],
      }),
    });

    const summary = await syncEngine.sync();
    expect(summary.conflicts).toBe(1);

    // Verify outbox entry is retained with CONFLICT status
    const persistedOp = await outboxRepo.getById(op.operation_id);
    expect(persistedOp?.status).toBe('CONFLICT');
    expect(persistedOp?.last_error).toContain('State version mismatch');

    // Verify incident marked with SYNC_ERROR
    const updatedIncident = await incidentRepo.getById('INC-CONFLICT-001');
    expect(updatedIncident?.sync_status).toBe('SYNC_ERROR');
  });

  it('handles network failure gracefully by reverting in-flight operations to PENDING', async () => {
    const localIncident: DurableIncident = {
      schema_version: '1.0.0',
      incident_id: 'INC-FAIL-001',
      event_type: 'FLOOD_INUNDATION',
      severity: 'HIGH',
      status: 'OPEN',
      priority: 1,
      location: { type: 'Point', coordinates: [80.223, 13.018] },
      reported_at: '2026-09-20T08:00:00Z',
      reported_by: 'FIELD_OFFICER_01',
      description: 'Test failure',
      source: 'field_officer',
      local_record_id: 'LOCAL-INC-003',
      created_locally_at: new Date().toISOString(),
      updated_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };
    await incidentRepo.save(localIncident);
    const op = await outboxRepo.enqueue('INCIDENT', 'INC-FAIL-001', 'CREATE', localIncident);

    (globalThis as any).fetch = vi.fn().mockRejectedValue(new Error('Network disconnected / 503 Server Error'));

    const summary = await syncEngine.sync();
    expect(summary.errors.length).toBe(1);

    // Verify operation returned to PENDING for retry
    const persistedOp = await outboxRepo.getById(op.operation_id);
    expect(persistedOp?.status).toBe('PENDING');
    expect(persistedOp?.last_error).toContain('Network disconnected');
  });
});

import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach } from 'vitest';
import { NexusFieldDatabase } from '../src/database/indexeddb/connection';
import { IncidentRepository } from '../src/database/repositories/IncidentRepository';
import { EvidenceRepository } from '../src/database/repositories/EvidenceRepository';
import { AssignmentRepository } from '../src/database/repositories/AssignmentRepository';
import { ResourceRequestRepository } from '../src/database/repositories/ResourceRequestRepository';
import { OutboxRepository } from '../src/database/repositories/OutboxRepository';
import { AppStateRepository } from '../src/database/repositories/AppStateRepository';
import { TransactionCoordinator } from '../src/database/repositories/TransactionCoordinator';
import {
  DurableIncident,
  DurableEvidence,
  DurableAssignment,
  DurableResourceRequest,
} from '../src/database/types';

describe('Phase 23 Durable IndexedDB Offline Storage Foundation', () => {
  beforeEach(async () => {
    const db = NexusFieldDatabase.getInstance();
    await db.resetDatabaseForTesting();
  });

  it('initializes IndexedDB with schema version 1 and all 6 required object stores', async () => {
    const db = NexusFieldDatabase.getInstance();
    const idb = await db.getDatabase();

    expect(idb.name).toBe('nexus-field');
    expect(idb.version).toBe(1);

    const storeNames = Array.from(idb.objectStoreNames);
    expect(storeNames).toContain('incidents');
    expect(storeNames).toContain('evidence');
    expect(storeNames).toContain('assignments');
    expect(storeNames).toContain('resource_requests');
    expect(storeNames).toContain('outbox');
    expect(storeNames).toContain('app_state');
  });

  it('persists, retrieves, and validates incident records adhering to Phase 04 schema', async () => {
    const repo = new IncidentRepository();

    const incident: DurableIncident = {
      schema_version: '1.0.0',
      incident_id: 'INC-IDB-001',
      event_type: 'FLOOD_INUNDATION',
      severity: 'CRITICAL',
      status: 'OPEN',
      priority: 1,
      location: {
        type: 'Point',
        coordinates: [80.223, 13.018],
      },
      reported_at: new Date().toISOString(),
      reported_by: 'FIELD_OFFICER_01',
      description: 'Severe 1.2m water level breach along river road',
      source: 'field_officer',
      local_record_id: 'LOCAL-001',
      created_locally_at: new Date().toISOString(),
      updated_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };

    await repo.save(incident);

    const retrieved = await repo.getById('INC-IDB-001');
    expect(retrieved).not.toBeNull();
    expect(retrieved?.description).toBe('Severe 1.2m water level breach along river road');
    expect(retrieved?.severity).toBe('CRITICAL');
    expect(retrieved?.sync_status).toBe('PENDING_SYNC');
    expect(retrieved?.location.coordinates).toEqual([80.223, 13.018]);
  });

  it('rejects invalid incident coordinates outside WGS84 range', async () => {
    const repo = new IncidentRepository();

    const invalidIncident: DurableIncident = {
      schema_version: '1.0.0',
      incident_id: 'INC-INVALID-001',
      event_type: 'FLOOD_INUNDATION',
      severity: 'HIGH',
      status: 'OPEN',
      priority: 1,
      location: {
        type: 'Point',
        coordinates: [200.0, 13.018], // Longitude > 180!
      },
      reported_at: new Date().toISOString(),
      reported_by: 'FIELD_OFFICER_01',
      description: 'Out of bounds test',
      source: 'field_officer',
      local_record_id: 'LOCAL-INV',
      created_locally_at: new Date().toISOString(),
      updated_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };

    await expect(repo.save(invalidIncident)).rejects.toThrow(/longitude must be between -180 and 180/);
  });

  it('persists evidence metadata associated with an incident', async () => {
    const evidenceRepo = new EvidenceRepository();

    const evidence: DurableEvidence = {
      evidence_id: 'EVD-001',
      incident_id: 'INC-IDB-001',
      type: 'photo',
      file_name: 'breach_photo.jpg',
      file_size: 1024 * 250,
      mime_type: 'image/jpeg',
      captured_at: new Date().toISOString(),
      description: 'Embankment gauge measurement',
      sync_status: 'PENDING_SYNC',
      local_record_id: 'LOCAL-EVD-001',
    };

    await evidenceRepo.save(evidence);

    const items = await evidenceRepo.getByIncidentId('INC-IDB-001');
    expect(items.length).toBe(1);
    expect(items[0].file_name).toBe('breach_photo.jpg');
    expect(items[0].type).toBe('photo');
  });

  it('persists field assignment with cached state distinction', async () => {
    const assignmentRepo = new AssignmentRepository();

    const assignment: DurableAssignment = {
      assignment_id: 'ASSIGN-TACTICAL-01',
      incident_id: 'INC-001',
      task_name: 'Evacuate Sector 4',
      instructions: 'Assist families stranded at junction',
      priority: 1,
      status: 'ON_SCENE',
      location: {
        name: 'Saidapet Corridor',
        latitude: 13.018,
        longitude: 80.223,
      },
      assigned_at: new Date().toISOString(),
      data_mode: 'DEMO',
      cached_at: new Date().toISOString(),
      is_cached: true,
      last_local_status_update: new Date().toISOString(),
    };

    await assignmentRepo.save(assignment);

    const retrieved = await assignmentRepo.getById('ASSIGN-TACTICAL-01');
    expect(retrieved).not.toBeNull();
    expect(retrieved?.status).toBe('ON_SCENE');
    expect(retrieved?.is_cached).toBe(true);
  });

  it('persists resource requests with local status metadata', async () => {
    const reqRepo = new ResourceRequestRepository();

    const request: DurableResourceRequest = {
      request_id: 'REQ-BOAT-001',
      resource_type: 'RESCUE_BOAT',
      quantity: 3,
      urgency: 'IMMEDIATE',
      location: [80.223, 13.018],
      reason: '12 civilians trapped on second floor',
      requested_by: 'FIELD_OFFICER_01',
      requested_at: new Date().toISOString(),
      status: 'PENDING_SYNC',
      local_record_id: 'LOCAL-REQ-001',
      created_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };

    await reqRepo.save(request);

    const retrieved = await reqRepo.getById('REQ-BOAT-001');
    expect(retrieved).not.toBeNull();
    expect(retrieved?.quantity).toBe(3);
    expect(retrieved?.urgency).toBe('IMMEDIATE');
  });

  it('durable outbox generates collision-resistant stable operation IDs and tracks pending state', async () => {
    const outbox = new OutboxRepository();

    const op = await outbox.enqueue('INCIDENT', 'INC-001', 'CREATE', { test: true });

    expect(op.operation_id.startsWith('OP-')).toBe(true);
    expect(op.status).toBe('PENDING');

    const pending = await outbox.getPending();
    expect(pending.length).toBe(1);
    expect(pending[0].operation_id).toBe(op.operation_id);
    expect(pending[0].entity_type).toBe('INCIDENT');
  });

  it('executes atomic offline creation (incident + evidence + outbox) transactionally', async () => {
    const coordinator = new TransactionCoordinator();
    const incidentRepo = new IncidentRepository();
    const evidenceRepo = new EvidenceRepository();
    const outboxRepo = new OutboxRepository();

    const incident: DurableIncident = {
      schema_version: '1.0.0',
      incident_id: 'INC-ATOMIC-001',
      event_type: 'EMBANKMENT_BREACH',
      severity: 'CRITICAL',
      status: 'OPEN',
      priority: 1,
      location: {
        type: 'Point',
        coordinates: [80.223, 13.018],
      },
      reported_at: new Date().toISOString(),
      reported_by: 'FIELD_OFFICER_01',
      description: 'South bund breach spreading 50m wide',
      source: 'field_officer',
      local_record_id: 'LOCAL-ATOMIC-001',
      created_locally_at: new Date().toISOString(),
      updated_locally_at: new Date().toISOString(),
      sync_status: 'PENDING_SYNC',
      sync_attempts: 0,
    };

    const evidence: DurableEvidence = {
      evidence_id: 'EVD-ATOMIC-001',
      incident_id: 'INC-ATOMIC-001',
      type: 'photo',
      file_name: 'bund_breach.jpg',
      file_size: 1024 * 500,
      mime_type: 'image/jpeg',
      captured_at: new Date().toISOString(),
      description: 'Breach opening photo',
      sync_status: 'PENDING_SYNC',
      local_record_id: 'LOCAL-EVD-ATOMIC',
    };

    const result = await coordinator.saveIncidentWithOutbox({
      incident,
      evidenceItems: [evidence],
    });

    expect(result.incident.incident_id).toBe('INC-ATOMIC-001');
    expect(result.outboxOperation.operation_id.startsWith('OP-')).toBe(true);

    // Verify all 3 stores contain persisted records
    const savedIncident = await incidentRepo.getById('INC-ATOMIC-001');
    expect(savedIncident).not.toBeNull();

    const savedEvidence = await evidenceRepo.getByIncidentId('INC-ATOMIC-001');
    expect(savedEvidence.length).toBe(1);

    const pendingOps = await outboxRepo.getPending();
    expect(pendingOps.length).toBe(1);
    expect(pendingOps[0].entity_id).toBe('INC-ATOMIC-001');
  });

  it('recovers all persisted offline records across simulated application reload / restart', async () => {
    // 1. First session: Create offline incident & outbox entry
    const coordinator = new TransactionCoordinator();
    await coordinator.saveIncidentWithOutbox({
      incident: {
        schema_version: '1.0.0',
        incident_id: 'INC-SURVIVE-001',
        event_type: 'FLOOD_INUNDATION',
        severity: 'HIGH',
        status: 'OPEN',
        priority: 2,
        location: {
          type: 'Point',
          coordinates: [80.25, 13.05],
        },
        reported_at: new Date().toISOString(),
        reported_by: 'FIELD_OFFICER_02',
        description: 'Water standing at road crossing',
        source: 'field_officer',
        local_record_id: 'LOCAL-S-01',
        created_locally_at: new Date().toISOString(),
        updated_locally_at: new Date().toISOString(),
        sync_status: 'PENDING_SYNC',
        sync_attempts: 0,
      },
    });

    // 2. Simulate complete application close by closing the DB connection
    await NexusFieldDatabase.getInstance().close();

    // 3. Simulate new application session opening fresh repository
    const freshDb = NexusFieldDatabase.getInstance();
    const freshIncidentRepo = new IncidentRepository(freshDb);
    const freshOutboxRepo = new OutboxRepository(freshDb);

    const recoveredIncident = await freshIncidentRepo.getById('INC-SURVIVE-001');
    expect(recoveredIncident).not.toBeNull();
    expect(recoveredIncident?.description).toBe('Water standing at road crossing');

    const recoveredPending = await freshOutboxRepo.getPending();
    expect(recoveredPending.length).toBe(1);
    expect(recoveredPending[0].entity_id).toBe('INC-SURVIVE-001');
  });

  it('stores and retrieves app state records', async () => {
    const appState = new AppStateRepository();
    await appState.set('last_user', 'OFFICER_CHENNAI_01');
    await appState.set('database_version', 1);

    const user = await appState.get<string>('last_user');
    const version = await appState.get<number>('database_version');

    expect(user).toBe('OFFICER_CHENNAI_01');
    expect(version).toBe(1);
  });
});

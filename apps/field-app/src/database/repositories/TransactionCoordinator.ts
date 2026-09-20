/**
 * Transaction Coordinator (Phase 23)
 * Implements atomic transactional offline creation workflows:
 * Incident + Evidence References + Outbox Operation in a single IDB transaction.
 */

import { NexusFieldDatabase } from '../indexeddb/connection';
import {
  STORE_INCIDENTS,
  STORE_EVIDENCE,
  STORE_OUTBOX,
  DurableIncident,
  DurableEvidence,
  OutboxOperation,
} from '../types';
import { DataValidator } from '../../services/validation/validator';

export interface AtomicOfflineIncidentParams {
  incident: DurableIncident;
  evidenceItems?: DurableEvidence[];
}

export interface AtomicOfflineResult {
  incident: DurableIncident;
  outboxOperation: OutboxOperation<DurableIncident>;
}

export class TransactionCoordinator {
  private db: NexusFieldDatabase;

  constructor(db: NexusFieldDatabase = NexusFieldDatabase.getInstance()) {
    this.db = db;
  }

  public async saveIncidentWithOutbox(
    params: AtomicOfflineIncidentParams
  ): Promise<AtomicOfflineResult> {
    const { incident, evidenceItems = [] } = params;

    // 1. Strict validation before beginning transaction
    DataValidator.validateIncident(incident);

    // 2. Prepare outbox operation
    const timestamp = Date.now();
    const randomPart = Math.random().toString(36).substring(2, 9);
    const op: OutboxOperation<DurableIncident> = {
      operation_id: `OP-${timestamp}-${randomPart}`,
      entity_type: 'INCIDENT',
      entity_id: incident.incident_id,
      operation_type: 'CREATE',
      payload: incident,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: 'PENDING',
      attempt_count: 0,
    };

    const database = await this.db.getDatabase();

    return new Promise<AtomicOfflineResult>((resolve, reject) => {
      // Open multi-store atomic transaction
      const tx = database.transaction(
        [STORE_INCIDENTS, STORE_EVIDENCE, STORE_OUTBOX],
        'readwrite'
      );

      const incidentStore = tx.objectStore(STORE_INCIDENTS);
      const evidenceStore = tx.objectStore(STORE_EVIDENCE);
      const outboxStore = tx.objectStore(STORE_OUTBOX);

      // Put incident
      incidentStore.put(incident);

      // Put evidence items
      for (const ev of evidenceItems) {
        evidenceStore.put(ev);
      }

      // Put outbox operation
      outboxStore.put(op);

      tx.oncomplete = () => {
        resolve({
          incident,
          outboxOperation: op,
        });
      };

      tx.onerror = () => {
        reject(tx.error || new Error('Transaction failed: unable to save incident and outbox atomically.'));
      };

      tx.onabort = () => {
        reject(tx.error || new Error('Transaction aborted: rolled back changes.'));
      };
    });
  }
}

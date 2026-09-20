/**
 * Evidence Repository (Phase 23)
 * Provides durable operations for evidence records associated with incidents.
 */

import { NexusFieldDatabase } from '../indexeddb/connection';
import { STORE_EVIDENCE, DurableEvidence } from '../types';

export class EvidenceRepository {
  private db: NexusFieldDatabase;

  constructor(db: NexusFieldDatabase = NexusFieldDatabase.getInstance()) {
    this.db = db;
  }

  public async save(evidence: DurableEvidence): Promise<DurableEvidence> {
    if (!evidence.evidence_id) {
      throw new Error('Validation Error: evidence_id is required.');
    }

    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_EVIDENCE], 'readwrite');
      const store = tx.objectStore(STORE_EVIDENCE);
      const request = store.put(evidence);

      request.onsuccess = () => resolve(evidence);
      request.onerror = () => reject(request.error || new Error('Failed to save evidence.'));
    });
  }

  public async getByIncidentId(incidentId: string): Promise<DurableEvidence[]> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_EVIDENCE], 'readonly');
      const store = tx.objectStore(STORE_EVIDENCE);
      const index = store.index('incident_id');
      const request = index.getAll(incidentId);

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error || new Error('Failed to get evidence by incident.'));
    });
  }

  public async list(): Promise<DurableEvidence[]> {
    const database = await this.db.getDatabase();
    return new Promise((resolve, reject) => {
      const tx = database.transaction([STORE_EVIDENCE], 'readonly');
      const store = tx.objectStore(STORE_EVIDENCE);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error || new Error('Failed to list evidence.'));
    });
  }
}

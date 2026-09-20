/**
 * Endpoint services for NEXUS Command Center
 */

import { apiClient } from './api-client';
import { StateVersionInfo, SimulationSummary, FacilitySummary } from '../types';

export const digitalTwinService = {
  async getStateVersion(): Promise<StateVersionInfo> {
    return apiClient.get<StateVersionInfo>('/api/v1/digital-twin/version');
  },
  async getOperationalSummary(): Promise<any> {
    return apiClient.get<any>('/api/v1/digital-twin/summary');
  },
};

export const incidentsService = {
  async getIncidents(params?: Record<string, string>): Promise<any> {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiClient.get<any>(`/api/v1/incidents${query}`);
  },
  async getIncidentById(id: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/incidents/${id}`);
  },
  async createIncident(payload: any): Promise<any> {
    return apiClient.post<any>('/api/v1/incidents', payload);
  },
  async transitionStatus(id: string, payload: { new_status: string; expected_state_version?: number; notes?: string; assigned_team_id?: string }): Promise<any> {
    return apiClient.post<any>(`/api/v1/incidents/${id}/transition`, payload);
  },
  async getIncidentHistory(id: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/incidents/${id}/history`);
  },
};

export const simulationService = {
  async listScenarios(): Promise<SimulationSummary[]> {
    return apiClient.get<SimulationSummary[]>('/api/v1/simulation/scenarios');
  },
  async runWhatIfScenario(payload: any): Promise<any> {
    return apiClient.post<any>('/api/v1/simulation/what-if', payload);
  },
};

export const facilitiesService = {
  // Legacy summary endpoints
  async getHospitalsSummary(): Promise<FacilitySummary[]> {
    return apiClient.get<FacilitySummary[]>('/api/v1/facilities/hospitals');
  },
  async getSheltersSummary(): Promise<FacilitySummary[]> {
    return apiClient.get<FacilitySummary[]>('/api/v1/facilities/shelters');
  },

  // Authoritative Phase 16 Hospital Endpoints
  async getHospitals(params?: Record<string, string>): Promise<{ total: number; limit: number; offset: number; items: any[] }> {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiClient.get<any>(`/api/v1/hospitals${query}`);
  },
  async getHospitalById(id: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/hospitals/${id}`);
  },
  async createHospital(payload: any): Promise<any> {
    return apiClient.post<any>('/api/v1/hospitals', payload);
  },
  async updateHospitalCapacity(id: string, payload: { available_capacity: number; capacity?: number; icu_available?: number; expected_state_version?: number; reason?: string }): Promise<any> {
    return apiClient.patch<any>(`/api/v1/hospitals/${id}/capacity`, payload);
  },
  async updateHospitalStatus(id: string, payload: { status: string; expected_state_version?: number; reason?: string }): Promise<any> {
    return apiClient.patch<any>(`/api/v1/hospitals/${id}/status`, payload);
  },
  async getHospitalHistory(id: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/hospitals/${id}/history`);
  },

  // Authoritative Phase 16 Shelter Endpoints
  async getShelters(params?: Record<string, string>): Promise<{ total: number; limit: number; offset: number; items: any[] }> {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiClient.get<any>(`/api/v1/shelters${query}`);
  },
  async getShelterById(id: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/shelters/${id}`);
  },
  async createShelter(payload: any): Promise<any> {
    return apiClient.post<any>('/api/v1/shelters', payload);
  },
  async updateShelterCapacity(id: string, payload: { available_capacity: number; capacity?: number; expected_state_version?: number; reason?: string }): Promise<any> {
    return apiClient.patch<any>(`/api/v1/shelters/${id}/capacity`, payload);
  },
  async updateShelterStatus(id: string, payload: { status: string; expected_state_version?: number; reason?: string }): Promise<any> {
    return apiClient.patch<any>(`/api/v1/shelters/${id}/status`, payload);
  },

  async getShelterHistory(id: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/shelters/${id}/history`);
  },
};

export const recommendationService = {
  async getRecommendations(params?: Record<string, string>): Promise<any[]> {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiClient.get<any[]>(`/api/v1/recommendations${query}`);
  },
  async getRecommendationById(id: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/recommendations/${id}`);
  },
  async generateRecommendations(payload: any): Promise<any[]> {
    return apiClient.post<any[]>('/api/v1/recommendations/generate', payload);
  },
  async approveRecommendation(id: string, payload: { actor?: string; reason: string; idempotency_key?: string }, headers?: Record<string, string>): Promise<any> {
    return apiClient.post<any>(`/api/v1/recommendations/${id}/approve`, payload, { headers });
  },
  async rejectRecommendation(id: string, payload: { actor?: string; reason: string; idempotency_key?: string }, headers?: Record<string, string>): Promise<any> {
    return apiClient.post<any>(`/api/v1/recommendations/${id}/reject`, payload, { headers });
  },
  async getRecommendationAudit(id: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/recommendations/${id}/audit`);
  },
  async getAuditLedger(params?: Record<string, string>): Promise<any[]> {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiClient.get<any[]>(`/api/v1/recommendations/audit/ledger${query}`);
  },
};


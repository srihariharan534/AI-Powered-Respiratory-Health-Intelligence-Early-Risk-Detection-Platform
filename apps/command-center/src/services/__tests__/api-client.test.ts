import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { NexusApiClient } from '../api-client';

describe('NexusApiClient', () => {
  let client: NexusApiClient;

  beforeEach(() => {
    client = new NexusApiClient('http://test-api:8000', 500);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should successfully perform a GET request', async () => {
    const mockData = { version: 42, authority: 'NEXUS Digital Twin' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockData,
    } as any);

    const result = await client.get('/api/v1/test');
    expect(result).toEqual(mockData);
  });

  it('should successfully perform a POST request with payload', async () => {
    const payload = { rainfall: 150 };
    const mockResponse = { scenarioId: 'SIM-001' };

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => mockResponse,
    } as any);

    const result = await client.post('/api/v1/simulation', payload);
    expect(result).toEqual(mockResponse);
    expect(fetchSpy).toHaveBeenCalledWith(
      'http://test-api:8000/api/v1/simulation',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      })
    );
  });

  it('should transform HTTP error responses into structured ApiError', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ message: 'Scenario not found' }),
    } as any);

    await expect(client.get('/api/v1/missing')).rejects.toMatchObject({
      status: 404,
      message: 'Scenario not found',
      code: 'HTTP_404',
    });
  });

  it('should handle network disconnection as structured NETWORK_ERROR', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Failed to fetch'));

    await expect(client.get('/api/v1/incidents')).rejects.toMatchObject({
      status: 0,
      code: 'NETWORK_ERROR',
      message: expect.stringContaining('Unable to connect to the NEXUS API'),
    });
  });

  it('should handle invalid JSON payload from server', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => {
        throw new Error('Bad JSON');
      },
    } as any);

    await expect(client.get('/api/v1/corrupt')).rejects.toMatchObject({
      status: 200,
      code: 'PARSE_ERROR',
    });
  });
});

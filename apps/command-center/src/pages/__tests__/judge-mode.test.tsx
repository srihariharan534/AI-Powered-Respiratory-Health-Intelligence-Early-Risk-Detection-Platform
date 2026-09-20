import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { JudgeModePage } from '../JudgeModePage';
import { JudgeModeManager } from '../../services/judgeModeManager';

describe('JudgeModePage & State Machine Flow', () => {
  it('initializes JudgeModeManager at Step 1 (Baseline) and steps forward sequentially', () => {
    const manager = new JudgeModeManager();
    expect(manager.getCurrentIndex()).toBe(0);
    expect(manager.getCurrentStep().state_id).toBe('BASELINE');
    expect(manager.getCurrentStep().digital_twin_version).toBe(42);

    // Advance to Step 2 (Flood)
    const step2 = manager.nextStep();
    expect(step2.state_id).toBe('FLOOD_SURGE');
    expect(step2.flood_extent_active).toBe(true);

    // Advance to Step 3 (Bridge Failure)
    const step3 = manager.nextStep();
    expect(step3.state_id).toBe('BRIDGE_FAILURE');
    expect(step3.bridge_status).toBe('FAILED');
    expect(step3.road_status).toBe('BLOCKED');

    // Advance to Step 4 (Dynamic Reroute)
    const step4 = manager.nextStep();
    expect(step4.state_id).toBe('DYNAMIC_REROUTE');
    expect(step4.route_status).toBe('REROUTED');

    // Reset back to baseline
    const resetStep = manager.reset();
    expect(resetStep.state_id).toBe('BASELINE');
    expect(manager.getCurrentIndex()).toBe(0);
  });

  it('renders JudgeModePage with interactive stepper buttons and keyboard instructions', () => {
    render(<JudgeModePage />);

    expect(screen.getByText(/JUDGE MODE/i)).toBeDefined();
    expect(screen.getByText(/Controlled Demo Environment/i)).toBeDefined();
    expect(screen.getByText(/Baseline Operational State/i)).toBeDefined();
    expect(screen.getByText(/Twin State:/i)).toBeDefined();

    // Click Next Event
    const nextButton = screen.getByText(/Next Event/i);
    fireEvent.click(nextButton);

    expect(screen.getByText(/Flood Inundation Scenario/i)).toBeDefined();

    // Click Reset
    const resetButton = screen.getByText(/Reset Demo/i);
    fireEvent.click(resetButton);

    expect(screen.getByText(/Baseline Operational State/i)).toBeDefined();
  });
});

/**
 * Judge Mode State Machine & Engine
 * Provides deterministic progression, rewind, reset, and technical evidence.
 */

import scenarioManifest from '../../../../demo/judge-mode/judge-scenario.json';

export interface JudgeStep {
  step_index: number;
  state_id: string;
  title: string;
  narration: string;
  digital_twin_version: number;
  data_mode: 'REAL' | 'SIMULATION' | 'DEMO';
  event_source: string;
  flood_extent_active: boolean;
  water_depth_m?: number;
  bridge_status: string;
  road_status: string;
  route_status: string;
  route_detour_km?: number;
  route_delay_min?: number;
  field_connectivity: 'ONLINE' | 'OFFLINE';
  offline_queue_count: number;
  queued_incident_id?: string;
  sync_status: string;
}

export interface JudgeScenario {
  scenario_id: string;
  name: string;
  description: string;
  mode: string;
  operational_area: {
    center: [number, number];
    defaultZoom: number;
    name: string;
  };
  steps: JudgeStep[];
}

export const JUDGE_SCENARIO: JudgeScenario = scenarioManifest as unknown as JudgeScenario;

export class JudgeModeManager {
  private currentStepIndex: number = 0; // 0-indexed into steps
  private totalSteps: number = JUDGE_SCENARIO.steps.length;

  public getCurrentStep(): JudgeStep {
    return JUDGE_SCENARIO.steps[this.currentStepIndex];
  }

  public getCurrentIndex(): number {
    return this.currentStepIndex;
  }

  public getTotalSteps(): number {
    return this.totalSteps;
  }

  public nextStep(): JudgeStep {
    if (this.currentStepIndex < this.totalSteps - 1) {
      this.currentStepIndex += 1;
    }
    return this.getCurrentStep();
  }

  public previousStep(): JudgeStep {
    if (this.currentStepIndex > 0) {
      this.currentStepIndex -= 1;
    }
    return this.getCurrentStep();
  }

  public reset(): JudgeStep {
    this.currentStepIndex = 0;
    return this.getCurrentStep();
  }

  public isFirstStep(): boolean {
    return this.currentStepIndex === 0;
  }

  public isLastStep(): boolean {
    return this.currentStepIndex === this.totalSteps - 1;
  }
}

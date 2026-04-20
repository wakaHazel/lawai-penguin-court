import type { CaseProfile } from "../../types/case";
import type {
  OpponentBehaviorSnapshot,
  ReplayReportSnapshot,
  WinRateAnalysisSnapshot,
} from "../../types/analysis";
import type {
  SimulationSnapshot,
  SimulationCheckpoint,
  SimulationHistoryItem,
  SimulationTurnRequest,
} from "../../types/turn";
import type { ApiClientConfig } from "./client";
import { requestEnvelope } from "./client";

const STAGE_LABELS: Record<SimulationSnapshot["current_stage"], string> = {
  prepare: "庭前准备",
  investigation: "法庭调查",
  evidence: "举证质证",
  debate: "法庭辩论",
  final_statement: "最后陈述",
  mediation_or_judgment: "调解/判决",
  report_ready: "复盘报告",
};

const LONG_RUNNING_TIMEOUT_MS = 90000;

interface RawSimulationCheckpoint {
  checkpoint_id: string;
  trial_run_id: string;
  source_node_id: string;
  turn_index: number;
  payload_json: string;
}

export async function createCase(
  payload: CaseProfile,
  config?: ApiClientConfig,
): Promise<CaseProfile> {
  const response = await requestEnvelope<CaseProfile>(
    "/api/cases",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    config,
  );

  return response.data as CaseProfile;
}

export async function getCaseList(
  config?: ApiClientConfig,
): Promise<CaseProfile[]> {
  const response = await requestEnvelope<CaseProfile[]>(
    "/api/cases",
    {
      method: "GET",
    },
    config,
  );

  return (response.data ?? []) as CaseProfile[];
}

export async function getCaseDetail(
  caseId: string,
  config?: ApiClientConfig,
): Promise<CaseProfile> {
  const response = await requestEnvelope<CaseProfile>(
    `/api/cases/${caseId}`,
    {
      method: "GET",
    },
    config,
  );

  return response.data as CaseProfile;
}

export async function getLatestSimulation(
  caseId: string,
  config?: ApiClientConfig,
): Promise<SimulationSnapshot | null> {
  const response = await requestEnvelope<SimulationSnapshot | null>(
    `/api/cases/${caseId}/simulate/latest`,
    {
      method: "GET",
    },
    config,
  );

  return (response.data ?? null) as SimulationSnapshot | null;
}

export async function startSimulation(
  caseId: string,
  config?: ApiClientConfig,
): Promise<SimulationSnapshot> {
  const response = await requestEnvelope<SimulationSnapshot>(
    `/api/cases/${caseId}/simulate/start`,
    {
      method: "POST",
    },
    {
      ...config,
      timeoutMs: config?.timeoutMs ?? LONG_RUNNING_TIMEOUT_MS,
    },
  );

  return response.data as SimulationSnapshot;
}

export async function advanceSimulationTurn(
  caseId: string,
  payload: SimulationTurnRequest,
  config?: ApiClientConfig,
): Promise<SimulationSnapshot> {
  const response = await requestEnvelope<SimulationSnapshot>(
    `/api/cases/${caseId}/simulate/turn`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    {
      ...config,
      timeoutMs: config?.timeoutMs ?? LONG_RUNNING_TIMEOUT_MS,
    },
  );

  return response.data as SimulationSnapshot;
}

export async function getOpponentBehaviorSnapshot(
  caseId: string,
  simulationId: string,
  config?: ApiClientConfig,
): Promise<OpponentBehaviorSnapshot> {
  const response = await requestEnvelope<OpponentBehaviorSnapshot>(
    `/api/cases/${caseId}/opponent-behavior/snapshot`,
    {
      method: "POST",
      body: JSON.stringify({
        simulation_id: simulationId,
      }),
    },
    config,
  );

  return response.data as OpponentBehaviorSnapshot;
}

export async function getLatestOpponentBehaviorSnapshot(
  caseId: string,
  config?: ApiClientConfig,
): Promise<OpponentBehaviorSnapshot | null> {
  const response = await requestEnvelope<OpponentBehaviorSnapshot | null>(
    `/api/cases/${caseId}/opponent-behavior/latest`,
    {
      method: "GET",
    },
    config,
  );

  return (response.data ?? null) as OpponentBehaviorSnapshot | null;
}

export async function analyzeWinRate(
  caseId: string,
  simulationId: string,
  config?: ApiClientConfig,
): Promise<WinRateAnalysisSnapshot> {
  const response = await requestEnvelope<WinRateAnalysisSnapshot>(
    `/api/cases/${caseId}/win-rate/analyze`,
    {
      method: "POST",
      body: JSON.stringify({
        simulation_id: simulationId,
      }),
    },
    config,
  );

  return response.data as WinRateAnalysisSnapshot;
}

export async function getLatestWinRateAnalysis(
  caseId: string,
  config?: ApiClientConfig,
): Promise<WinRateAnalysisSnapshot | null> {
  const response = await requestEnvelope<WinRateAnalysisSnapshot | null>(
    `/api/cases/${caseId}/win-rate/latest`,
    {
      method: "GET",
    },
    config,
  );

  return (response.data ?? null) as WinRateAnalysisSnapshot | null;
}

export async function generateReplayReport(
  caseId: string,
  simulationId: string,
  config?: ApiClientConfig,
): Promise<ReplayReportSnapshot> {
  const response = await requestEnvelope<ReplayReportSnapshot>(
    `/api/cases/${caseId}/replay-report/generate`,
    {
      method: "POST",
      body: JSON.stringify({
        simulation_id: simulationId,
      }),
    },
    config,
  );

  return response.data as ReplayReportSnapshot;
}

export async function getLatestReplayReport(
  caseId: string,
  config?: ApiClientConfig,
): Promise<ReplayReportSnapshot | null> {
  const response = await requestEnvelope<ReplayReportSnapshot | null>(
    `/api/cases/${caseId}/replay-report/latest`,
    {
      method: "GET",
    },
    config,
  );

  return (response.data ?? null) as ReplayReportSnapshot | null;
}

export async function getSimulationHistory(
  caseId: string,
  simulationId?: string,
  config?: ApiClientConfig,
): Promise<SimulationHistoryItem[]> {
  const search = simulationId
    ? `?simulation_id=${encodeURIComponent(simulationId)}`
    : "";
  const response = await requestEnvelope<SimulationSnapshot[]>(
    `/api/cases/${caseId}/simulate/history${search}`,
    {
      method: "GET",
    },
    config,
  );

  return ((response.data ?? []) as SimulationSnapshot[]).map((item) => ({
    simulation_id: item.simulation_id,
    node_id: item.node_id,
    stage: item.current_stage,
    turn_index: item.turn_index,
    scene_title: item.scene_title,
    branch_focus: item.branch_focus,
  }));
}

export async function getSimulationCheckpoints(
  caseId: string,
  simulationId?: string,
  config?: ApiClientConfig,
): Promise<SimulationCheckpoint[]> {
  const search = simulationId
    ? `?simulation_id=${encodeURIComponent(simulationId)}`
    : "";
  const response = await requestEnvelope<RawSimulationCheckpoint[]>(
    `/api/cases/${caseId}/simulate/checkpoints${search}`,
    {
      method: "GET",
    },
    config,
  );

  return ((response.data ?? []) as RawSimulationCheckpoint[]).map((item) => ({
    checkpoint_id: item.checkpoint_id,
    trial_run_id: item.trial_run_id,
    source_node_id: item.source_node_id,
    turn_index: item.turn_index,
    stage_label: resolveCheckpointStageLabel(item.payload_json),
  }));
}

export async function resumeSimulationFromCheckpoint(
  caseId: string,
  checkpointId: string,
  config?: ApiClientConfig,
): Promise<SimulationSnapshot> {
  const response = await requestEnvelope<SimulationSnapshot>(
    `/api/cases/${caseId}/simulate/checkpoints/${checkpointId}/resume`,
    {
      method: "POST",
    },
    config,
  );

  return response.data as SimulationSnapshot;
}

function resolveCheckpointStageLabel(payloadJson: string): string {
  try {
    const parsed = JSON.parse(payloadJson) as { current_stage?: SimulationSnapshot["current_stage"] };
    if (parsed.current_stage) {
      return STAGE_LABELS[parsed.current_stage];
    }
  } catch {
    // Keep the fallback below.
  }

  return "关键节点";
}

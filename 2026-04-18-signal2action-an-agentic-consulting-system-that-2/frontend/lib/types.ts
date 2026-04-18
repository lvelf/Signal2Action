export type SponsorToolUsage = {
  tool: string;
  mode: "mock" | "live" | "disabled";
  detail: string;
};

export type StageMetadata = {
  stage: string;
  status: "ready" | "running" | "completed" | "error";
  tool_usages: SponsorToolUsage[];
};

export type IntakeResponse = {
  normalized_input: string;
  extracted_signals: string[];
  assumptions: string[];
  missing_information: string[];
  problem_statement: string;
  clarifying_questions: string[];
  metadata: StageMetadata;
};

export type ClarifyResponse = {
  problem_statement: string;
  clarified_scope: string;
  assumptions: string[];
  missing_information: string[];
  clarifying_questions: string[];
  metadata: StageMetadata;
};

export type ReviewResponse = {
  problem_statement: string;
  approved_scope: string;
  review_notes: string[];
  assumptions: string[];
  missing_information: string[];
  metadata: StageMetadata;
};

export type FunctionalModule = {
  name: string;
  objective: string;
  inputs: string[];
  outputs: string[];
  recommended_approach: string;
  priority: "high" | "medium" | "low";
  complexity: "high" | "medium" | "low";
  depends_on: string[];
  include_in_deliverable: boolean;
  owner_hint: string;
};

export type SearchContextItem = {
  title: string;
  summary: string;
  source: string;
};

export type AssessmentResponse = {
  problem_statement: string;
  decomposition_summary: string;
  current_state: string[];
  constraints: string[];
  dependencies: string[];
  gaps: string[];
  modules: FunctionalModule[];
  critical_path: string[];
  parallel_workstreams: string[];
  external_context: SearchContextItem[];
  metadata: StageMetadata;
};

export type Recommendation = {
  title: string;
  rationale: string;
  priority: "high" | "medium" | "low";
};

export type Tradeoff = {
  option: string;
  upside: string;
  downside: string;
  recommendation_bias: string;
};

export type ActionItem = {
  phase: string;
  timeline: string;
  owner: string;
  action: string;
  outcome: string;
};

export type SuccessMetric = {
  name: string;
  target: string;
  timeframe: string;
};

export type PlanResponse = {
  recommendations: Recommendation[];
  tradeoffs: Tradeoff[];
  action_plan: ActionItem[];
  success_metrics: SuccessMetric[];
  summary: string;
  metadata: StageMetadata;
};

export type SimulationResponse = {
  simulation_mode: string;
  status: "passed" | "warning" | "failed";
  checks: string[];
  risks: string[];
  metadata: StageMetadata;
};

export type RunDemoResponse = {
  intake: IntakeResponse;
  clarify: ClarifyResponse;
  review: ReviewResponse;
  assess: AssessmentResponse;
  plan: PlanResponse;
  simulate: SimulationResponse;
};

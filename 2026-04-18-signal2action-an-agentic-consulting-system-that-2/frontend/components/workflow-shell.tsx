"use client";

import { useState } from "react";

import { API_BASE_URL, apiPost } from "@/lib/api";
import type {
  AssessmentResponse,
  ClarifyResponse,
  IntakeResponse,
  PlanResponse,
  ReviewResponse,
  RunDemoResponse,
  SimulationResponse,
  SponsorToolUsage
} from "@/lib/types";

const EXAMPLE_TEXT = "Our margins are down in Q3. We need to know what to do next.";
const EXAMPLE_VOICE = "Our margins are down in Q3. What should we do?";
const EXAMPLE_NOTES = "Leadership wants an executive-ready recommendation within three weeks.";

function SponsorBadges({ usages }: { usages: SponsorToolUsage[] }) {
  if (!usages.length) {
    return <span className="badge badge-neutral">Internal logic</span>;
  }

  return (
    <div className="badge-row">
      {usages.map((usage) => (
        <span className={`badge badge-${usage.mode}`} key={`${usage.tool}-${usage.mode}`}>
          {usage.tool} · {usage.mode}
        </span>
      ))}
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="list-block">
      <h4>{title}</h4>
      {items.length ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="empty-copy">No items yet.</p>
      )}
    </div>
  );
}

function SectionHeader({
  title,
  subtitle,
  usages
}: {
  title: string;
  subtitle: string;
  usages: SponsorToolUsage[];
}) {
  return (
    <div className="panel-header">
      <div>
        <p className="panel-kicker">{subtitle}</p>
        <h3>{title}</h3>
      </div>
      <SponsorBadges usages={usages} />
    </div>
  );
}

export function WorkflowShell() {
  const [textInput, setTextInput] = useState(EXAMPLE_TEXT);
  const [voiceTranscript, setVoiceTranscript] = useState(EXAMPLE_VOICE);
  const [contextNotes, setContextNotes] = useState(EXAMPLE_NOTES);
  const [reviewDraft, setReviewDraft] = useState("");
  const [reviewNotes, setReviewNotes] = useState("Keep pricing redesign out of scope. Focus on operational levers.");
  const [error, setError] = useState<string | null>(null);
  const [activeAction, setActiveAction] = useState<string | null>(null);

  const [intake, setIntake] = useState<IntakeResponse | null>(null);
  const [clarify, setClarify] = useState<ClarifyResponse | null>(null);
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [assess, setAssess] = useState<AssessmentResponse | null>(null);
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [simulate, setSimulate] = useState<SimulationResponse | null>(null);

  const resetDownstream = (stage: "intake" | "clarify" | "review" | "assess" | "plan") => {
    if (stage === "intake") {
      setClarify(null);
      setReview(null);
      setAssess(null);
      setPlan(null);
      setSimulate(null);
    }
    if (stage === "clarify") {
      setReview(null);
      setAssess(null);
      setPlan(null);
      setSimulate(null);
    }
    if (stage === "review") {
      setAssess(null);
      setPlan(null);
      setSimulate(null);
    }
    if (stage === "assess") {
      setPlan(null);
      setSimulate(null);
    }
    if (stage === "plan") {
      setSimulate(null);
    }
  };

  const withAction = (action: string, task: () => Promise<void>) => {
    setError(null);
    setActiveAction(action);
    task()
      .catch((caught) => {
        const message = caught instanceof Error ? caught.message : "Unexpected error";
        setError(message);
      })
      .finally(() => {
        setActiveAction(null);
      });
  };

  const runIntake = () =>
    withAction("intake", async () => {
      resetDownstream("intake");
      const response = await apiPost<IntakeResponse>("/api/intake", {
        text_input: textInput,
        voice_transcript: voiceTranscript,
        context_notes: contextNotes,
        attachments: ["Q3_financial_report.pdf", "sku_margin_export.xlsx"]
      });
      setIntake(response);
    });

  const runClarify = () =>
    withAction("clarify", async () => {
      const source = intake;
      if (!source) {
        throw new Error("Run intake before clarification.");
      }
      resetDownstream("clarify");
      const response = await apiPost<ClarifyResponse>("/api/clarify", {
        normalized_input: source.normalized_input,
        extracted_signals: source.extracted_signals,
        assumptions: source.assumptions,
        missing_information: source.missing_information,
        context_notes: contextNotes
      });
      setClarify(response);
      setReviewDraft(response.clarified_scope);
    });

  const runReview = () =>
    withAction("review", async () => {
      const source = clarify;
      if (!source) {
        throw new Error("Run clarification before human review.");
      }
      resetDownstream("review");
      const response = await apiPost<ReviewResponse>("/api/review", {
        problem_statement: source.problem_statement,
        clarified_scope: source.clarified_scope,
        assumptions: source.assumptions,
        missing_information: source.missing_information,
        approved: true,
        reviewer_edits: reviewDraft || source.clarified_scope,
        reviewer_notes: reviewNotes
      });
      setReview(response);
    });

  const runAssess = () =>
    withAction("assess", async () => {
      const source = review;
      if (!source) {
        throw new Error("Complete the human review step before assessment.");
      }
      resetDownstream("assess");
      const response = await apiPost<AssessmentResponse>("/api/assess", {
        problem_statement: source.problem_statement,
        approved_scope: source.approved_scope,
        assumptions: source.assumptions,
        missing_information: source.missing_information,
        include_external_context: true
      });
      setAssess(response);
    });

  const runPlan = () =>
    withAction("plan", async () => {
      const source = assess;
      const reviewed = review;
      if (!source || !reviewed) {
        throw new Error("Run assessment before planning.");
      }
      resetDownstream("plan");
      const response = await apiPost<PlanResponse>("/api/plan", {
        problem_statement: reviewed.problem_statement,
        approved_scope: reviewed.approved_scope,
        current_state: source.current_state,
        constraints: source.constraints,
        dependencies: source.dependencies,
        gaps: source.gaps,
        modules: source.modules,
        external_context: source.external_context
      });
      setPlan(response);
    });

  const runSimulation = () =>
    withAction("simulate", async () => {
      const response = await apiPost<SimulationResponse>("/api/simulate", {
        stage: "full_workflow",
        scenario_id: "margin_q3",
        payload: {
          text_input: textInput,
          clarified_scope: review?.approved_scope,
          recommendation_count: plan?.recommendations.length ?? 0
        }
      });
      setSimulate(response);
    });

  const runDemo = () =>
    withAction("demo", async () => {
      const response = await apiPost<RunDemoResponse>("/api/run-demo", {
        scenario_id: "margin_q3",
        overrides: {
          text_input: textInput,
          voice_transcript: voiceTranscript,
          context_notes: contextNotes,
          attachments: ["Q3_financial_report.pdf", "sku_margin_export.xlsx"]
        }
      });
      setIntake(response.intake);
      setClarify(response.clarify);
      setReview(response.review);
      setAssess(response.assess);
      setPlan(response.plan);
      setSimulate(response.simulate);
      setReviewDraft(response.review.approved_scope);
    });

  const stageBusy = (name: string) => activeAction === name;
  const anyStageBusy = Boolean(activeAction);

  return (
    <main className="workspace">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Signal2Action</p>
          <h1>From ambiguous enterprise signals to decision-ready action plans.</h1>
          <p className="hero-copy">
            A production-style MVP for a multi-stage agentic consulting workflow. This UI is built for structured
            handoffs, human scope confirmation, sponsor-tool visibility, and a demo that can survive hackathon conditions.
          </p>
        </div>
        <div className="hero-actions">
          <button className="primary-button" onClick={runDemo} disabled={anyStageBusy}>
            {stageBusy("demo") ? "Running full workflow..." : "Run Full Demo"}
          </button>
          <button
            className="secondary-button"
            onClick={() => {
              setTextInput(EXAMPLE_TEXT);
              setVoiceTranscript(EXAMPLE_VOICE);
              setContextNotes(EXAMPLE_NOTES);
            }}
            disabled={anyStageBusy}
          >
            Reload Example
          </button>
        </div>
        <div className="hero-meta">
          <span className="status-pill">Workflow System, not chatbot</span>
          <span className="status-pill">API base: {API_BASE_URL}</span>
        </div>
      </section>

      {error ? <section className="error-banner">{error}</section> : null}

      <section className="panel input-panel">
        <SectionHeader
          title="Input Workspace"
          subtitle="Stage 0 · Enterprise signal intake"
          usages={intake?.metadata.tool_usages ?? []}
        />
        <div className="input-grid">
          <label className="field">
            <span>Text input</span>
            <textarea
              value={textInput}
              onChange={(event) => setTextInput(event.target.value)}
              placeholder="Paste the business problem, brief, or report summary."
            />
          </label>
          <label className="field">
            <span>Voice transcript</span>
            <textarea
              value={voiceTranscript}
              onChange={(event) => setVoiceTranscript(event.target.value)}
              placeholder="VoiceRun transcript or local mock transcript."
            />
          </label>
          <label className="field field-wide">
            <span>Context notes</span>
            <textarea
              value={contextNotes}
              onChange={(event) => setContextNotes(event.target.value)}
              placeholder="Extra context, attachment notes, urgency, constraints."
            />
          </label>
        </div>
        <div className="button-row">
          <button className="primary-button" onClick={runIntake} disabled={anyStageBusy}>
            {stageBusy("intake") ? "Normalizing..." : "Run Intake"}
          </button>
          <button className="secondary-button" onClick={runClarify} disabled={anyStageBusy}>
            {stageBusy("clarify") ? "Clarifying..." : "Run Clarification"}
          </button>
          <button className="secondary-button" onClick={runReview} disabled={anyStageBusy}>
            {stageBusy("review") ? "Confirming..." : "Confirm Scope"}
          </button>
          <button className="secondary-button" onClick={runAssess} disabled={anyStageBusy}>
            {stageBusy("assess") ? "Assessing..." : "Run Assessment"}
          </button>
          <button className="secondary-button" onClick={runPlan} disabled={anyStageBusy}>
            {stageBusy("plan") ? "Planning..." : "Generate Plan"}
          </button>
          <button className="secondary-button" onClick={runSimulation} disabled={anyStageBusy}>
            {stageBusy("simulate") ? "Simulating..." : "Run QA"}
          </button>
        </div>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <SectionHeader
            title="Clarification"
            subtitle="Agent 1 · Intake + clarification"
            usages={clarify?.metadata.tool_usages ?? intake?.metadata.tool_usages ?? []}
          />
          <div className="rich-block">
            <h4>Problem statement</h4>
            <p>{clarify?.problem_statement ?? intake?.problem_statement ?? "No problem statement yet."}</p>
          </div>
          <ListBlock title="Extracted signals" items={intake?.extracted_signals ?? []} />
          <ListBlock title="Clarifying questions" items={clarify?.clarifying_questions ?? intake?.clarifying_questions ?? []} />
          <ListBlock title="Missing information" items={clarify?.missing_information ?? intake?.missing_information ?? []} />
        </article>

        <article className="panel">
          <SectionHeader title="Human Review" subtitle="Checkpoint · Scope confirmation" usages={review?.metadata.tool_usages ?? []} />
          <label className="field">
            <span>Approved scope</span>
            <textarea
              value={reviewDraft}
              onChange={(event) => setReviewDraft(event.target.value)}
              placeholder="Edit the clarified scope before downstream analysis."
            />
          </label>
          <label className="field">
            <span>Reviewer notes</span>
            <textarea
              value={reviewNotes}
              onChange={(event) => setReviewNotes(event.target.value)}
              placeholder="Add human feedback that should shape downstream reasoning."
            />
          </label>
          <ListBlock title="Review notes" items={review?.review_notes ?? []} />
          <ListBlock title="Assumptions" items={review?.assumptions ?? clarify?.assumptions ?? intake?.assumptions ?? []} />
        </article>

        <article className="panel">
          <SectionHeader title="Assessment" subtitle="Agent 2 · Current state analysis" usages={assess?.metadata.tool_usages ?? []} />
          <ListBlock title="Current state" items={assess?.current_state ?? []} />
          <ListBlock title="Constraints" items={assess?.constraints ?? []} />
          <ListBlock title="Dependencies" items={assess?.dependencies ?? []} />
          <ListBlock title="Gaps" items={assess?.gaps ?? []} />
        </article>

        <article className="panel">
          <SectionHeader title="Functional Decomposition" subtitle="Agent 2 · Module breakdown" usages={assess?.metadata.tool_usages ?? []} />
          <div className="module-stack">
            {assess?.modules?.length ? (
              assess.modules.map((module) => (
                <div className="module-card" key={module.name}>
                  <div className="module-card-head">
                    <h4>{module.name}</h4>
                    <span>{module.owner_hint}</span>
                  </div>
                  <p>{module.objective}</p>
                  <ul>
                    {module.outputs.map((output) => (
                      <li key={output}>{output}</li>
                    ))}
                  </ul>
                </div>
              ))
            ) : (
              <p className="empty-copy">Modules will appear after assessment.</p>
            )}
          </div>
          <div className="external-context">
            <h4>External context</h4>
            {assess?.external_context?.length ? (
              assess.external_context.map((item) => (
                <div className="context-item" key={item.title}>
                  <strong>{item.title}</strong>
                  <p>{item.summary}</p>
                  <span>{item.source}</span>
                </div>
              ))
            ) : (
              <p className="empty-copy">No search enrichment yet.</p>
            )}
          </div>
        </article>

        <article className="panel">
          <SectionHeader title="Solution" subtitle="Agent 3 · Recommendations + trade-offs" usages={plan?.metadata.tool_usages ?? []} />
          <div className="recommendation-stack">
            {plan?.recommendations?.length ? (
              plan.recommendations.map((item) => (
                <div className="recommendation-card" key={item.title}>
                  <div className="recommendation-head">
                    <h4>{item.title}</h4>
                    <span className={`priority priority-${item.priority}`}>{item.priority}</span>
                  </div>
                  <p>{item.rationale}</p>
                </div>
              ))
            ) : (
              <p className="empty-copy">Recommendations will appear after planning.</p>
            )}
          </div>
          <div className="tradeoff-stack">
            <h4>Trade-offs</h4>
            {plan?.tradeoffs?.length ? (
              plan.tradeoffs.map((item) => (
                <div className="tradeoff-card" key={item.option}>
                  <strong>{item.option}</strong>
                  <p>Upside: {item.upside}</p>
                  <p>Downside: {item.downside}</p>
                  <span>{item.recommendation_bias}</span>
                </div>
              ))
            ) : (
              <p className="empty-copy">Trade-off analysis will appear here.</p>
            )}
          </div>
        </article>

        <article className="panel">
          <SectionHeader title="Action Plan" subtitle="Agent 3 · Roadmap + KPIs" usages={plan?.metadata.tool_usages ?? []} />
          <div className="rich-block">
            <h4>Summary</h4>
            <p>{plan?.summary ?? "No plan summary yet."}</p>
          </div>
          <div className="action-stack">
            {plan?.action_plan?.length ? (
              plan.action_plan.map((item) => (
                <div className="action-card" key={`${item.phase}-${item.action}`}>
                  <div className="action-card-head">
                    <h4>{item.phase}</h4>
                    <span>{item.timeline}</span>
                  </div>
                  <p className="owner-line">Owner: {item.owner}</p>
                  <p>{item.action}</p>
                  <p className="outcome-line">Expected outcome: {item.outcome}</p>
                </div>
              ))
            ) : (
              <p className="empty-copy">Roadmap items will appear after planning.</p>
            )}
          </div>
          <div className="metrics-grid">
            {plan?.success_metrics?.length ? (
              plan.success_metrics.map((metric) => (
                <div className="metric-card" key={metric.name}>
                  <span>{metric.name}</span>
                  <strong>{metric.target}</strong>
                  <p>{metric.timeframe}</p>
                </div>
              ))
            ) : (
              <p className="empty-copy">Success metrics will appear here.</p>
            )}
          </div>
        </article>

        <article className="panel qa-panel">
          <SectionHeader title="QA / Simulation" subtitle="Veris adapter + local fallback" usages={simulate?.metadata.tool_usages ?? []} />
          <div className="qa-status-row">
            <span className={`status-chip status-${simulate?.status ?? "idle"}`}>{simulate?.status ?? "idle"}</span>
            <span className="status-pill">Mode: {simulate?.simulation_mode ?? "not run"}</span>
          </div>
          <ListBlock title="Checks" items={simulate?.checks ?? []} />
          <ListBlock title="Risks" items={simulate?.risks ?? []} />
        </article>
      </section>
    </main>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";

import { apiPost } from "@/lib/api";
import type {
  AssessmentResponse,
  ClarifyResponse,
  IntakeResponse,
  PlanResponse,
  ReviewResponse,
  SimulationResponse,
  SponsorToolUsage
} from "@/lib/types";

type Step = 1 | 2 | 3;
type Tab = "ppt" | "card";

type RequirementAnalysis = {
  clarified_problem: string;
  assumptions: string[];
  scope: string;
  urgency: "high" | "medium" | "low";
  clarifying_questions: string[];
};

type Slide =
  | {
      type: "title";
      tag: string;
      title: string;
      subtitle: string;
    }
  | {
      type: "problem" | "solution";
      tag: string;
      title: string;
      bullets: string[];
    }
  | {
      type: "modules";
      tag: string;
      title: string;
      modules: Array<{ name: string; description: string }>;
    }
  | {
      type: "timeline";
      tag: string;
      title: string;
      timeline: Record<string, string[]>;
    };

type Deliverables = {
  slides: Slide[];
  summary_card: {
    headline: string;
    scope: string;
    modules: string[];
    key_actions: string[];
    timeline: string;
  };
};

type AttachmentState = {
  googleDrive: { url: string; name: string } | null;
  voiceTranscript: string;
};

const examples = [
  {
    problem:
      "Our Q3 margins are down 15% and we cannot identify which product line is causing the compression. We have 3 product lines, a 200-person company, and a finance team but they are overwhelmed with manual reporting.",
    industry: "Consumer Goods",
    size: "Mid-market (500–5k)",
    horizon: "Short-term (weeks)"
  },
  {
    problem:
      "We are a fintech startup considering expanding into Southeast Asia. We have strong product-market fit in the US but no international playbook, limited local knowledge, and unclear regulatory requirements.",
    industry: "Financial Services",
    size: "SMB (50–500)",
    horizon: "Medium-term (1–3 months)"
  },
  {
    problem:
      "Post-merger, we have two overlapping engineering organizations of 400 people total with duplicated roles, different tech stacks, and low morale. Leadership wants a restructuring recommendation in 6 weeks.",
    industry: "Technology",
    size: "Enterprise (5k+)",
    horizon: "Medium-term (1–3 months)"
  }
] as const;

function getUrgency(horizon: string): "high" | "medium" | "low" {
  if (horizon.includes("Immediate") || horizon.includes("Short-term")) {
    return "high";
  }
  if (horizon.includes("Medium-term")) {
    return "medium";
  }
  return "low";
}

function buildRequirementAnalysis(
  intake: IntakeResponse,
  clarify: ClarifyResponse,
  horizon: string
): RequirementAnalysis {
  return {
    clarified_problem: clarify.problem_statement,
    assumptions: clarify.assumptions.length ? clarify.assumptions : intake.assumptions,
    scope: clarify.clarified_scope,
    urgency: getUrgency(horizon),
    clarifying_questions: clarify.clarifying_questions.length
      ? clarify.clarifying_questions
      : intake.clarifying_questions
  };
}

function buildDeliverables(
  analysis: RequirementAnalysis,
  assess: AssessmentResponse,
  plan: PlanResponse
): Deliverables {
  const actionByPhase = plan.action_plan.reduce<Record<string, string[]>>((accumulator, item) => {
    if (!accumulator[item.phase]) {
      accumulator[item.phase] = [];
    }
    accumulator[item.phase].push(item.action);
    return accumulator;
  }, {});

  return {
    slides: [
      {
        type: "title",
        tag: "Signal2Action",
        title: analysis.clarified_problem,
        subtitle: analysis.scope
      },
      {
        type: "problem",
        tag: "Requirement Analysis",
        title: "What the system clarified",
        bullets: [
          ...analysis.assumptions.slice(0, 2),
          ...assess.gaps.slice(0, 2)
        ]
      },
      {
        type: "modules",
        tag: "Functional Decomposition",
        title: "Module breakdown",
        modules: assess.modules.map((module) => ({
          name: module.name,
          description: module.objective
        }))
      },
      {
        type: "solution",
        tag: "Recommendations",
        title: "Recommended path",
        bullets: [
          ...plan.recommendations.map((item) => `${item.title} — ${item.rationale}`),
          ...plan.tradeoffs.slice(0, 1).map((item) => `${item.option}: ${item.recommendation_bias}`)
        ].slice(0, 4)
      },
      {
        type: "timeline",
        tag: "Action Plan",
        title: "Execution roadmap",
        timeline:
          Object.keys(actionByPhase).length > 0
            ? actionByPhase
            : {
                "30 days": plan.action_plan.slice(0, 1).map((item) => item.action),
                "60 days": plan.action_plan.slice(1, 2).map((item) => item.action),
                "90 days": plan.action_plan.slice(2, 3).map((item) => item.action)
              }
      }
    ],
    summary_card: {
      headline: analysis.clarified_problem,
      scope: analysis.scope,
      modules: assess.modules.map((module) => module.name),
      key_actions: plan.action_plan.slice(0, 3).map((item) => item.action),
      timeline:
        plan.success_metrics[0]?.timeframe ||
        plan.action_plan.map((item) => item.phase).join(" · ") ||
        "30–90 days"
    }
  };
}

function getToolUsage(toolName: string, usages: SponsorToolUsage[] | undefined): SponsorToolUsage | null {
  return usages?.find((usage) => usage.tool === toolName) ?? null;
}

function SponsorStatus({
  label,
  usage
}: {
  label: string;
  usage: SponsorToolUsage | null;
}) {
  if (!usage) {
    return <span className="api-status idle">{label} idle</span>;
  }

  return <span className={`api-status ${usage.mode}`}>{label} {usage.mode}</span>;
}

function StepDot({
  number,
  label,
  active,
  done,
  onClick
}: {
  number: string;
  label: string;
  active: boolean;
  done: boolean;
  onClick: () => void;
}) {
  return (
    <div className={`step-dot${active ? " active" : ""}${done ? " done" : ""}`} onClick={onClick}>
      <div className="step-dot-circle">{number}</div>
      <span className="step-dot-label">{label}</span>
    </div>
  );
}

function SlideView({ slide, index, total }: { slide: Slide; index: number; total: number }) {
  let body: React.ReactNode = null;

  if (slide.type === "title") {
    body = (
      <>
        <div className="slide-tag-text">{slide.tag}</div>
        <div className="slide-h1">{slide.title}</div>
        <div className="slide-sub-text">{slide.subtitle}</div>
      </>
    );
  }

  if (slide.type === "problem" || slide.type === "solution") {
    body = (
      <>
        <div className="slide-tag-text">{slide.tag}</div>
        <div className="slide-h1">{slide.title}</div>
        <div className="slide-bullets">
          {slide.bullets.map((bullet) => (
            <div className="slide-bullet" key={bullet}>
              {bullet}
            </div>
          ))}
        </div>
      </>
    );
  }

  if (slide.type === "modules") {
    body = (
      <>
        <div className="slide-tag-text">{slide.tag}</div>
        <div className="slide-h1">{slide.title}</div>
        <div className="slide-modules-grid">
          {slide.modules.map((module) => (
            <div className="slide-module-box" key={module.name}>
              <div className="slide-module-name">{module.name}</div>
              <div className="slide-module-desc">{module.description}</div>
            </div>
          ))}
        </div>
      </>
    );
  }

  if (slide.type === "timeline") {
    body = (
      <>
        <div className="slide-tag-text">{slide.tag}</div>
        <div className="slide-h1">{slide.title}</div>
        <div className="slide-timeline">
          {Object.entries(slide.timeline).map(([phase, items]) => (
            <div className="timeline-col" key={phase}>
              <div className="timeline-label">{phase}</div>
              {items.map((item) => (
                <div className="timeline-item" key={item}>
                  {item}
                </div>
              ))}
            </div>
          ))}
        </div>
      </>
    );
  }

  return (
    <div className={`slide ${slide.type === "title" || slide.type === "modules" || slide.type === "timeline" ? "slide-title" : "slide-dark"} active`}>
      {body}
      <div className="slide-footer">
        <div className="slide-footer-brand">Signal2Action</div>
        <div className="slide-page">
          {index + 1} / {total}
        </div>
      </div>
    </div>
  );
}

export function WorkflowShell() {
  const [step, setStep] = useState<Step>(1);
  const [scrolled, setScrolled] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("ppt");
  const [currentSlide, setCurrentSlide] = useState(0);
  const [problem, setProblem] = useState("");
  const [industry, setIndustry] = useState("");
  const [companySize, setCompanySize] = useState("");
  const [timeHorizon, setTimeHorizon] = useState("");
  const [attachments, setAttachments] = useState<AttachmentState>({
    googleDrive: null,
    voiceTranscript: ""
  });
  const [analysis, setAnalysis] = useState<RequirementAnalysis | null>(null);
  const [functions, setFunctions] = useState<AssessmentResponse | null>(null);
  const [deliverables, setDeliverables] = useState<Deliverables | null>(null);
  const [activeAction, setActiveAction] = useState<"analysis" | "functions" | "deliverables" | null>(null);
  const [reqLoadingStep, setReqLoadingStep] = useState(1);
  const [funcLoadingStep, setFuncLoadingStep] = useState(1);
  const [delLoadingStep, setDelLoadingStep] = useState(1);
  const [error, setError] = useState<string | null>(null);

  const [intake, setIntake] = useState<IntakeResponse | null>(null);
  const [clarify, setClarify] = useState<ClarifyResponse | null>(null);
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [simulate, setSimulate] = useState<SimulationResponse | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const sponsorUsages = useMemo(() => {
    return {
      voicerun: getToolUsage("VoiceRun", intake?.metadata.tool_usages),
      you: getToolUsage("You.com", functions?.metadata.tool_usages),
      baseten: getToolUsage("Baseten", plan?.metadata.tool_usages),
      veris: getToolUsage("Veris", simulate?.metadata.tool_usages)
    };
  }, [functions, intake, plan, simulate]);

  const inputModeLabel = useMemo(() => {
    const parts: string[] = [];
    if (problem.trim()) {
      parts.push("Text");
    }
    if (attachments.googleDrive) {
      parts.push("Drive");
    }
    if (attachments.voiceTranscript) {
      parts.push("Voice");
    }
    return parts.length ? parts.join(" + ") : "Text only";
  }, [attachments, problem]);

  const anyLoading = activeAction !== null;

  const goToStep = (nextStep: Step) => {
    setStep(nextStep);
    if (typeof window !== "undefined") {
      document.getElementById("app")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const fillExample = (index: number) => {
    const example = examples[index];
    setProblem(example.problem);
    setIndustry(example.industry);
    setCompanySize(example.size);
    setTimeHorizon(example.horizon);
  };

  const handleGoogleDriveImport = () => {
    const driveLink = window.prompt("Paste a Google Drive share link for the requirement doc.");
    if (!driveLink) {
      return;
    }

    const trimmed = driveLink.trim();
    if (!trimmed.includes("drive.google.com")) {
      window.alert("Please paste a valid Google Drive share link.");
      return;
    }

    const fileName = trimmed.split("/").filter(Boolean).pop() || "Drive file";
    setAttachments((current) => ({
      ...current,
      googleDrive: { url: trimmed, name: fileName }
    }));
    setProblem((current) =>
      current.trim()
        ? `${current}\n\n[Attached context]\nGoogle Drive reference: ${trimmed}`
        : `[Attached context]\nGoogle Drive reference: ${trimmed}`
    );
  };

  const handleVoiceCapture = () => {
    const transcript = window.prompt("Paste the VoiceRun transcript or a short voice note summary.");
    if (!transcript) {
      return;
    }

    const cleaned = transcript.trim();
    setAttachments((current) => ({
      ...current,
      voiceTranscript: cleaned
    }));
    setProblem((current) =>
      current.trim() ? `${current}\n\n[VoiceRun transcript]\n${cleaned}` : `[VoiceRun transcript]\n${cleaned}`
    );
  };

  const runAnalysis = async () => {
    if (problem.trim().length < 20) {
      setError("Please enter a fuller business problem before starting analysis.");
      return;
    }

    setError(null);
    setActiveAction("analysis");
    setReqLoadingStep(1);
    setAnalysis(null);
    setFunctions(null);
    setDeliverables(null);
    setPlan(null);
    setSimulate(null);
    setReview(null);

    try {
      const intakeResponse = await apiPost<IntakeResponse>("/api/intake", {
        text_input: problem,
        voice_transcript: attachments.voiceTranscript || undefined,
        attachments: attachments.googleDrive ? [attachments.googleDrive.url] : [],
        context_notes: [
          industry ? `Industry: ${industry}` : "",
          companySize ? `Company size: ${companySize}` : "",
          timeHorizon ? `Time horizon: ${timeHorizon}` : ""
        ]
          .filter(Boolean)
          .join(" · ")
      });
      setIntake(intakeResponse);

      setReqLoadingStep(2);
      const clarifyResponse = await apiPost<ClarifyResponse>("/api/clarify", {
        normalized_input: intakeResponse.normalized_input,
        extracted_signals: intakeResponse.extracted_signals,
        assumptions: intakeResponse.assumptions,
        missing_information: intakeResponse.missing_information,
        context_notes: problem
      });
      setClarify(clarifyResponse);
      setReqLoadingStep(3);

      const nextAnalysis = buildRequirementAnalysis(intakeResponse, clarifyResponse, timeHorizon);
      setAnalysis(nextAnalysis);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Analysis failed.";
      setError(message);
    } finally {
      setActiveAction(null);
    }
  };

  const runFunctionDecomposition = async () => {
    if (!clarify) {
      setError("Run requirement analysis before decomposing functions.");
      return;
    }

    setError(null);
    setActiveAction("functions");
    setFuncLoadingStep(1);
    goToStep(2);

    try {
      const reviewResponse = await apiPost<ReviewResponse>("/api/review", {
        problem_statement: clarify.problem_statement,
        clarified_scope: clarify.clarified_scope,
        assumptions: clarify.assumptions,
        missing_information: clarify.missing_information,
        approved: true,
        reviewer_edits: analysis?.scope || clarify.clarified_scope,
        reviewer_notes: "Human review confirmed the clarified scope before decomposition."
      });
      setReview(reviewResponse);

      setFuncLoadingStep(2);
      const assessResponse = await apiPost<AssessmentResponse>("/api/assess", {
        problem_statement: reviewResponse.problem_statement,
        approved_scope: reviewResponse.approved_scope,
        assumptions: reviewResponse.assumptions,
        missing_information: reviewResponse.missing_information,
        include_external_context: true
      });
      setFunctions(assessResponse);
      setFuncLoadingStep(3);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Function decomposition failed.";
      setError(message);
    } finally {
      setActiveAction(null);
    }
  };

  const runGenerateDeliverables = async () => {
    if (!functions || !review || !analysis) {
      setError("Complete the decomposition step before generating deliverables.");
      return;
    }

    setError(null);
    setActiveAction("deliverables");
    setDelLoadingStep(1);
    goToStep(3);

    try {
      const planResponse = await apiPost<PlanResponse>("/api/plan", {
        problem_statement: review.problem_statement,
        approved_scope: review.approved_scope,
        current_state: functions.current_state,
        constraints: functions.constraints,
        dependencies: functions.dependencies,
        gaps: functions.gaps,
        modules: functions.modules,
        external_context: functions.external_context
      });
      setPlan(planResponse);

      setDelLoadingStep(2);
      const simulationResponse = await apiPost<SimulationResponse>("/api/simulate", {
        stage: "full_workflow",
        scenario_id: "margin_q3",
        payload: {
          problem_statement: review.problem_statement,
          approved_scope: review.approved_scope,
          recommendations: planResponse.recommendations.length
        }
      });
      setSimulate(simulationResponse);
      setDelLoadingStep(3);

      const nextDeliverables = buildDeliverables(analysis, functions, planResponse);
      setDeliverables(nextDeliverables);
      setCurrentSlide(0);
      setActiveTab("ppt");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Deliverable generation failed.";
      setError(message);
    } finally {
      setActiveAction(null);
    }
  };

  const copyCard = async () => {
    if (!deliverables) {
      return;
    }

    const card = deliverables.summary_card;
    const text = `Signal2Action Analysis\n\n${card.headline}\n\nScope: ${card.scope}\n\nModules: ${card.modules.join(", ")}\n\nKey Actions:\n${card.key_actions
      .map((item, index) => `${index + 1}. ${item}`)
      .join("\n")}\n\nTimeline: ${card.timeline}`;
    await navigator.clipboard.writeText(text);
  };

  const resetAll = () => {
    setStep(1);
    setActiveTab("ppt");
    setCurrentSlide(0);
    setProblem("");
    setIndustry("");
    setCompanySize("");
    setTimeHorizon("");
    setAttachments({ googleDrive: null, voiceTranscript: "" });
    setAnalysis(null);
    setFunctions(null);
    setDeliverables(null);
    setIntake(null);
    setClarify(null);
    setReview(null);
    setPlan(null);
    setSimulate(null);
    setError(null);
    setActiveAction(null);
  };

  const slides = deliverables?.slides ?? [];
  const activeSlide = slides[currentSlide] ?? null;

  return (
    <>
      <nav id="nav" className={scrolled ? "scrolled" : ""}>
        <div className="logo" onClick={() => document.getElementById("hero")?.scrollIntoView({ behavior: "smooth" })}>
          Signal<em>2</em>Action
        </div>
        <div className="nav-steps">
          <button className={`nav-step-btn${step === 1 ? " active" : ""}`} onClick={() => goToStep(1)}>
            01 Requirements
          </button>
          <button className={`nav-step-btn${step === 2 ? " active" : ""}`} onClick={() => goToStep(2)}>
            02 Functions
          </button>
          <button className={`nav-step-btn${step === 3 ? " active" : ""}`} onClick={() => goToStep(3)}>
            03 Deliverables
          </button>
        </div>
        <button className="nav-cta" onClick={() => goToStep(1)}>
          Start analysis
        </button>
      </nav>

      <section id="hero">
        <div className="hero-glow" />
        <div className="hero-content">
          <h1 className="hero-title">
            <span className="line">
              <span className="line-inner">Signal2Action</span>
            </span>
            <span className="line">
              <span className="line-inner hero-tagline">We make consulting better.</span>
            </span>
          </h1>
        </div>
        <div className="hero-cta-hint" onClick={() => document.getElementById("pain-section")?.scrollIntoView({ behavior: "smooth" })}>
          <span>See the pain points</span>
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </section>

      <section id="pain-section">
        <div className="pain-shell">
          <div className="pain-hero">
            <div className="pain-intro">
              <div className="pain-kicker">Why Consulting Breaks</div>
              <h2 className="pain-headline">Consulting is still too manual to scale.</h2>
              <p className="pain-subcopy">
                Repeated work, messy discovery, and weak execution handoffs make consulting expensive to repeat.
                Signal2Action turns that process into a reusable workflow.
              </p>
            </div>
            <div className="pain-quote">
              <div>
                <div className="pain-quote-mark">“</div>
                <div className="pain-quote-copy">
                  The issue is not expertise. The issue is that the process is too slow, fragmented, and hard to reuse.
                </div>
              </div>
              <div className="pain-quote-note">
                Signal2Action standardizes clarification, assessment, decomposition, and action planning into one
                agentic system.
              </div>
            </div>
          </div>

          <div className="pain-grid">
            {[
              ["01", "Low Reusability", "Repeated work", "Consulting work is repeated, but not reusable.", "Standardize intake, assessment, and decomposition as a reusable agent pipeline."],
              ["02", "High Cost of Discovery", "Ambiguous inputs", "Most time is spent figuring out what the problem actually is.", "Parse voice, PDF, and Excel input and converge on a clear problem definition in minutes."],
              ["03", "Misalignment & Iteration Cost", "Scope drift", "Misunderstanding is expensive.", "Use a clarification loop and human review to lock scope early."],
              ["04", "Insight to Action Gap", "Execution risk", "Consulting often stops at insight, not action.", "Generate roadmap, next steps, and KPIs alongside the analysis."],
              ["05", "Not Scalable", "Human bottleneck", "Consulting expertise does not scale easily.", "Turn consulting know-how into a repeatable system instead of a people bottleneck."],
              ["06", "Fragmented Signals", "Messy enterprise inputs", "Enterprises do not have clean inputs. They have messy signals.", "Normalize fragmented inputs into one structured signal."]
            ].map(([index, title, tag, core, solution]) => (
              <article className="pain-card" key={index}>
                <div className="pain-card-head">
                  <div>
                    <div className="pain-card-index">{index}</div>
                    <h3 className="pain-card-title">{title}</h3>
                  </div>
                  <div className="pain-card-tag">{tag}</div>
                </div>
                <div className="pain-core">
                  <div className="pain-core-label">Core problem</div>
                  <div className="pain-core-text">{core}</div>
                </div>
                <div className="pain-solution">
                  <div className="pain-solution-label">Signal2Action</div>
                  <div className="pain-solution-copy">{solution}</div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <div id="app">
        <div id="api-bar">
          <label>Sponsor stack</label>
          <div className="api-stack">
            <SponsorStatus label="VoiceRun" usage={sponsorUsages.voicerun} />
            <SponsorStatus label="You.com" usage={sponsorUsages.you} />
            <SponsorStatus label="Baseten" usage={sponsorUsages.baseten} />
            <SponsorStatus label="Veris" usage={sponsorUsages.veris} />
          </div>
          <span className="api-bar-hint">Backend-controlled integration state. Mock, live, and disabled modes reflect actual adapter output.</span>
        </div>

        <div className="step-indicator" id="step-indicator">
          <StepDot number="01" label="Requirements" active={step === 1} done={step > 1} onClick={() => goToStep(1)} />
          <div className={`step-line${step > 1 ? " done" : ""}`} />
          <StepDot number="02" label="Functions" active={step === 2} done={step > 2} onClick={() => goToStep(2)} />
          <div className={`step-line${step > 2 ? " done" : ""}`} />
          <StepDot number="03" label="Deliverables" active={step === 3} done={false} onClick={() => goToStep(3)} />
        </div>

        {error ? <div className="error-strip">{error}</div> : null}

        <section className={`step-section${step !== 1 ? " hidden" : ""}`} id="step-requirements">
          <div className="step-header">
            <div className="step-tag">Step 01 — Requirement Analysis</div>
            <h2 className="step-title">Describe your business challenge</h2>
            <p className="step-sub">Type freely. Signal2Action extracts the signal, clarifies the scope, and prepares the handoff.</p>
          </div>

          {activeAction !== "analysis" && !analysis ? (
            <div className="req-form" id="req-form">
              <div className="req-input-toolbar">
                <div className="req-mode-card">
                  <div className="req-mode-icon">
                    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.75 6.75h14.5M4.75 12h14.5M4.75 17.25h8.5" />
                    </svg>
                  </div>
                  <div className="req-mode-copy">
                    <div className="req-mode-title">Requirement intake</div>
                    <div className="req-mode-desc">
                      Support direct text input, pasted Google Drive links, or VoiceRun transcript capture that flows
                      into the requirement field below.
                    </div>
                  </div>
                </div>

                <button className="req-tool-btn" type="button" onClick={handleGoogleDriveImport}>
                  <div className="req-tool-btn-top">
                    <div className="req-tool-icon drive">G</div>
                    <div className="req-tool-label">
                      <strong>Google Drive</strong>
                      <span>Import share link</span>
                    </div>
                  </div>
                  <div className="req-tool-status">{attachments.googleDrive ? "Drive linked" : "Paste drive link"}</div>
                </button>

                <button className="req-tool-btn" type="button" onClick={handleVoiceCapture}>
                  <div className="req-tool-btn-top">
                    <div className="req-tool-icon voice">V</div>
                    <div className="req-tool-label">
                      <strong>VoiceRun</strong>
                      <span>Speech to text</span>
                    </div>
                  </div>
                  <div className="req-tool-status">{attachments.voiceTranscript ? "Transcript ready" : "Tap to add transcript"}</div>
                </button>
              </div>

              <div className="req-inline-meta">
                <div className="meta-pill">
                  <strong>Input</strong>
                  <span>{inputModeLabel}</span>
                </div>
                <div className="meta-pill">
                  <strong>Drive</strong>
                  <span>{attachments.googleDrive?.name ?? "No file linked"}</span>
                </div>
                <div className="meta-pill">
                  <strong>Voice</strong>
                  <span>{attachments.voiceTranscript ? "Transcript ready" : "Idle"}</span>
                </div>
              </div>

              <div className="req-main-input">
                <label htmlFor="problem-input">Problem description</label>
                <textarea
                  id="problem-input"
                  value={problem}
                  onChange={(event) => setProblem(event.target.value)}
                  placeholder="e.g. Our Q3 margins are down 15% and we do not know which product line is causing it..."
                />
              </div>

              <div className="req-context-row">
                <div className="req-field">
                  <label>Industry</label>
                  <select value={industry} onChange={(event) => setIndustry(event.target.value)}>
                    <option value="">Select industry</option>
                    <option>Consumer Goods</option>
                    <option>Financial Services</option>
                    <option>Healthcare</option>
                    <option>Technology</option>
                    <option>Manufacturing</option>
                    <option>Retail</option>
                    <option>Professional Services</option>
                    <option>Energy</option>
                    <option>Other</option>
                  </select>
                </div>
                <div className="req-field">
                  <label>Company size</label>
                  <select value={companySize} onChange={(event) => setCompanySize(event.target.value)}>
                    <option value="">Select size</option>
                    <option>Startup (&lt;50)</option>
                    <option>SMB (50–500)</option>
                    <option>Mid-market (500–5k)</option>
                    <option>Enterprise (5k+)</option>
                  </select>
                </div>
                <div className="req-field">
                  <label>Time horizon</label>
                  <select value={timeHorizon} onChange={(event) => setTimeHorizon(event.target.value)}>
                    <option value="">Select horizon</option>
                    <option>Immediate (days)</option>
                    <option>Short-term (weeks)</option>
                    <option>Medium-term (1–3 months)</option>
                    <option>Long-term (3–12 months)</option>
                  </select>
                </div>
              </div>

              <div className="req-submit-row">
                <div className="req-examples">
                  <span className="example-label">Try:</span>
                  {examples.map((_, index) => (
                    <button className="example-chip" key={index} onClick={() => fillExample(index)}>
                      {index === 0 ? "Margin compression" : index === 1 ? "Market entry" : "Org restructure"}
                    </button>
                  ))}
                </div>
                <button className="btn-primary" onClick={runAnalysis} disabled={anyLoading}>
                  Analyze requirements
                </button>
              </div>
            </div>
          ) : null}

          {activeAction === "analysis" ? (
            <div className="loading-block">
              <div className="spinner" />
              <div className="loading-label">Analyzing requirements</div>
              <div className="loading-steps">
                <div className={`loading-step${reqLoadingStep === 1 ? " active" : reqLoadingStep > 1 ? " done" : ""}`}>Parsing problem statement</div>
                <div className={`loading-step${reqLoadingStep === 2 ? " active" : reqLoadingStep > 2 ? " done" : ""}`}>Identifying key context & assumptions</div>
                <div className={`loading-step${reqLoadingStep === 3 ? " active" : ""}`}>Formulating clarifying questions</div>
              </div>
            </div>
          ) : null}

          {analysis ? (
            <div className="result-block">
              <div className="result-card accent-blue">
                <div className="result-card-label">Clarified problem statement</div>
                <div className="result-card-content">{analysis.clarified_problem}</div>
              </div>
              <div className="result-card accent-amber">
                <div className="result-card-label">Key context & assumptions</div>
                <div className="tag-list">
                  {analysis.assumptions.map((assumption) => (
                    <span className="tag" key={assumption}>
                      {assumption}
                    </span>
                  ))}
                </div>
              </div>
              <div className="result-card accent-purple">
                <div className="result-card-label">Scope</div>
                <div className="result-card-content">{analysis.scope}</div>
              </div>
              <div className="result-card">
                <div className="result-card-label">Clarifying questions (to consider before proceeding)</div>
                <div className="questions-list">
                  {analysis.clarifying_questions.map((question, index) => (
                    <div className="question-item" key={question}>
                      <span className="q-num">Q{index + 1}</span>
                      <span>{question}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="step-action-row">
                <button className="btn-secondary" onClick={() => setAnalysis(null)}>
                  ← Revise input
                </button>
                <button className="btn-primary" onClick={runFunctionDecomposition} disabled={anyLoading}>
                  Confirm scope & decompose functions
                </button>
              </div>
            </div>
          ) : null}
        </section>

        <section className={`step-section${step !== 2 ? " hidden" : ""}`} id="step-functions">
          <div className="step-header">
            <div className="step-tag">Step 02 — Function Decomposition</div>
            <h2 className="step-title">Functional module breakdown</h2>
            <p className="step-sub">
              The problem decomposed into actionable modules, each with inputs, outputs, and recommended approach.
            </p>
          </div>

          {activeAction === "functions" ? (
            <div className="loading-block">
              <div className="spinner" />
              <div className="loading-label">Decomposing functions</div>
              <div className="loading-steps">
                <div className={`loading-step${funcLoadingStep === 1 ? " active" : funcLoadingStep > 1 ? " done" : ""}`}>Confirming reviewed scope</div>
                <div className={`loading-step${funcLoadingStep === 2 ? " active" : funcLoadingStep > 2 ? " done" : ""}`}>Building functional module tree</div>
                <div className={`loading-step${funcLoadingStep === 3 ? " active" : ""}`}>Mapping dependencies & critical path</div>
              </div>
            </div>
          ) : null}

          {functions ? (
            <div>
              <div className="critical-path-bar">
                <span className="critical-path-label">Critical Path</span>
                <div className="critical-path-items">
                  {functions.critical_path.map((item, index) => (
                    <span key={item} className="critical-path-segment">
                      <span className="cp-item">{item}</span>
                      {index < functions.critical_path.length - 1 ? <span className="cp-arrow">→</span> : null}
                    </span>
                  ))}
                </div>
              </div>
              <div className="module-grid">
                {functions.modules.map((module, index) => (
                  <div className={`module-card p-${module.priority}`} key={module.name}>
                    <div className="module-header">
                      <span className="module-num">M{String(index + 1).padStart(2, "0")}</span>
                      <span className="module-name">{module.name}</span>
                      <div className="module-badges">
                        <span className={`badge priority-${module.priority}`}>{module.priority}</span>
                        <span className={`badge complexity-${module.complexity}`}>{module.complexity} complexity</span>
                      </div>
                    </div>
                    <p className="module-desc">{module.objective}</p>
                    <div className="module-io">
                      <div className="module-io-box">
                        <div className="io-l">Input</div>
                        <div className="io-v">{module.inputs.join(", ")}</div>
                      </div>
                      <div className="module-io-box">
                        <div className="io-l">Output</div>
                        <div className="io-v">{module.outputs.join(", ")}</div>
                      </div>
                    </div>
                    <div className="module-approach">{module.recommended_approach}</div>
                  </div>
                ))}
              </div>
              <div className="result-card">
                <div className="result-card-label">External context</div>
                <div className="questions-list">
                  {functions.external_context.map((item) => (
                    <div className="question-item" key={item.title}>
                      <span className="q-num">CTX</span>
                      <span>
                        <strong>{item.title}</strong> — {item.summary}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="step-action-row">
                <button className="btn-secondary" onClick={() => goToStep(1)}>
                  ← Back to requirements
                </button>
                <button className="btn-primary" onClick={runGenerateDeliverables} disabled={anyLoading}>
                  Generate deliverables
                </button>
              </div>
            </div>
          ) : null}
        </section>

        <section className={`step-section${step !== 3 ? " hidden" : ""}`} id="step-deliverables">
          <div className="step-header">
            <div className="step-tag">Step 03 — Deliverables</div>
            <h2 className="step-title">Consulting outputs</h2>
            <p className="step-sub">Your analysis packaged as a presentation deck and a shareable display card.</p>
          </div>

          {activeAction === "deliverables" ? (
            <div className="loading-block">
              <div className="spinner" />
              <div className="loading-label">Generating deliverables</div>
              <div className="loading-steps">
                <div className={`loading-step${delLoadingStep === 1 ? " active" : delLoadingStep > 1 ? " done" : ""}`}>Generating Agent 3 recommendations</div>
                <div className={`loading-step${delLoadingStep === 2 ? " active" : delLoadingStep > 2 ? " done" : ""}`}>Submitting final QA to Veris</div>
                <div className={`loading-step${delLoadingStep === 3 ? " active" : ""}`}>Packaging consulting outputs</div>
              </div>
            </div>
          ) : null}

          {deliverables ? (
            <div>
              <div className="deliverables-tabs">
                <button className={`del-tab${activeTab === "ppt" ? " active" : ""}`} onClick={() => setActiveTab("ppt")}>
                  Presentation deck
                </button>
                <button className={`del-tab${activeTab === "card" ? " active" : ""}`} onClick={() => setActiveTab("card")}>
                  Display card
                </button>
              </div>

              <div className={`del-panel${activeTab === "ppt" ? " active" : ""}`} id="panel-ppt">
                <div className="ppt-controls">
                  <div className="slide-nav">
                    <button className="slide-btn" onClick={() => setCurrentSlide((value) => Math.max(0, value - 1))} disabled={currentSlide === 0}>
                      ‹
                    </button>
                    <span className="slide-counter">
                      {currentSlide + 1} / {slides.length}
                    </span>
                    <button
                      className="slide-btn"
                      onClick={() => setCurrentSlide((value) => Math.min(slides.length - 1, value + 1))}
                      disabled={currentSlide >= slides.length - 1}
                    >
                      ›
                    </button>
                  </div>
                  <div className="slide-dots">
                    {slides.map((_, index) => (
                      <div
                        className={`slide-dot${index === currentSlide ? " active" : ""}`}
                        key={index}
                        onClick={() => setCurrentSlide(index)}
                      />
                    ))}
                  </div>
                  <button className="btn-secondary btn-icon" onClick={() => window.print()}>
                    Print / Export PDF
                  </button>
                </div>
                <div className="slide-viewport">{activeSlide ? <SlideView slide={activeSlide} index={currentSlide} total={slides.length} /> : null}</div>
              </div>

              <div className={`del-panel${activeTab === "card" ? " active" : ""}`} id="panel-card">
                <div className="display-card-wrapper">
                  <div className="display-card">
                    <div className="dc-header">
                      <div className="dc-brand">Signal2Action</div>
                      <div className="dc-headline">{deliverables.summary_card.headline}</div>
                      <div className="dc-scope">{deliverables.summary_card.scope}</div>
                    </div>
                    <div className="dc-body">
                      <div>
                        <div className="dc-section-label">Functional modules</div>
                        <div className="dc-modules-row">
                          {deliverables.summary_card.modules.map((module) => (
                            <span className="dc-module-tag" key={module}>
                              {module}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <div className="dc-section-label">Key actions</div>
                        <div className="dc-actions-list">
                          {deliverables.summary_card.key_actions.map((action, index) => (
                            <div className="dc-action" key={action}>
                              <span className="dc-action-num">{String(index + 1).padStart(2, "0")}</span>
                              <span>{action}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="dc-footer">
                      <span className="dc-timeline-pill">{deliverables.summary_card.timeline}</span>
                      <span className="dc-event">
                        {simulate ? `QA: ${simulate.simulation_mode} · ${simulate.status}` : "Awaiting QA"}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="output-action-row">
                  <button className="btn-secondary btn-icon" onClick={copyCard}>
                    Copy as text
                  </button>
                </div>
              </div>

              <div className="result-card qa-card">
                <div className="result-card-label">Final QA status</div>
                <div className="qa-summary-row">
                  <span className={`api-status ${simulate?.status === "failed" ? "disabled" : simulate?.status === "passed" ? "live" : "demo"}`}>
                    {simulate?.simulation_mode ?? "not run"}
                  </span>
                  <span className="qa-note">{sponsorUsages.veris?.detail ?? "Veris adapter has not returned metadata yet."}</span>
                </div>
              </div>

              <div className="step-action-row">
                <button className="btn-secondary" onClick={() => goToStep(2)}>
                  ← Back to functions
                </button>
                <button className="btn-primary btn-icon" onClick={resetAll}>
                  New analysis
                </button>
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </>
  );
}

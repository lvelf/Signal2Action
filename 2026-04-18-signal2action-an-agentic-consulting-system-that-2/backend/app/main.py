from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    ClarifyRequest,
    ClarifyResponse,
    IntakeRequest,
    IntakeResponse,
    PlanRequest,
    PlanResponse,
    ReviewRequest,
    ReviewResponse,
    RunDemoRequest,
    RunDemoResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.services.baseten_inference import BasetenInferenceAdapter
from app.services.veris_adapter import VerisAdapter
from app.services.voicerun_adapter import VoiceRunAdapter
from app.services.you_search import YouSearchAdapter
from app.workflow import run_assess, run_clarify, run_demo, run_intake, run_plan, run_review, run_simulation


def create_app() -> FastAPI:
    app = FastAPI(title="Signal2Action API", version="0.1.0")

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin, "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_voice_adapter(config: Settings = Depends(get_settings)) -> VoiceRunAdapter:
        return VoiceRunAdapter(config)

    def get_you_adapter(config: Settings = Depends(get_settings)) -> YouSearchAdapter:
        return YouSearchAdapter(config)

    def get_baseten_adapter(config: Settings = Depends(get_settings)) -> BasetenInferenceAdapter:
        return BasetenInferenceAdapter(config)

    def get_veris_adapter(config: Settings = Depends(get_settings)) -> VerisAdapter:
        return VerisAdapter(config)

    @app.get("/health")
    async def health(config: Settings = Depends(get_settings)) -> dict:
        return {
            "status": "ok",
            "app": config.app_name,
            "environment": config.app_env,
        }

    @app.post("/api/intake", response_model=IntakeResponse)
    async def intake(
        payload: IntakeRequest,
        voice_adapter: VoiceRunAdapter = Depends(get_voice_adapter),
    ) -> IntakeResponse:
        return await run_intake(payload, voice_adapter)

    @app.post("/api/clarify", response_model=ClarifyResponse)
    async def clarify(payload: ClarifyRequest) -> ClarifyResponse:
        return await run_clarify(payload)

    @app.post("/api/review", response_model=ReviewResponse)
    async def review(payload: ReviewRequest) -> ReviewResponse:
        return await run_review(payload)

    @app.post("/api/assess", response_model=AssessmentResponse)
    async def assess(
        payload: AssessmentRequest,
        you_adapter: YouSearchAdapter = Depends(get_you_adapter),
    ) -> AssessmentResponse:
        return await run_assess(payload, you_adapter)

    @app.post("/api/plan", response_model=PlanResponse)
    async def plan(
        payload: PlanRequest,
        baseten_adapter: BasetenInferenceAdapter = Depends(get_baseten_adapter),
    ) -> PlanResponse:
        return await run_plan(payload, baseten_adapter)

    @app.post("/api/run-demo", response_model=RunDemoResponse)
    async def demo(
        payload: RunDemoRequest,
        voice_adapter: VoiceRunAdapter = Depends(get_voice_adapter),
        you_adapter: YouSearchAdapter = Depends(get_you_adapter),
        baseten_adapter: BasetenInferenceAdapter = Depends(get_baseten_adapter),
        veris_adapter: VerisAdapter = Depends(get_veris_adapter),
    ) -> RunDemoResponse:
        return await run_demo(payload, voice_adapter, you_adapter, baseten_adapter, veris_adapter)

    @app.post("/api/simulate", response_model=SimulationResponse)
    async def simulate(
        payload: SimulationRequest,
        veris_adapter: VerisAdapter = Depends(get_veris_adapter),
    ) -> SimulationResponse:
        return await run_simulation(payload, veris_adapter)

    return app


app = create_app()

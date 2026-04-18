from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from app.config import Settings
from app.schemas import SearchContextItem, SponsorToolUsage


@dataclass
class SearchResult:
    items: list[SearchContextItem] = field(default_factory=list)
    tool_usage: SponsorToolUsage | None = None


class YouSearchAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def search(self, query: str, scenario_context: dict | None = None) -> SearchResult:
        if self._use_mock():
            context = scenario_context or {}
            items = [
                SearchContextItem(
                    title=item["title"],
                    summary=item["summary"],
                    source=item["source"],
                )
                for item in context.get("external_context", [])
            ]
            return SearchResult(
                items=items,
                tool_usage=SponsorToolUsage(
                    tool="You.com",
                    mode="mock",
                    detail="Mock search enrichment sourced from local scenario data.",
                ),
            )

        if not self.settings.you_api_key or not self.settings.you_search_endpoint:
            raise RuntimeError("You.com live mode requires YOU_API_KEY and YOU_SEARCH_ENDPOINT.")

        headers = {"X-API-Key": self.settings.you_api_key}
        params = {"query": query}
        # Official Search API: GET /v1/search with X-API-Key auth.
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(self.settings.you_search_endpoint, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        web_results = (data.get("results") or {}).get("web") or []
        news_results = (data.get("results") or {}).get("news") or []
        unified_results = [*web_results, *news_results][:3]

        items = []
        for result in unified_results:
            snippets = result.get("snippets") or []
            items.append(
                SearchContextItem(
                    title=result.get("title", "Untitled result"),
                    summary=snippets[0] if snippets else result.get("description", ""),
                    source=result.get("url", "unknown"),
                )
            )

        return SearchResult(
            items=items,
            tool_usage=SponsorToolUsage(
                tool="You.com",
                mode="live",
                detail="External context enriched with live You.com search results.",
            ),
        )

    def _use_mock(self) -> bool:
        return self.settings.mock_all_services or self.settings.mock_you

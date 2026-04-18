from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from reqANA.agent import RequirementAgent, render_markdown, save_markdown
from reqANA.models import IntakeSource, RequirementInput

load_dotenv(override=True)


def generate_requirement_from_voicerun_text(
    user_text: str,
    source: str = "speech",
) -> tuple[str, str]:
    """Convert VoiceRun text into a requirement document.

    Returns a short spoken summary and the generated Markdown.
    """
    text = user_text.strip()
    if not text:
        raise ValueError("VoiceRun text is empty.")

    document = RequirementAgent().generate(
        [
            RequirementInput(
                source=IntakeSource.VOICERUN,
                content=text,
                metadata={"voice_source": source},
            )
        ]
    )
    markdown = render_markdown(document)
    saved_path = save_markdown(document, Path("outputs"))
    summary = (
        f"I created a requirement document titled {document.title}. "
        f"There are {len(document.open_questions)} open questions and "
        f"{len(document.next_steps)} next steps. "
        f"The Markdown file is saved at {saved_path}."
    )
    return summary, markdown


async def handler(event, context):
    """VoiceRun function entrypoint.

    VoiceRun transcribes speech into TextEvent. Deploy this file's logic in the VoiceRun
    function editor, or adapt the body to your VoiceRun project structure.
    """
    from primfunctions.events import StartEvent, TextEvent, TextToSpeechEvent

    if isinstance(event, StartEvent):
        yield TextToSpeechEvent(
            text="Please describe the consulting requirement. I will turn it into a requirement document.",
            voice="nova",
        )
        return

    if isinstance(event, TextEvent):
        user_text = event.data.get("text", "").strip()
        if not user_text:
            yield TextToSpeechEvent(text="I did not catch that. Please repeat the requirement.", voice="nova")
            return

        summary, markdown = generate_requirement_from_voicerun_text(
            user_text,
            source=event.data.get("source", "speech"),
        )
        context.state["latest_requirement_document"] = markdown
        yield TextToSpeechEvent(text=summary, voice="nova")

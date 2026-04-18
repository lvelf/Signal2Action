# VoiceRun Microphone Test

This tests the real flow:

```text
Browser microphone
  -> VoiceRun speech-to-text
  -> TextEvent
  -> reqANA/Baseten requirement generation
  -> VoiceRun text-to-speech response
```

## 1. Create Or Open A VoiceRun Agent

Go to the VoiceRun dashboard and open your agent.

If you do not have one yet:

1. Create Agent.
2. Add an environment, for example `development`.
3. Create a Function.

## 2. Add Environment Variables

In the VoiceRun environment variables, add:

```text
BASETEN_API_KEY=your_baseten_key
BASETEN_BASE_URL=https://inference.baseten.co/v1
BASETEN_MODEL=deepseek-ai/DeepSeek-V3.1
```

Use the model slug that works in your Baseten account.

## 3. Paste The Handler

For the first microphone test, use the standalone handler:

```text
reqANA/voicerun_standalone_handler.py
```

Copy the file contents into the VoiceRun Function editor.

This standalone version is easier to test in VoiceRun because it does not import the local
`reqANA` package from your laptop.

## 4. Deploy

Click Save, then Deploy Version, and deploy to your environment, for example `development`.

## 5. Open Debugger

Open the VoiceRun Debugger panel.

Click:

```text
Start
```

Your browser should ask for microphone permission. Click:

```text
Allow
```

If the browser does not ask, check:

- Chrome/Safari address bar microphone icon
- Browser site settings
- macOS System Settings -> Privacy & Security -> Microphone
- Make sure your browser has microphone permission

## 6. Speak A Requirement

Say something like:

```text
The client wants a 90-day CRM rollout roadmap. Leads are tracked in spreadsheets.
Sales managers need pipeline visibility by region. Marketing handoff is inconsistent.
The solution must integrate with finance reporting.
```

## 7. What Success Looks Like

In the debugger event log, you should see:

```text
StartEvent
TextEvent
TextToSpeechEvent
```

The `TextEvent` should include:

```json
{
  "source": "speech",
  "text": "The client wants a 90-day CRM rollout roadmap..."
}
```

The agent should speak back something like:

```text
I created a requirement document titled 90-Day CRM Rollout Roadmap...
```

The generated Markdown is stored in VoiceRun session state:

```python
context.get_data("latest_requirement_document")
```

## Common Issues

### No Microphone Prompt

The browser did not grant microphone access.

Fix:

- Use Chrome first.
- Click the lock/microphone icon in the address bar.
- Allow microphone for the VoiceRun site.
- On macOS, allow microphone access for your browser.

### No TextEvent

VoiceRun did not receive speech or speech-to-text did not detect your voice.

Fix:

- Check your input device.
- Speak closer to the microphone.
- Watch the debugger audio/input indicator if available.

### Unauthorized From Baseten

The VoiceRun function cannot call Baseten.

Fix:

- Confirm `BASETEN_API_KEY` is set in the VoiceRun environment, not only in local `.env`.
- Confirm the deployed environment is the same environment where the variables are set.
- Confirm `BASETEN_MODEL` matches your Baseten model slug.


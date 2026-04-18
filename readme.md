# Signal2Action

这是一个 consulting requirement analysis 小项目。核心代码现在集中在 `reqANA/`。

## 项目结构

```text
Signal2Action/
  reqANA/
    agent.py                         需求分析 AI agent
    api.py                           本地 FastAPI 接口
    file_loader.py                   读取 req 文件
    models.py                        数据模型
    transcription.py                 音频文件转写
    voicerun_handler.py              VoiceRun agent function
    integrations/
      veris/
        veris.yaml.example           Veris 配置模板
        Dockerfile.sandbox.example   Veris sandbox Dockerfile 模板
    README.md                        reqANA 模块说明
  examples/
    sample_requirement.txt           测试需求文件
  .env.example                       环境变量模板
  pyproject.toml                     Python 依赖
```

## 这几个 API 分别做什么

- `POST /requirements/from-text`: 输入文字需求，生成需求文档
- `POST /requirements/from-file`: 上传一个或多个 `.txt/.md/.csv/.json/.yaml/.yml/.tsv/.xlsx/.xlsm` 文件
- `POST /requirements/from-voice`: 上传音频文件，先转写，再生成需求文档
- `POST /requirements/from-mixed`: 同时输入文字、文件、音频
- `POST /veris/requirement-agent`: 给 Veris simulation 用的简单入口

## 第一步：本地运行

在项目根目录运行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

编辑 `.env`，如果你现在用 Baseten 做模型 API，至少填这些：

```bash
MODEL_PROVIDER=baseten
BASETEN_API_KEY=your_baseten_key
BASETEN_BASE_URL=https://inference.baseten.co/v1
BASETEN_MODEL=deepseek-ai/DeepSeek-V3.1
```

如果你暂时不用本地音频文件上传，只用 VoiceRun 实时语音，那么不需要配置本地 STT。
如果你要调用 `POST /requirements/from-voice` 上传 `.m4a/.wav/.mp3` 文件，目前还需要：

```bash
OPENAI_API_KEY=your_openai_key_for_transcription
OPENAI_TRANSCRIBE_MODEL=gpt-4o-mini-transcribe
```

启动服务：

```bash
uvicorn reqANA.api:app --reload
```

打开浏览器：

```text
http://127.0.0.1:8000/docs
```

先点 `GET /health` 测试，应该返回：

```json
{"status":"ok"}
```

## 第二步：测试 requirement analysis

### 文字输入

```bash
curl -X POST http://127.0.0.1:8000/requirements/from-text \
  -H "Content-Type: application/json" \
  -d '{"content":"Client wants a 90-day CRM rollout roadmap. Sales leads are currently tracked in spreadsheets."}'
```

### 文件输入

```bash
curl -X POST http://127.0.0.1:8000/requirements/from-file \
  -F "files=@examples/sample_requirement.txt"
```

### 多文件输入

```bash
curl -X POST http://127.0.0.1:8000/requirements/from-file \
  -F "files=@examples/sample_requirement.txt" \
  -F "files=@requirements.xlsx"
```

### 音频文件输入

```bash
curl -X POST http://127.0.0.1:8000/requirements/from-voice \
  -F "audio=@meeting-notes.m4a" \
  -F "context=This is a consulting discovery call."
```

注意：这个接口是“上传音频文件 -> 转写 -> 分析需求”。当前转写用 OpenAI STT。
如果你走 VoiceRun 实时语音，VoiceRun 会直接把语音转成 `TextEvent`，不经过这个接口。

输出会包含 JSON 结构和 Markdown。Markdown 文件会保存到 `outputs/`。

## 第三步：使用 VoiceRun API

这里有两种用法。

### A. 在 VoiceRun 里部署 voice agent

这是最适合你“语音输入分析 consulting requirement”的方式。

1. 登录 VoiceRun / Prim Voices dashboard。
2. Create Agent。
3. Add Environment，比如 `development`。
4. Create Function。
5. 把 `reqANA/voicerun_handler.py` 的 handler 逻辑放进去。
6. 在 VoiceRun 的 environment variables 里设置：

```text
MODEL_PROVIDER=baseten
BASETEN_API_KEY=your_baseten_key
BASETEN_MODEL=deepseek-ai/DeepSeek-V3.1
```

7. Deploy Version。
8. 在 Debugger 里点 Start，然后直接说需求。

VoiceRun 会把你说的话转成 `TextEvent`，我们的代码读取：

```python
event.data.get("text")
```

然后调用 `RequirementAgent` 生成需求文档。

### B. 用 VoiceRun API 发起电话会话

如果你的 VoiceRun API key 是用来发起 outbound call，可以调用：

```bash
curl 'https://api.primvoices.com/v1/agents/<AGENT_ID>/sessions/start' \
  -X 'POST' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <VOICERUN_API_KEY>' \
  --data-raw '{
    "inputType": "phone",
    "inputParameters": {
      "phoneNumber": "+15555555555"
    },
    "environment": "development",
    "parameters": {
      "purpose": "consulting_requirement_analysis"
    }
  }'
```

`parameters` 里的值可以在 VoiceRun handler 里通过 `context.get_data("purpose")` 读取。

## 第四步：接入 Veris

Veris 不是 GPT 替代品。它更像一个 agent simulation / evaluation sandbox：

- GPT/OpenAI 仍然负责生成需求文档。
- Veris 负责模拟用户、跑场景、测试你的 agent 是否稳定。
- 你的 agent 需要暴露 HTTP 或 WebSocket 入口。

我们已经加了一个 Veris 专用 HTTP 入口：

```text
POST /veris/requirement-agent
```

输入：

```json
{"message":"We need a CRM rollout requirement analysis."}
```

输出：

```json
{"response":"# Requirement Document ..."}
```

### Veris 接入步骤

安装 Veris CLI：

```bash
pip install veris-cli
```

登录：

```bash
veris login YOUR_VERIS_API_KEY
```

创建 Veris environment：

```bash
veris env create --name "reqANA"
```

Veris 会生成 `.veris/` 文件夹。然后把模板内容复制进去：

```bash
cp reqANA/integrations/veris/veris.yaml.example .veris/veris.yaml
cp reqANA/integrations/veris/Dockerfile.sandbox.example .veris/Dockerfile.sandbox
```

把 Baseten key 设置成 Veris secret：

```bash
veris env vars set MODEL_PROVIDER=baseten
veris env vars set BASETEN_API_KEY=your_baseten_key --secret
veris env vars set BASETEN_BASE_URL=https://inference.baseten.co/v1
veris env vars set BASETEN_MODEL=deepseek-ai/DeepSeek-V3.1
```

推送 agent：

```bash
veris env push
```

生成测试场景：

```bash
veris scenarios create
```

运行 simulation/evaluation/report：

```bash
veris run
```

## 推荐理解顺序

1. 先跑本地 API：`uvicorn reqANA.api:app --reload`
2. 用 `/requirements/from-text` 确认 GPT 能生成需求文档
3. 用 `/requirements/from-voice` 测试音频文件输入
4. 把 `reqANA/voicerun_handler.py` 放到 VoiceRun function
5. 用 VoiceRun Debugger 说一段需求
6. 最后再用 Veris 跑 simulation，看 agent 表现是否稳定

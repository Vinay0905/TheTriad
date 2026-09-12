# TriadCouncil: LangGraph Multi-Agent Software Team

TriadCouncil is an autonomous multi-agent software engineering system built natively on **LangGraph (0.2+)** and **LangChain**. It models a 5-role engineering department featuring cross-model tournaments, adversarial QA red-teaming, and an **immutable Human Confirmation Gate** before any code is executed.

---

## The Council Roles & Model Specializations

| Role | Model / Provider | Purpose | Cost |
| :--- | :--- | :--- | :--- |
| **Manager** | **Anthropic / DeepSeek** via OpenRouter | High-level scoping, RFC authoring, pre-flight gate, final reporting. | Pay-as-you-go |
| **Researcher** | **Google Gemini 2.5 Flash** (Google Search Grounding) | Live web search grounding, API deprecation detection, library audits. | **Free Tier** |
| **QA & Security Red-Teamer**| **ZhipuAI GLM-4-Flash** (30B MoE) | Adversarial FMEA audit, injection vulnerability detection, negative tests. | **100% Free** |
| **Junior Dev 1** | **Meta Llama 3.1 8B** via Groq | Fast synthesis of **Candidate A** (Lean / StdLib / Direct). | **Free Tier** |
| **Junior Dev 2 (Co-Dev)**| **ZhipuAI GLM-4-Flash** (30B MoE) | Independent synthesis of **Candidate B** (Modular / Robust / Defensive). | **100% Free** |
| **Senior Dev** | **Google Antigravity SDK** (Gemini) | TDD contract author, tournament judge, hybrid synthesizer, and sandboxed executor. | Shared with Gemini Key |

---

## How to Get Your API Keys & Configure `.env`

> [!TIP]
> For detailed, click-by-click instructions with screenshots and direct portal links, read **[KEYS_SETUP_GUIDE.md](KEYS_SETUP_GUIDE.md)**!

Copy `.env.example` to create your local `.env`:

```bash
cp .env.example .env
```

### 1. OpenRouter API Key (`OPENROUTER_API_KEY`)
- **For**: Manager role.
- **Get it**: [https://openrouter.ai/keys](https://openrouter.ai/keys)

### 2. Google Gemini API Key (`GEMINI_API_KEY`)
- **For**: Researcher (Google Search Grounding) & Senior Dev (Antigravity SDK).
- **Get it**: [https://aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys) *(Free tier available)*

### 3. Groq API Key (`GROQ_API_KEY`)
- **For**: Junior Dev 1 (Candidate A drafting on fast LPUs).
- **Get it**: [https://console.groq.com/keys](https://console.groq.com/keys) *(Free tier available)*

### 4. ZhipuAI GLM-4-Flash Keys (`ZHIPUAI_DEV_API_KEY` & `ZHIPUAI_QA_API_KEY`)
- **For**: Junior Dev 2 (Candidate B) & Dedicated QA Red-Teamer.
- **Get it**: [https://bigmodel.cn](https://bigmodel.cn)
  1. Register for an account.
  2. Navigate to API Keys.
  3. You can generate two keys (one for `ZHIPUAI_DEV_API_KEY` and one for `ZHIPUAI_QA_API_KEY`) to isolate rate limits.
- **Cost**: **Permanently 100% Free** for GLM-4-Flash!

---

## Running the System

### 1. Run Automated Unit & Integration Tests
```bash
python3 -m pytest tests/ -v
```

### 2. Run the LangGraph CLI
```bash
python3 -m ai_team.cli "Build a Python function that converts CSV to JSON with row validation"
```
1. Watch the nodes stream live: Manager RFC, Researcher Grounding, GLM-4-Flash QA Red-Teaming, TDD Contract, and the Cross-Model Tournament between Groq (Candidate A) and GLM-4-Flash (Candidate B).
2. The graph pauses cleanly at the **Human Steering Gate (`interrupt`)**.
3. Enter `y` to approve and run inside the isolated sandbox, or `n` to abort cleanly.
# TheTriad

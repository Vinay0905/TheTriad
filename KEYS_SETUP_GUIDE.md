# API Keys Setup Guide for TriadCouncil

This guide walks you click-by-click through getting every API key needed for your multi-agent system and putting them in the right place.

---

## Quick Summary of Required Keys

| Key Variable Name | Role in AI Team | Provider | Cost | Direct Link |
| :--- | :--- | :--- | :--- | :--- |
| **`OPENROUTER_API_KEY`** | **Manager** (Planning & Scope) | OpenRouter | Pay-as-you-go | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **`GEMINI_API_KEY`** | **Researcher** (Search) & **Senior Dev** (Antigravity) | Google AI Studio | **Free Tier** | [aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys) |
| **`GROQ_API_KEY`** | **Junior Dev 1** (Candidate A) | Groq | **Free Tier** | [console.groq.com/keys](https://console.groq.com/keys) |
| **`ZHIPUAI_DEV_API_KEY`** | **Junior Dev 2** (Candidate B) | ZhipuAI (GLM-4-Flash) | **100% Free** | [bigmodel.cn/usercenter/apikeys](https://bigmodel.cn/usercenter/apikeys) |
| **`ZHIPUAI_QA_API_KEY`** | **QA & Security Red-Teamer** | ZhipuAI (GLM-4-Flash) | **100% Free** | [bigmodel.cn/usercenter/apikeys](https://bigmodel.cn/usercenter/apikeys) |

---

## Step 1: Create Your Local `.env` File

In your project directory (`TriadCouncil`), run this command in your terminal to create your `.env` file from the template:

```bash
cp .env.example .env
```

Now open the `.env` file in your editor (VS Code, Cursor, or your favorite text editor). This is where you will paste the keys you get below.

---

## Step 2: Get Each API Key (Step-by-Step)

### 1. Google Gemini API Key (`GEMINI_API_KEY`)
> **Note**: This single key powers **both** the Researcher (Google Search Grounding) and the Senior Dev (Google Antigravity SDK).

1. Open your browser and go to: **[https://aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys)**
2. Sign in with your standard Google account.
3. Click the blue button that says **"Create API key"** (or "Get API key").
4. Select **"Create API key in new project"** (or select an existing Google Cloud project if prompted).
5. A box will appear showing your new key (starts with `AIzaSy...`). Click **Copy**.
6. In your `.env` file, find the line for `GEMINI_API_KEY` and paste it:
   ```bash
   GEMINI_API_KEY=AIzaSyYourCopiedKeyHere
   ```

---

### 2. Groq API Key (`GROQ_API_KEY`)
> **Note**: Powers Junior Dev 1 for blazing-fast code drafting on LPU hardware.

1. Open your browser and go to: **[https://console.groq.com/keys](https://console.groq.com/keys)**
2. Sign in using your Google account, GitHub account, or email.
3. Click on **"API Keys"** in the left sidebar menu.
4. Click the orange/black button: **"Create API Key"**.
5. Type a name (for example: `triad-council`), then click **Submit**.
6. Copy the key (starts with `gsk_...`). *(Make sure to copy it now, as it won't be shown again).*
7. In your `.env` file, find the line for `GROQ_API_KEY` and paste it:
   ```bash
   GROQ_API_KEY=gsk_YourCopiedKeyHere
   ```

---

### 3. OpenRouter API Key (`OPENROUTER_API_KEY`)
> **Note**: Powers the Manager for frontier reasoning models (Claude 3.5 Sonnet / DeepSeek).

1. Open your browser and go to: **[https://openrouter.ai/keys](https://openrouter.ai/keys)**
2. Sign in with Google or GitHub.
3. Click the blue button: **"Create Key"**.
4. Enter a name (for example: `triad-manager`).
5. Set credit limit to blank or leave default, then click **Create**.
6. Copy the key shown (starts with `sk-or-v1-...`).
7. In your `.env` file, find the line for `OPENROUTER_API_KEY` and paste it:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-YourCopiedKeyHere
   ```

---

### 4. ZhipuAI GLM-4-Flash Keys (`ZHIPUAI_DEV_API_KEY` & `ZHIPUAI_QA_API_KEY`)
> **Note**: GLM-4-Flash is **permanently 100% free**. We create two keys so the Coder (Junior Dev 2) and the QA Red-Teamer never hit rate limits against each other.

1. Open your browser and go to: **[https://bigmodel.cn/usercenter/apikeys](https://bigmodel.cn/usercenter/apikeys)**
   *(Or the international portal at [https://z.ai](https://z.ai) if you prefer English).*
2. Sign up / log in with your phone or email.
3. Navigate to **"API Keys"** (or **API 密钥** in the user center).
4. Click **"创建 API Key"** (Create API Key).
   - Name the first key: `triad-dev` and click confirm. Copy the key.
   - Click Create API Key again, name the second key: `triad-qa` and click confirm. Copy the second key.
5. In your `.env` file, paste both keys:
   ```bash
   ZHIPUAI_DEV_API_KEY=your_first_glm_key_here
   ZHIPUAI_QA_API_KEY=your_second_glm_key_here
   ```
   *(If you only created one key, you can just paste the same key into both lines or set `ZHIPUAI_API_KEY=your_key`, and the system will automatically use it for both!)*

---

## Step 3: What Your Final `.env` Should Look Like

After following the steps above, your `.env` file should look like this:

```bash
# OpenRouter (Manager Role)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Google Gemini (Researcher & Senior Dev Roles)
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_RESEARCHER_MODEL=gemini-2.5-flash

# Groq (Junior Dev 1 - Candidate A)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.1-8b-instant

# ZhipuAI GLM-4-Flash (Junior Dev 2 & QA Red-Teamer - 100% Free)
ZHIPUAI_DEV_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxx
ZHIPUAI_QA_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxx
GLM_MODEL=glm-4-flash

# Operational Settings
AI_TEAM_RUNS_DIR=.runs
AI_TEAM_EXECUTION_TIMEOUT_SECONDS=120
AI_TEAM_MAX_RETRY_ATTEMPTS=3
```

---

## Step 4: Verify Your Configuration

Once your `.env` is saved, you can run this quick one-liner in your terminal to verify that your environment loads all keys properly:

```bash
python3 -c "from ai_team.config import get_config; c = get_config(); print('Gemini Key:', bool(c.gemini_api_key)); print('Groq Key:', bool(c.groq_api_key)); print('OpenRouter Key:', bool(c.openrouter_api_key)); print('GLM Dev Key:', bool(c.zhipuai_dev_api_key)); print('GLM QA Key:', bool(c.zhipuai_qa_api_key))"
```

If it prints `True` for all keys, you are 100% ready to run live multi-agent tasks!

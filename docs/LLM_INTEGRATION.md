# LLM Integration — CORTEX-C2 × OpenRouter

**Version:** 1.0.0  
**Module:** `frontend/cortex_c2.html` — LLM Analysis Panel  
**Gateway:** [OpenRouter](https://openrouter.ai) — multi-LLM API  
**Status:** Implemented, secured via backend proxy (`agent_backend.py`)

---

## 1. Purpose & Architecture

The CORTEX-C2 LLM integration brings a generative AI layer on top of the deterministic CORTEX-1 COA engine. While CORTEX-1 computes mathematically optimal Weapon-Target Assignments (WTA) and generates three Courses of Action (COA), the LLM layer provides:

- Human-readable, military-doctrinal **tactical narrative**
- **Risk articulation** that the WTA utility score cannot express
- **Commander's recommendation** in plain language
- **Follow-on threat anticipation** beyond the current picture
- **Strategic Audit Analysis** — interpreting Monte Carlo 200-iteration survival and intercept probabilities
- A second opinion to cross-check the algorithmic output

The integration uses **OpenRouter** as the API gateway, which provides a single unified endpoint (`https://openrouter.ai/api/v1/chat/completions`) compatible with the OpenAI chat completions specification, routing to any of 100+ frontier models.

```
Operator loads scenario
        ↓
CORTEX-1 COA Engine (deterministic WTA + MCTS)
        ↓
Strategic Audit (200-iteration Monte Carlo rollout) — Survival % / Intercept %
        ↓
buildTacticalPrompt() — assembles scenario + MC metrics + COA + inventory
        ↓
Internal Proxy (/llm/proxy) → uses server-side OPENROUTER_API_KEY
        ↓
OpenRouter API → selected LLM model (streaming SSE)
        ↓
Streaming tokens → #llm-body (with typewriter cursor animation)
        ↓
Final text rendered → token count + elapsed time displayed
        ↓
Summary echoed to AI Commentary feed
```

---

## 2. Supported Models

| Model ID | Label | Best Use |
|---|---|---|
| `anthropic/claude-3.5-sonnet` | Claude 3.5 Sonnet | Best overall military reasoning, nuanced risk assessment |
| `anthropic/claude-3-haiku` | Claude 3 Haiku (fast) | Speed-optimised, good for rapid scenario refresh |
| `openai/gpt-4o` | GPT-4o | Strong structured output, good at military doctrine |
| `openai/gpt-4o-mini` | GPT-4o mini | Cost-optimised, suitable for demo |
| `google/gemini-pro-1.5` | Gemini Pro 1.5 | Very long context, good for multi-scenario reasoning |
| `mistralai/mistral-large` | Mistral Large | Strong reasoning, European privacy compliance |
| `meta-llama/llama-3.1-70b-instruct` | Llama 3.1 70B | Open-weight option for air-gapped / sovereign deployments |

**Recommended for production:** `anthropic/claude-3.5-sonnet` — consistent military tone, avoids hedging, precise about Pk values and follow-on risk.

---

## 3. API Key Setup

### 3.1 Server-Side Configuration

1. Go to [https://openrouter.ai](https://openrouter.ai) and create an account.
2. Navigate to **Keys** → **Create key** and copy it (starts with `sk-or-v1-`).
3. Set the environment variable in your local launcher script:
   - **Windows:** Edit `scripts/run_local_windows.ps1` and update the `$env:OPENROUTER_API_KEY` line.
   - **Manual:** Set it in your current terminal session:
     ```powershell
     $env:OPENROUTER_API_KEY="sk-or-v1-..."
     ```
4. Restart the system using `scripts/run_local_windows.ps1`. The backend will log `[SYSTEM] OpenRouter API Key detected` on startup.

### 3.2 Security Model (V2.0)

| Property | Detail |
|---|---|
| Storage | **Environment Variable** — Key never touches the browser or `localStorage` |
| Transmission | Browser calls `/llm/proxy`; Backend appends key and forwards to OpenRouter |
| Visibility | UI shows "Secure Backend Integration Active" — no input field for keys |
| Server-side | Managed via `httpx.stream` for secure, memory-efficient token forwarding |
| Benefit | **Production-ready.** Protects your API budget from client-side scraping. |

---

## 4. Prompt Engineering

### 4.1 System Prompt

```
You are CORTEX-1, a NATO-standard Command & Control AI tactical advisor
embedded in the CORTEX-C2 operator console. Be concise and precise.
```

The system prompt keeps the LLM in role as a military C2 advisor, preventing off-topic responses and encouraging precise, doctrine-aligned language.

### 4.2 User Prompt Structure

`buildTacticalPrompt(sc, m, coas)` constructs a structured context block with the following sections:

```
=== CURRENT TACTICAL PICTURE ===
Scenario: <title>
Theater: <BOREAL|SWEDEN>  | Command Mode: <AUTO|HITL|MANUAL>
SA-Health: <N>% → Autonomy Mode: <AUTONOMOUS|ADVISE|DEFER>
Track Count: <N> total (real / decoy / ghost)
Threat Types: <Nx TYPE, ...>
Jamming: <YES / No>
Complexity Index: <0.0–1.0>  | Stakes Index: <0.0–1.0>  | TQI: <0.0–1.0>
Total Inbound Value: <N>
MC Survival Prob: <N>% | MC Intercept Prob: <N>% | Mean Leaked: <N>

=== RECOMMENDED COA (COA-1) ===
Utility: <N>  | Coverage: <N>%  | Follow-on Risk: <0.0–1.0>
Engagements: <N>
  - <BaseName> [<ID>] fires <Effector> at <ThreatID> (<Type>) → Pk <0.XX>
  ...

=== THEATER INVENTORY (<THEATER>) ===
  <ID> <Name>: HP <N>% | SAM <N>/<max> | <operational|DESTROYED>
  ...
```

The user prompt then instructs the LLM to produce a **6-section military assessment**:

1. **SITUATION SUMMARY** — threat picture in 1–2 sentences
2. **KEY RISKS** — top 2 risks
3. **COA-1 ASSESSMENT** — evaluate the recommended COA
4. **ALTERNATIVE CONSIDERATION** — what COA-2 or COA-3 does better
5. **COMMANDER'S RECOMMENDATION** — single recommended action with rationale
6. **FOLLOW-ON THREAT ASSESSMENT** — likely next-wave composition

### 4.3 Prompt Design Decisions

- **200–280 word target** — long enough to be substantive, short enough to stream quickly
- **Pk values included** — grounds the LLM in the actual engagement probabilities rather than speculation
- **Inventory state included** — allows LLM to flag low-stock bases and advise conservation
- **COA-1, COA-2, COA-3 fingerprints included** — enables comparative COA analysis
- **Jamming flag explicit** — prevents LLM from ignoring the DEFER-mode trigger conditions
- `temperature: 0.35` — low enough for consistent, precise output; not zero (avoids robotic repetition)
- `max_tokens: 600` — generous budget for the 6-section format; typically uses 350–500

---

## 5. Streaming Implementation

The integration uses the OpenAI-compatible streaming API via **Server-Sent Events (SSE)**.

### 5.1 Request

```javascript
fetch('/llm/proxy', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: selectedModel,
    stream: true,
    max_tokens: 600,
    temperature: 0.35,
    messages: [systemMessage, userMessage],
  }),
})
```

The `HTTP-Referer` and `X-Title` headers (identifying CORTEX-C2) are now appended by the backend proxy for usage attribution; they are advisory and do not affect API behaviour.

### 5.2 SSE Parsing

Each chunk is decoded, split on newlines, and filtered for `data: ` prefixes:

```javascript
const reader  = response.body.getReader();
const decoder = new TextDecoder('utf-8');
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value, { stream: true });
  for (const line of chunk.split('\n').filter(l => l.startsWith('data: '))) {
    const raw = line.slice(6).trim();
    if (raw === '[DONE]') continue;
    const delta = JSON.parse(raw)?.choices?.[0]?.delta?.content || '';
    // append to DOM
  }
}
```

The `{ stream: true }` option on `TextDecoder.decode()` handles partial multi-byte UTF-8 sequences across chunk boundaries.

### 5.3 Visual Feedback

| State | Dot colour | Button text |
|---|---|---|
| Idle | Grey | ▶ ANALYSE |
| Streaming | Blue pulsing | ● THINKING… (disabled) |
| Complete | Green | ▶ ANALYSE (re-enabled) |
| Error | Grey | ▶ ANALYSE (re-enabled) |

A CSS blinking cursor is appended during streaming and removed on completion.

### 5.4 Token Counter

A client-side approximation counts tokens by splitting streamed text on whitespace. Displayed as `~N tokens · X.Xs`. This is an estimate — actual billing uses the model's tokenizer.

---

## 6. Error Handling

| HTTP Status | User message |
|---|---|
| 401 | ⚠ Invalid API key — check your OpenRouter key and try again |
| 402 | ⚠ OpenRouter credits exhausted — top up at openrouter.ai |
| 429 | ⚠ Rate limited — wait a moment and retry |
| Any other | ⚠ Error: `<truncated message>` |

Network errors (e.g., offline, CORS) surface the raw error message truncated to 120 characters.

All errors are also echoed as `[warn]` lines in the AI Commentary feed for the operator log.

---

## 7. Integration with CORTEX-1

The LLM is deliberately **subordinate** to the deterministic CORTEX-1 engine:

- CORTEX-1 always runs first on scenario load
- The LLM assessment is **triggered manually** (click ANALYSE) — never runs automatically without the key saved
- The LLM cannot modify assignments, inventory, or COA weights — it is read-only
- The LLM output is displayed in a separate panel and echoed to the commentary log
- The CORTEX-1 HITL approval queue still requires commander action regardless of LLM advice

This separation ensures the LLM layer supplements but never replaces the deterministic WTA optimiser, matching NATO STANAG doctrine on human-machine teaming for kinetic engagement authority.

---

## 8. Scenario-Level Test Results

> **Note:** To reproduce these results, a valid OpenRouter API key with sufficient credits is required. The outputs below are representative of typical model responses; LLM outputs are non-deterministic.

### 8.1 Scenario: Clean Picture (3 BALLISTIC, SA=82%, AUTONOMOUS)

**Expected LLM behaviour:**
- Should confirm AUTONOMOUS mode is appropriate
- Should validate PAC-3 selection for BALLISTIC threats (Pk 0.95)
- Should note low follow-on risk (0.05) from RECOMMENDED COA
- Should identify Reserve Conserving as viable if a follow-on wave is anticipated

**Claude 3.5 Sonnet sample (condensed):**
```
SITUATION SUMMARY — Three inbound BALLISTIC track(s) converging on northern HVAs.
Clean picture, high TQI (1.00), no EW degradation. Autonomy envelope met.

KEY RISKS — (1) All three engagements rely on PAC-3; sequential failures compound leak
probability. (2) No THAAD salvos reserved — a simultaneous follow-on wave would face
reduced high-tier coverage.

COA-1 ASSESSMENT — RECOMMENDED is optimal for this picture. PAC-3 Pk 0.95 across all
three threats delivers expected 99.97% intercept probability at acceptable cost. Coverage
100%.

ALTERNATIVE CONSIDERATION — RISK MINIMISING (COA-3) substitutes THAAD at Arktholm and
Highridge (Pk 0.98 each) at higher missile cost, reducing follow-on risk to 0.03.
Warranted if intel suggests follow-on wave within 30 minutes.

COMMANDER'S RECOMMENDATION — Execute RECOMMENDED COA immediately. Probability of
simultaneous intercept failure is <0.01%. Retain THAAD reserve at Arktholm for follow-on.

FOLLOW-ON THREAT ASSESSMENT — High-stakes scenario (value 240) suggests priority target
set. Likely follow-on: cruise or hypersonic barrage targeting Arktholm (ARK HVA).
Recommend activating reserve NASAMS at Gotland pre-emptively.
```

### 8.2 Scenario: Swarm + Fast-Mover (SA=76%, ADVISE)

**Expected LLM behaviour:**
- Should acknowledge complexity (0.66) driving ADVISE mode
- Should note ghost track ambiguity as a risk factor
- Should discuss C-RAM / HELWS for drone saturation
- Should flag FIGHTER+HYPERSONIC combination as priority vs. drone swarm

**Key difference from clean scenario:** LLM should express more uncertainty, flag the ghost track G01, and recommend the commander retain decision authority consistent with ADVISE mode.

### 8.3 Scenario: Jammed Sensors (SA=46%, DEFER)

**Expected LLM behaviour:**
- Should explicitly explain why DEFER mode is correct (SA=46%, jamming active)
- Should warn against firing on degraded track data (decoy risk)
- Should recommend cueing additional off-platform sensors before engagement
- Should note hypersonic track H01 as highest priority once track quality improves

**Key LLM value here:** The LLM can articulate *why* deferring is correct in language a commander can understand, which the SA-Health number alone does not convey.

---

## 9. Known Limitations

| Limitation | Notes |
|---|---|
| Proxy Architecture | COMPLETED — Keys managed via `agent_backend.py` environment variables |
| No RAG / doctrine database | LLM draws on training data, not a live military doctrine corpus |
| Hallucination risk | LLM may occasionally fabricate threat classifications or doctrine citations — always cross-check with CORTEX-1 output |
| Context window | Prompt ~400 tokens; well within all listed model limits (32K–200K) |
| Non-streaming fallback | No fallback if SSE is blocked by a proxy; add `stream:false` fallback for restricted networks |
| Rate limits | OpenRouter free tier: 200 requests/day. Paid tier: model-specific rate limits apply |

---

## 10. Future Enhancements

- **Persistent conversation context** — multi-turn LLM dialogue for drill-down questions ("What if we only had NASAMS?")
- **RAG overlay** — ground LLM output against STANAG 2044 / ATP-3.3.1 doctrine corpus
- **Scenario comparison** — ask LLM to compare before/after inventory replenishment impacts
- **Audio output** — text-to-speech TTS API call for hands-free operator briefings
- **Fine-tuning** — fine-tune on historical C2 engagement logs for domain-specific accuracy

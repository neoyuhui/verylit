# CLAUDE.md
*Project instructions for Claude Code (and any teammate) working in this repository.*
*Status: DRAFT v0.2 — several items below are still open. See "Open questions" at the bottom.*

## What this project is

A Chrome extension + lightweight backend built for a legal-tech hackathon (Problem Statement 4 — Min Law), scoped to a 1.5-day build. It helps self-represented persons (SRPs) prepare a case for Singapore's Small Claims Tribunals (SCT) by turning their raw, informal account of a dispute into an organised, fact-checked, bias-flagged record — without ever practising law. It must comply in spirit with the Singapore Courts' Guide on the Use of Generative AI Tools by Court Users.

**Current build target: Feature 1 (Issue Distillation), sequenced after a minimal Feature 2 (eligibility checklist).** Decided: Issue Distillation runs *after* the eligibility checklist, not before — see "Feature roadmap" for why this creates a small but real build-order dependency for the demo. Feature 3 and full Feature 4 remain roadmap-only — don't build beyond what's specified for Feature 1 below unless asked.

---

## Hard rules — apply to every prompt, every endpoint, every line of generated code

These are non-negotiable. If a task conflicts with one of these, stop and flag it instead of finding a workaround.

**Reformat, never classify (decided, not a style choice):** This tool restates the user's own account — what they said, what's missing, what to gather. It never labels the dispute with a legal category ("this is a breach of contract," "this is a defective-goods claim"). A wrong *fact* or *gap* is self-correcting — the user can just add the missing detail. A wrong *classification* is not: the user has no independent way to check it, and may act on a false sense of confidence or chase the wrong evidence entirely. That asymmetry is why classification is out, permanently, not just for this MVP.

**Never:**
- State or imply a claim is valid, invalid, strong, weak, will win, or will lose.
- Give legal advice, a legal strategy, or cite a legal test as settled fact.
- Assign the dispute a legal category or cause of action, even a tentative or hedged one.
- Invent: court deadlines, filing fees, claim limits, jurisdictional rules, required documents, ACRA information, enforcement procedures, case outcomes, names/addresses, or any fact the user did not supply.
- Fabricate, alter, embellish, or strengthen evidence. Never coach the user to omit unfavourable facts or mislead the tribunal.
- Let one AI response "verify" another AI response.
- Persist or submit anything as final without explicit user confirmation.

**Always:**
- Use hedged, procedural language — "this may be relevant to check," "you may need to confirm," "a legal adviser or official source may need to confirm this."
- Separate what the user *stated* from what the user *assumed or inferred*.
- Ask one or two clarifying questions at a time — this is a structured interview, not a one-shot Q&A dump.
- Point to an official source (Singapore Courts / CJTS / ACRA / Singapore Statutes Online) or say plainly that verified information isn't available: *"I do not have enough verified information to answer that confidently. Please check the current Singapore Courts or CJTS guidance, or obtain appropriate legal help."*
- Preserve evidence, don't solicit it — when telling a user to gather messages, they collect what already exists; never draft a message designed to bait an admission out of the other party.
- Carry a compliance/disclaimer notice on every substantive output.

If a user asks for fake evidence, refuse briefly and redirect to organising real evidence.

---

## Repo layout (proposed — scaffold this if it doesn't exist yet)

```
extension/          Chrome extension, Manifest V3 (popup or side panel UI + background worker) — not built yet
extension/shared/distillation-reference.js  Storage + reference-panel rendering for Feature 1 output (implemented)
backend/main.py      FastAPI wrapper around the Anthropic API (implemented, tested)
backend/llm_client.py Provider-agnostic LLM call (direct Anthropic or OpenRouter) (implemented, tested)
backend/guardrails.py Regex-based post-generation leakage scanner (implemented, tested)
backend/static/index.html  Same-origin test-chat page for Feature 1 — NOT the extension UI, just a fast way to run and click through the feature today (implemented, tested)
docs/prompts/        One markdown file per system prompt, versioned, loaded at runtime
                      — not hardcoded as Python string literals
docs/sources.md       Running list of verified official links (claim limits, fees, forms)
                      — the only place fee/limit numbers may be copied from
```

Right now only a `main.py` and `README.md` snippet exist as pasted text — no repo has actually been scaffolded. Treat the layout above as the target structure.

---

## Feature roadmap

1. **Issue Distillation** (build now) — turn one free-text or voice account into a structured, bias-flagged problem statement. Runs **after** the eligibility checklist (Feature 2) confirms SCT looks like the right forum. Prompt lives at `docs/prompts/issue-distillation.md` (paste in verbatim from the team's planning doc). Treat its "gap test," "no conclusions," and "reformat-not-classify" rules as testable invariants, not style guidance.
2. **Pre-filing eligibility checklist** (Feature 2 — **now a build dependency for the demo, not just roadmap**) — the parties/jurisdiction/service branching questions: individual vs corporate claimant/respondent, ACRA/liquidation checks, motor-vehicle damage exclusion, 31 Oct 2018 cut-off, service-in-Singapore branch. This is pure decision-tree logic — no model call needed — which keeps it cheap relative to Feature 1, but it still needs a UI and needs to exist for the demo to flow start-to-finish as intended. If time runs short, fall back to demoing the two screens independently (checklist and distillation shown separately, not hard-gated) rather than skipping the checklist UI silently.
3. **Structured interview** (Feature 3, later) — full order: jurisdiction → procedural stage → issue category → claimant identity → respondent identity → chronology → remedy → evidence → gaps → review. One or two questions at a time.
4. **Voice input** (Feature 4, later) — Audio → transcription (shown, editable) → user correction → structured summary → user confirmation → optional draft form wording. A transcription must never reach the model, or reach storage, before the user has had a chance to edit it.

---

## Feature 1 spec — Issue Distillation

**Input:** one free-text message (may originate from voice transcription later; treat as plain text for now). Treat all of it as the user's account, never as established fact — expect typos, emotion, second-hand statements, and unstated assumptions.

**Length cap — decided: Moderate tier.** Soft target ~500 words / ~3,000 characters (live counter, gentle nudge, no block); hard ceiling ~1,000 words / ~6,000 characters (safety net against an accidental full-thread paste, not the expected normal limit).

**Output:** prose, one section per distinct factual/procedural matter, each with, in this order: *Facts as stated → Gap → Steps*. No sub-headings, no bullet points inside a section. Followed by two closing blocks: *Inferences detected* (quote the user's own words, name the assumption, ask what supports it or note it should be left out) and *Facts still needed* (one sentence).

**Rules specific to this prompt** (full detail + worked example in `docs/prompts/issue-distillation.md`):
- **The gap test:** every Gap sentence must read naturally as "you have not shown / mentioned / recorded ___." If it only reads naturally as "the question is whether ___," that's a legal issue leaking through — rewrite before returning it.
- **Pure-law matters** (no evidentiary gap — e.g. "what orders can the tribunal make") get a pointer to the specific official source to check, not analysis.
- **No conclusions, ever** — not even softened ones ("good claim," "weak argument," "at fault").
- **No fabrication** — dates, amounts, message contents, the other party's words: if the user didn't say it, it's a gap, not a fact.
- Output length is proportionate to input length — a two-sentence account gets a short output, not a padded five-section report.

**Contract (ASSUMED — confirm with team):** stateless, single-shot call. No `conversation_history` needed for this endpoint, matching the prompt's own "single free-text message" framing. If the team wants iterative refinement (user adds more facts and re-runs), that's a different, multi-turn contract — flag before building it this way.

**Automated guardrail (decided, implemented):** `backend/guardrails.py` — a deterministic, regex-based scanner run on every response before it reaches the user. Chosen over a second model call because it's free, instant, and — this was the point — fully readable and testable by a human, not another layer of "trust the model." It checks six categories (outcome prediction, validity judgment, fault/liability assertions, legal classification, gap-test failures, and advice-giving) and is not meant to be exhaustive — paraphrased violations it doesn't have a pattern for will slip through, so treat a clean scan as "nothing obvious," not "verified safe." Run `python guardrails.py` directly to see it validate itself against one clean example and one deliberate violation per category. On a hit in production, log it — do not silently rewrite the model's text, since silent edits are their own source of subtle errors.

---

## Voice input (decided: in scope for Feature 1)

**Important constraint:** the Claude API does not accept audio input directly (text, images, and PDFs only) — don't lose time trying to send an audio file straight to the Messages API.

**Recommended architecture for a Chrome extension, 1.5-day budget:** use the browser's built-in `SpeechRecognition` (`webkitSpeechRecognition`) API. It's free, requires no API key, needs no backend call, and Chrome — the only browser this extension has to work in — supports it natively.

- It must run in a page context with DOM + microphone access — the **side panel or popup page**, not the background service worker (which has no mic access).
- A **side panel** (`chrome.sidePanel`, Manifest V3) is more robust than a popup here, since a popup closing on focus loss can kill an in-progress recording; a side panel stays open.
- Flow: mic button → `SpeechRecognition` streams interim + final results into the *same* text box used for typed input → user edits freely → user submits. This satisfies the spec's "show transcription, allow correction before use" requirement without any extra UI beyond a mic button next to the text box.
- `lang` must be set explicitly before starting recognition (e.g. `en-SG`, `zh-CN`, `ms-MY`, `ta-SG`) — there's no reliable auto-detect, so if multiple languages are supported (see below), the user needs a language picker before they hit record.

## Multi-language support (recommended scope — confirm before building)

Claude is natively multilingual, so no separate translation service is required. But two things are worth being deliberate about before wiring this in broadly:

- **Quoting fidelity risk:** "Inferences detected" works by quoting the user's *own words* verbatim so they can self-check that nothing was put in their mouth. If input and output both get translated, that quote is no longer literally what the user said — it's a re-expression of it, which quietly undermines the one part of the prompt designed to be independently checkable by the user.
- **Guardrail coverage is English-only right now.** The gap test, no-conclusion rule, and disclaimer language were written and are only known to hold in English. Cross-lingual instruction-following is generally strong for Claude but hasn't been verified here — Malay and Tamil in particular are less deeply represented than English or Mandarin, so quality on legal/procedural phrasing is less predictable.

**Recommended MVP scope:**
1. Accept input in any language as-is (the model reads non-English input fine) — no separate detection/translation step needed on the way in.
2. Run the actual distillation (and all guardrail logic) in English — this is the only path that's actually been designed and reasoned about above.
3. Offer a **"view in [language]" toggle at the end**, as one extra translation pass over the *already-generated* English output — not a change to the core pipeline. Keep any directly quoted user words in their original language/wording in the translated view, translating only the surrounding scaffolding.
4. Keep official names (ACRA, Bizfile, SCT, tribunal, form field names) in English regardless of display language, since that's how they appear on the actual government portals the user has to navigate.
5. Voice input `lang` picker: start with English + Mandarin (best-supported pair); add Malay/Tamil only if there's time to spot-check the output quality with someone who reads that language before demo day.

This keeps the risk isolated to a skippable display feature — if it runs out of time or reads awkwardly in testing, the English pipeline underneath is unaffected. Full end-to-end generation in other languages (skipping step 2) is possible but not recommended for a 1.5-day build, since it would mean trusting untested guardrail behaviour live at a demo.

---

## Backend / API conventions

- **LLM calls go through `backend/llm_client.py`**, not a direct SDK call in `main.py`. It exposes one function, `call_llm(system_prompt, user_message)`, and hides which provider is behind it.
- **Provider options, both supported by `llm_client.py`:**
  - **Direct Anthropic API** (`LLM_PROVIDER=anthropic`, the default): key from `ANTHROPIC_API_KEY` env var, model `claude-sonnet-5`.
  - **OpenRouter** (`LLM_PROVIDER=openrouter`): feasible, and reasonable given the $15 credit already in hand — OpenRouter serves Claude Sonnet 5 at the slug `anthropic/claude-sonnet-5` through an OpenAI-compatible endpoint (`https://openrouter.ai/api/v1`), so it's the `openai` Python package pointed at a different base URL, not a different product. At roughly $2/M input + $10/M output tokens, $15 covers many thousands of distillation calls — plenty for dev and demo day. Trade-offs: one more network hop that can fail live (worth having the direct-Anthropic path as a tested fallback, which the abstraction gives you for free), and a second administrative party seeing the prompt before it reaches Anthropic. On that second point: OpenRouter doesn't log prompts by default, but confirm "prompt logging" is OFF in the OpenRouter account settings before sending real dispute text through it — `llm_client.py` also requests per-request Zero Data Retention (`zdr=True`), worth verifying is actually honored for this model in OpenRouter's current docs before relying on it.
- **Model:** default to `claude-sonnet-5` regardless of provider. `main.py`'s original pasted snippet pointed at `claude-3-5-sonnet-20241022` — a much older dated snapshot — this is superseded by `llm_client.py` now. If time allows during dev, run 5–10 realistic test inputs (including adversarial ones like "just tell me if I'll win") through both `claude-sonnet-5` and `claude-opus-5` and compare rule adherence, not just fluency — this prompt is rule-dense (gap test, no-conclusions, reformat-not-classify), and Opus's edge is instruction-following on exactly that kind of thing. Verify current model IDs and pricing at https://docs.claude.com before demo day.
- **Temperature — correction: this parameter no longer exists.** Earlier advice here said to set `temperature=0.3` for consistency. Caught while actually running the code: the current `anthropic` SDK's `messages.create()` has no `temperature`, `top_p`, or `top_k` parameter at all — checked by inspecting the installed SDK directly, not assumed from memory. In its place is `output_config={"effort": ...}` (`low`/`medium`/`high`/`xhigh`/`max`), which controls how much effort the model spends rather than sampling randomness. `llm_client.py` now uses `effort="high"` as the closer analog for a rule-dense prompt like this one — not verified against a live key yet, so treat it as a starting point to test, not a settled choice.
- One system prompt per endpoint, loaded from a file in `docs/prompts/`, not inlined as a Python string literal — **implemented**: `main.py` loads `docs/prompts/issue-distillation.md` at import time via `load_prompt()`.
- Every response object must carry a `compliance_notice` field (already present in `main.py`) — do not drop this when adding new endpoints.
- **Decided and implemented: separate endpoint**, `POST /api/distill-issue`, not multiplexed into `/api/analyze-claim`. Reasoning: the two prompts have genuinely different contracts (this one stateless/single-shot, the other stateful with `conversation_history`) — branching on a flag inside one endpoint means conditional validation and messier request models for basically zero benefit, since FastAPI makes a second endpoint trivial (one more `@app.post(...)`).
- **Decided and implemented: stateless re-run, no `conversation_history`.** If a user wants to add facts after reading the output, the client resends the *edited/extended original text* as a fresh single message to the same endpoint — no backend session state, no history plumbing. This matches the prompt's own "single free-text message" design exactly, and "let the user edit their own draft and resubmit" is a client-side textbox feature you already need, not new backend work. Prefill that textbox with their previous text plus the model's own "Facts still needed" line as a hint of what to add.

**Status: implemented and tested.** `backend/main.py`, `backend/llm_client.py`, and `backend/guardrails.py` exist, boot cleanly under `uvicorn`, and were verified end-to-end against the real `api.anthropic.com` (with a placeholder key, confirming routing/prompt-loading/guardrail wiring all the way to Anthropic's own auth check — a real key is the only thing needed to get an actual distillation back). The sketch below is what's actually in `main.py` now, not a plan.

**What's actually in `main.py`:**

```python
from llm_client import call_llm
from guardrails import scan_for_leakage

class DistillRequest(BaseModel):
    user_message: str  # the full free-text account (edits/re-runs just resend this, extended)

@app.post("/api/distill-issue")
async def distill_issue(payload: DistillRequest):
    try:
        reply = call_llm(ISSUE_DISTILLATION_PROMPT, [{"role": "user", "content": payload.user_message}])  # loaded from docs/prompts/issue-distillation.md

        flags = scan_for_leakage(reply)
        if flags:
            print(f"[guardrail] {len(flags)} flag(s): {[f.category for f in flags]}")  # see Privacy section — do not log payload.user_message itself

        return {
            "status": "success",
            "reply": reply,
            "compliance_notice": "Generated output requires independent human verification pursuant to Singapore Court guidelines.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```


---

## Privacy & data handling (decided: minimize + don't persist)

There's a real constraint here, not just a nice-to-have — dispute accounts routinely contain names, amounts, and sometimes NRIC-adjacent details. Layered approach, cheapest/highest-impact first:

1. **Don't log the payload, ever.** The most common accidental leak in a fast-moving hackathon codebase is a stray `print(payload.user_message)` or `logging.info(payload)` added for debugging and never removed. FastAPI/uvicorn's own access logs already don't include the request body by default — the risk is entirely from code *you* add. Rule for the repo: never log a full request/response body; if you need to debug, log `len(payload.user_message)` or the first ~20 characters, not the text itself.
2. **Don't persist it.** The MVP already has no backend DB (see Assumptions) — keep it that way for this feature specifically. Process the request, return the response, keep nothing server-side. You can't leak a row that was never written. If a "save my case" feature gets added later, that's the point to add encryption-at-rest and a real retention/deletion policy — don't build storage now "just in case."
3. **Minimize at the point of entry.** Nothing stops a user pasting an NRIC or full address into the free-text box even though the prompt doesn't need it. A simple client-side regex check before submission (Singapore NRIC pattern: `[STFG]\d{7}[A-Z]`, plus a basic phone-number pattern) that shows a gentle inline warning — "you don't usually need to include this here" — is cheap to build and doubles as a good "privacy by design" demo talking point.
4. **Third-party exposure to Anthropic is real but bounded, verify the specifics yourself.** The account text necessarily goes to Anthropic's API to generate a response — that's structural, not a bug. Anthropic's commercial/API terms state that API inputs and outputs are not used to train models by default and are retained only briefly (not indefinitely) for abuse-monitoring purposes, separate from the consumer claude.ai terms. Don't state a specific retention number to judges/users without checking — sources disagree on the exact current window and it has changed over time. Point to https://privacy.claude.com and https://www.anthropic.com/legal/commercial-terms for the current figures rather than asserting one.
5. **Browser-side storage is local, but add a clear-data control.** If the "carry forward as reference panel" pattern uses `localStorage`/`sessionStorage` in the extension, that data never leaves the user's own browser — but on a shared/public machine it would persist for the next person on that Chrome profile. A one-click "clear my data" button is cheap and closes that gap.
6. **Say what happens, briefly, on-screen.** A short line near the input box — "your text is sent to Anthropic's Claude API to generate this summary and is not stored on our servers" — is honest, PDPA-consistent in spirit, and a good demo point for a legal audience.

One thing worth telling me if you know it: is the constraint you have in mind a specific rule from the hackathon organisers or a data-residency requirement (e.g. "no personal data may leave Singapore" or "no third party may receive it at all")? That would change the architecture more fundamentally — e.g. it could rule out sending raw text to any cloud API at all and push toward on-device redaction before any network call. The six steps above assume it's closer to "minimize and don't hoard it," which is the more common version of this constraint.

---

## Source-of-truth rules for anyone (human or Claude Code) writing copy or code here

- Any number that could be a filing fee, claim limit, or deadline must come from `docs/sources.md` with a link — never from memory or model output.
- If `docs/sources.md` doesn't have it yet, write the on-screen text as "check the current fee/limit at [official page]" rather than guessing a number.

---

## Decided

- Reformat only, never classify — permanent rule, see Hard rules above.
- Feature 1 runs **after** the eligibility checklist (Feature 2), not before — creates a build dependency, see Feature roadmap.
- Voice input is in scope for Feature 1, via browser `SpeechRecognition` (not the Claude API — it doesn't take audio).
- Separate endpoint (`POST /api/distill-issue`), not multiplexed with `/api/analyze-claim`.
- Stateless re-run pattern: no `conversation_history`; client resends the edited/extended text as a fresh message.
- Automated leakage check: regex-based, in `backend/guardrails.py`, run on every response before it reaches the user.
- No server-side logging or persistence of user-submitted dispute text; minimize what's collected at the point of entry. See "Privacy & data handling."
- Input length cap: Moderate tier (~500 words soft / ~1,000 words hard) — see Feature 1 spec.
- Output continuity: carried forward automatically via `chrome.storage.session` as a read-only reference panel with per-block copy buttons — not field-level autopopulate. Implemented in `extension/shared/distillation-reference.js`. Splits on blank lines client-side (matches the prompt's existing per-matter title+paragraph structure) — no prompt or backend contract change needed. `session` storage (not `local`) so it clears with the browser session rather than lingering, consistent with the privacy plan.
- LLM provider is swappable via one env var (`LLM_PROVIDER=anthropic` default, or `openrouter`), implemented in `backend/llm_client.py` — see "Backend / API conventions" for why and the OpenRouter specifics.

## Assumptions still open (override any of these — see open questions)

- Whether to actually run on OpenRouter for this hackathon vs. keep a direct Anthropic key as primary (with OpenRouter as a tested fallback) — the abstraction supports either; **team to confirm which is primary for demo day**.
- Multi-language depth — scoped recommendation given above (English-only core pipeline + end-stage translation toggle) — **TBC**.
- Default model `claude-sonnet-5` (test against `claude-opus-5` if time allows) — change here if the team decides otherwise.
- Exact nature of the data-privacy constraint (self-imposed minimization vs. an organizer-mandated or data-residency requirement) — **TBC**, see "Privacy & data handling."

---

## Local dev

```bash
cd backend
pip install -r requirements.txt --break-system-packages   # drop the flag first if your image doesn't need it
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload --port 8000
```

Then open the forwarded port 8000 URL in a browser (Codespaces prompts to forward it, or use the "Ports" tab) — that serves `backend/static/index.html`, a same-origin test-chat page for Feature 1. It is **not** the Chrome extension; it exists so there's something to actually click through today without needing to load an unpacked extension yet. Because it's served by the same FastAPI app it calls, it works identically whether opened via `localhost:8000` inside the Codespace or via the codespace's public forwarded URL — no CORS or host-mismatch issues either way.

Extension (not built yet): once `extension/` exists, load it unpacked via `chrome://extensions` → Developer mode → "Load unpacked" — in a **local** Chrome browser, since unpacked extensions load from the local filesystem. If developing in a Codespace, that means either syncing the extension folder to your machine, or pointing the extension's fetch calls at the Codespace's forwarded backend URL instead of `localhost` (the extension runs in your local browser, not inside the Codespace's network namespace, so `localhost:8000` won't resolve to the Codespace's server from there).

---

## Open questions still blocking a finished spec (see chat for full context)

1. Is the English-core + end-stage-translation-toggle scope for multi-language acceptable, or is full non-English generation actually required?
2. Should "Inferences detected" get distinct visual treatment beyond the reference-panel blocks?
3. Explicit user-confirmation step before output is treated as final?
4. Is the data-privacy constraint self-imposed minimization, or a specific organizer/data-residency requirement? (Changes the architecture if it's the latter — see "Privacy & data handling.")
5. Given Feature 2 (eligibility checklist) is now a build dependency for the demo — who's building it, and by when, relative to Feature 1?
6. OpenRouter vs. direct Anthropic API as the primary provider for demo day (both work via `llm_client.py` — just needs a call).

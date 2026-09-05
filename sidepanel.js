/*
 * sidepanel.js — controller for the CJTS Co-Pilot side panel.
 *
 * This is the first working wiring for the extension. Before this file,
 * sidepanel.html was a static mockup with no <script> tag at all — no
 * prompt in this repo was actually reachable from the extension UI.
 * This drives Prompt 1 (existing /api/distill-issue), Prompt 2 (new
 * /api/build-evidence-list), category confirmation (new /api/infer-category),
 * and Prompt 4 (new /api/build-contest-evidence) as one continuous flow.
 *
 * NOT IN SCOPE HERE (see chat for why): the eligibility checklist
 * (CLAUDE.md's Feature 2), voice input (Feature 4), and multi-language
 * display are all left as the disabled/decorative controls already in
 * sidepanel.html — wire them up as their own follow-ups.
 *
 * BACKEND URL: configurable at runtime via the "Backend connection settings"
 * panel in sidepanel.html (persisted in chrome.storage.local), because this
 * extension runs in your local Chrome while the backend may be running
 * remotely (e.g. a Codespace) — "localhost" only works if the backend is on
 * the same machine as the browser. See CLAUDE.md "Local dev" for details.
 */
// Defaults to this Codespace's forwarded backend URL (already allow-listed in
// manifest.json's host_permissions) since the extension runs in your local
// Chrome, not inside the Codespace — "localhost" here would not resolve to
// it. If you run the backend locally instead, change this via the "Backend
// connection settings" panel in the side panel (saved across sessions).
const DEFAULT_API_BASE_URL = "https://opulent-capybara-97r5w4r6wx9rfxx69-8000.app.github.dev";
const API_BASE_KEY = "cjts_api_base_url";
let API_BASE_URL = DEFAULT_API_BASE_URL;

/* ---------------------------------------------------------------------
 * State
 *
 * Persisted to chrome.storage.session as CLAUDE.md's design intended
 * (cleared with the browser session, not lingering on a shared machine).
 * Uploaded files are NEVER put in here — File objects aren't JSON-
 * serialisable, and per CLAUDE.md's privacy rules files shouldn't be
 * persisted anyway. They live only in `uploadedFiles` below, in memory,
 * for the current panel session, and are re-sent to the backend on every
 * call that needs them (the backend itself never stores them either).
 * ------------------------------------------------------------------- */
const STORAGE_KEY = "cjts_case_state_v1";

let state = {
  step: 1,
  accountText: "",
  prompt1Output: "",
  evidenceRows: [],   // {row_number, what_it_shows, document, source, missing_status, missing_detail, _new?}
  category: null,     // confirmed category key
  contest: null,      // {disclaimer, already_covered, points_to_check, inconsistencies, still_cannot_show}
  confirmed: false,
};

let uploadedFiles = []; // File[] — in memory only, never persisted

async function saveState() {
  try {
    if (chrome?.storage?.session) {
      await chrome.storage.session.set({ [STORAGE_KEY]: state });
    }
  } catch (e) {
    console.warn("Could not persist session state:", e);
  }
}

async function loadState() {
  try {
    if (chrome?.storage?.session) {
      const result = await chrome.storage.session.get(STORAGE_KEY);
      return result?.[STORAGE_KEY] || null;
    }
  } catch (e) {
    console.warn("Could not read session state:", e);
  }
  return null;
}

async function clearState() {
  try {
    if (chrome?.storage?.session) {
      await chrome.storage.session.remove(STORAGE_KEY);
    }
  } catch (e) {
    console.warn("Could not clear session state:", e);
  }
}

/* ---------------------------------------------------------------------
 * Backend URL settings — persisted across sessions (unlike the case state,
 * which is intentionally chrome.storage.session) since it's a per-install
 * connection setting, not case data.
 * ------------------------------------------------------------------- */
async function loadApiBase() {
  try {
    if (chrome?.storage?.local) {
      const result = await chrome.storage.local.get(API_BASE_KEY);
      return result?.[API_BASE_KEY] || DEFAULT_API_BASE_URL;
    }
  } catch (e) {
    console.warn("Could not read saved API base URL:", e);
  }
  return DEFAULT_API_BASE_URL;
}

async function saveApiBase(url) {
  try {
    if (chrome?.storage?.local) {
      await chrome.storage.local.set({ [API_BASE_KEY]: url });
    }
  } catch (e) {
    console.warn("Could not persist API base URL:", e);
  }
}

function initApiBaseSettings() {
  const input = document.getElementById("api-base-input");
  const saveBtn = document.getElementById("api-base-save");
  const status = document.getElementById("api-base-status");
  if (!input || !saveBtn) return;

  input.value = API_BASE_URL;
  saveBtn.addEventListener("click", async () => {
    const val = input.value.trim().replace(/\/$/, "");
    if (!val) return;
    API_BASE_URL = val;
    await saveApiBase(val);
    if (status) {
      status.textContent = "Saved. New requests will use this backend URL.";
      setTimeout(() => { status.textContent = ""; }, 3000);
    }
  });
}

/* ---------------------------------------------------------------------
 * Small DOM helpers
 * ------------------------------------------------------------------- */
const chatEl = document.getElementById("chat");
const composerInput = document.getElementById("composer-input");
const composerSend = document.getElementById("composer-send");
const composerHint = document.getElementById("composer-hint");
const composer = document.getElementById("composer");

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

function escapeAttr(s) {
  return (s ?? "").toString().replace(/"/g, "&quot;");
}

function setActiveStep(n) {
  document.querySelectorAll("#step-bar .step").forEach((el) => {
    el.classList.toggle("step-primary", Number(el.dataset.step) <= n);
  });
}

/** Adds a chat bubble and returns the element holding its inner content,
 * so callers can keep updating it (e.g. swap a "thinking" indicator for
 * a real result) without re-rendering the whole transcript. */
function addBubble(role, innerHtml, { header } = {}) {
  const wrap = document.createElement("div");
  wrap.className = role === "user" ? "chat chat-end" : "chat chat-start";

  const headerHtml = header
    ? `<div class="chat-header text-xs text-gray-500 mb-1">${escapeHtml(header)}</div>`
    : role === "user"
      ? `<div class="chat-header text-xs text-gray-500 mb-1">You</div>`
      : `<div class="chat-header text-xs text-gray-500 mb-1">Co-Pilot Assistant</div>`;

  const bubbleClass = role === "user" ? "chat-bubble bg-gray-200 text-gray-800 text-sm" : "chat-bubble chat-bubble-primary text-sm";

  wrap.innerHTML = `${headerHtml}<div class="${bubbleClass}" style="max-width: 100%;"></div>`;
  const bubble = wrap.querySelector(".chat-bubble");
  bubble.innerHTML = innerHtml;

  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
  return bubble;
}

function thinkingBubble(text) {
  return addBubble("assistant", `<span class="loading loading-dots loading-sm"></span> <span class="text-xs opacity-70">${escapeHtml(text)}</span>`);
}

async function apiFetch(path, options) {
  const res = await fetch(`${API_BASE_URL}${path}`, options);
  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json() : { detail: await res.text() };
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

function missingLabel(status) {
  return { no: "No", no_note_it: "No — note it", yes: "Yes", none_found: "None found" }[status] || status;
}

/* ---------------------------------------------------------------------
 * Evidence table rendering — shared by Prompt 2's initial build and
 * Prompt 4's appended rows, since it's the same 5(+source-type) column
 * table throughout, per the spec's own "continue Prompt 2's table" design.
 * ------------------------------------------------------------------- */
function renderEvidenceTableHtml() {
  const rows = [...state.evidenceRows].sort((a, b) => a.row_number - b.row_number);
  const rowsHtml = rows.map((row) => `
    <tr class="${row._new ? "bg-green-50" : ""}" data-row="${row.row_number}">
      <td class="text-xs text-gray-500">${row.row_number}${row._new ? '<span class="badge badge-success badge-xs ml-1">new</span>' : ""}</td>
      <td><input type="text" class="input input-bordered input-xs w-full" data-field="what_it_shows" value="${escapeAttr(row.what_it_shows)}"></td>
      <td><input type="text" class="input input-bordered input-xs w-full" data-field="document" value="${escapeAttr(row.document)}"></td>
      <td><input type="text" class="input input-bordered input-xs w-full" data-field="source" value="${escapeAttr(row.source)}"></td>
      <td>
        <select class="select select-bordered select-xs w-full" data-field="missing_status">
          ${["no", "no_note_it", "yes", "none_found"].map((s) => `<option value="${s}" ${s === row.missing_status ? "selected" : ""}>${missingLabel(s)}</option>`).join("")}
        </select>
      </td>
      <td><button class="btn btn-ghost btn-xs" data-action="delete-row">✕</button></td>
    </tr>
  `).join("");

  return `
    <div class="overflow-x-auto">
      <table class="table table-xs table-zebra" id="evidence-table">
        <thead>
          <tr><th>#</th><th>What it shows</th><th>Document</th><th>Source</th><th>Missing?</th><th></th></tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>
    <button class="btn btn-ghost btn-xs mt-2" data-action="add-row">+ Add row manually</button>
  `;
}

function wireEvidenceTable(bubbleEl, { onContinue, continueLabel } = {}) {
  function refreshRow(tr) {
    const rowNum = Number(tr.dataset.row);
    const row = state.evidenceRows.find((r) => r.row_number === rowNum);
    if (!row) return;
    tr.querySelectorAll("[data-field]").forEach((el) => {
      row[el.dataset.field] = el.value;
    });
  }

  bubbleEl.querySelectorAll("input[data-field], select[data-field]").forEach((el) => {
    el.addEventListener("input", () => { refreshRow(el.closest("tr")); saveState(); });
  });

  bubbleEl.querySelectorAll("[data-action='delete-row']").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tr = btn.closest("tr");
      const rowNum = Number(tr.dataset.row);
      state.evidenceRows = state.evidenceRows.filter((r) => r.row_number !== rowNum);
      saveState();
      tr.remove();
    });
  });

  const addBtn = bubbleEl.querySelector("[data-action='add-row']");
  if (addBtn) {
    addBtn.addEventListener("click", () => {
      const nextNum = Math.max(0, ...state.evidenceRows.map((r) => r.row_number)) + 1;
      state.evidenceRows.push({ row_number: nextNum, what_it_shows: "", document: "", source: "", missing_status: "yes", missing_detail: "" });
      saveState();
      const tableWrap = bubbleEl.querySelector(".overflow-x-auto").parentElement;
      const continueBtnHtml = onContinue ? `<button class="btn btn-secondary btn-sm mt-3" data-action="continue">${continueLabel}</button>` : "";
      bubbleEl.innerHTML = renderEvidenceTableHtml() + continueBtnHtml;
      wireEvidenceTable(bubbleEl, { onContinue, continueLabel });
    });
  }

  if (onContinue) {
    const continueBtn = bubbleEl.querySelector("[data-action='continue']");
    if (continueBtn) continueBtn.addEventListener("click", onContinue);
  }
}

/* ---------------------------------------------------------------------
 * Step 1 — account narrative -> Prompt 1 (Issue Distillation)
 * ------------------------------------------------------------------- */
function startStep1() {
  addBubble("assistant", "Hi! Tell me what happened, in your own words, and I'll help you organise it for your SCT filing. This restates your facts and flags gaps — it never tells you whether your claim is strong or weak.");
  composerHint.textContent = "Tell us what happened, in your own words.";
  composer.style.display = "flex".length ? "" : ""; // no-op, kept visible by default
}

async function handleAccountSubmit() {
  const text = composerInput.value.trim();
  if (!text) return;
  addBubble("user", escapeHtml(text));
  composerInput.value = "";
  composerInput.disabled = true;
  composerSend.disabled = true;

  const thinking = thinkingBubble("Reading your account...");
  try {
    const data = await apiFetch("/api/distill-issue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_message: text }),
    });

    state.accountText = text;
    state.prompt1Output = data.reply;
    await saveState();

    thinking.innerHTML = renderPrompt1ReviewHtml(data.reply, data.guardrail_flags);
    wirePrompt1Review(thinking);

    // Composer's only job (Step 1) is done — everything after this is button-driven.
    composer.style.display = "none";
    setActiveStep(1);
  } catch (err) {
    thinking.innerHTML = `<span class="text-error text-xs">Failed: ${escapeHtml(err.message)}. Is the backend running at ${escapeHtml(API_BASE_URL)}?</span>`;
    composerInput.disabled = false;
    composerSend.disabled = false;
  }
}

function renderPrompt1ReviewHtml(reply, flags) {
  return `
    <div class="text-sm mb-2">Here's your account restated as facts, gaps, and next steps. <strong>Edit anything below</strong> before continuing — this is your only chance to correct an assumption before it's carried forward.</div>
    <textarea class="textarea textarea-bordered w-full text-xs" style="min-height: 220px;" id="prompt1-editable">${escapeHtml(reply)}</textarea>
    ${flags?.length ? `<div class="text-xs opacity-60 mt-1">[dev note] guardrail flagged: ${escapeHtml(flags.join(", "))}</div>` : ""}
    <button class="btn btn-secondary btn-sm mt-2" data-action="confirm-prompt1">Looks good — build my evidence list</button>
  `;
}

function wirePrompt1Review(bubbleEl) {
  bubbleEl.querySelector("[data-action='confirm-prompt1']").addEventListener("click", async () => {
    state.prompt1Output = bubbleEl.querySelector("#prompt1-editable").value;
    state.step = 2;
    await saveState();
    setActiveStep(2);
    startStep2();
  });
}

/* ---------------------------------------------------------------------
 * Step 2 — Prompt 2 (evidence list, lite)
 * ------------------------------------------------------------------- */
function startStep2() {
  const bubble = addBubble("assistant", `
    <div class="text-sm mb-2">Now let's build your evidence list. Upload any messages, receipts, or records you have — optional, but the more you attach the more this can actually check. Files go straight to Claude and are never saved on our server.</div>
    <input type="file" id="evidence-files" multiple accept="image/jpeg,image/png,image/gif,image/webp,application/pdf" class="file-input file-input-bordered file-input-sm w-full" />
    <div id="evidence-file-list" class="text-xs mt-1"></div>
    <button class="btn btn-primary btn-sm mt-2" data-action="build-evidence">Build evidence list</button>
  `);

  const fileInput = bubble.querySelector("#evidence-files");
  const fileListEl = bubble.querySelector("#evidence-file-list");
  function renderFiles() {
    fileListEl.innerHTML = uploadedFiles.map((f, i) =>
      `<div class="flex items-center gap-2">${escapeHtml(f.name)} <button class="btn btn-ghost btn-xs" data-remove="${i}">remove</button></div>`
    ).join("");
    fileListEl.querySelectorAll("[data-remove]").forEach((btn) => {
      btn.addEventListener("click", () => { uploadedFiles.splice(Number(btn.dataset.remove), 1); renderFiles(); });
    });
  }
  fileInput.addEventListener("change", () => { uploadedFiles.push(...Array.from(fileInput.files)); fileInput.value = ""; renderFiles(); });

  bubble.querySelector("[data-action='build-evidence']").addEventListener("click", async () => {
    const btn = bubble.querySelector("[data-action='build-evidence']");
    btn.disabled = true;
    const thinking = thinkingBubble("Reading your files and building your list...");
    try {
      const fd = new FormData();
      fd.append("prompt1_output", state.prompt1Output);
      uploadedFiles.forEach((f) => fd.append("files", f));

      const data = await apiFetch("/api/build-evidence-list", { method: "POST", body: fd });
      state.evidenceRows = data.rows;
      await saveState();

      const continueLabel = "Continue — confirm category";
      thinking.innerHTML = renderEvidenceTableHtml() +
        (data.guardrail_flags?.length ? `<div class="text-xs opacity-60 mt-1">[dev note] guardrail flagged: ${escapeHtml(data.guardrail_flags.join(", "))}</div>` : "") +
        `<button class="btn btn-secondary btn-sm mt-3" data-action="continue">${continueLabel}</button>`;
      wireEvidenceTable(thinking, {
        continueLabel,
        onContinue: async () => {
          state.step = 3;
          await saveState();
          setActiveStep(3);
          startStep3();
        },
      });
    } catch (err) {
      thinking.innerHTML = `<span class="text-error text-xs">Failed: ${escapeHtml(err.message)}</span>`;
    } finally {
      btn.disabled = false;
    }
  });
}

/* ---------------------------------------------------------------------
 * Step 3 — category confirmation (routing label only, see chat notes)
 * ------------------------------------------------------------------- */
function startStep3() {
  const bubble = addBubble("assistant", `
    <div class="text-sm mb-2">Which of these best matches your situation? This is used only to check your evidence against typical opposing positions for that type of dispute — it is never used to characterise your claim.</div>
    <button class="btn btn-primary btn-sm" data-action="suggest-category">Suggest a category</button>
  `);

  bubble.querySelector("[data-action='suggest-category']").addEventListener("click", async () => {
    const btn = bubble.querySelector("[data-action='suggest-category']");
    btn.disabled = true;
    const thinking = thinkingBubble("Reading your account...");
    try {
      const fd = new FormData();
      fd.append("prompt1_output", state.prompt1Output);
      const data = await apiFetch("/api/infer-category", { method: "POST", body: fd });

      const optionsHtml = data.all_categories.map((c) => `
        <label class="flex items-start gap-2 border border-base-300 rounded-lg p-2 cursor-pointer text-sm ${c.key === data.suggested_category ? "border-primary bg-primary/5" : ""}">
          <input type="radio" name="category" class="radio radio-primary radio-sm mt-0.5" value="${c.key}" ${c.key === data.suggested_category ? "checked" : ""}>
          <span>${escapeHtml(c.label)}</span>
        </label>
      `).join("");

      thinking.innerHTML = `
        <div class="bg-primary/10 rounded-lg p-2 text-xs mb-2"><strong>Suggested:</strong> ${escapeHtml(data.suggested_category_label)}<br>${escapeHtml(data.reasoning)}<br><em>For evidence-checking purposes only — change it below if it doesn't fit.</em></div>
        <div class="flex flex-col gap-1">${optionsHtml}</div>
        <button class="btn btn-secondary btn-sm mt-2" data-action="confirm-category">Confirm category</button>
      `;
      thinking.querySelector("[data-action='confirm-category']").addEventListener("click", async () => {
        const checked = thinking.querySelector("input[name='category']:checked");
        if (!checked) return;
        state.category = checked.value;
        state.step = 4;
        await saveState();
        setActiveStep(4);
        startStep4();
      });
    } catch (err) {
      thinking.innerHTML = `<span class="text-error text-xs">Failed: ${escapeHtml(err.message)}</span>`;
    } finally {
      btn.disabled = false;
    }
  });
}

/* ---------------------------------------------------------------------
 * Step 4 — Prompt 4 (contest evidence)
 * ------------------------------------------------------------------- */
function startStep4() {
  const bubble = addBubble("assistant", `
    <div class="text-sm mb-2">Now let's check what you might be asked for if the other party disputes this. This reads your files a second time against common positions for this type of dispute.</div>
    <button class="btn btn-primary btn-sm" data-action="build-contest">Check</button>
  `);

  bubble.querySelector("[data-action='build-contest']").addEventListener("click", async () => {
    const btn = bubble.querySelector("[data-action='build-contest']");
    btn.disabled = true;
    const thinking = thinkingBubble("Checking your files against common positions...");
    try {
      const fd = new FormData();
      fd.append("prompt1_output", state.prompt1Output);
      fd.append("evidence_rows_json", JSON.stringify(state.evidenceRows));
      fd.append("category", state.category);
      uploadedFiles.forEach((f) => fd.append("files", f));

      const data = await apiFetch("/api/build-contest-evidence", { method: "POST", body: fd });

      data.new_rows.forEach((r) => state.evidenceRows.push({
        ...r,
        source: `${r.source_type === "other_party_quote" ? "Other party said" : "Common position"}: "${r.source_text}"`,
        _new: true,
      }));
      state.contest = {
        disclaimer: data.disclaimer,
        already_covered: data.already_covered,
        points_to_check: data.points_to_check,
        inconsistencies: data.inconsistencies,
        still_cannot_show: data.still_cannot_show,
      };
      await saveState();

      thinking.innerHTML = renderStep4ResultHtml(data);
      wireEvidenceTable(thinking.querySelector("#step4-table-slot"), {}); // editable, no continue button here — final review has it
      thinking.querySelector("[data-action='continue-review']").addEventListener("click", async () => {
        state.step = 5;
        await saveState();
        startStep5();
      });
    } catch (err) {
      thinking.innerHTML = `<span class="text-error text-xs">Failed: ${escapeHtml(err.message)}</span>`;
    } finally {
      btn.disabled = false;
    }
  });
}

function renderStep4ResultHtml(data) {
  const list = (items, render) => items.length ? items.map(render).join("") : `<div class="text-xs opacity-60">None.</div>`;

  return `
    <div class="alert alert-warning text-xs mb-3">${escapeHtml(data.disclaimer)}</div>
    <div id="step4-table-slot">${renderEvidenceTableHtml()}</div>

    <div class="mt-3">
      <div class="font-semibold text-xs mb-1">Already covered by existing rows</div>
      ${list(data.already_covered, (a) => `<div class="border-l-2 border-base-300 pl-2 text-xs mb-1"><strong>${escapeHtml(a.position_or_excuse)}</strong> — row ${a.covered_by_row}. ${escapeHtml(a.note)}</div>`)}
    </div>
    <div class="mt-3">
      <div class="font-semibold text-xs mb-1">Points to check officially</div>
      ${list(data.points_to_check, (p) => `<div class="border-l-2 border-base-300 pl-2 text-xs mb-1"><strong>${escapeHtml(p.topic)}</strong><br>${escapeHtml(p.official_source)}</div>`)}
    </div>
    <div class="mt-3">
      <div class="font-semibold text-xs mb-1">Inconsistencies</div>
      ${list(data.inconsistencies, (i) => `<div class="border-l-2 border-base-300 pl-2 text-xs mb-1"><strong>${escapeHtml(i.topic)}</strong><br>A: ${escapeHtml(i.version_a)}<br>B: ${escapeHtml(i.version_b)}<br><em>${escapeHtml(i.instruction)}</em></div>`)}
    </div>
    <div class="mt-3">
      <div class="font-semibold text-xs mb-1">What you still cannot show</div>
      <div class="text-xs">${escapeHtml(data.still_cannot_show)}</div>
    </div>
    ${data.guardrail_flags?.length ? `<div class="text-xs opacity-60 mt-2">[dev note] guardrail flagged: ${escapeHtml(data.guardrail_flags.join(", "))}</div>` : ""}
    <button class="btn btn-secondary btn-sm mt-3" data-action="continue-review">Continue to review</button>
  `;
}

/* ---------------------------------------------------------------------
 * Step 5 — explicit confirmation, per CLAUDE.md's hard rule: never treat
 * anything as final without it.
 * ------------------------------------------------------------------- */
function startStep5() {
  const bubble = addBubble("assistant", `
    <div class="text-sm mb-2">Review everything above. Nothing is treated as final until you confirm — you can still go back and edit any row before you do.</div>
    <button class="btn btn-primary btn-sm" data-action="confirm-final">Confirm as final</button>
  `);
  bubble.querySelector("[data-action='confirm-final']").addEventListener("click", async () => {
    state.confirmed = true;
    await saveState();
    bubble.innerHTML = `<div class="alert alert-success text-xs">Confirmed at ${new Date().toLocaleString()}. This still requires independent human verification before filing — see the disclaimer above.</div>`;
    composer.style.display = "none";
  });
}

/* ---------------------------------------------------------------------
 * Boot
 * ------------------------------------------------------------------- */
async function boot() {
  API_BASE_URL = await loadApiBase();
  initApiBaseSettings();

  const saved = await loadState();
  if (saved && (saved.prompt1Output || saved.evidenceRows?.length)) {
    addBubble("assistant", `
      <div class="text-sm mb-2">We found evidence from an earlier session on this device. Files aren't kept between sessions, so you'll need to re-attach anything you uploaded before if you continue.</div>
      <button class="btn btn-secondary btn-sm" data-action="resume">Resume where I left off</button>
      <button class="btn btn-ghost btn-sm" data-action="fresh">Start fresh</button>
    `);
    const lastBubble = chatEl.lastElementChild.querySelector(".chat-bubble");
    lastBubble.querySelector("[data-action='resume']").addEventListener("click", () => {
      lastBubble.parentElement.remove();
      resumeFrom(saved);
    });
    lastBubble.querySelector("[data-action='fresh']").addEventListener("click", async () => {
      await clearState();
      state = { step: 1, accountText: "", prompt1Output: "", evidenceRows: [], category: null, contest: null, confirmed: false };
      lastBubble.parentElement.remove();
      startStep1();
    });
    return;
  }
  startStep1();
}

function resumeFrom(saved) {
  state = saved;
  composer.style.display = "none";

  if (state.accountText) addBubble("user", escapeHtml(state.accountText));
  if (state.prompt1Output) {
    const b = addBubble("assistant", renderPrompt1ReviewHtml(state.prompt1Output, []));
    wirePrompt1Review(b);
  }
  if (state.evidenceRows?.length && state.step >= 2) {
    const continueLabel = "Continue — confirm category";
    const b = addBubble("assistant", renderEvidenceTableHtml() + `<button class="btn btn-secondary btn-sm mt-3" data-action="continue">${continueLabel}</button>`);
    wireEvidenceTable(b, { continueLabel, onContinue: async () => { state.step = 3; await saveState(); setActiveStep(3); startStep3(); } });
  }
  if (state.category && state.step >= 3) {
    setActiveStep(3);
  }
  if (state.contest && state.step >= 4) {
    setActiveStep(4);
    const b = addBubble("assistant", renderStep4ResultHtml({ ...state.contest, new_rows: [], guardrail_flags: [] }));
    wireEvidenceTable(b.querySelector("#step4-table-slot"), {});
    b.querySelector("[data-action='continue-review']").addEventListener("click", async () => { state.step = 5; await saveState(); startStep5(); });
  }
  if (state.confirmed) {
    addBubble("assistant", `<div class="alert alert-success text-xs">Previously confirmed as final. Use "Start fresh" (reload the panel) to begin a new case.</div>`);
  } else if (state.step >= 4 && state.contest) {
    startStep5();
  } else if (state.step === 3 && state.category) {
    startStep4();
  } else if (state.step === 2 && !state.evidenceRows?.length) {
    setActiveStep(2);
    startStep2();
  }
  setActiveStep(state.step);
}

composerSend.addEventListener("click", handleAccountSubmit);
composerInput.addEventListener("keydown", (e) => { if (e.key === "Enter") handleAccountSubmit(); });

boot();

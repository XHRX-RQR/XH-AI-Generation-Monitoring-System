/* ═══════════════════════════════════════════════════════
   XH AI Generation Monitoring System - Frontend Logic
   ═══════════════════════════════════════════════════════ */

const CONFIG_KEY = "xh_ai_monitor_config";
const THEME_KEY = "xh_ai_monitor_theme";

// ── 主题 ──
function initTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved) {
        document.documentElement.setAttribute("data-theme", saved);
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem(THEME_KEY, next);
}

// ── 配置 ──
function loadConfig() {
    try {
        const saved = localStorage.getItem(CONFIG_KEY);
        if (saved) {
            const c = JSON.parse(saved);
            if (c.api_base) document.getElementById("api-base").value = c.api_base;
            if (c.api_key) document.getElementById("api-key").value = c.api_key;
            if (c.model) document.getElementById("model-name").value = c.model;
            if (c.temperature !== undefined) document.getElementById("temperature").value = c.temperature;
        }
    } catch (_) {}
}

function saveConfig() {
    const cfg = {
        api_base: document.getElementById("api-base").value.trim(),
        api_key: document.getElementById("api-key").value.trim(),
        model: document.getElementById("model-name").value.trim(),
        temperature: parseFloat(document.getElementById("temperature").value) || 0.1,
    };
    localStorage.setItem(CONFIG_KEY, JSON.stringify(cfg));
}

function saveConfigAndClose() {
    saveConfig();
    closeSettings();
    showToast("配置已保存");
}

function toggleApiKeyVisibility() {
    const el = document.getElementById("api-key");
    el.type = el.type === "password" ? "text" : "password";
}

// ── 设置弹窗 ──
function openSettings() {
    document.getElementById("settings-modal").classList.remove("hidden");
}

function closeSettings() {
    document.getElementById("settings-modal").classList.add("hidden");
}

function onModalOverlayClick(e) {
    if (e.target === e.currentTarget) closeSettings();
}

// ── 初始化 ──
initTheme();
document.addEventListener("DOMContentLoaded", () => {
    loadConfig();
    document.getElementById("input-text").addEventListener("input", updateTextStats);
    document.addEventListener("keydown", e => {
        if (e.key === "Escape") closeSettings();
    });
});

function updateTextStats() {
    const text = document.getElementById("input-text").value;
    document.getElementById("char-count").textContent = `${text.length} 个字符`;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    document.getElementById("word-count").textContent = `${words} 个词`;
}

// ── UI 状态 ──
function showState(s) {
    ["result-placeholder", "result-loading", "result-content", "result-error"].forEach(id => {
        document.getElementById(id).classList.toggle("hidden", id !== s);
    });
}

function resetUI() {
    showState("result-placeholder");
    document.getElementById("detect-btn").disabled = false;
    document.getElementById("detect-btn").textContent = "开始检测";
    for (let i = 1; i <= 3; i++) document.getElementById(`step-${i}`).classList.remove("active", "done");
}

function showToast(msg) {
    let t = document.getElementById("toast-msg");
    if (!t) {
        t = document.createElement("div");
        t.id = "toast-msg";
        t.style.cssText = `position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;background:var(--bg-card);color:var(--text);border:1px solid var(--border-light);border-radius:4px;padding:0.6rem 1rem;font-size:0.8rem;box-shadow:0 4px 12px rgba(0,0,0,0.3);transform:translateY(16px);opacity:0;transition:all 0.25s ease;`;
        document.body.appendChild(t);
    }
    t.textContent = msg;
    requestAnimationFrame(() => { t.style.opacity = "1"; t.style.transform = "translateY(0)"; });
    setTimeout(() => { t.style.opacity = "0"; t.style.transform = "translateY(16px)"; }, 2200);
}

// ── 检测 ──
async function runDetection() {
    const text = document.getElementById("input-text").value.trim();
    const apiBase = document.getElementById("api-base").value.trim();
    const apiKey = document.getElementById("api-key").value.trim();
    const model = document.getElementById("model-name").value.trim();
    const temp = parseFloat(document.getElementById("temperature").value) || 0.1;

    if (!apiBase || !apiKey || !model) {
        showToast("请先在设置中配置 API 参数");
        openSettings();
        return;
    }
    if (!text) { showToast("请输入待检测文本"); return; }
    if (text.length < 50) { showToast("文本至少需要 50 个字符"); return; }

    const btn = document.getElementById("detect-btn");
    btn.disabled = true;
    btn.textContent = "检测中...";
    showState("result-loading");
    simulateProgress();

    try {
        const r = await fetch("/api/detect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, api_base: apiBase, api_key: apiKey, model, temperature: temp }),
        });
        const data = await r.json();
        if (!r.ok || data.error) throw new Error(data.error || `服务器错误 (${r.status})`);

        for (let i = 1; i <= 3; i++) {
            document.getElementById(`step-${i}`).classList.remove("active");
            document.getElementById(`step-${i}`).classList.add("done");
        }
        await sleep(300);
        renderResult(data.result);
        showState("result-content");
    } catch (err) {
        document.getElementById("error-message").textContent = err.message;
        showState("result-error");
    } finally {
        btn.disabled = false;
        btn.textContent = "开始检测";
    }
}

function simulateProgress() {
    [500, 8000, 16000].forEach((d, i) => {
        setTimeout(() => {
            for (let j = 1; j <= 3; j++) {
                if (j <= i) { document.getElementById(`step-${j}`).classList.remove("active"); document.getElementById(`step-${j}`).classList.add("done"); }
            }
            const s = document.getElementById(`step-${i + 1}`);
            if (s && !s.classList.contains("done")) s.classList.add("active");
        }, d);
    });
}

// ── 渲染 ──
function renderResult(result) {
    const verdict = (result.verdict || "Inconclusive").toLowerCase();
    const card = document.getElementById("verdict-card");
    card.className = "verdict-card";

    let vc, vl;
    if (verdict.includes("ai")) { vc = "ai"; vl = "AI 生成"; }
    else if (verdict.includes("human")) { vc = "human"; vl = "人类撰写"; }
    else { vc = "uncertain"; vl = "无法确定"; }

    card.classList.add(vc);
    document.getElementById("verdict-badge").textContent = vl;

    const conf = result.confidence || 0;
    const circ = 2 * Math.PI * 52;
    const off = circ - (conf / 100) * circ;
    const rf = document.getElementById("confidence-ring-fill");
    const rc = vc === "ai" ? "var(--ai-color)" : vc === "human" ? "var(--human-color)" : "var(--uncertain-color)";
    rf.style.stroke = rc;
    setTimeout(() => { rf.style.strokeDashoffset = off; }, 80);
    document.getElementById("confidence-text").textContent = `${conf}%`;

    const ap = result.ai_probability || 0;
    const pf = document.getElementById("ai-prob-fill");
    const pc = ap >= 70 ? "var(--ai-color)" : ap >= 40 ? "var(--warning)" : "var(--human-color)";
    pf.style.background = pc;
    setTimeout(() => { pf.style.width = `${ap}%`; }, 80);
    document.getElementById("ai-prob-value").textContent = `${ap}%`;
    document.getElementById("ai-prob-value").style.color = pc;

    document.getElementById("result-summary").textContent = result.summary || "暂无摘要。";

    const il = document.getElementById("indicators-list");
    il.innerHTML = "";
    (result.key_indicators || []).forEach(ind => {
        const sc = (ind.signal || "").toLowerCase().includes("ai") ? "ai" : "human";
        const sr = (ind.strength || "moderate").toLowerCase();
        const scl = sr.includes("strong") ? "strong" : sr.includes("weak") ? "weak" : "moderate";
        const sl = sr.includes("strong") ? "强" : sr.includes("weak") ? "弱" : "中";
        const el = document.createElement("div");
        el.className = "indicator-item";
        el.innerHTML = `<span class="indicator-signal ${sc}"></span><span class="indicator-name">${esc(ind.feature||"")}</span><span class="indicator-strength ${scl}">${sl}</span>${ind.detail?`<div class="indicator-detail">${esc(ind.detail)}</div>`:""}`;
        il.appendChild(el);
    });

    renderRound("round1-details", result.analysis_rounds?.round1_features || {},
        { lexical_diversity: "词汇多样性", sentence_burstiness: "句式突变性", discourse_patterns: "篇章组织", content_semantics: "内容语义", stylistic_consistency: "风格一致性" }, "evidence");

    renderRound("round2-details", result.analysis_rounds?.round2_deep_analysis || {},
        { micro_patterns: "微观模式", semantic_depth: "语义深度", linguistic_fingerprint: "语言指纹", ai_telltales: "AI 特征" }, "details");

    const r2 = result.analysis_rounds?.round2_deep_analysis || {};
    if (r2.key_evidence?.length) {
        const ev = document.createElement("div");
        ev.style.cssText = "margin-top:0.6rem;padding-top:0.6rem;border-top:1px solid var(--border);";
        ev.innerHTML = `<div class="score-name" style="margin-bottom:0.4rem">关键证据</div>`;
        r2.key_evidence.forEach(e => { const p = document.createElement("div"); p.className = "score-evidence"; p.style.paddingLeft = "0.8rem"; p.textContent = `- ${e}`; ev.appendChild(p); });
        document.getElementById("round2-details").appendChild(ev);
    }

    const caveats = result.caveats || [];
    const cs = document.getElementById("caveats-section");
    const cl = document.getElementById("caveats-list");
    cl.innerHTML = "";
    if (caveats.length) { cs.classList.remove("hidden"); caveats.forEach(c => { const li = document.createElement("li"); li.textContent = c; cl.appendChild(li); }); }
    else { cs.classList.add("hidden"); }

    document.getElementById("meta-model").textContent = `模型：${result.model_used || "N/A"}`;
    document.getElementById("meta-time").textContent = `耗时：${result.elapsed_seconds || 0} 秒`;
    document.getElementById("meta-length").textContent = `文本：${result.text_length || 0} 字符`;
}

function renderRound(elId, data, map, detailKey) {
    const el = document.getElementById(elId);
    el.innerHTML = "";
    Object.entries(map).forEach(([key, label]) => {
        const f = data[key]; if (!f) return;
        const s = f.score ?? 0;
        const c = s <= 3 ? "score-low" : s <= 6 ? "score-mid" : "score-high";
        const d = document.createElement("div");
        d.innerHTML = `<div class="score-item"><span class="score-name">${label}</span><div class="score-bar-container"><div class="score-bar"><div class="score-bar-fill ${c}" style="width:${s*10}%"></div></div><span class="score-value ${c}">${s}/10</span></div></div>${f[detailKey]?`<div class="score-evidence">${esc(f[detailKey])}</div>`:""}`;
        el.appendChild(d);
    });
}

function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

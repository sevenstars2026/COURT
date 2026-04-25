// ===== WebSocket 连接 =====
const socket = io();
let currentCaseId = null;

socket.on('connect', () => {
    console.log('✅ WebSocket 已连接');
});

socket.on('trial_progress', (data) => {
    if (currentCaseId && data.case_id === currentCaseId) {
        updateTrialProgress(data);
    }
});

socket.on('execution_output', (data) => {
    if (currentCaseId && data.case_id === currentCaseId) {
        appendExecutionOutput(data.output);
    }
});

// ===== 标签页切换 =====
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
        if (tab.dataset.tab === 'hall') { loadCases(); }
        if (tab.dataset.tab === 'config') { loadApiSettings(); }
        loadAgentStatus();
    });
});

// ===== Agent 状态 =====
async function loadAgentStatus() {
    try {
        const [sr, hr] = await Promise.all([
            fetch('/api/agents/status'),
            fetch('/api/agents/health')
        ]);
        const sd = await sr.json();
        let health = {};
        try { const hd = await hr.json(); if (hd.success) health = hd.health; } catch(e) {}

        if (!sd.success) return;
        for (const [id, info] of Object.entries(sd.agents)) {
            const el = document.getElementById('mode-' + id);
            if (!el) continue;

            if (info.mode === 'api') {
                const h = health[id];
                const statusDot = h === 'online' ? '🟢' : h === 'offline' ? '🔴' : '●';
                const statusText = h === 'online' ? '在线' : h === 'offline' ? '离线' : '未检测';
                el.className = 'agent-mode ' + (h === 'online' ? 'online' : 'offline');
                el.textContent = `${statusDot} ${info.model} (${statusText})`;
            } else {
                el.className = 'agent-mode rule';
                el.textContent = '● 规则引擎';
            }
        }
    } catch (e) { /* ignore */ }
}

// ===== 提交动议 =====
document.getElementById('motion-form').addEventListener('submit', async e => {
    e.preventDefault();
    const btn = document.getElementById('btn-submit');
    btn.disabled = true; btn.textContent = '提交中...';

    const data = {
        title: document.getElementById('motion-title').value,
        motion_type: document.getElementById('motion-type').value,
        description: document.getElementById('motion-desc').value,
        proposed_changes: [],
        affected_files: [],
        risks: [],
        benefits: [],
        priority: parseInt(document.getElementById('motion-priority').value)
    };

    const fileInput = document.getElementById('motion-file');
    const fileCount = fileInput.files.length;

    try {
        // 1. 提交动议
        const r = await fetch('/api/motions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const d = await r.json();
        const box = document.getElementById('submit-result');
        box.style.display = 'block';

        if (!d.success) {
            box.className = 'msg-box error';
            box.textContent = '❌ ' + d.error;
            btn.disabled = false; btn.textContent = '提交动议';
            return;
        }

        // 2. 如果有附件，逐个上传
        let fileMsg = '';
        const files = fileInput.files;
        if (files.length > 0 && d.case_id) {
            const uploaded = [];
            const failed = [];
            for (const f of files) {
                const fd = new FormData();
                fd.append('file', f);
                fd.append('case_id', d.case_id);
                fd.append('submitted_by', 'prosecutor');
                const evResp = await fetch('/api/upload', { method: 'POST', body: fd });
                const evData = await evResp.json();
                if (evData.success) {
                    uploaded.push(`${f.name}(${evData.content_length}字符)`);
                } else {
                    failed.push(f.name);
                }
            }
            if (uploaded.length) fileMsg = ` 📎已上传: ${uploaded.join(', ')}`;
            if (failed.length) fileMsg += ` ⚠️失败: ${failed.join(', ')}`;
        }

        box.className = 'msg-box success';
        box.textContent = '✅ ' + d.message + fileMsg;
        document.getElementById('motion-form').reset();
        document.getElementById('file-info').textContent = '';
        loadCases();
    } catch (err) {
        const box = document.getElementById('submit-result');
        box.style.display = 'block';
        box.className = 'msg-box error';
        box.textContent = '❌ 提交失败: ' + err.message;
    }
    btn.disabled = false; btn.textContent = '提交动议';
});

// ===== 案件列表 =====
async function loadCases() {
    try {
        const r = await fetch('/api/motions');
        const d = await r.json();
        const el = document.getElementById('case-list');
        if (!d.success || !d.motions.length) {
            el.innerHTML = '<div class="empty-state">暂无案件，提交动议后显示</div>';
            return;
        }
        el.innerHTML = d.motions.sort((a, b) => new Date(b.filed_at) - new Date(a.filed_at)).map(m => {
            const statusText = { filed: '待审理', trial: '庭审中', deliberation: '评议中', verdict: '已判决' }[m.status] || m.status;
            return `<div class="case-card">
                <div class="case-info">
                    <div class="case-title">${esc(m.title)}</div>
                    <div class="case-meta">${m.case_id} · ${getTypeLabel(m.motion_type)} · ${fmt(m.filed_at)}</div>
                </div>
                <span class="case-status status-${m.status}">${statusText}</span>
                <div class="case-actions">
                    ${m.status === 'filed' ? `<button class="btn-action primary" onclick="startTrial('${m.case_id}')">⚖️ 庭审</button>` : ''}
                    ${m.status === 'verdict' ? `<button class="btn-action success" onclick="showVerdict('${m.case_id}')">📄 判决</button><button class="btn-action" onclick="downloadCode('${m.case_id}')">📦 代码</button><button class="btn-action" onclick="retrial('${m.case_id}')">重审</button>` : ''}
                    ${m.status === 'trial' || m.status === 'deliberation' ? `<button class="btn-action danger" onclick="resetTrial('${m.case_id}')">重置</button>` : ''}
                </div>
            </div>`;
        }).join('');
    } catch (e) {
        document.getElementById('case-list').innerHTML = '<div class="empty-state">加载失败</div>';
    }
}

// ===== 开始庭审（实时进度 - WebSocket 版本） =====
async function startTrial(caseId) {
    try {
        currentCaseId = caseId;

        // 显示进度弹窗
        showModal(`<h2>⚖️ 庭审进行中</h2>
            <div id="trial-progress" style="margin:12px 0;">
                <div id="tp-phase" style="font-weight:600;font-size:1.1rem;margin-bottom:8px;">准备开庭...</div>
                <div id="tp-bar" style="height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden;margin-bottom:12px;">
                    <div id="tp-fill" style="height:100%;width:0%;background:var(--primary);border-radius:3px;transition:width .5s;"></div>
                </div>
                <div id="tp-lines" style="font-size:.85rem;color:var(--gray-600);max-height:300px;overflow-y:auto;text-align:left;background:var(--gray-50);padding:10px;border-radius:8px;font-family:monospace;white-space:pre-wrap;"></div>
            </div>
            <div id="tp-done" style="display:none;text-align:center;padding:20px;">
                <div style="font-size:2rem;margin-bottom:8px;">✅</div>
                <div id="tp-result" style="font-weight:600;margin-bottom:12px;"></div>
                <button class="btn btn-primary" onclick="closeTrial()">关闭</button>
            </div>`);

        // 启动异步庭审
        const r = await fetch(`/api/trial/${caseId}/async`, { method: 'POST' });
        const d = await r.json();
        if (!d.success) {
            alert('❌ ' + d.error);
            currentCaseId = null;
            return;
        }

        console.log('✅ 异步庭审已启动，任务ID:', d.task_id);
    } catch (e) {
        alert('❌ 请求失败: ' + e.message);
        currentCaseId = null;
    }
}

function updateTrialProgress(data) {
    const phaseEl = document.getElementById('tp-phase');
    const fillEl = document.getElementById('tp-fill');
    const linesEl = document.getElementById('tp-lines');
    const doneEl = document.getElementById('tp-done');
    const resultEl = document.getElementById('tp-result');

    if (phaseEl) {
        const phaseNames = {
            'starting': '准备开庭...',
            'prosecutor_opening': '👨‍⚖️ 检察官开场陈述',
            'prosecutor_opening_done': '👨‍⚖️ 检察官陈述完毕',
            'defender_opening': '👩‍⚖️ 辩护律师开场陈述',
            'defender_opening_done': '👩‍⚖️ 辩护律师陈述完毕',
            'debate': '⚔️ 交叉辩论',
            'prosecutor_rebut': '👨‍⚖️ 检察官反驳',
            'defender_cross': '👩‍⚖️ 辩护律师质询',
            'closing': '📝 结案陈词',
            'prosecutor_closing': '👨‍⚖️ 检察官结案陈词',
            'defender_closing': '👩‍⚖️ 辩护律师结案陈词',
            'jury': '🗳️ 陪审团评议中',
            'jury_done': '🗳️ 陪审团投票完成',
            'judge': '⚖️ 法官评议中',
            'verdict': '⚖️ 法官宣判',
            'executing': '⚙️ 执行判决中',
            'qa_check': '🔍 质量检查中',
            'strategy_selected': '🎯 选择执行策略',
            'copilot_executing': '🤖 Copilot 生成中',
            'claude_executing': '🧠 Claude Code 执行中',
            'claude_step': '📋 分步执行中',
            'fallback': '🔄 降级策略'
        };
        phaseEl.textContent = phaseNames[data.phase] || data.summary || data.phase;
    }

    if (fillEl && data.progress !== undefined) {
        fillEl.style.width = (data.progress * 100) + '%';
    }

    if (linesEl && data.message) {
        linesEl.textContent += data.message + '\n';
        linesEl.scrollTop = linesEl.scrollHeight;
    }

    if (data.status === 'done' || data.status === 'error') {
        if (phaseEl) phaseEl.textContent = data.status === 'done' ? '✅ 庭审结束' : '❌ 庭审失败';
        if (fillEl) {
            fillEl.style.width = '100%';
            fillEl.style.background = data.status === 'done' ? 'var(--success)' : 'var(--danger)';
        }
        if (doneEl) {
            doneEl.style.display = 'block';
            // 添加下载代码按钮和策略信息
            if (data.status === 'done' && data.case_id) {
                let strategyInfo = '';
                if (data.strategy_info) {
                    const complexityLabels = {
                        'trivial': '微小',
                        'simple': '简单',
                        'moderate': '中等',
                        'complex': '复杂',
                        'very_complex': '极复杂'
                    };
                    const complexity = complexityLabels[data.strategy_info.complexity] || data.strategy_info.complexity;
                    strategyInfo = `<div style="font-size:0.85rem;color:var(--gray-600);margin-bottom:8px;">
                        执行策略: ${data.strategy_info.strategy} | 复杂度: ${complexity} | 尝试: ${data.strategy_info.attempts?.length || 1} 次
                    </div>`;
                }
                doneEl.innerHTML = `
                    <div style="font-size:2rem;margin-bottom:8px;">✅</div>
                    <div id="tp-result" style="font-weight:600;margin-bottom:12px;">${data.result || data.summary}</div>
                    ${strategyInfo}
                    <div style="display:flex;gap:8px;justify-content:center;">
                        <button class="btn btn-primary" onclick="downloadCode('${data.case_id}')">📦 下载代码</button>
                        <button class="btn btn-secondary" onclick="closeTrial()">关闭</button>
                    </div>`;
            }
        }
        if (resultEl) resultEl.textContent = data.result || data.summary;
        loadCases();
        loadAgentStatus();
        currentCaseId = null;
    }
}

function appendExecutionOutput(output) {
    const linesEl = document.getElementById('tp-lines');
    if (linesEl) {
        linesEl.textContent += output;
        linesEl.scrollTop = linesEl.scrollHeight;
    }
}

function closeTrial() {
    currentCaseId = null;
    document.querySelector('.modal-overlay')?.remove();
}

// ===== 开始庭审（旧版本 - 轮询，保留作为后备） =====
async function startTrialPolling(caseId) {
    try {
        const r = await fetch(`/api/trial/${caseId}`, { method: 'POST' });
        const d = await r.json();
        if (!d.success) { alert('❌ ' + d.error); return; }

        // 显示进度弹窗
        showModal(`<h2>⚖️ 庭审进行中</h2>
            <div id="trial-progress" style="margin:12px 0;">
                <div id="tp-phase" style="font-weight:600;font-size:1.1rem;margin-bottom:8px;">准备开庭...</div>
                <div id="tp-bar" style="height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden;margin-bottom:12px;">
                    <div id="tp-fill" style="height:100%;width:0%;background:var(--primary);border-radius:3px;transition:width .5s;"></div>
                </div>
                <div id="tp-lines" style="font-size:.85rem;color:var(--gray-600);max-height:300px;overflow-y:auto;text-align:left;background:var(--gray-50);padding:10px;border-radius:8px;font-family:monospace;white-space:pre-wrap;"></div>
            </div>
            <div id="tp-done" style="display:none;text-align:center;padding:20px;">
                <div style="font-size:2rem;margin-bottom:8px;">✅</div>
                <div id="tp-result" style="font-weight:600;margin-bottom:12px;"></div>
                <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">关闭</button>
            </div>`);

        // 轮询进度
        const poll = setInterval(async () => {
            const pr = await fetch(`/api/trial-progress/${caseId}`);
            const pd = await pr.json();
            if (!pd.success) return;

            const p = pd.progress;
            const phaseEl = document.getElementById('tp-phase');
            const fillEl = document.getElementById('tp-fill');
            const linesEl = document.getElementById('tp-lines');
            const doneEl = document.getElementById('tp-done');
            const resultEl = document.getElementById('tp-result');

            if (phaseEl) {
                const phaseNames = {
                    'starting': '准备开庭...',
                    'prosecutor_opening': '👨‍⚖️ 检察官开场陈述',
                    'prosecutor_opening_done': '👨‍⚖️ 检察官陈述完毕',
                    'defender_opening': '👩‍⚖️ 辩护律师开场陈述',
                    'defender_opening_done': '👩‍⚖️ 辩护律师陈述完毕',
                    'debate': '⚔️ 交叉辩论',
                    'prosecutor_rebut': '👨‍⚖️ 检察官反驳',
                    'defender_cross': '👩‍⚖️ 辩护律师质询',
                    'closing': '📝 结案陈词',
                    'prosecutor_closing': '👨‍⚖️ 检察官结案陈词',
                    'defender_closing': '👩‍⚖️ 辩护律师结案陈词',
                    'jury': '🗳️ 陪审团评议中',
                    'jury_done': '🗳️ 陪审团投票完成',
                    'judge': '⚖️ 法官评议中',
                    'verdict': '⚖️ 法官宣判'
                };
                phaseEl.textContent = phaseNames[p.phase] || p.summary || p.phase;
            }
            if (fillEl) {
                const phases = ['starting','prosecutor_opening','defender_opening','debate','closing','jury','judge','verdict','done'];
                const idx = phases.indexOf(p.phase === 'starting' || p.phase === 'prosecutor_opening' || p.phase === 'prosecutor_opening_done' || p.phase === 'defender_opening' || p.phase === 'defender_opening_done' ? 'starting' :
                    p.phase.includes('debate') || p.phase === 'prosecutor_rebut' || p.phase === 'defender_cross' ? 'debate' :
                    p.phase === 'prosecutor_closing' || p.phase === 'defender_closing' ? 'closing' :
                    p.phase === 'jury' || p.phase === 'jury_done' ? 'jury' :
                    p.phase === 'judge' ? 'judge' :
                    p.phase === 'verdict' ? 'verdict' : p.phase);
                if (idx > 0) fillEl.style.width = ((idx / (phases.length - 1)) * 100) + '%';
            }

            if (p.status === 'done' || p.status === 'error') {
                clearInterval(poll);
                if (phaseEl) phaseEl.textContent = p.status === 'done' ? '✅ 庭审结束' : '❌ 庭审失败';
                if (fillEl) fillEl.style.width = '100%';
                fillEl.style.background = p.status === 'done' ? 'var(--success)' : 'var(--danger)';
                if (doneEl) doneEl.style.display = 'block';
                if (resultEl) resultEl.textContent = p.result || p.summary;
                loadCases();
                loadAgentStatus();
            }
        }, 1000);
    } catch (e) {
        alert('❌ 请求失败: ' + e.message);
    }
}

// ===== 重申 =====
async function retrial(caseId) {
    if (!confirm(`确定对案件 ${caseId} 进行重申吗？会清除旧判决。`)) return;
    try {
        const r = await fetch(`/api/motions/${caseId}/retrial`, { method: 'POST' });
        const d = await r.json();
        if (d.success) { loadCases(); }
        else { alert('重申失败: ' + d.error); }
    } catch (e) { alert('重申失败: ' + e.message); }
}

// ===== 下载生成的代码 =====
async function downloadCode(caseId) {
    try {
        // 先检查是否有代码输出
        const checkResp = await fetch(`/api/cases/${caseId}/code-versions`);
        const checkData = await checkResp.json();

        if (!checkData.versions || checkData.versions.length === 0) {
            alert('该案件暂无生成的代码');
            return;
        }

        // 显示版本选择（如果有多个版本）
        if (checkData.versions.length > 1) {
            const versionList = checkData.versions.map((v, i) =>
                `${i + 1}. ${v.version_id} (${v.files.length} 个文件)`
            ).join('\n');

            if (!confirm(`该案件有 ${checkData.versions.length} 个代码版本:\n${versionList}\n\n点击确定下载最新版本`)) {
                return;
            }
        }

        // 下载最新版本
        window.location.href = `/api/cases/${caseId}/download-code`;

    } catch (e) {
        alert('下载失败: ' + e.message);
    }
}

// ===== 重置卡住案件 =====
async function resetTrial(caseId) {
    if (!confirm(`确定重置案件 ${caseId} 吗？重置后可以重新庭审。`)) return;
    try {
        const r = await fetch(`/api/motions/${caseId}/reset`, { method: 'POST' });
        const d = await r.json();
        if (d.success) {
            loadCases();
        } else {
            alert('重置失败: ' + d.error);
        }
    } catch (e) {
        alert('重置失败: ' + e.message);
    }
}

// ===== 查看判决 =====
async function showVerdict(caseId) {
    try {
        const r = await fetch(`/api/verdicts/${caseId}`);
        const d = await r.json();
        if (!d.success) { alert('判决不存在'); return; }
        const v = d.verdict;
        const vt = { approved: '✅ 批准', rejected: '❌ 驳回', modified: '⚠️ 修改后批准', approved_with_modifications: '⚠️ 有条件批准', deferred: '⏸️ 延期' }[v.verdict_type] || v.verdict_type;
        const verdictClass = { approved: 'verdict-approved', rejected: 'verdict-rejected', modified: 'verdict-modified', approved_with_modifications: 'verdict-modified', deferred: 'verdict-modified' }[v.verdict_type] || '';
        showModal(`
            <h2>⚖️ 判决书</h2>
            <p><strong>案件：</strong>${v.case_id}</p>
            <span class="verdict-badge ${verdictClass}">${vt}</span>
            <div class="label">判决理由</div>
            <pre>${esc(v.reasoning)}</pre>
            ${v.approved_changes && v.approved_changes.length ? `<div class="label">✅ 批准的变更</div><pre>${esc(v.approved_changes.join('\n'))}</pre>` : ''}
            ${v.execution_plan && v.execution_plan.length ? `<div class="label">📋 执行计划</div><pre>${esc(v.execution_plan.join('\n'))}</pre>` : ''}
        `);
    } catch (e) {
        alert('加载判决失败');
    }
}

// ===== 弹窗 =====
function showModal(html) {
    const existing = document.querySelector('.modal-overlay');
    if (existing) existing.remove();
    const ov = document.createElement('div');
    ov.className = 'modal-overlay';
    ov.innerHTML = `<div class="modal-box"><button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>${html}</div>`;
    ov.addEventListener('click', e => { if (e.target === ov) ov.remove(); });
    document.body.appendChild(ov);
}

// ===== API 设置 =====
async function loadApiSettings() {
    try {
        const r = await fetch('/api/settings');
        const d = await r.json();
        if (!d.success) return;
        document.getElementById('api-url').value = d.settings.url || '';
        document.getElementById('api-key').value = d.settings.api_key || '';
        document.getElementById('api-model').value = d.settings.model || 'gpt-4o-mini';

        // 恢复每个 Agent 的开关和独立配置
        const agents = d.settings.agents || {};
        document.querySelectorAll('.switch-group').forEach(group => {
            const id = group.dataset.agent;
            const cb = group.querySelector('.switch-row input[type="checkbox"]');
            const mode = group.querySelector('.switch-mode');
            const fields = group.querySelector('.agent-api-fields');
            const cfg = agents[id] || {};

            const isApi = cfg.mode === 'api';
            if (cb) {
                cb.checked = isApi;
                cb.onchange = () => { toggleAgentFields(group); saveSwitches(); };
                mode.textContent = isApi ? '外部 API' : '规则引擎';
                mode.className = 'switch-mode' + (isApi ? ' api' : '');
            }
            // 恢复独立配置
            if (isApi) {
                const urlInp = group.querySelector('.agent-url');
                const keyInp = group.querySelector('.agent-key');
                const modelInp = group.querySelector('.agent-model');
                if (urlInp) urlInp.value = cfg.url || '';
                if (keyInp) keyInp.value = cfg.api_key || '';
                if (modelInp) modelInp.value = cfg.model || '';
                fields.classList.add('open');
            }
        });
    } catch (e) { /* ignore */ }
}

function toggleAgentFields(group) {
    const cb = group.querySelector('.switch-row input[type="checkbox"]');
    const fields = group.querySelector('.agent-api-fields');
    const mode = group.querySelector('.switch-mode');
    fields.classList.toggle('open', cb.checked);
    mode.textContent = cb.checked ? '外部 API' : '规则引擎';
    mode.className = 'switch-mode' + (cb.checked ? ' api' : '');
}

function saveSwitches() {
    const agents = {};
    document.querySelectorAll('.switch-group').forEach(group => {
        const id = group.dataset.agent;
        const cb = group.querySelector('.switch-row input[type="checkbox"]');
        if (!cb) return;
        if (cb.checked) {
            const urlInp = group.querySelector('.agent-url');
            const keyInp = group.querySelector('.agent-key');
            const modelInp = group.querySelector('.agent-model');
            agents[id] = { mode: 'api', url: urlInp ? urlInp.value.trim() : '', api_key: keyInp ? keyInp.value.trim() : '', model: modelInp ? modelInp.value.trim() : '' };
        } else {
            agents[id] = { mode: 'rule' };
        }
    });
    fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agents })
    }).catch(() => {});
}

function toggleKey() {
    const inp = document.getElementById('api-key');
    inp.type = inp.type === 'password' ? 'text' : 'password';
}

async function saveApi() {
    const data = {
        url: document.getElementById('api-url').value.trim(),
        api_key: document.getElementById('api-key').value.trim(),
        model: document.getElementById('api-model').value.trim() || 'gpt-4o-mini',
        agents: {}
    };

    document.querySelectorAll('.switch-group').forEach(group => {
        const id = group.dataset.agent;
        const cb = group.querySelector('.switch-row input[type="checkbox"]');
        if (!cb) return;
        if (cb.checked) {
            const urlInp = group.querySelector('.agent-url');
            const keyInp = group.querySelector('.agent-key');
            const modelInp = group.querySelector('.agent-model');
            data.agents[id] = {
                mode: 'api',
                url: urlInp ? urlInp.value.trim() : '',
                api_key: keyInp ? keyInp.value.trim() : '',
                model: modelInp ? modelInp.value.trim() : ''
            };
        } else {
            data.agents[id] = { mode: 'rule' };
        }
    });

    try {
        const r = await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const d = await r.json();
        showApiMsg(d.success ? '✅ 设置已保存！' : '❌ ' + d.error, d.success ? 'success' : 'error');
        if (d.success) loadAgentStatus();
    } catch (e) {
        showApiMsg('❌ 保存失败: ' + e.message, 'error');
    }
}

async function testApi() {
    const data = {
        url: document.getElementById('api-url').value.trim(),
        api_key: document.getElementById('api-key').value.trim(),
        model: document.getElementById('api-model').value.trim() || 'gpt-4o-mini'
    };
    if (!data.url || !data.api_key) { showApiMsg('请先填写 API 地址和 Key', 'error'); return; }

    showApiMsg('🔄 测试连接中...', 'info');
    try {
        const r = await fetch('/api/test-api', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const d = await r.json();
        showApiMsg(d.success ? '✅ 连接成功！' : '❌ ' + (d.error || '连接失败'), d.success ? 'success' : 'error');
    } catch (e) {
        showApiMsg('❌ 连接失败: ' + e.message, 'error');
    }
}

function showApiMsg(msg, type) {
    const el = document.getElementById('api-msg');
    el.style.display = 'block'; el.className = 'msg-box ' + type; el.textContent = msg;
}

// ===== 工具函数 =====
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function fmt(d) { return new Date(d).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }); }
function getTypeLabel(t) { return { new_feature: '新功能', bug_fix: 'Bug修复', refactor: '重构', performance: '性能优化', security: '安全', architecture: '架构' }[t] || t; }

// ===== 自由讨论 =====
async function startDiscuss() {
    const q = document.getElementById('discuss-question').value.trim();
    if (!q) { showDiscussMsg('请输入问题', 'error'); return; }

    const btn = document.getElementById('btn-discuss');
    btn.disabled = true; btn.textContent = '讨论中...';
    showDiscussMsg('🔄 讨论进行中，请稍候...', 'info');
    document.getElementById('discuss-results').style.display = 'none';
    document.getElementById('discuss-summary-area').style.display = 'none';

    try {
        const r = await fetch('/api/discuss', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: q })
        });
        const d = await r.json();

        if (!d.success) { showDiscussMsg('❌ ' + d.error, 'error'); btn.disabled = false; btn.textContent = '🚀 开始讨论'; return; }

        // 显示结果
        document.getElementById('discuss-results').style.display = 'block';

        const agents = {
            'prosecutor': { label: '方案提出', el: 'discuss-prosecutor' },
            'defender': { label: '风险审查', el: 'discuss-defender' },
            'jury': { label: '专家补充', el: 'discuss-jury' }
        };

        for (const [id, info] of Object.entries(agents)) {
            const el = document.getElementById(info.el);
            if (d.answers[id]) {
                el.innerHTML = formatDiscussAnswer(d.answers[id]);
            } else {
                el.innerHTML = '<span class="dim">无回答</span>';
            }
        }

        // 法官总结
        if (d.summary) {
            document.getElementById('discuss-summary-area').style.display = 'block';
            document.getElementById('discuss-summary').innerHTML = formatDiscussAnswer(d.summary);
        }

        showDiscussMsg('✅ 讨论完成', 'success');
    } catch (e) {
        showDiscussMsg('❌ 失败: ' + e.message, 'error');
    }
    btn.disabled = false; btn.textContent = '🚀 开始讨论';
}

function formatDiscussAnswer(text) {
    if (!text) return '<span class="dim">无回答</span>';
    if (text.startsWith('错误:')) return `<span class="error-text">${esc(text)}</span>`;

    // 把代码块转成可执行的 HTML
    let html = '';
    let remaining = text;
    const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
        // 代码块前的内容
        if (match.index > lastIndex) {
            html += esc(text.slice(lastIndex, match.index)).replace(/\n/g, '<br>');
        }

        const lang = match[1].toLowerCase();
        const code = match[2].trim();

        if (lang === 'bash' || lang === 'sh' || lang === 'shell' || lang === 'cmd') {
            // 可执行的命令
            const safeCode = esc(code);
            const cmdAttr = esc(code).replace(/"/g, '&quot;');
            html += `<div class="exec-block"><pre class="code-block">${safeCode}</pre><button class="btn btn-sm btn-exec" data-cmd="${cmdAttr}" onclick="execCmd(this)">▶ 执行</button></div>`;
        } else {
            html += `<pre class="code-block">${esc(code)}</pre>`;
        }

        lastIndex = match.index + match[0].length;
    }

    // 剩余内容
    if (lastIndex < text.length) {
        html += esc(text.slice(lastIndex)).replace(/\n/g, '<br>');
    }

    return html || esc(text).replace(/\n/g, '<br>');
}

async function execCmd(btn) {
    const cmd = btn.dataset.cmd;
    if (!cmd) return;
    if (!confirm(`确定执行以下命令吗？\n\n${cmd}`)) return;
    btn.disabled = true; btn.textContent = '执行中...';
    try {
        const r = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cmd })
        });
        const d = await r.json();
        if (d.success) {
            let output = '';
            if (d.stdout) output += '输出:\n' + d.stdout;
            if (d.stderr) output += '\n错误:\n' + d.stderr;
            if (d.returncode !== 0) output += `\n退出码: ${d.returncode}`;
            alert(output || '✅ 执行成功（无输出）');
        } else {
            alert('❌ 执行失败: ' + (d.error || '未知错误'));
        }
    } catch (e) {
        alert('❌ 请求失败: ' + e.message);
    }
    btn.disabled = false; btn.textContent = '▶ 执行';
}

function showDiscussMsg(msg, type) {
    const el = document.getElementById('discuss-status');
    el.style.display = 'block'; el.className = 'msg-box ' + type; el.textContent = msg;
}

// ===== 文件选择提示 =====
document.getElementById('discuss-file').addEventListener('change', function() {
    const info = document.getElementById('discuss-file-info');
    if (this.files.length > 0) {
        info.textContent = `已选择 ${this.files.length} 个文件`;
    } else {
        info.textContent = '';
    }
});

document.getElementById('motion-file').addEventListener('change', function() {
    const info = document.getElementById('file-info');
    if (this.files.length > 0) {
        const names = Array.from(this.files).map(f => `${f.name} (${(f.size / 1024).toFixed(1)} KB)`);
        info.textContent = `已选择 ${this.files.length} 个文件: ${names.join(', ')}`;
    } else {
        info.textContent = '';
    }
});

// ===== 初始化 =====
loadCases();
loadAgentStatus();
// 每 15 秒刷新 Agent 状态
setInterval(loadAgentStatus, 15000);

// ===== 用户头像管理 =====
let selectedAvatarFile = null;
let currentAvatarUrl = null;

document.getElementById('avatar-file').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    // 验证文件类型
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showAvatarMsg('❌ 不支持的文件格式，仅支持 PNG、JPG、GIF、WebP', 'error');
        return;
    }

    // 验证文件大小
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        showAvatarMsg('❌ 文件过大，最大支持 5MB', 'error');
        return;
    }

    selectedAvatarFile = file;

    // 预览图片
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('avatar-img').src = e.target.result;
        document.getElementById('btn-upload-avatar').disabled = false;
        document.getElementById('avatar-info').textContent = `已选择: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    };
    reader.readAsDataURL(file);
});

async function uploadAvatar() {
    if (!selectedAvatarFile) {
        showAvatarMsg('❌ 请先选择头像文件', 'error');
        return;
    }

    const btn = document.getElementById('btn-upload-avatar');
    btn.disabled = true;
    btn.textContent = '上传中...';

    try {
        const formData = new FormData();
        formData.append('avatar', selectedAvatarFile);
        formData.append('user_id', 'default_user');

        const response = await fetch('/api/avatar/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            currentAvatarUrl = data.avatar_url;
            showAvatarMsg('✅ ' + data.message, 'success');
            document.getElementById('btn-delete-avatar').style.display = 'inline-block';
            document.getElementById('avatar-info').textContent = `当前头像: ${data.filename}`;
            selectedAvatarFile = null;
        } else {
            showAvatarMsg('❌ ' + data.error, 'error');
            btn.disabled = false;
        }
    } catch (error) {
        showAvatarMsg('❌ 上传失败: ' + error.message, 'error');
        btn.disabled = false;
    }

    btn.textContent = '💾 上传';
}

async function deleteAvatar() {
    if (!currentAvatarUrl) {
        showAvatarMsg('❌ 没有可删除的头像', 'error');
        return;
    }

    if (!confirm('确定要删除当前头像吗？')) return;

    try {
        const filename = currentAvatarUrl.split('/').pop();
        const response = await fetch(`/api/avatar/${filename}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showAvatarMsg('✅ ' + data.message, 'success');
            document.getElementById('avatar-img').src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Crect fill=%22%23e5e7eb%22 width=%22120%22 height=%22120%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2248%22 fill=%22%236b7280%22%3E👤%3C/text%3E%3C/svg%3E';
            document.getElementById('btn-delete-avatar').style.display = 'none';
            document.getElementById('avatar-info').textContent = '';
            currentAvatarUrl = null;
        } else {
            showAvatarMsg('❌ ' + data.error, 'error');
        }
    } catch (error) {
        showAvatarMsg('❌ 删除失败: ' + error.message, 'error');
    }
}

function showAvatarMsg(msg, type) {
    const el = document.getElementById('avatar-msg');
    el.style.display = 'block';
    el.className = 'msg-box ' + type;
    el.textContent = msg;
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

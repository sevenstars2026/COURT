// 庭审系统 Web UI - 前端逻辑

const API_BASE = '';

// 标签页切换
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;

        // 更新标签页状态
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // 更新内容区域
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        // 加载对应数据
        if (tabName === 'dashboard') {
            loadDashboard();
        } else if (tabName === 'motions') {
            loadMotions();
        } else if (tabName === 'evidence') {
            loadCasesForEvidence();
        }
    });
});

// 加载仪表盘
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;

            // 更新统计数字
            document.getElementById('total-cases').textContent = stats.total_cases;
            document.getElementById('pending-cases').textContent = stats.by_status.pending || 0;
            document.getElementById('approved-cases').textContent = stats.by_status.decided || 0;
            document.getElementById('rejected-cases').textContent = stats.by_status.rejected || 0;

            // 显示最近案件
            const recentCasesDiv = document.getElementById('recent-cases');
            recentCasesDiv.innerHTML = stats.recent_cases.map(c => `
                <div class="case-card" onclick="showMotionDetail('${c.case_id}')">
                    <div class="case-header">
                        <div class="case-title">${c.title}</div>
                        <span class="case-badge badge-${c.status}">${getStatusText(c.status)}</span>
                    </div>
                    <div class="case-meta">
                        案件编号: ${c.case_id} | 提交时间: ${formatDate(c.filed_at)}
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载仪表盘失败:', error);
    }
}

// 加载动议列表
async function loadMotions() {
    try {
        const response = await fetch(`${API_BASE}/api/motions`);
        const data = await response.json();

        if (data.success) {
            displayMotions(data.motions);
        }
    } catch (error) {
        console.error('加载动议列表失败:', error);
    }
}

// 显示动议列表
function displayMotions(motions) {
    const motionListDiv = document.getElementById('motion-list');

    if (motions.length === 0) {
        motionListDiv.innerHTML = '<p>暂无动议</p>';
        return;
    }

    motionListDiv.innerHTML = motions.map(motion => `
        <div class="case-card" onclick="showMotionDetail('${motion.case_id}')">
            <div class="case-header">
                <div class="case-title">${motion.title}</div>
                <span class="case-badge badge-${motion.status}">${getStatusText(motion.status)}</span>
            </div>
            <div class="case-meta">
                类型: ${getTypeText(motion.motion_type)} |
                优先级: ${motion.priority}/10 |
                提交时间: ${formatDate(motion.filed_at)}
            </div>
            <p style="margin-top: 10px; color: #6b7280;">${motion.description}</p>
        </div>
    `).join('');
}

// 显示动议详情
async function showMotionDetail(caseId) {
    try {
        const response = await fetch(`${API_BASE}/api/motions/${caseId}`);
        const data = await response.json();

        if (data.success) {
            const motion = data.motion;
            const modal = document.getElementById('motion-modal');
            const detailDiv = document.getElementById('motion-detail');

            detailDiv.innerHTML = `
                <h2>${motion.title}</h2>
                <p><strong>案件编号:</strong> ${motion.case_id}</p>
                <p><strong>状态:</strong> <span class="case-badge badge-${motion.status}">${getStatusText(motion.status)}</span></p>
                <p><strong>类型:</strong> ${getTypeText(motion.motion_type)}</p>
                <p><strong>优先级:</strong> ${motion.priority}/10</p>
                <p><strong>提交时间:</strong> ${formatDate(motion.filed_at)}</p>

                <h3>描述</h3>
                <p>${motion.description}</p>

                ${motion.proposed_changes.length > 0 ? `
                    <h3>提议的变更</h3>
                    <ul>${motion.proposed_changes.map(c => `<li>${c}</li>`).join('')}</ul>
                ` : ''}

                ${motion.affected_files.length > 0 ? `
                    <h3>影响的文件</h3>
                    <ul>${motion.affected_files.map(f => `<li><code>${f}</code></li>`).join('')}</ul>
                ` : ''}

                ${motion.risks.length > 0 ? `
                    <h3>已知风险</h3>
                    <ul>${motion.risks.map(r => `<li>${r}</li>`).join('')}</ul>
                ` : ''}

                ${motion.benefits.length > 0 ? `
                    <h3>预期收益</h3>
                    <ul>${motion.benefits.map(b => `<li>${b}</li>`).join('')}</ul>
                ` : ''}

                ${motion.status === 'pending' ? `
                    <button class="btn btn-primary" onclick="startTrial('${motion.case_id}')">
                        开始庭审
                    </button>
                ` : ''}

                ${motion.status === 'decided' ? `
                    <button class="btn btn-primary" onclick="showVerdict('${motion.case_id}')">
                        查看判决
                    </button>
                ` : ''}
            `;

            modal.style.display = 'block';
        }
    } catch (error) {
        console.error('加载动议详情失败:', error);
    }
}

// 开始庭审
async function startTrial(caseId) {
    if (!confirm('确定要开始庭审吗？')) return;

    try {
        const response = await fetch(`${API_BASE}/api/trial/${caseId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_rounds: 2, use_llm: false })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
            document.getElementById('motion-modal').style.display = 'none';
            loadDashboard();
        } else {
            alert('庭审失败: ' + data.error);
        }
    } catch (error) {
        console.error('开始庭审失败:', error);
        alert('开始庭审失败');
    }
}

// 查看判决
async function showVerdict(caseId) {
    try {
        const response = await fetch(`${API_BASE}/api/verdicts/${caseId}`);
        const data = await response.json();

        if (data.success) {
            alert(data.verdict_text);
        }
    } catch (error) {
        console.error('加载判决失败:', error);
    }
}

// 提交动议表单
document.getElementById('motion-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        title: formData.get('title'),
        motion_type: formData.get('motion_type'),
        description: formData.get('description'),
        proposed_changes: formData.get('proposed_changes').split('\n').filter(s => s.trim()),
        affected_files: formData.get('affected_files').split('\n').filter(s => s.trim()),
        risks: formData.get('risks').split('\n').filter(s => s.trim()),
        benefits: formData.get('benefits').split('\n').filter(s => s.trim()),
        priority: parseInt(formData.get('priority'))
    };

    try {
        const response = await fetch(`${API_BASE}/api/motions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);
            e.target.reset();
            document.getElementById('priority-value').textContent = '5';
        } else {
            alert('提交失败: ' + result.error);
        }
    } catch (error) {
        console.error('提交动议失败:', error);
        alert('提交失败');
    }
});

// 优先级滑块
document.querySelector('input[name="priority"]').addEventListener('input', (e) => {
    document.getElementById('priority-value').textContent = e.target.value;
});

// 加载案件列表（用于证据管理）
async function loadCasesForEvidence() {
    try {
        const response = await fetch(`${API_BASE}/api/motions`);
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('evidence-case-select');
            select.innerHTML = '<option value="">请选择案件</option>' +
                data.motions.map(m => `<option value="${m.case_id}">${m.title} (${m.case_id})</option>`).join('');
        }
    } catch (error) {
        console.error('加载案件列表失败:', error);
    }
}

// 加载证据列表
document.getElementById('evidence-case-select').addEventListener('change', async (e) => {
    const caseId = e.target.value;
    if (!caseId) {
        document.getElementById('evidence-list').innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/evidence/${caseId}`);
        const data = await response.json();

        if (data.success) {
            const evidenceListDiv = document.getElementById('evidence-list');

            if (data.evidence.length === 0) {
                evidenceListDiv.innerHTML = '<p>该案件暂无证据</p>';
                return;
            }

            evidenceListDiv.innerHTML = data.evidence.map(e => `
                <div class="evidence-card">
                    <div class="evidence-header">
                        <div class="evidence-title">${e.title}</div>
                        <span class="evidence-type">${e.evidence_type}</span>
                    </div>
                    <p><strong>提交者:</strong> ${getSubmitterText(e.submitted_by)}</p>
                    <p><strong>描述:</strong> ${e.description}</p>
                    <div class="evidence-content">${e.content}</div>
                    <p style="font-size: 0.85rem; color: #6b7280; margin-top: 10px;">
                        提交时间: ${formatDate(e.submitted_at)}
                    </p>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载证据列表失败:', error);
    }
});

// 模态框关闭
document.querySelector('.close').addEventListener('click', () => {
    document.getElementById('motion-modal').style.display = 'none';
});

window.addEventListener('click', (e) => {
    const modal = document.getElementById('motion-modal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// 工具函数
function getStatusText(status) {
    const statusMap = {
        'pending': '待审理',
        'in_trial': '审理中',
        'deliberation': '评议中',
        'decided': '已判决',
        'rejected': '已驳回'
    };
    return statusMap[status] || status;
}

function getTypeText(type) {
    const typeMap = {
        'feature': '新功能',
        'bugfix': 'Bug修复',
        'refactor': '重构',
        'performance': '性能优化',
        'security': '安全',
        'documentation': '文档',
        'test': '测试'
    };
    return typeMap[type] || type;
}

function getSubmitterText(submitter) {
    const submitterMap = {
        'prosecutor': '检察官',
        'defender': '辩护律师',
        'jury': '陪审团'
    };
    return submitterMap[submitter] || submitter;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

"""
庭审系统 Web UI - Flask 应用（异步版本）
"""
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from pathlib import Path
import json
import os
import requests
import threading
import io
import time
from datetime import datetime

from courtroom import Court, MotionType
from courtroom.evidence import EvidenceManager
from courtroom.websocket_events import socketio
from courtroom.api_routes import api_bp

app = Flask(__name__,
            static_folder='courtroom/web/static',
            template_folder='courtroom/web/templates')
CORS(app)

# 注册 API 蓝图
app.register_blueprint(api_bp)

# 初始化 SocketIO
socketio.init_app(app, cors_allowed_origins="*")

# 初始化
courtroom_root = Path(__file__).parent / "courtroom"
court = Court(courtroom_root, use_llm=False)
evidence_manager = EvidenceManager(courtroom_root / "evidence")

api_settings_file = courtroom_root / "api_settings.json"

# ====== API 设置 ======

def load_api_settings():
    if api_settings_file.exists():
        with open(api_settings_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"url": "", "api_key": "", "model": "gpt-4o-mini", "agents": {}}


def save_api_settings(data):
    with open(api_settings_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_agent_api(agent_id):
    """获取 Agent 的 API 配置（合并全局 + 个人设置）"""
    settings = load_api_settings()
    global_url = settings.get("url", "").rstrip("/")
    global_key = settings.get("api_key", "")
    global_model = settings.get("model", "gpt-4o-mini")

    agent_cfg = settings.get("agents", {}).get(agent_id, {})
    if agent_cfg.get("mode") != "api":
        return None

    url = (agent_cfg.get("url") or global_url).rstrip("/")
    key = agent_cfg.get("api_key") or global_key
    model = agent_cfg.get("model") or global_model

    if not url or not key:
        return None
    return {"url": url, "api_key": key, "model": model}


def call_openai_api(motion, api_conf, role_prompt, user_extra=""):
    """调用 OpenAI 兼容 API，失败返回 None"""
    if not api_conf:
        return None
    url = api_conf["url"].rstrip("/")
    try:
        headers = {"Authorization": f"Bearer {api_conf['api_key']}", "Content-Type": "application/json"}
        payload = {
            "model": api_conf["model"],
            "messages": [
                {"role": "system", "content": role_prompt},
                {"role": "user", "content": f"动议标题：{motion.title}\n描述：{motion.description}\n{user_extra}"}
            ]
        }
        resp = requests.post(f"{url}/chat/completions", headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"API 调用失败: {e}")
    return None


def call_openai_api_with_error(motion, api_conf, role_prompt, user_extra=""):
    """调用 API，失败时返回错误信息而不是静默退回"""
    if not api_conf:
        return "错误: 未配置 API"
    url = api_conf["url"].rstrip("/")
    # 重试一次
    for attempt in range(2):
        try:
            headers = {"Authorization": f"Bearer {api_conf['api_key']}", "Content-Type": "application/json"}
            payload = {
                "model": api_conf["model"],
                "messages": [
                    {"role": "system", "content": role_prompt},
                    {"role": "user", "content": f"动议标题：{motion.title}\n描述：{motion.description}\n{user_extra}"}
                ]
            }
            resp = requests.post(f"{url}/chat/completions", headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                return f"错误: API 返回状态码 {resp.status_code} - {resp.text[:200]}"
        except Exception as e:
            if attempt == 0:
                continue  # 重试一次
            return f"错误: API 调用异常 - {e}"
    return "错误: API 调用失败"


# ====== Agent 状态 ======

AGENT_DEFS = {
    "prosecutor":     {"label": "检察官",     "icon": "👨‍⚖️"},
    "defender":       {"label": "辩护律师",   "icon": "👩‍⚖️"},
    "judge":          {"label": "法官",       "icon": "⚖️"},
    "jury":           {"label": "陪审团",     "icon": "🗳️"},
    "court_reporter": {"label": "书记员",     "icon": "📝"},
}


@app.route('/api/agents/status')
def agent_status():
    """返回各 Agent 的运行模式"""
    settings = load_api_settings()
    agent_configs = settings.get("agents", {})
    result = {}
    for agent_id, info in AGENT_DEFS.items():
        cfg = agent_configs.get(agent_id, {})
        mode = cfg.get("mode", "rule") if isinstance(cfg, dict) else "rule"
        api = get_agent_api(agent_id)
        result[agent_id] = {
            "label": info["label"],
            "icon": info["icon"],
            "mode": mode,
            "model": api["model"] if api else None,
        }
    return jsonify({"success": True, "agents": result})


@app.route('/api/agents/health')
def agent_health():
    """检测各 Agent 配置的 API 是否连通"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def check(agent_id, api_conf):
        try:
            headers = {"Authorization": f"Bearer {api_conf['api_key']}", "Content-Type": "application/json", "Accept": "application/json"}
            payload = {"model": api_conf["model"], "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}
            r = requests.post(f"{api_conf['url'].rstrip('/')}/chat/completions", json=payload, headers=headers, timeout=5)
            return agent_id, r.status_code == 200
        except Exception as e:
            return agent_id, False

    result = {"prosecutor": "rule", "defender": "rule", "judge": "rule", "jury": "rule", "court_reporter": "rule"}
    tasks = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for agent_id in ["prosecutor", "defender", "judge", "jury"]:
            api = get_agent_api(agent_id)
            if api:
                tasks.append(pool.submit(check, agent_id, api))
        for f in as_completed(tasks):
            aid, ok = f.result()
            result[aid] = "online" if ok else "offline"

    return jsonify({"success": True, "health": result})


# ====== 庭审进度追踪 ======

trial_progress = {}
trial_lock = threading.Lock()


def make_progress_callback(case_id):
    """创建进度回调函数"""
    def cb(phase, summary):
        with trial_lock:
            if case_id not in trial_progress:
                trial_progress[case_id] = {"lines": [], "status": "running"}
            trial_progress[case_id]["phase"] = phase
            trial_progress[case_id]["summary"] = summary
    return cb


def load_evidence_text(case_id):
    """加载案件的上传证据，拼接成文本"""
    try:
        evs = evidence_manager.list_evidence(case_id)
        parts = []
        for ev in evs:
            if ev.content and len(ev.content.strip()) > 10:
                parts.append(f"=== {ev.title} ===\n{ev.content[:8000]}")
        return "\n\n".join(parts)
    except:
        return ""


def setup_agents_for_trial(case_id=""):
    """根据 API 配置设置 Agent，让它们分析代码给出优化建议"""
    from courtroom.schemas import Argument, ArgumentType
    from datetime import datetime

    used_api = False
    code = load_evidence_text(case_id)

    api_p = get_agent_api("prosecutor")
    if api_p:
        used_api = True
        def _make_proxy(api_conf, name):
            return type('Proxy', (), {
                'name': name,
                'opening_statement': lambda self, m, _a=api_conf, _c=code: Argument(
                    speaker=name, argument_type=ArgumentType.OPENING,
                    content=call_openai_api(m, _a, f'你是一位方案提出者。请仔细分析以下需求，提出具体、可行的实施方案。如果有代码，直接输出修改后的代码。\n\n参考材料：\n{_c[:4000]}\n\n请直接给出完整方案。') or '方案如下。',
                    timestamp=datetime.now()),
                'rebut': lambda self, a, m, _a=api_conf, _c=code: Argument(
                    speaker=name, argument_type=ArgumentType.REBUTTAL,
                    content=call_openai_api(m, _a, f'请审查以下方案，指出问题和改进点，并给出修正版。\n\n当前方案：{a.content[:1000]}\n\n参考材料：{_c[:2000]}') or '改进如下。',
                    timestamp=datetime.now()),
                'closing_statement': lambda self, m, _a=api_conf, _c=code, **kw: Argument(
                    speaker=name, argument_type=ArgumentType.CLOSING,
                    content=call_openai_api(m, _a, f'请综合所有讨论，输出最终方案。\n\n参考材料：\n{_c[:3000]}') or '最终方案如下。',
                    timestamp=datetime.now()),
            })()
        court.prosecutor = _make_proxy(api_p, 'prosecutor')
    else:
        from courtroom.agents import Prosecutor
        court.prosecutor = Prosecutor()

    api_d = get_agent_api("defender")
    if api_d:
        used_api = True
        court.defender = type('Proxy', (), {
            'name': 'defender',
            'opening_statement': lambda self, m, _a=api_d, _c=code: Argument(
                speaker='defender', argument_type=ArgumentType.OPENING,
                content=call_openai_api(m, _a, f'你是一位审查专家。请审查以下需求和方案，指出潜在问题、风险和被忽略的地方。\n\n材料：\n{_c[:4000]}\n\n直接指出具体问题。') or '审查意见如下。',
                timestamp=datetime.now()),
            'cross_examine': lambda self, a, m, _a=api_d, _c=code: Argument(
                speaker='defender', argument_type=ArgumentType.REBUTTAL,
                content=call_openai_api(m, _a, f'请审查对方方案，指出遗漏和风险，给出改进版本。\n\n对方方案：{a.content[:1000]}\n\n参考材料：{_c[:2000]}') or '改进如下。',
                timestamp=datetime.now()),
            'closing_statement': lambda self, m, _a=api_d, _c=code, **kw: Argument(
                speaker='defender', argument_type=ArgumentType.CLOSING,
                content=call_openai_api(m, _a, f'总结所有审查意见，输出最终建议。\n\n材料：\n{_c[:3000]}') or '总结如下。',
                timestamp=datetime.now()),
        })()
    else:
        from courtroom.agents import Defender
        court.defender = Defender()

    api_j = get_agent_api("judge")
    if api_j:
        used_api = True
        original_make = court.judge.make_verdict
        def patched_verdict(case_id, transcript, reasoning="", _api=api_j, _orig=original_make):
            debate = f"【参考材料】\n{code[:3000]}\n\n【讨论记录】\n"
            for arg in transcript.arguments:
                role = "方案提出者" if arg.speaker == "prosecutor" else "审查专家" if arg.speaker == "defender" else arg.speaker
                debate += f"{role}：{arg.content[:500]}\n\n"
            if transcript.jury_votes:
                for v in transcript.jury_votes:
                    debate += f"陪审团({v.juror})：{v.vote.value} - {v.reasoning[:200]}\n"
            result = call_openai_api_with_error(transcript.motion, _api,
                f'你是决策者。综合以上所有讨论，输出最终结论。如果涉及代码，输出完整代码。\n\n{debate[:5000]}')
            if result.startswith("错误:"):
                reasoning = result
            else:
                reasoning = result
            return _orig(case_id, transcript, reasoning=reasoning)
        court.judge.make_verdict = patched_verdict

    return used_api


def background_trial(case_id):
    """后台运行庭审"""
    try:
        setup_agents_for_trial(case_id)
        cb = make_progress_callback(case_id)
        result = court.trial(case_id, max_rounds=2, on_progress=cb)
        with trial_lock:
            trial_progress[case_id] = {
                "status": "done",
                "result": result,
                "phase": "完成",
                "summary": "庭审结束"
            }
    except Exception as e:
        with trial_lock:
            trial_progress[case_id] = {
                "status": "error",
                "result": str(e),
                "phase": "失败",
                "summary": f"出错: {e}"
            }


def background_trial_with_websocket(case_id):
    """后台运行庭审（使用 WebSocket 推送进度）"""
    try:
        setup_agents_for_trial(case_id)

        def ws_progress_callback(phase, summary):
            """通过 WebSocket 推送进度"""
            with trial_lock:
                if case_id not in trial_progress:
                    trial_progress[case_id] = {"lines": [], "status": "running"}
                trial_progress[case_id]["phase"] = phase
                trial_progress[case_id]["summary"] = summary

            # 推送到 WebSocket
            socketio.emit('trial_progress', {
                'case_id': case_id,
                'stage': phase,
                'message': summary
            }, namespace='/')

        result = court.trial(case_id, max_rounds=2, on_progress=ws_progress_callback)

        with trial_lock:
            trial_progress[case_id] = {
                "status": "done",
                "result": result,
                "phase": "完成",
                "summary": "庭审结束"
            }

        # 推送完成消息
        socketio.emit('trial_progress', {
            'case_id': case_id,
            'stage': 'completed',
            'message': '庭审结束'
        }, namespace='/')

    except Exception as e:
        with trial_lock:
            trial_progress[case_id] = {
                "status": "error",
                "result": str(e),
                "phase": "失败",
                "summary": f"出错: {e}"
            }

        # 推送错误消息
        socketio.emit('trial_progress', {
            'case_id': case_id,
            'stage': 'error',
            'message': f'出错: {e}'
        }, namespace='/')


# ====== 自由讨论 ======

discuss_progress = {}
discuss_lock = threading.Lock()


@app.route('/api/discuss', methods=['POST'])
def start_discuss():
    """自由讨论：所有 Agent 直接回答问题"""
    try:
        data = request.json
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"success": False, "error": "请输入问题"}), 400

        from concurrent.futures import ThreadPoolExecutor, as_completed
        from copy import deepcopy

        discuss_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 各 Agent 的系统提示词
        prompts = {
            "prosecutor": "你是一位解决方案专家。请针对用户的问题，提出详细可行的解决方案。要具体、可操作。",
            "defender": "你是一位风险评估专家。请针对用户的问题和已有的方案，指出潜在的风险和容易被忽略的问题。",
            "jury": "你是一位资深顾问。请从技术、成本、效率等不同角度，补充额外的建议和最佳实践。",
            "judge": "你是一位决策顾问。请综合所有意见，给出一个最全面、最可行的最终方案。"
        }

        # 初始化进度
        with discuss_lock:
            discuss_progress[discuss_id] = {
                "status": "running",
                "answers": {},
                "summary": ""
            }

        def ask(agent_id):
            api = get_agent_api(agent_id)
            if not api:
                return agent_id, "(规则引擎模式，无法回答)"
            result = call_openai_api_with_error(
                type('M', (), {'title': question, 'description': question})(),
                api, prompts[agent_id], f"用户问题：{question}"
            )
            return agent_id, result

        # 检察官、辩护律师、陪审团并行
        answers = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(ask, aid): aid for aid in ["prosecutor", "defender", "jury"]}
            for f in as_completed(futures):
                aid, resp = f.result()
                answers[aid] = resp
                with discuss_lock:
                    if discuss_id in discuss_progress:
                        discuss_progress[discuss_id]["answers"] = dict(answers)

        # 法官综合总结
        summary_prompt = f"用户问题：{question}\n\n方案建议：\n{answers.get('prosecutor', '无')[:1000]}\n\n风险意见：\n{answers.get('defender', '无')[:1000]}\n\n专家补充：\n{answers.get('jury', '无')[:1000]}\n\n请综合以上所有意见，给出一个完整、可行的最终方案。"
        api = get_agent_api("judge")
        if api:
            summary = call_openai_api_with_error(
                type('M', (), {'title': question, 'description': question})(),
                api, prompts["judge"], summary_prompt
            )
        else:
            summary = "(法官规则引擎模式)"

        with discuss_lock:
            if discuss_id in discuss_progress:
                discuss_progress[discuss_id]["answers"] = answers
                discuss_progress[discuss_id]["summary"] = summary
                discuss_progress[discuss_id]["status"] = "done"

        return jsonify({"success": True, "discuss_id": discuss_id, "answers": answers, "summary": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/discuss/<discuss_id>')
def get_discuss(discuss_id):
    """获取讨论进度"""
    with discuss_lock:
        p = discuss_progress.get(discuss_id, {"status": "unknown"})
        return jsonify({"success": True, "progress": p})


# ====== 命令执行 ======


@app.route('/api/execute', methods=['POST'])
def execute_command():
    """执行 shell 命令（需用户确认后调用）"""
    try:
        data = request.json
        cmd = data.get("cmd", "").strip()
        if not cmd:
            return jsonify({"success": False, "error": "无命令"}), 400

        # 安全检查：禁止危险命令
        dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "> /dev/sda", "wget ", "curl -s "]
        for d in dangerous:
            if d in cmd:
                return jsonify({"success": False, "error": f"危险命令被阻止: {d}"}), 400

        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return jsonify({
            "success": True,
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-1000:]
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "命令执行超时（30秒）"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ====== 庭审 ======

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/motions', methods=['GET'])
def list_motions():
    try:
        motions = court.list_motions()
        return jsonify({'success': True, 'motions': [m.model_dump(mode='json') for m in motions]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motions', methods=['POST'])
def create_motion():
    try:
        data = request.json
        case_id = court.file_motion(
            title=data['title'],
            motion_type=MotionType(data['motion_type']),
            description=data['description'],
            proposed_changes=data.get('proposed_changes', []),
            affected_files=data.get('affected_files', []),
            risks=data.get('risks', []),
            benefits=data.get('benefits', []),
            priority=data.get('priority', 5)
        )
        # 从返回值提取 case_id
        import re
        cid = re.search(r'case_[\d_]+', case_id)
        return jsonify({'success': True, 'case_id': cid.group() if cid else case_id, 'message': f'动议已提交，案件编号：{cid.group() if cid else case_id}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motions/<case_id>', methods=['GET'])
def get_motion(case_id):
    try:
        motion = court.get_motion(case_id)
        if not motion:
            return jsonify({'success': False, 'error': '案件不存在'}), 404
        return jsonify({'success': True, 'motion': motion.model_dump(mode='json')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motions/<case_id>/retrial', methods=['POST'])
def retrial_motion(case_id):
    """重申：重置案件状态并清除旧判决"""
    try:
        motion = court.get_motion(case_id)
        if not motion:
            return jsonify({'success': False, 'error': '案件不存在'}), 404
        from courtroom.schemas import MotionStatus
        court.judge.update_motion_status(case_id, MotionStatus.FILED)
        # 清除旧判决和庭审记录
        vf = courtroom_root / "verdicts" / f"{case_id}.json"
        tf = courtroom_root / "transcripts" / f"{case_id}.md"
        if vf.exists(): vf.unlink()
        if tf.exists(): tf.unlink()
        # 从已结案件移到活跃
        if case_id in court.judge.state.completed_cases:
            court.judge.state.completed_cases.remove(case_id)
        if case_id not in court.judge.state.active_cases:
            court.judge.state.active_cases.append(case_id)
        court.judge._save_state()
        # 清理进度
        with trial_lock:
            trial_progress.pop(case_id, None)
        return jsonify({'success': True, 'message': f'案件 {case_id} 已重置，可重新庭审'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motions/<case_id>/reset', methods=['POST'])
def reset_motion(case_id):
    """重置卡住的案件状态为待审理"""
    try:
        motion = court.get_motion(case_id)
        if not motion:
            return jsonify({'success': False, 'error': '案件不存在'}), 404
        from courtroom.schemas import MotionStatus
        court.judge.update_motion_status(case_id, MotionStatus.FILED)
        # 清理进度
        with trial_lock:
            trial_progress.pop(case_id, None)
        return jsonify({'success': True, 'message': f'案件 {case_id} 已重置为待审理'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify({'success': True, 'settings': load_api_settings()})


@app.route('/api/settings', methods=['POST'])
def update_settings():
    try:
        save_api_settings(request.json)
        return jsonify({'success': True, 'message': '设置已保存'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-api', methods=['POST'])
def test_api():
    try:
        data = request.json
        url = data.get("url", "").rstrip("/")
        key = data.get("api_key", "")
        model = data.get("model", "gpt-4o-mini")
        if not url or not key:
            return jsonify({'success': False, 'error': '缺少 API 地址或 Key'}), 400
        from courtroom.schemas import Motion
        dummy = Motion(case_id="test", title="测试连接", motion_type="performance", description="这是一条测试消息")
        result = call_openai_api(dummy, {"url": url, "api_key": key, "model": model}, "你是一个助手。", '请回复"连接成功"。')
        if result:
            return jsonify({'success': True, 'message': '连接成功', 'response': result[:200]})
        return jsonify({'success': False, 'error': 'API 返回为空'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trial/<case_id>', methods=['POST'])
def start_trial(case_id):
    """开始庭审（后台运行，实时查进度）"""
    try:
        # 检查是否已经在跑
        with trial_lock:
            if case_id in trial_progress and trial_progress[case_id].get("status") == "running":
                return jsonify({'success': False, 'error': '该案件正在审理中'}), 400

        # 初始化进度
        with trial_lock:
            trial_progress[case_id] = {"status": "running", "phase": "starting", "summary": "准备开庭", "lines": []}

        # 后台线程跑庭审
        t = threading.Thread(target=background_trial, args=(case_id,), daemon=True)
        t.start()

        return jsonify({'success': True, 'message': '庭审已开始，请查看实时进度'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trial/<case_id>/async', methods=['POST'])
def start_trial_async(case_id):
    """开始异步庭审（使用 Celery + WebSocket）"""
    try:
        # 检查案件是否存在
        case_file = courtroom_root / "cases" / f"{case_id}.json"
        if not case_file.exists():
            return jsonify({'success': False, 'error': '案件不存在'}), 404

        # 初始化进度
        with trial_lock:
            trial_progress[case_id] = {
                "status": "running",
                "phase": "starting",
                "summary": "准备开庭",
                "lines": [],
                "case_id": case_id
            }

        # 后台线程跑庭审（使用 WebSocket 推送进度）
        t = threading.Thread(target=background_trial_with_websocket, args=(case_id,), daemon=True)
        t.start()

        return jsonify({'success': True, 'message': '异步庭审已开始', 'case_id': case_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trial-progress/<case_id>')
def get_trial_progress(case_id):
    """获取庭审进度"""
    with trial_lock:
        p = trial_progress.get(case_id, {"status": "unknown", "phase": "", "summary": ""})
        return jsonify({"success": True, "progress": dict(p)})


@app.route('/api/verdicts/<case_id>', methods=['GET'])
def get_verdict(case_id):
    try:
        verdict_file = courtroom_root / "verdicts" / f"{case_id}.json"
        if not verdict_file.exists():
            return jsonify({'success': False, 'error': '判决不存在'}), 404
        with open(verdict_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({'success': True, 'verdict': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件，自动提取文字保存为证据"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        f = request.files['file']
        case_id = request.form.get('case_id', '')
        submitted_by = request.form.get('submitted_by', 'prosecutor')
        if not f.filename or not case_id:
            return jsonify({'success': False, 'error': '缺少文件或案件编号'}), 400

        # 保存文件到 uploads 目录
        upload_dir = courtroom_root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{f.filename}"
        f.save(file_path)

        # 提取文字内容
        content = ""
        ext = os.path.splitext(f.filename)[1].lower()
        if ext == '.pdf':
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            content = file_path.read_text(encoding='utf-8', errors='replace')

        content = content[:50000]  # 限制长度

        # 保存为证据
        ev = evidence_manager.submit_evidence(
            case_id=case_id,
            submitted_by=submitted_by,
            evidence_type='documentation',
            title=f"附件: {f.filename}",
            description=f"上传的文件 ({f.filename})",
            content=content,
            file_path=str(file_path)
        )

        return jsonify({
            'success': True,
            'evidence_id': ev.evidence_id,
            'title': ev.title,
            'content_length': len(content),
            'message': f'文件已上传，提取了 {len(content)} 个字符'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/evidence/<case_id>', methods=['GET'])
def list_evidence(case_id):
    try:
        ev_list = evidence_manager.list_evidence(case_id)
        return jsonify({'success': True, 'evidence': [e.model_dump(mode='json') for e in ev_list]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/evidence', methods=['POST'])
def submit_evidence():
    try:
        data = request.json
        ev = evidence_manager.submit_evidence(
            case_id=data['case_id'],
            submitted_by=data.get('submitted_by', 'prosecutor'),
            evidence_type=data.get('evidence_type', 'documentation'),
            title=data.get('title', '证据'),
            description=data.get('description', ''),
            content=data.get('content', ''),
            file_path=data.get('file_path'),
            metadata=data.get('metadata'),
            tags=data.get('tags')
        )
        return jsonify({'success': True, 'evidence_id': ev.evidence_id, 'message': '证据已提交'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transcripts/<case_id>', methods=['GET'])
def get_transcript(case_id):
    try:
        tf = courtroom_root / "transcripts" / f"{case_id}.md"
        if not tf.exists():
            return jsonify({'success': False, 'error': '庭审记录不存在'}), 404
        return jsonify({'success': True, 'transcript': tf.read_text(encoding='utf-8')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        motions = court.list_motions()
        by_status, by_type = {}, {}
        for m in motions:
            s = m.status.value
            by_status[s] = by_status.get(s, 0) + 1
            t = m.motion_type.value
            by_type[t] = by_type.get(t, 0) + 1
        recent = sorted(motions, key=lambda m: m.filed_at, reverse=True)[:10]
        return jsonify({'success': True, 'stats': {
            'total_cases': len(motions),
            'by_status': by_status,
            'by_type': by_type,
            'recent_cases': [{'case_id': m.case_id, 'title': m.title, 'status': m.status.value, 'filed_at': m.filed_at.isoformat()} for m in recent]
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ====== 用户头像管理 ======

ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_avatar_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


@app.route('/api/avatar/upload', methods=['POST'])
def upload_avatar():
    """上传用户头像"""
    try:
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'error': '未选择文件'}), 400

        file = request.files['avatar']
        user_id = request.form.get('user_id', 'default_user')

        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        if not allowed_avatar_file(file.filename):
            return jsonify({'success': False, 'error': f'不支持的文件格式，仅支持: {", ".join(ALLOWED_AVATAR_EXTENSIONS)}'}), 400

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_AVATAR_SIZE:
            return jsonify({'success': False, 'error': f'文件过大，最大支持 {MAX_AVATAR_SIZE // (1024*1024)}MB'}), 400

        # 保存头像
        avatar_dir = courtroom_root / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)

        ext = file.filename.rsplit('.', 1)[1].lower()
        avatar_filename = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        avatar_path = avatar_dir / avatar_filename

        file.save(avatar_path)

        # 生成访问URL
        avatar_url = f"/api/avatar/{avatar_filename}"

        return jsonify({
            'success': True,
            'avatar_url': avatar_url,
            'filename': avatar_filename,
            'size': file_size,
            'message': '头像上传成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/avatar/<filename>', methods=['GET'])
def get_avatar(filename):
    """获取用户头像"""
    try:
        avatar_dir = courtroom_root / "avatars"
        avatar_path = avatar_dir / filename

        if not avatar_path.exists():
            return jsonify({'success': False, 'error': '头像不存在'}), 404

        from flask import send_file
        return send_file(avatar_path, mimetype=f'image/{filename.rsplit(".", 1)[1].lower()}')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/avatar/<filename>', methods=['DELETE'])
def delete_avatar(filename):
    """删除用户头像"""
    try:
        avatar_dir = courtroom_root / "avatars"
        avatar_path = avatar_dir / filename

        if not avatar_path.exists():
            return jsonify({'success': False, 'error': '头像不存在'}), 404

        avatar_path.unlink()

        return jsonify({
            'success': True,
            'message': '头像删除成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("🌐 启动庭审系统 Web UI（异步版本）")
    print("📍 访问地址: http://localhost:5000")
    print("🔌 WebSocket 已启用，支持实时进度推送")
    print("📦 启动前请确保 Redis 和 Celery Worker 已运行：")
    print("   redis-server")
    print("   celery -A courtroom.tasks worker --loglevel=info")

    # 使用 eventlet 运行
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

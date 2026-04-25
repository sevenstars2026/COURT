"""
庭审系统 Web UI - Flask 应用
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import json
from datetime import datetime

from courtroom import Court, MotionType
from courtroom.evidence import EvidenceManager

app = Flask(__name__,
            static_folder='web/static',
            template_folder='web/templates')
CORS(app)

# 初始化法庭和证据管理器
courtroom_root = Path(__file__).parent / "courtroom"
court = Court(courtroom_root, use_llm=False)  # 默认使用规则引擎
evidence_manager = EvidenceManager(courtroom_root / "evidence")


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/motions', methods=['GET'])
def list_motions():
    """列出所有动议"""
    try:
        motions = court.list_motions()
        return jsonify({
            'success': True,
            'motions': [m.model_dump(mode='json') for m in motions]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motions', methods=['POST'])
def create_motion():
    """创建新动议"""
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

        return jsonify({
            'success': True,
            'case_id': case_id,
            'message': f'动议已提交，案件编号：{case_id}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/motions/<case_id>', methods=['GET'])
def get_motion(case_id):
    """获取动议详情"""
    try:
        motion = court.get_motion(case_id)
        if not motion:
            return jsonify({'success': False, 'error': '案件不存在'}), 404

        return jsonify({
            'success': True,
            'motion': motion.model_dump(mode='json')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trial/<case_id>', methods=['POST'])
def start_trial(case_id):
    """开始庭审"""
    try:
        data = request.json or {}
        max_rounds = data.get('max_rounds', 2)
        use_llm = data.get('use_llm', False)

        # 临时切换 LLM 模式
        original_use_llm = court.use_llm
        court.use_llm = use_llm

        result = court.trial(case_id, max_rounds=max_rounds)

        # 恢复原始设置
        court.use_llm = original_use_llm

        return jsonify({
            'success': True,
            'message': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/verdicts/<case_id>', methods=['GET'])
def get_verdict(case_id):
    """获取判决"""
    try:
        verdict_text = court.show_verdict(case_id)
        if not verdict_text:
            return jsonify({'success': False, 'error': '判决不存在'}), 404

        # 读取判决 JSON
        verdict_file = courtroom_root / "verdicts" / f"{case_id}.json"
        with open(verdict_file, 'r', encoding='utf-8') as f:
            verdict_data = json.load(f)

        return jsonify({
            'success': True,
            'verdict': verdict_data,
            'verdict_text': verdict_text
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transcripts/<case_id>', methods=['GET'])
def get_transcript(case_id):
    """获取庭审记录"""
    try:
        transcript_file = courtroom_root / "transcripts" / f"{case_id}.md"
        if not transcript_file.exists():
            return jsonify({'success': False, 'error': '庭审记录不存在'}), 404

        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_text = f.read()

        return jsonify({
            'success': True,
            'transcript': transcript_text
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/evidence/<case_id>', methods=['GET'])
def list_evidence(case_id):
    """列出案件的所有证据"""
    try:
        evidence_list = evidence_manager.list_evidence(case_id)
        return jsonify({
            'success': True,
            'evidence': [e.model_dump(mode='json') for e in evidence_list]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/evidence', methods=['POST'])
def submit_evidence():
    """提交证据"""
    try:
        data = request.json

        evidence = evidence_manager.submit_evidence(
            case_id=data['case_id'],
            submitted_by=data['submitted_by'],
            evidence_type=data['evidence_type'],
            title=data['title'],
            description=data['description'],
            content=data['content'],
            file_path=data.get('file_path'),
            metadata=data.get('metadata'),
            tags=data.get('tags')
        )

        return jsonify({
            'success': True,
            'evidence_id': evidence.evidence_id,
            'message': '证据已提交'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        motions = court.list_motions()

        stats = {
            'total_cases': len(motions),
            'by_status': {},
            'by_type': {},
            'recent_cases': []
        }

        for motion in motions:
            # 按状态统计
            status = motion.status.value
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

            # 按类型统计
            motion_type = motion.motion_type.value
            stats['by_type'][motion_type] = stats['by_type'].get(motion_type, 0) + 1

        # 最近的案件
        recent = sorted(motions, key=lambda m: m.filed_at, reverse=True)[:5]
        stats['recent_cases'] = [
            {
                'case_id': m.case_id,
                'title': m.title,
                'status': m.status.value,
                'filed_at': m.filed_at.isoformat()
            }
            for m in recent
        ]

        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("🌐 启动庭审系统 Web UI")
    print("📍 访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

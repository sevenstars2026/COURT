"""任务管理 API 路由"""
from flask import Blueprint, jsonify, request, send_file
from celery.result import AsyncResult
from .celery_app import celery_app
from .tasks import run_trial_async
from .code_output_manager import CodeOutputManager
import io
import zipfile

api_bp = Blueprint('api', __name__, url_prefix='/api')
output_manager = CodeOutputManager()


@api_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    task = AsyncResult(task_id, app=celery_app)

    response = {
        'task_id': task_id,
        'state': task.state,
        'ready': task.ready(),
        'successful': task.successful() if task.ready() else None,
        'failed': task.failed() if task.ready() else None,
    }

    if task.state == 'PROGRESS':
        response['progress'] = task.info
    elif task.ready():
        if task.successful():
            response['result'] = task.result
        else:
            response['error'] = str(task.info)

    return jsonify(response)


@api_bp.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    task = AsyncResult(task_id, app=celery_app)
    task.revoke(terminate=True)

    return jsonify({
        'task_id': task_id,
        'status': 'cancelled'
    })


@api_bp.route('/tasks/<task_id>/retry', methods=['POST'])
def retry_task(task_id):
    """重试失败的任务"""
    task = AsyncResult(task_id, app=celery_app)

    if not task.failed():
        return jsonify({'error': 'Task is not in failed state'}), 400

    # 获取原始参数（需要从任务元数据中恢复）
    # 这里简化处理，实际需要存储原始参数
    return jsonify({'error': 'Retry not implemented yet'}), 501


@api_bp.route('/cases/<case_id>/trial', methods=['POST'])
def start_trial(case_id):
    """启动异步庭审"""
    data = request.get_json() or {}
    max_rounds = data.get('max_rounds', 3)

    # 启动异步任务
    task = run_trial_async.delay(case_id, max_rounds)

    return jsonify({
        'task_id': task.id,
        'case_id': case_id,
        'status': 'started'
    })


@api_bp.route('/cases', methods=['GET'])
def list_cases():
    """列出所有案件"""
    from pathlib import Path
    import json

    cases_dir = Path("courtroom/cases")
    cases = []

    if cases_dir.exists():
        for case_file in cases_dir.glob("case_*.json"):
            try:
                with open(case_file, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                    cases.append({
                        'case_id': case_data.get('case_id'),
                        'title': case_data.get('motion', {}).get('title'),
                        'created_at': case_data.get('created_at'),
                        'status': case_data.get('status', 'pending')
                    })
            except Exception as e:
                print(f"Error reading case {case_file}: {e}")

    return jsonify({'cases': cases})


@api_bp.route('/cases/<case_id>', methods=['GET'])
def get_case(case_id):
    """获取案件详情"""
    from pathlib import Path
    import json

    case_file = Path(f"courtroom/cases/{case_id}.json")

    if not case_file.exists():
        return jsonify({'error': 'Case not found'}), 404

    with open(case_file, 'r', encoding='utf-8') as f:
        case_data = json.load(f)

    return jsonify(case_data)


@api_bp.route('/cases/<case_id>/transcript', methods=['GET'])
def get_transcript(case_id):
    """获取庭审记录"""
    from pathlib import Path

    transcript_file = Path(f"courtroom/transcripts/transcript_{case_id}.md")

    if not transcript_file.exists():
        return jsonify({'error': 'Transcript not found'}), 404

    with open(transcript_file, 'r', encoding='utf-8') as f:
        content = f.read()

    return jsonify({
        'case_id': case_id,
        'content': content
    })


@api_bp.route('/cases/<case_id>/outputs', methods=['GET'])
def get_case_outputs(case_id):
    """获取案件生成的代码文件"""
    from pathlib import Path

    outputs_dir = Path(f"courtroom/outputs/{case_id}")

    if not outputs_dir.exists():
        return jsonify({'files': []})

    files = []
    for file_path in outputs_dir.rglob('*'):
        if file_path.is_file():
            files.append({
                'path': str(file_path.relative_to(outputs_dir)),
                'size': file_path.stat().st_size,
                'modified': file_path.stat().st_mtime
            })

    return jsonify({'files': files})


@api_bp.route('/cases/<case_id>/outputs/<path:file_path>', methods=['GET'])
def get_output_file(case_id, file_path):
    """获取生成的代码文件内容"""
    from pathlib import Path

    full_path = Path(f"courtroom/outputs/{case_id}/{file_path}")

    if not full_path.exists() or not full_path.is_file():
        return jsonify({'error': 'File not found'}), 404

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return jsonify({
        'path': file_path,
        'content': content
    })


@api_bp.route('/cases/<case_id>/code-versions', methods=['GET'])
def get_code_versions(case_id):
    """获取案件的所有代码版本"""
    versions = output_manager.get_versions(case_id)
    return jsonify({'versions': versions})


@api_bp.route('/cases/<case_id>/code-output', methods=['GET'])
def get_code_output(case_id):
    """获取案件生成的代码（最新版本或指定版本）"""
    version_id = request.args.get('version_id')
    files = output_manager.get_output(case_id, version_id)

    if files is None:
        return jsonify({'error': 'Code output not found'}), 404

    return jsonify({
        'case_id': case_id,
        'version_id': version_id,
        'files': files
    })


@api_bp.route('/cases/<case_id>/download-code', methods=['GET'])
def download_code(case_id):
    """下载案件生成的代码为 ZIP 文件"""
    version_id = request.args.get('version_id')
    files = output_manager.get_output(case_id, version_id)

    if files is None:
        return jsonify({'error': 'Code output not found'}), 404

    # 创建内存中的 ZIP 文件
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel_path, content in files.items():
            zf.writestr(rel_path, content)

    memory_file.seek(0)

    # 返回 ZIP 文件
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{case_id}_code.zip'
    )

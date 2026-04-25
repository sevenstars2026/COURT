"""异步任务定义"""
from celery import Task
from courtroom.celery_app import celery_app
from courtroom.court import Court
import json
import os
from datetime import datetime

class TrialTask(Task):
    """庭审任务基类，支持进度回调"""
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

@celery_app.task(bind=True, base=TrialTask, name='courtroom.trial')
def run_trial_async(self, case_id, codebase_path, motion_data, api_config):
    """异步执行庭审任务

    Args:
        case_id: 案件ID
        codebase_path: 代码库路径
        motion_data: 动议数据字典
        api_config: API配置字典
    """
    try:
        # 更新状态：开始
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'initializing', 'progress': 0, 'message': '初始化庭审...'}
        )

        # 创建法庭实例
        court = Court(
            api_key=api_config['api_key'],
            base_url=api_config.get('base_url'),
            model=api_config.get('model', 'gpt-4'),
            codebase_path=codebase_path
        )

        # 进度回调函数
        def progress_callback(stage, progress, message):
            self.update_state(
                state='PROGRESS',
                meta={
                    'stage': stage,
                    'progress': progress,
                    'message': message,
                    'case_id': case_id
                }
            )

        # 执行庭审（传入回调）
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'trial', 'progress': 10, 'message': '开始庭审...'}
        )

        verdict = court.trial(
            case_id=case_id,
            progress_callback=progress_callback
        )

        # 返回结果
        return {
            'case_id': case_id,
            'verdict': verdict.model_dump() if verdict else None,
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={
                'case_id': case_id,
                'error': str(e),
                'stage': 'error'
            }
        )
        raise

@celery_app.task(name='courtroom.code_analysis')
def run_code_analysis_async(case_id, codebase_path, motion_data, api_config):
    """异步执行代码分析"""
    from courtroom.agents.code_analyst import CodeAnalyst

    analyst = CodeAnalyst(
        api_key=api_config['api_key'],
        base_url=api_config.get('base_url'),
        model=api_config.get('model', 'gpt-4')
    )

    report = analyst.analyze(
        case_id=case_id,
        codebase_path=codebase_path,
        description=motion_data.get('description', ''),
        files=motion_data.get('files', [])
    )

    return {
        'case_id': case_id,
        'report': report,
        'status': 'completed'
    }

@celery_app.task(name='courtroom.execution')
def run_execution_async(case_id, verdict_data, codebase_path, api_config):
    """异步执行代码变更"""
    from courtroom.agents.execution_engineer import ExecutionEngineer

    engineer = ExecutionEngineer(
        api_key=api_config['api_key'],
        base_url=api_config.get('base_url'),
        model=api_config.get('model', 'gpt-4')
    )

    # 重建 Verdict 对象
    from courtroom.models import Verdict
    verdict = Verdict(**verdict_data)

    result = engineer.execute(
        case_id=case_id,
        verdict=verdict,
        codebase_path=codebase_path
    )

    return {
        'case_id': case_id,
        'execution_result': result,
        'status': 'completed'
    }

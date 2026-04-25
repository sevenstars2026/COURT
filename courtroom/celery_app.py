"""Celery 配置和应用实例"""
from celery import Celery
import os

def make_celery(app_name='courtroom'):
    """创建 Celery 实例"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    celery = Celery(
        app_name,
        broker=redis_url,
        backend=redis_url
    )

    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Shanghai',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1小时硬限制
        task_soft_time_limit=3000,  # 50分钟软限制
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50,
    )

    return celery

celery_app = make_celery()

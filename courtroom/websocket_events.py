"""WebSocket 事件处理"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from typing import Dict, Any

socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

# 活跃的任务房间
active_rooms: Dict[str, set] = {}


@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'ok'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f"Client disconnected: {request.sid}")


@socketio.on('join_task')
def handle_join_task(data):
    """加入任务房间以接收实时更新"""
    task_id = data.get('task_id')
    if not task_id:
        emit('error', {'message': 'task_id required'})
        return

    join_room(task_id)
    if task_id not in active_rooms:
        active_rooms[task_id] = set()
    active_rooms[task_id].add(request.sid)

    emit('joined', {'task_id': task_id, 'room': task_id})
    print(f"Client {request.sid} joined task room: {task_id}")


@socketio.on('leave_task')
def handle_leave_task(data):
    """离开任务房间"""
    task_id = data.get('task_id')
    if not task_id:
        return

    leave_room(task_id)
    if task_id in active_rooms and request.sid in active_rooms[task_id]:
        active_rooms[task_id].remove(request.sid)
        if not active_rooms[task_id]:
            del active_rooms[task_id]

    emit('left', {'task_id': task_id})
    print(f"Client {request.sid} left task room: {task_id}")


def broadcast_task_progress(task_id: str, stage: str, progress: int, message: str):
    """向任务房间广播进度更新"""
    socketio.emit('task_progress', {
        'task_id': task_id,
        'stage': stage,
        'progress': progress,
        'message': message
    }, room=task_id)


def broadcast_task_output(task_id: str, output_type: str, content: str):
    """向任务房间广播输出流"""
    socketio.emit('task_output', {
        'task_id': task_id,
        'type': output_type,
        'content': content
    }, room=task_id)


def broadcast_task_complete(task_id: str, status: str, result: Any):
    """向任务房间广播任务完成"""
    socketio.emit('task_complete', {
        'task_id': task_id,
        'status': status,
        'result': result
    }, room=task_id)


def broadcast_task_error(task_id: str, error: str):
    """向任务房间广播错误"""
    socketio.emit('task_error', {
        'task_id': task_id,
        'error': error
    }, room=task_id)

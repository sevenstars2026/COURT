"""
代码输出管理器
管理执行工程师生成的代码输出，支持版本控制和回滚
"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class CodeOutputManager:
    """代码输出管理器"""

    def __init__(self, base_dir: str = "courtroom/code_outputs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_output(self, case_id: str, files: Dict[str, str], metadata: Optional[Dict] = None) -> str:
        """
        保存代码输出

        Args:
            case_id: 案件ID
            files: 文件字典 {相对路径: 内容}
            metadata: 元数据（可选）

        Returns:
            版本ID
        """
        # 创建案件目录
        case_dir = self.base_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # 生成版本ID（时间戳）
        version_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_dir = case_dir / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        for rel_path, content in files.items():
            file_path = version_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')

        # 保存元数据
        meta = {
            "version_id": version_id,
            "timestamp": datetime.now().isoformat(),
            "files": list(files.keys()),
            "metadata": metadata or {}
        }
        (version_dir / "metadata.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        return version_id

    def get_versions(self, case_id: str) -> List[Dict]:
        """
        获取案件的所有版本

        Args:
            case_id: 案件ID

        Returns:
            版本列表，按时间倒序
        """
        case_dir = self.base_dir / case_id
        if not case_dir.exists():
            return []

        versions = []
        for version_dir in sorted(case_dir.iterdir(), reverse=True):
            if not version_dir.is_dir():
                continue

            meta_file = version_dir / "metadata.json"
            if meta_file.exists():
                meta = json.loads(meta_file.read_text(encoding='utf-8'))
                versions.append(meta)

        return versions

    def get_output(self, case_id: str, version_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        获取代码输出

        Args:
            case_id: 案件ID
            version_id: 版本ID（可选，默认最新版本）

        Returns:
            文件字典 {相对路径: 内容}，如果不存在返回 None
        """
        case_dir = self.base_dir / case_id
        if not case_dir.exists():
            return None

        # 如果未指定版本，使用最新版本
        if version_id is None:
            versions = self.get_versions(case_id)
            if not versions:
                return None
            version_id = versions[0]["version_id"]

        version_dir = case_dir / version_id
        if not version_dir.exists():
            return None

        # 读取元数据
        meta_file = version_dir / "metadata.json"
        if not meta_file.exists():
            return None

        meta = json.loads(meta_file.read_text(encoding='utf-8'))

        # 读取文件
        files = {}
        for rel_path in meta["files"]:
            file_path = version_dir / rel_path
            if file_path.exists():
                files[rel_path] = file_path.read_text(encoding='utf-8')

        return files

    def apply_output(self, case_id: str, target_dir: str, version_id: Optional[str] = None) -> bool:
        """
        应用代码输出到目标目录

        Args:
            case_id: 案件ID
            target_dir: 目标目录
            version_id: 版本ID（可选，默认最新版本）

        Returns:
            是否成功
        """
        files = self.get_output(case_id, version_id)
        if files is None:
            return False

        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        for rel_path, content in files.items():
            file_path = target_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')

        return True

    def delete_version(self, case_id: str, version_id: str) -> bool:
        """
        删除指定版本

        Args:
            case_id: 案件ID
            version_id: 版本ID

        Returns:
            是否成功
        """
        version_dir = self.base_dir / case_id / version_id
        if not version_dir.exists():
            return False

        shutil.rmtree(version_dir)
        return True

    def cleanup_old_versions(self, case_id: str, keep_count: int = 5) -> int:
        """
        清理旧版本，只保留最新的 N 个版本

        Args:
            case_id: 案件ID
            keep_count: 保留版本数

        Returns:
            删除的版本数
        """
        versions = self.get_versions(case_id)
        if len(versions) <= keep_count:
            return 0

        deleted = 0
        for version in versions[keep_count:]:
            if self.delete_version(case_id, version["version_id"]):
                deleted += 1

        return deleted

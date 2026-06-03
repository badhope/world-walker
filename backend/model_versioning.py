"""
模型版本管理和回滚模块
"""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.utils.model_security import load_with_signature, save_with_signature

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """模型版本管理器"""

    def __init__(self, base_dir: str = "models"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.base_dir / "versions.json"
        self.current_version = None
        self.versions = self._load_versions()

    def _load_versions(self) -> list[dict]:
        """加载版本列表"""
        if self.versions_file.exists():
            try:
                with open(self.versions_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_versions(self):
        tmp_file = self.versions_file.with_suffix(".json.tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(self.versions, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp_file, self.versions_file)

    def save_version(self, model: Any, version_info: dict, model_path: str = None, metadata: dict = None) -> str:
        """
        保存新版本

        Args:
            model: 训练好的模型
            version_info: 版本信息字典
            model_path: 模型保存路径（可选，会自动生成）
            metadata: 元数据

        Returns:
            版本ID
        """
        # 生成版本ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        version_id = f"v_{timestamp}_{unique_id}"

        version_dir = self.base_dir / version_id
        retry_count = 0
        while version_dir.exists() and retry_count < 3:
            retry_count += 1
            unique_id = uuid.uuid4().hex[:8]
            version_id = f"v_{timestamp}_{unique_id}"
            version_dir = self.base_dir / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        # 保存模型
        if model_path is None:
            model_path = version_dir / "model.pkl"
        else:
            model_path = Path(model_path)

        save_with_signature(model, model_path)
        logger.info(f"模型已保存到: {model_path}")

        # 保存元数据
        if metadata is None:
            metadata = {}

        full_info = {
            "version_id": version_id,
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_path": str(model_path),
            "version_info": version_info,
            "metadata": metadata,
        }

        # 保存元数据
        with open(version_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(full_info, f, ensure_ascii=False, indent=2, default=str)

        # 添加到版本列表
        self.versions.append(full_info)
        self._save_versions()

        # 设置为当前版本
        self.current_version = version_id

        logger.info(f"版本 {version_id} 已保存")
        return version_id

    def load_version(self, version_id: str = None) -> tuple:
        """
        加载指定版本

        Args:
            version_id: 版本ID，如果None则加载最新版本

        Returns:
            (model, metadata)
        """
        if version_id is None:
            if not self.versions:
                raise ValueError("没有可用的模型版本")
            # 加载最新版本
            version_id = self.versions[-1]["version_id"]

        version_info = next((v for v in self.versions if v["version_id"] == version_id), None)

        if not version_info:
            raise ValueError(f"版本 {version_id} 不存在")

        # 加载模型
        model_path = Path(version_info["model_path"])
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        model = load_with_signature(model_path)

        # 加载元数据
        metadata_path = model_path.parent / "metadata.json"
        metadata = None
        if metadata_path.exists():
            with open(metadata_path, encoding="utf-8") as f:
                metadata = json.load(f)

        self.current_version = version_id
        logger.info(f"版本 {version_id} 已加载")

        return model, metadata

    def rollback(self, version_id: str) -> str:
        """
        回滚到指定版本

        Args:
            version_id: 要回滚的版本ID

        Returns:
            回滚后的版本ID
        """
        logger.info(f"回滚到版本: {version_id}")

        # 验证版本存在
        version_info = next((v for v in self.versions if v["version_id"] == version_id), None)

        if not version_info:
            raise ValueError(f"版本 {version_id} 不存在")

        # 复制为新版本（保留回滚历史）
        self.current_version = version_id

        logger.info(f"已回滚到版本: {version_id}")
        return version_id

    def delete_version(self, version_id: str, keep_files: bool = False):
        """
        删除指定版本

        Args:
            version_id: 要删除的版本ID
            keep_files: 是否保留文件
        """
        version_info = next((v for v in self.versions if v["version_id"] == version_id), None)

        if not version_info:
            raise ValueError(f"版本 {version_id} 不存在")

        # 删除目录
        version_dir = Path(version_info["model_path"]).parent
        if not keep_files and version_dir.exists():
            shutil.rmtree(version_dir)

        # 从版本列表中删除
        self.versions = [v for v in self.versions if v["version_id"] != version_id]
        self._save_versions()

        logger.info(f"版本 {version_id} 已删除")

    def list_versions(self) -> list[dict]:
        """列出所有版本"""
        return self.versions.copy()

    def get_latest_version(self) -> dict | None:
        """获取最新版本"""
        if not self.versions:
            return None
        return self.versions[-1]

    def get_version(self, version_id: str) -> dict | None:
        """获取指定版本信息"""
        return next((v for v in self.versions if v["version_id"] == version_id), None)


class FeedbackLoop:
    """
    反馈闭环系统
    用于收集实际表现数据，更新模型
    """

    def __init__(self, version_manager: ModelVersionManager):
        self.version_manager = version_manager
        self.feedback_data: list[dict] = []
        self.feedback_file = version_manager.base_dir / "feedback.json"

    def add_feedback(self, feedback: dict):
        """添加反馈数据"""
        feedback["timestamp"] = datetime.now().isoformat()
        self.feedback_data.append(feedback)

        # 保存到文件
        self._save_feedback()
        logger.info("反馈数据已添加")

    def _save_feedback(self):
        """保存反馈数据到文件"""
        with open(self.feedback_file, "w", encoding="utf-8") as f:
            json.dump(self.feedback_data, f, ensure_ascii=False, indent=2, default=str)

    def load_feedback(self) -> list[dict]:
        """加载反馈数据"""
        if self.feedback_file.exists():
            with open(self.feedback_file, encoding="utf-8") as f:
                self.feedback_data = json.load(f)
        return self.feedback_data

    def get_feedback_summary(self) -> dict:
        """获取反馈数据统计"""
        if not self.feedback_data:
            return {"total": 0}

        total = len(self.feedback_data)
        avg_accuracy = None

        # 如果有accuracy字段，计算平均值
        accuracy_values = [
            f["accuracy"] for f in self.feedback_data if "accuracy" in f and isinstance(f["accuracy"], int | float)
        ]

        if accuracy_values:
            avg_accuracy = sum(accuracy_values) / len(accuracy_values)

        return {"total": total, "avg_accuracy": avg_accuracy}

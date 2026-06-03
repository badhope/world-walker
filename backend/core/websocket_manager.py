"""
WebSocket 实时通信管理器 - 支持实时数据推送和双向通信
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举"""

    # 系统消息
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

    # 数据消息
    DATA_UPDATE = "data_update"  # 数据更新
    DATA_INSERT = "data_insert"  # 数据插入
    DATA_DELETE = "data_delete"  # 数据删除
    DATA_COMPLETE = "data_complete"  # 数据完整推送

    # 分析消息
    ANALYSIS_START = "analysis_start"  # 分析开始
    ANALYSIS_PROGRESS = "analysis_progress"  # 分析进度
    ANALYSIS_COMPLETE = "analysis_complete"  # 分析完成
    ANALYSIS_ERROR = "analysis_error"  # 分析错误

    # 通知消息
    NOTIFICATION = "notification"  # 通知
    WARNING = "warning"  # 警告
    SUCCESS = "success"  # 成功
    INFO = "info"  # 信息

    # 实时消息
    REALTIME_DATA = "realtime_data"  # 实时数据
    SUBSCRIPTION = "subscription"  # 订阅确认
    UNSUBSCRIPTION = "unsubscription"  # 取消订阅


@dataclass
class WebSocketMessage:
    """WebSocket 消息结构"""

    type: MessageType
    channel: str  # 频道
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    sender: str | None = None  # 发送者
    target: str | None = None  # 目标用户

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(
            {
                "type": self.type.value,
                "channel": self.channel,
                "data": self.data,
                "timestamp": self.timestamp.isoformat(),
                "sender": self.sender,
                "target": self.target,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        """从 JSON 字符串解析"""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            channel=data["channel"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sender=data.get("sender"),
            target=data.get("target"),
        )


@dataclass
class ChannelSubscription:
    """频道订阅信息"""

    channel: str
    filters: dict[str, Any] = field(default_factory=dict)
    subscribed_at: datetime = field(default_factory=datetime.now)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        """初始化连接管理器"""
        # 活跃连接 {connection_id: WebSocket}
        self.active_connections: dict[str, WebSocket] = {}

        # 用户连接映射 {user_id: Set[connection_id]}
        self.user_connections: dict[str, set[str]] = {}

        # 连接元数据 {connection_id: metadata}
        self.connection_metadata: dict[str, dict[str, Any]] = {}

        # 频道订阅 {channel: Set[connection_id]}
        self.channel_subscriptions: dict[str, set[str]] = {}

        # 连接订阅 {connection_id: List[ChannelSubscription]}
        self.connection_subscriptions: dict[str, list[ChannelSubscription]] = {}

        # 心跳检测 {connection_id: last_ping_time}
        self.heartbeats: dict[str, datetime] = {}

        # 锁
        self._lock = asyncio.Lock()

        # 回调函数
        self._callbacks: dict[str, Callable] = {}

        logger.info("WebSocket 连接管理器初始化完成")

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        建立连接

        Args:
            websocket: WebSocket 连接
            connection_id: 连接ID
            user_id: 用户ID
            metadata: 连接元数据
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections[connection_id] = websocket
            self.connection_metadata[connection_id] = metadata or {}
            self.connection_subscriptions[connection_id] = []
            self.heartbeats[connection_id] = datetime.now()

            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)

        logger.info(f"WebSocket 连接已建立: {connection_id}, 用户: {user_id}")

        # 发送连接成功消息
        await self.send_personal_message(
            WebSocketMessage(
                type=MessageType.INFO,
                channel="system",
                data={"status": "connected", "connection_id": connection_id},
                sender="system",
            ),
            connection_id,
        )

    async def disconnect(self, connection_id: str):
        """
        断开连接

        Args:
            connection_id: 连接ID
        """
        async with self._lock:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]

                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.close()
                except Exception as e:
                    logger.warning(f"关闭 WebSocket 时出错: {e}")

                del self.active_connections[connection_id]

            # 清理元数据
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]

            # 清理心跳
            if connection_id in self.heartbeats:
                del self.heartbeats[connection_id]

            # 清理订阅
            if connection_id in self.connection_subscriptions:
                for sub in self.connection_subscriptions[connection_id]:
                    if sub.channel in self.channel_subscriptions:
                        self.channel_subscriptions[sub.channel].discard(connection_id)
                del self.connection_subscriptions[connection_id]

            # 清理用户连接映射
            for user_id, connections in self.user_connections.items():
                connections.discard(connection_id)
                if not connections:
                    del self.user_connections[user_id]

        logger.info(f"WebSocket 连接已断开: {connection_id}")

    async def subscribe(self, connection_id: str, channel: str, filters: dict[str, Any] | None = None):
        """
        订阅频道

        Args:
            connection_id: 连接ID
            channel: 频道名称
            filters: 过滤条件
        """
        async with self._lock:
            if connection_id not in self.active_connections:
                logger.warning(f"订阅失败: 连接不存在 {connection_id}")
                return False

            # 添加到频道订阅
            if channel not in self.channel_subscriptions:
                self.channel_subscriptions[channel] = set()
            self.channel_subscriptions[channel].add(connection_id)

            # 添加到连接订阅
            subscription = ChannelSubscription(channel=channel, filters=filters or {})
            self.connection_subscriptions[connection_id].append(subscription)

            logger.info(f"订阅成功: {connection_id} -> {channel}")

            # 发送订阅确认
            await self.send_personal_message(
                WebSocketMessage(
                    type=MessageType.SUBSCRIPTION,
                    channel=channel,
                    data={"channel": channel, "filters": filters},
                    sender="system",
                ),
                connection_id,
            )

            return True

    async def unsubscribe(self, connection_id: str, channel: str):
        """
        取消订阅

        Args:
            connection_id: 连接ID
            channel: 频道名称
        """
        async with self._lock:
            # 从频道订阅移除
            if channel in self.channel_subscriptions:
                self.channel_subscriptions[channel].discard(connection_id)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]

            # 从连接订阅移除
            if connection_id in self.connection_subscriptions:
                self.connection_subscriptions[connection_id] = [
                    sub for sub in self.connection_subscriptions[connection_id] if sub.channel != channel
                ]

            logger.info(f"取消订阅: {connection_id} -> {channel}")

            # 发送取消订阅确认
            await self.send_personal_message(
                WebSocketMessage(
                    type=MessageType.UNSUBSCRIPTION, channel=channel, data={"channel": channel}, sender="system"
                ),
                connection_id,
            )

    async def broadcast(self, message: WebSocketMessage, channel: str | None = None):
        """
        广播消息

        Args:
            message: WebSocket 消息
            channel: 频道名称（如果为 None，则发送给所有连接）
        """
        connections_to_send = set()

        async with self._lock:
            if channel:
                # 发送给订阅该频道的所有连接
                if channel in self.channel_subscriptions:
                    connections_to_send = self.channel_subscriptions[channel].copy()
            else:
                # 发送给所有连接
                connections_to_send = set(self.active_connections.keys())

        # 发送消息
        disconnected = []
        for connection_id in connections_to_send:
            try:
                await self.send_personal_message(message, connection_id)
            except Exception as e:
                logger.error(f"广播消息失败 {connection_id}: {e}")
                disconnected.append(connection_id)

        # 清理断开的连接
        for connection_id in disconnected:
            await self.disconnect(connection_id)

    async def broadcast_to_channel(
        self, channel: str, message: WebSocketMessage, filter_func: Callable[[str, dict], bool] | None = None
    ):
        """
        向指定频道广播消息，可选过滤

        Args:
            channel: 频道名称
            message: WebSocket 消息
            filter_func: 过滤函数，接受 (connection_id, filters) 返回是否发送
        """
        if channel not in self.channel_subscriptions:
            return

        connections_to_send = []

        async with self._lock:
            for connection_id in self.channel_subscriptions[channel]:
                # 获取该连接的过滤条件
                filters = {}
                if connection_id in self.connection_subscriptions:
                    for sub in self.connection_subscriptions[connection_id]:
                        if sub.channel == channel:
                            filters = sub.filters
                            break

                # 应用过滤
                if filter_func is None or filter_func(connection_id, filters):
                    connections_to_send.append(connection_id)

        # 发送消息
        disconnected = []
        for connection_id in connections_to_send:
            try:
                await self.send_personal_message(message, connection_id)
            except Exception as e:
                logger.error(f"广播消息失败 {connection_id}: {e}")
                disconnected.append(connection_id)

        # 清理断开的连接
        for connection_id in disconnected:
            await self.disconnect(connection_id)

    async def send_personal_message(self, message: WebSocketMessage, connection_id: str):
        """
        发送个人消息

        Args:
            message: WebSocket 消息
            connection_id: 连接ID
        """
        if connection_id not in self.active_connections:
            raise ConnectionError(f"连接不存在: {connection_id}")

        websocket = self.active_connections[connection_id]
        await websocket.send_text(message.to_json())

    async def send_to_user(self, message: WebSocketMessage, user_id: str):
        """
        发送给指定用户的所有连接

        Args:
            message: WebSocket 消息
            user_id: 用户ID
        """
        if user_id not in self.user_connections:
            return

        for connection_id in self.user_connections[user_id].copy():
            try:
                await self.send_personal_message(message, connection_id)
            except Exception as e:
                logger.error(f"发送消息失败 {connection_id}: {e}")

    def get_connection_count(self) -> int:
        """获取连接数量"""
        return len(self.active_connections)

    def get_channel_subscribers(self, channel: str) -> int:
        """获取频道订阅者数量"""
        return len(self.channel_subscriptions.get(channel, set()))

    def get_user_connections(self, user_id: str) -> set[str]:
        """获取用户的所有连接"""
        return self.user_connections.get(user_id, set())

    async def ping(self, connection_id: str):
        """
        发送心跳检测

        Args:
            connection_id: 连接ID
        """
        await self.send_personal_message(
            WebSocketMessage(
                type=MessageType.PING, channel="system", data={"timestamp": datetime.now().isoformat()}, sender="system"
            ),
            connection_id,
        )
        self.heartbeats[connection_id] = datetime.now()

    async def pong(self, connection_id: str):
        """
        收到心跳响应

        Args:
            connection_id: 连接ID
        """
        self.heartbeats[connection_id] = datetime.now()

    def is_connected(self, connection_id: str) -> bool:
        """检查连接是否活跃"""
        return connection_id in self.active_connections


# 全局实例
connection_manager = ConnectionManager()


class RealtimeDataPublisher:
    """实时数据发布器"""

    def __init__(self, manager: ConnectionManager):
        """
        初始化发布器

        Args:
            manager: 连接管理器
        """
        self.manager = manager
        self._data_cache: dict[str, Any] = {}
        self._update_handlers: dict[str, list[Callable]] = {}

    async def publish_data_update(self, channel: str, data: Any):
        """
        发布数据更新

        Args:
            channel: 频道名称
            data: 数据内容
        """
        message = WebSocketMessage(type=MessageType.DATA_UPDATE, channel=channel, data=data, sender="system")

        # 更新缓存
        self._data_cache[channel] = data

        # 广播消息
        await self.manager.broadcast(message, channel)

    async def publish_analysis_progress(self, channel: str, progress: int, status: str, details: dict | None = None):
        """
        发布分析进度

        Args:
            channel: 频道名称
            progress: 进度百分比
            status: 状态描述
            details: 详细信息
        """
        message = WebSocketMessage(
            type=MessageType.ANALYSIS_PROGRESS,
            channel=channel,
            data={"progress": progress, "status": status, "details": details or {}},
            sender="system",
        )

        await self.manager.broadcast(message, channel)

    async def publish_notification(self, channel: str, title: str, content: str, level: str = "info"):
        """
        发布通知

        Args:
            channel: 频道名称
            title: 通知标题
            content: 通知内容
            level: 通知级别 (info/success/warning/error)
        """
        message_type = MessageType.INFO
        if level == "success":
            message_type = MessageType.SUCCESS
        elif level == "warning":
            message_type = MessageType.WARNING
        elif level == "error":
            message_type = MessageType.ERROR

        message = WebSocketMessage(
            type=message_type,
            channel=channel,
            data={"title": title, "content": content, "level": level, "timestamp": datetime.now().isoformat()},
            sender="system",
        )

        await self.manager.broadcast(message, channel)

    def register_update_handler(self, channel: str, handler: Callable):
        """
        注册数据更新处理器

        Args:
            channel: 频道名称
            handler: 处理函数
        """
        if channel not in self._update_handlers:
            self._update_handlers[channel] = []
        self._update_handlers[channel].append(handler)

    def get_cached_data(self, channel: str) -> Any | None:
        """获取缓存数据"""
        return self._data_cache.get(channel)


# 全局实例
realtime_publisher = RealtimeDataPublisher(connection_manager)

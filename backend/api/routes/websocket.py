"""
WebSocket 路由 - 处理实时通信和消息推送
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.core.websocket_manager import MessageType, WebSocketMessage, connection_manager, realtime_publisher
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


def resolve_websocket_user(token: str | None, client_user_id: str | None) -> str | None:
    """从合法 token 中解析出 user_id,绝不相信客户端自报的 user_id。

    - 有 token: 用 jwt 解析,提取 'sub'。客户端的 client_user_id 一律忽略。
    - 无 token 或 token 非法: 返回 None,调用方应拒绝握手或降权(只读频道)。
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return str(sub) if sub else None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    connection_id: str | None = Query(None),
    user_id: str | None = Query(None),
    token: str | None = Query(None),
):
    """
    WebSocket 连接端点

    连接参数:
    - connection_id: 连接ID（可选,如果不提供则自动生成）
    - user_id: 用户ID(可选,**会被忽略**,仅作向后兼容;真实身份以 token 中的 sub 为准)
    - token: 访问令牌(可选)。不提供则视为匿名(只允许订阅 public 频道)

    消息格式:
    {
        "type": "ping/subscribe/unsubscribe/custom",
        "channel": "频道名称",
        "data": {...},
        "target": "目标用户ID（可选）"
    }
    """
    # 生成或使用提供的连接ID
    if not connection_id:
        connection_id = str(uuid.uuid4())

    # 从 token 解析出权威 user_id,绝不信任客户端自报的 user_id
    authenticated_user = resolve_websocket_user(token, user_id)
    is_authenticated = authenticated_user is not None

    # 建立连接
    await connection_manager.connect(
        websocket,
        connection_id=connection_id,
        user_id=authenticated_user,  # 传解析后的值
        metadata={
            "user_id": authenticated_user,
            "is_authenticated": is_authenticated,
            "connected_at": datetime.now().isoformat(),
            "remote_addr": websocket.client.host if websocket.client else None,
        },
    )

    try:
        # 监听消息
        while True:
            data = await websocket.receive_text()

            try:
                # 解析消息
                message_data = json.loads(data)
                message_type = message_data.get("type")
                channel = message_data.get("channel", "")
                payload = message_data.get("data", {})
                target = message_data.get("target")

                # 处理不同类型的消息
                if message_type == "ping":
                    # 心跳检测
                    await connection_manager.pong(connection_id)

                elif message_type == "subscribe":
                    # 订阅频道(匿名用户只能订阅 public 频道)
                    if not is_authenticated and not channel.startswith("public/"):
                        await connection_manager.send_personal_message(
                            WebSocketMessage(
                                type=MessageType.ERROR,
                                channel="system",
                                data={"error": "Authentication required for this channel"},
                                sender="system",
                            ),
                            connection_id,
                        )
                        continue
                    filters = payload.get("filters", {})
                    await connection_manager.subscribe(connection_id, channel, filters)

                elif message_type == "unsubscribe":
                    # 取消订阅
                    await connection_manager.unsubscribe(connection_id, channel)

                elif message_type == "broadcast":
                    # 广播消息: 必须已认证
                    if not is_authenticated:
                        await connection_manager.send_personal_message(
                            WebSocketMessage(
                                type=MessageType.ERROR,
                                channel="system",
                                data={"error": "Authentication required to broadcast"},
                                sender="system",
                            ),
                            connection_id,
                        )
                        continue
                    message = WebSocketMessage(
                        type=MessageType.REALTIME_DATA,
                        channel=channel,
                        data=payload,
                        sender=authenticated_user,
                    )
                    await connection_manager.broadcast(message, channel)

                elif message_type == "send_to_user":
                    # 发送给指定用户: 必须已认证,且 target 必须是 token 中的 sub 自己或被授权目标
                    if not is_authenticated:
                        await connection_manager.send_personal_message(
                            WebSocketMessage(
                                type=MessageType.ERROR,
                                channel="system",
                                data={"error": "Authentication required to send messages"},
                                sender="system",
                            ),
                            connection_id,
                        )
                        continue
                    # 防止用 send_to_user 冒充他人,target 必须等于自己的 user_id
                    if target != authenticated_user:
                        await connection_manager.send_personal_message(
                            WebSocketMessage(
                                type=MessageType.ERROR,
                                channel="system",
                                data={"error": "Cannot send to other users"},
                                sender="system",
                            ),
                            connection_id,
                        )
                        continue
                    message = WebSocketMessage(
                        type=MessageType.REALTIME_DATA,
                        channel=channel,
                        data=payload,
                        sender=authenticated_user,
                    )
                    await connection_manager.send_to_user(message, target)

                elif message_type == "get_subscriptions":
                    # 获取订阅列表
                    subscriptions = connection_manager.connection_subscriptions.get(connection_id, [])
                    await connection_manager.send_personal_message(
                        WebSocketMessage(
                            type=MessageType.INFO,
                            channel="system",
                            data={
                                "subscriptions": [
                                    {"channel": sub.channel, "filters": sub.filters} for sub in subscriptions
                                ]
                            },
                            sender="system",
                        ),
                        connection_id,
                    )

                elif message_type == "get_status":
                    # 获取连接状态
                    await connection_manager.send_personal_message(
                        WebSocketMessage(
                            type=MessageType.INFO,
                            channel="system",
                            data={
                                "connection_id": connection_id,
                                "active_connections": connection_manager.get_connection_count(),
                                "channels": {
                                    channel: connection_manager.get_channel_subscribers(channel)
                                    for channel in connection_manager.channel_subscriptions
                                },
                            },
                            sender="system",
                        ),
                        connection_id,
                    )

                else:
                    # 自定义消息类型，触发回调
                    logger.info(f"收到自定义消息: {message_type} from {connection_id}")

            except json.JSONDecodeError:
                logger.error(f"JSON 解析失败: {data}")
                await connection_manager.send_personal_message(
                    WebSocketMessage(
                        type=MessageType.ERROR, channel="system", data={"error": "Invalid JSON format"}, sender="system"
                    ),
                    connection_id,
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket 连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
    finally:
        # 断开连接
        await connection_manager.disconnect(connection_id)


@router.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    """
    实时数据推送 WebSocket

    自动订阅实时数据频道
    """
    connection_id = str(uuid.uuid4())

    await connection_manager.connect(
        websocket,
        connection_id=connection_id,
        metadata={"type": "live_data", "connected_at": datetime.now().isoformat()},
    )

    # 自动订阅实时数据频道
    await connection_manager.subscribe(connection_id, "live_data")

    try:
        # 保持连接并处理心跳
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "ping":
                await connection_manager.pong(connection_id)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"实时数据 WebSocket 错误: {e}")
    finally:
        await connection_manager.disconnect(connection_id)


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, user_id: str = Query(...)):
    """
    用户通知 WebSocket

    专门用于推送用户通知
    """
    connection_id = str(uuid.uuid4())

    await connection_manager.connect(
        websocket, connection_id=connection_id, user_id=user_id, metadata={"type": "notifications", "user_id": user_id}
    )

    # 自动订阅用户通知频道
    await connection_manager.subscribe(connection_id, f"notifications:{user_id}")

    try:
        # 保持连接并处理心跳
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "ping":
                await connection_manager.pong(connection_id)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"通知 WebSocket 错误: {e}")
    finally:
        await connection_manager.disconnect(connection_id)


# WebSocket admin REST API


@router.post("/ws/publish/data")
async def publish_data_update(channel: str, data: dict[str, Any]):
    """
    发布数据更新（通过 HTTP）

    Args:
        channel: 频道名称
        data: 数据内容
    """
    await realtime_publisher.publish_data_update(channel, data)
    return {"success": True, "channel": channel}


@router.post("/ws/publish/notification")
async def publish_notification(channel: str, title: str, content: str, level: str = "info"):
    """
    发布通知（通过 HTTP）

    Args:
        channel: 频道名称
        title: 通知标题
        content: 通知内容
        level: 通知级别 (info/success/warning/error)
    """
    await realtime_publisher.publish_notification(channel, title, content, level)
    return {"success": True, "channel": channel}


@router.post("/ws/publish/analysis-progress")
async def publish_analysis_progress(channel: str, progress: int, status: str, details: dict[str, Any] | None = None):
    """
    发布分析进度（通过 HTTP）

    Args:
        channel: 频道名称
        progress: 进度百分比 (0-100)
        status: 状态描述
        details: 详细信息
    """
    await realtime_publisher.publish_analysis_progress(channel, progress, status, details)
    return {"success": True, "channel": channel}


@router.get("/ws/status")
async def get_websocket_status():
    """
    获取 WebSocket 状态
    """
    return {
        "success": True,
        "status": {
            "active_connections": connection_manager.get_connection_count(),
            "channels": {
                channel: connection_manager.get_channel_subscribers(channel)
                for channel in connection_manager.channel_subscriptions
            },
            "timestamp": datetime.now().isoformat(),
        },
    }


@router.get("/ws/connections/{user_id}")
async def get_user_connections(user_id: str):
    """
    获取用户的所有连接
    """
    connections = connection_manager.get_user_connections(user_id)
    return {
        "success": True,
        "user_id": user_id,
        "connection_count": len(connections),
        "connection_ids": list(connections),
    }

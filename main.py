"""astrbot_plugin_astrmesh - 把现场事件通过指令发布进本地 AstrMesh Runtime。

本插件只是一个薄适配器:它把一条现场事件 POST 到本地 AstrMesh Runtime 的
loopback API(astrmesh-runtime serve),由 AstrMesh 的 EventGrid 领域账本负责持久化。
插件不拥有任何账本、不做真机投递——MeshCAP/Meshtastic 那段仍由 AstrMesh 的 G0 门管着。
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import aiohttp

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, StarTools


class AstrMeshPlugin(Star):
    """把现场事件上报到本地 AstrMesh Runtime 的 loopback API。整个插件唯一的 Star 子类。"""

    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config
        self._session: aiohttp.ClientSession | None = None
        self._tasks: set[asyncio.Task] = set()

    async def initialize(self):
        """插件激活时调用。建立 aiohttp 会话。"""
        self.data_dir = StarTools.get_data_dir()
        timeout = self._conf_int("request_timeout", 10)
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))
        logger.info("astrmesh 插件初始化完成")

    def _conf_str(self, key: str, default: str) -> str:
        value = self.config.get(key) if self.config else None
        return str(value) if value else default

    def _conf_int(self, key: str, default: int) -> int:
        value = self.config.get(key) if self.config else None
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    @filter.command("astrmesh", alias={"上报"})
    async def report(self, event: AstrMessageEvent, area: str):
        """上报一条 RESOURCE_LOW 现场事件到本地 AstrMesh Runtime。用法: /astrmesh <区域> <简述>"""
        try:
            # 区域由框架按位置解析;简述取区域之后的全部文本,支持多词(不依赖内部 GreedyStr)。
            summary = event.message_str.partition(area)[2].strip()
            if not summary:
                yield event.plain_result(
                    "用法: /astrmesh <区域> <简述>,例如 /astrmesh B_ZONE 饮水点断供"
                )
                return
            base = self._conf_str("api_base_url", "http://127.0.0.1:8787").rstrip("/")
            environment = self._conf_str("environment", "PRODUCTION")
            source_id = self._conf_str("source_id", "astrmesh.local")
            token = uuid.uuid4().hex[:12]
            now = datetime.now(UTC)
            payload = {
                "command_id": f"cmd-{token}",
                "environment": environment,
                "canonical_event_id": f"evt-{area.lower()}-{token}",
                "source_id": source_id,
                "event_id": f"{area.lower()}-{token}",
                "revision": 1,
                "category": "RESOURCE_LOW",
                "severity": "IMPORTANT",
                "area": area,
                "issued_at": now.isoformat(),
                "effective_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=2)).isoformat(),
                "title": f"{area} {summary}",
                "short_text": summary,
                "drill": False,
            }
            if self._session is None:
                yield event.plain_result("插件尚未就绪,请稍后再试。")
                return
            async with self._session.post(f"{base}/api/v1/events", json=payload) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    yield event.plain_result(
                        f"已发布 ✅ 事件 {data['canonical_event_id']} "
                        f"(rev {data['revision']}, outbox {data['outbox_id']})"
                    )
                elif resp.status == 403:
                    yield event.plain_result(f"无发布权限:区域 {area} 未在 Runtime 授予 PUBLISH_EVENT。")
                elif resp.status == 409:
                    yield event.plain_result("命令冲突:相同 command id 已用于不同内容。")
                else:
                    body = (await resp.text())[:200]
                    yield event.plain_result(f"发布失败(HTTP {resp.status}):{body}")
        except aiohttp.ClientError:
            logger.exception("astrmesh 连接 Runtime 失败")
            yield event.plain_result("连不上 AstrMesh Runtime。请确认已运行 `astrmesh-runtime serve`。")
        except Exception:
            logger.exception("astrmesh 上报执行失败")
            yield event.plain_result("出了点问题,请稍后再试~")

    async def terminate(self):
        """禁用/卸载/重载/更新时调用。清理会话与后台任务;禁止定义 __del__。"""
        for task in list(self._tasks):
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        if self._session and not self._session.closed:
            await self._session.close()
        logger.info("astrmesh 插件已终止")

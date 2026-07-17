# astrbot_plugin_astrmesh

把现场"资源不足 / 断供"事件通过指令发布进本地 [AstrMesh](https://github.com/Ayleovelle/AstrMesh) Runtime。

> An AstrBot plugin that publishes field `RESOURCE_LOW` events into a local AstrMesh Runtime over its
> loopback API. It is a thin adapter — it owns no ledger and performs no radio delivery; MeshCAP /
> Meshtastic delivery stays behind AstrMesh's G0 gate.

- AstrBot 版本要求:`>=4.16,<5`
- 支持平台:aiocqhttp

## 定位

这是 AstrMesh 的一个可选适配器,严格遵守 AstrMesh 设计修订第 7 节:只调 AstrMesh 的版本化
loopback API,不拥有业务账本或传输队列,不改 ACK/Receipt/Task/CLEAR 语义,故障也不阻塞主链路。
事件的持久化、归并、Outbox 全部由 AstrMesh 的 EventGrid 领域账本负责,插件只是个"上报按钮"。

## 前置

先在装了 AstrMesh 的机器上把本地 Runtime 跑起来(只绑 loopback):

```bash
astrmesh-runtime serve --db runtime.db --area B_ZONE
```

## 安装

- 手动:`git clone https://github.com/Ayleovelle/astrbot_plugin_astrmesh` 到 `AstrBot/data/plugins/`,在 WebUI 重载
- 或 WebUI 本地安装(AstrBot v4.26.3+)

## 配置

| 配置项 | 说明 | 默认 |
|---|---|---|
| api_base_url | 本地 AstrMesh Runtime 的 loopback API 地址 | `http://127.0.0.1:8787` |
| environment | 发布环境,需与 Runtime 授予发布权的 environment 一致 | `PRODUCTION` |
| source_id | 事件来源标识 | `astrmesh.local` |
| request_timeout | 调用 Runtime API 的超时秒数 | `10` |

## 指令

| 指令 | 参数 | 权限 | 说明 |
|---|---|---|---|
| `/astrmesh` (别名 `/上报`) | `<区域> <简述>` | 所有人 | 发布一条 RESOURCE_LOW 事件,例如 `/astrmesh B_ZONE 饮水点断供` |

发布成功会回一条 `已发布 ✅ 事件 <id> (rev 1, outbox <id>)`。区域未在 Runtime 授权则回无权限;
连不上则提示先 `astrmesh-runtime serve`。

## 反馈

Issue: https://github.com/Ayleovelle/astrbot_plugin_astrmesh/issues

## 许可证

AGPL-3.0,见 [LICENSE](./LICENSE)

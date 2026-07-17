# Changelog

本文件遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 格式,版本号遵循语义化版本。

## [v0.1.0]

### Added

- 初始版本。`/astrmesh <区域> <简述>`(别名 `/上报`)把一条 RESOURCE_LOW 现场事件
  POST 到本地 AstrMesh Runtime 的 loopback API,由 EventGrid 领域账本持久化。
- 可配置 `api_base_url` / `environment` / `source_id` / `request_timeout`。
- 薄适配器:不拥有账本、不做真机投递;区域未授权返回无权限,连不上给出明确提示。

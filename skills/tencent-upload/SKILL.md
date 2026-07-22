---
name: tencent-upload
description: 当 agent 需要通过 `sau tencent` 完成视频号登录、Cookie 校验、视频上传、定时发布、保存草稿或同时提交四比三横封面与三比四竖封面时使用。适用于多账号视频号发布和无人值守矩阵任务。
---

# 视频号上传

优先使用统一 CLI `sau tencent`，不要从旧 `examples/` 启动。

## 工作流

1. 先执行 `sau tencent check --account <name>`。
2. Cookie 无效时执行 `sau tencent login --account <name> --headed`。
3. 登录流程产生二维码时，直接展示或发送二维码给用户扫码，然后等待登录完成。
4. 发布前检查视频、四比三横封面、三比四竖封面、标题和账号名。
5. 四比三横封面和三比四竖封面都必须确认上传且封面弹窗已关闭；任一封面找不到入口或保存失败时，必须在提交作品前显式失败。
6. Agent 或调度器调用时同时传 `--json --result-file <path>`，以结果文件为准判断成功。
7. 失败时保留结果文件和日志，不要自动改账号或重复直发。

## 视频发布

```bash
sau tencent upload-video \
  --account <name> \
  --file <video.mp4> \
  --title "<title>" \
  --desc "<description>" \
  --tags tag1,tag2 \
  --thumbnail-landscape <cover-4x3.png> \
  --thumbnail-portrait <cover-3x4.png> \
  --short-title "<short-title>" \
  --headless \
  --json \
  --result-file <result.json>
```

不传 `--schedule` 时立即发布；传入 `--draft` 时保存草稿。详细参数见 [CLI 契约](references/cli-contract.md)，登录和页面异常见 [故障排查](references/troubleshooting.md)。

## 边界

- 首次登录、二维码、短信验证和平台验证码必须由用户完成。
- 不把 Cookie、二维码内容或账号凭据写入日志、仓库或 Telegram 文本。
- 同一账号发布任务串行执行，避免复用 Cookie 时发生浏览器会话冲突。
- 作品发出但微信转发缩略图为黑或空白，按横版封面未成功提交处理；视频上传成功不等于发布流程完整成功。
- `--result-file` 成功写入且 `success` 为 `true` 才算任务成功。

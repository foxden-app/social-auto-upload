# 视频号 CLI 契约

## 登录与检查

```bash
sau tencent login --account <name> --headed
sau tencent check --account <name> --json --result-file <result.json>
```

账号文件保存为 `cookies/tencent_<name>.json`。一个 `name` 对应一个视频号账号。

## 上传视频

```bash
sau tencent upload-video \
  --account <name> \
  --file <video.mp4> \
  --title "<title>" \
  [--desc "<description>"] \
  [--tags tag1,tag2] \
  [--schedule "YYYY-MM-DD HH:MM"] \
  [--thumbnail <cover-3x4.png>] \
  [--thumbnail-landscape <cover-4x3.png>] \
  [--thumbnail-portrait <cover-3x4.png>] \
  [--short-title "<short-title>"] \
  [--category "<category>"] \
  [--draft] \
  [--headless | --headed] \
  [--json] \
  [--result-file <path>]
```

`--thumbnail` 是旧兼容参数，等同于竖封面。矩阵任务应明确传横竖两张封面。

## 机器结果

`--json` 把命令日志转到标准错误，并在标准输出写一个 JSON 对象。`--result-file` 原子写入同一对象，自动任务优先读取结果文件。

关键字段：

```json
{
  "schema_version": 1,
  "success": true,
  "exit_code": 0,
  "status": "succeeded",
  "platform": "tencent",
  "action": "upload-video",
  "account": "wuya"
}
```

# hermes-tdai-session

一个 Hermes 插件：向经过 [TDAI MemoryProxy](https://github.com/TencentCloud/TencentDB-Agent-Memory) 的 LLM 请求注入当前会话的 `metadata.session_id`。

> 非官方项目，与腾讯云无关。

## 为什么需要

Hermes 的 `custom_providers.extra_headers` 和 `extra_body` 都是静态配置，每个请求携带同一份内容。而 TDAI MemoryProxy 需要请求级的会话 id 才能把不同会话区分开——否则所有 Hermes topic 会合并成同一个 proxy session。

Hermes 提供了 `llm_request` middleware，可以改写 provider kwargs，并且能拿到当前的 `session_id`。本插件用它注入：

```json
{ "metadata": { "session_id": "<当前会话 id>" } }
```

只对 `base_url` 匹配 Proxy 的请求生效。

## 安装

```bash
git clone https://github.com/ArtomYuan/hermes-tdai-session.git \
  ~/.hermes/plugins/hermes-tdai-session
hermes plugins enable hermes-tdai-session
```

重启网关（或新开会话）后生效。

## 配置

参考 [`examples/config.yaml`](examples/config.yaml)。要点：

- `model.provider: custom`，`base_url` 指向 `http://<proxy-host>:8096/hermes/<space-id>/v1`
- `extra_headers` 必须带 `x-team-id` 和 `x-agent-id`。新 session 的**第一个请求**必须带上，否则 Proxy 会把会话注册成没有 agent 的状态，之后永久跳过注入。
- **不要**设置 `x-conversation-id`：静态值会压过本插件注入的 body 字段。

## 环境变量

| 变量 | 默认值 | 说明 |
|:--|:--|:--|
| `TDAI_PROXY_MARK` | `:8096/hermes/` | 用于识别 Proxy `base_url` 的子串 |
| `TDAI_SESSION_FIELD` | `session_id` | 注入到 `metadata` 下的字段名 |

## 验证

```
[hermes-tdai-session] llm_request middleware registered (mark=':8096/hermes/', field='session_id')
[hermes-tdai-session] injected metadata.session_id=20261023_040202_c892857b
```

Proxy 侧：

```
[identity] sessionId=20261023_040202_c892857b
[session-init:cb] session=hermes:20261023_040202_c892857b → initialized
```

## 说明

- Proxy 侧读取 `metadata.session_id` 的支持进度见
  [TencentCloud/TencentDB-Agent-Memory#1764](https://github.com/TencentCloud/TencentDB-Agent-Memory/issues/1764)。
  1.0.2 上需要小补丁；官方版本发布后本插件无需改动。
- 不匹配 `TDAI_PROXY_MARK` 的请求会被原样放行，因此可以和其他 provider 共存。

## 许可证

GPL-3.0-or-later，见 [LICENSE](LICENSE)。

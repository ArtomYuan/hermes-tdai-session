# hermes-tdai-session

A Hermes plugin that injects a per-session `metadata.session_id` into LLM
requests routed through [TDAI MemoryProxy](https://github.com/TencentCloud/TencentDB-Agent-Memory).

> Unofficial. Not affiliated with Tencent Cloud.

## Why

Hermes' `custom_providers.extra_headers` and `extra_body` are static: every
request carries the same values. TDAI MemoryProxy needs a per-request session id
to keep conversations isolated — without it, every Hermes topic collapses into a
single proxy session.

Hermes exposes an `llm_request` middleware hook that can rewrite provider
kwargs, and it receives the current `session_id`. This plugin uses it to add:

```json
{ "metadata": { "session_id": "<current session>" } }
```

…only for requests whose `base_url` matches the proxy.

## Install

```bash
git clone https://github.com/ArtomYuan/hermes-tdai-session.git \
  ~/.hermes/plugins/hermes-tdai-session
hermes plugins enable hermes-tdai-session
```

Restart the gateway (or start a new session) to load it.

## Configure

See [`examples/config.yaml`](examples/config.yaml). Key points:

- `model.provider: custom` with `base_url: http://<proxy-host>:8096/hermes/<space-id>/v1`
- `extra_headers` must carry `x-team-id` and `x-agent-id`. The first request of a
  new session must include them, otherwise the proxy registers the session
  without an agent and permanently bypasses it.
- do **not** set `x-conversation-id`: a static value takes precedence over the
  injected body field.

## Environment variables

| Variable | Default | Meaning |
|:--|:--|:--|
| `TDAI_PROXY_MARK` | `:8096/hermes/` | Substring that identifies the proxy `base_url` |
| `TDAI_SESSION_FIELD` | `session_id` | Field name under `metadata` |

## Verify

```
[hermes-tdai-session] llm_request middleware registered (mark=':8096/hermes/', field='session_id')
[hermes-tdai-session] injected metadata.session_id=20261023_040202_c892857b
```

On the proxy side:

```
[identity] sessionId=20261023_040202_c892857b
[session-init:cb] session=hermes:20261023_040202_c892857b → initialized
```

## Notes

- Proxy-side support for reading `metadata.session_id` is tracked in
  [TencentCloud/TencentDB-Agent-Memory#1764](https://github.com/TencentCloud/TencentDB-Agent-Memory/issues/1764).
  On 1.0.2 it requires a small patch; once released, this plugin works unchanged.
- Requests that do not match `TDAI_PROXY_MARK` are left untouched, so the plugin
  is safe to keep enabled alongside other providers.

## License

Apache-2.0. See [LICENSE](LICENSE).

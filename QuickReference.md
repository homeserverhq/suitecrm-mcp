# Quick Reference — SuiteCRM MCP Server

## Build & Run

```bash
# Build Docker image (ALWAYS cached — never --no-cache)
docker build -t suitecrm-mcp:latest .

# Stop old container, start new one
docker rm -f suitecrm-mcp 2>/dev/null
docker run -d --name suitecrm-mcp --network dock-ext \
    -p 6031:6031 \
    -e SUITECRM_BASE_URL="http://suitecrm-web:80" \
    -e MCP_SERVER_PORT=6031 \
    -e API_KEY="obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC" \
    -e ALLOW_ALL_AGGREGATE=false \
    -e IS_STATEFUL=false \
    suitecrm-mcp:latest
```

## Test

```bash
# Run full test suite (146 tests, all run every time)
API_KEY="obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC" MCP_SERVER_PORT=6031 \
    python src/test_runner.py > /tmp/output.txt 2>&1
```

## Direct MCP Server Query (debug without test runner)

```python
import json, httpx
h = {'Authorization': 'Bearer obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC', 'Content-Type': 'application/json'}
r1 = httpx.post('http://localhost:6031/mcp', headers=h,
    json={'jsonrpc':'2.0','id':1,'method':'initialize',
          'params':{'protocolVersion':'2024-11-05','capabilities':{},
                    'clientInfo':{'name':'debug','version':'1.0'}}})
sid = r1.headers.get('mcp-session-id')
h['mcp-session-id'] = sid
httpx.post('http://localhost:6031/mcp', headers=h,
    json={'jsonrpc':'2.0','method':'notifications/initialized'})
r2 = httpx.post('http://localhost:6031/mcp', headers=h,
    json={'jsonrpc':'2.0','id':2,'method':'tools/list'})
tools = r2.json()
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SUITECRM_BASE_URL` | Backend SuiteCRM instance URL (no `/Api/V8` suffix needed) | — |
| `MCP_SERVER_PORT` | Listen port for MCP server | 6031 |
| `API_KEY` | SuiteCRM API bearer token (required) | — |
| `ALLOW_ALL_AGGREGATE` | When `true`, aggregate list tools pass through caller's `include_all_fields`. When `false`, forces `include_all_fields=False` on all bulk-list tools. | false |
| `IS_STATEFUL` | When `true`, uses stateful Streamable HTTP with session tracking. When `false`, uses stateless mode. | false |

## Project Structure

```
/app/           (inside container)
  src/
    main.py     — MCP tool definitions (120 tools, tagged by read/write + basic/primary/advanced)
    client.py   — HTTP client calling SuiteCRM V8 API (client-side field filtering, datetime validation)
    test_runner.py — End-to-end test harness (flat, unconditional, 146 tests)
  Dockerfile
  pyproject.toml
```

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Tool definitions — add/modify MCP tools here (Literal enums, ALLOW_ALL_AGGREGATE gating) |
| `src/client.py` | SuiteCRM API client — add/modify API calls here (COMMON_FIELDS, client-side filtering) |
| `src/test_runner.py` | Test harness — add/modify tests here (zero branches, zero try/catch, only PASS/FAIL) |

## Important Rules

- **Only modify** `src/main.py`, `src/client.py`, `src/test_runner.py` — no other files
- **Test runner is FLAT** — zero `if`, `for`, `try`, `or` in `main()` function
- **Every test runs unconditionally** — no prerequisites, no skips
- **Exceptions crash the runner** — no `try`/`except`
- **No hardcoded fallback values** — tools receive real data or crash
- **Docker build is ALWAYS cached** — `--no-cache` is wasteful and never needed
- **SuiteCRM rejects `fields[]` on POST/PATCH** — create/update use client-side filtering
- **Datetime requires explicit UTC offset** — `2026-06-22T15:00:00-04:00`, not naive `2026-06-22T15:00:00`
- **Date-only fields use `YYYY-MM-DD`** — date_closed, active_date, estimated_start/end, start_date, end_date, due_date, valid_until

## Quick Commands

```bash
# Rebuild + redeploy + test (full loop)
docker build -t suitecrm-mcp:latest . && \
docker rm -f suitecrm-mcp 2>/dev/null && \
docker run -d --name suitecrm-mcp --network dock-ext \
    -p 6031:6031 \
    -e SUITECRM_BASE_URL=http://suitecrm-web:80 \
    -e MCP_SERVER_PORT=6031 \
    -e API_KEY="obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC" \
    -e ALLOW_ALL_AGGREGATE=false \
    -e IS_STATEFUL=false \
    suitecrm-mcp:latest && \
sleep 3 && \
API_KEY="obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC" MCP_SERVER_PORT=6031 python src/test_runner.py

# Test runner only (no rebuild needed after test_runner.py changes)
API_KEY="obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC" MCP_SERVER_PORT=6031 python src/test_runner.py

# Build only (needed after main.py or client.py changes)
docker build -t suitecrm-mcp:latest .
```

## Common Debugging

```bash
# Check container logs
docker logs suitecrm-mcp

# Restart container
docker restart suitecrm-mcp && sleep 3
```

## Backend API (curl)

```bash
# SuiteCRM V8 REST API examples
SUITECRM="http://localhost:8020/Api/V8"
TOKEN="obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC"

# List accounts
curl -s -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/vnd.api+json" \
    "$SUITECRM/module/Accounts?page[size]=5"

# Create account
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/vnd.api+json" \
    "$SUITECRM/module" \
    -d '{"data":{"type":"Accounts","attributes":{"name":"Test Account"}}}'

# Get record by ID
curl -s -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/vnd.api+json" \
    "$SUITECRM/module/Accounts/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# List relationships
curl -s -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/vnd.api+json" \
    "$SUITECRM/module/Accounts/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/relationship/contacts"
```

## Python MCP Client (direct tool calls)

```python
import json, httpx
h = {'Authorization': 'Bearer obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC',
     'Content-Type': 'application/json', 'Accept': 'application/json'}
r = httpx.post('http://localhost:6031/mcp', headers=h,
    json={'jsonrpc':'2.0','id':1,'method':'initialize',
          'params':{'protocolVersion':'2024-11-05','capabilities':{},
                    'clientInfo':{'name':'debug','version':'1.0'}}})
sid = r.headers.get('mcp-session-id')
h['mcp-session-id'] = sid
httpx.post('http://localhost:6031/mcp', headers=h,
    json={'jsonrpc':'2.0','method':'notifications/initialized'})
# Call any tool:
r = httpx.post('http://localhost:6031/mcp', headers=h,
    json={'jsonrpc':'2.0','id':2,'method':'tools/call',
          'params':{'name':'get_all_accounts','arguments':{'limit':5}}})
print(r.json()['result'])
```

# CRITICAL

You MUST adhere to the following rules:
  - DO NOT under ANY circumstances run --no-cache build in docker build commands - YOU WILL BREAK EVERYTHING if you do!!!
  - Run the test runner ONE SINGLE FUCKING TIME after building the container and redirect the result to file in /tmp/, then you can read the file all you want.
  - DO NOT under ANY circumstances run ANY git commands, they are ALL STRICTLY OFF LIMITS.
  - DO NOT mess with ANY other files besides src/main.py, src/client.py, and src/test_runner.py. These are the ONLY three files you are allowed to edit.
  - DO NOT run any docker commands besides the ones explicitly defined in THIS document. NO OTHER DOCKER COMMANDS!!!!

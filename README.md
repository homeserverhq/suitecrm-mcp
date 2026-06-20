# SuiteCRM MCP Server

Multi-tenant MCP proxy server for SuiteCRM V8 REST API.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUITECRM_BASE_URL` | Yes | Docker-internal URL of the SuiteCRM API (e.g. `http://suitecrm-nginx:80/Api/V8`) |
| `MCP_SERVER_PORT` | Yes | Port number the MCP server listens on |

## Usage

```bash
docker build -t suitecrm-mcp:latest .
docker run -d --name suitecrm-mcp --network dock-ext \
    -e SUITECRM_BASE_URL="http://suitecrm-nginx:80/Api/V8" \
    -e MCP_SERVER_PORT=6031 \
    -p 6031:6031 \
    suitecrm-mcp:latest
```

The MCP server serves at `http://localhost:6031/mcp` (Streamable HTTP).

## Tools (120)

### Module CRUD (22 modules × 5 tools = 110)

Each module has: `get_all_*`, `get_*_by_id`, `create_*`, `update_*`, `delete_*_by_id`.

Modules: Accounts, Contacts, Leads, Opportunities, Cases, Notes, Calls, Meetings, Tasks, Emails, Documents, Project, Prospects, Campaigns, Bugs, Products, Contracts, Invoices, Quotes, KnowledgeBase, Events, Reports.

### Additional Tools (7)

- `get_current_user` — authenticated user profile
- `check_server_status` — backend connectivity check
- `get_calendar_events` — merged Calls + Meetings + Tasks by date range
- `get_calendar_event_by_id` — lookup by ID across calendar modules
- `get_activities_related_to_record` — calls, meetings, tasks, notes, emails linked to a record
- `get_history_related_to_record` — same but only completed/closed items
- `get_activity_history_by_id` — lookup by ID across activity modules

### Relationship Tools (3)

- `get_record_relationships` — list linked records
- `create_record_relationship` — link two records
- `delete_record_relationship` — unlink records

## TOON Compression

Bulk list responses are automatically compressed using TOON (Token-Optimized Object Notation) to reduce token consumption.

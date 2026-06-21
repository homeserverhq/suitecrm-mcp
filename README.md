# SuiteCRM MCP Multitenant Proxy Server

This repository contains a Model Context Protocol (MCP) server that acts as a secure, multi-tenant proxy between an AI Assistant and the SuiteCRM V8 REST API. It exposes **120 MCP tools** covering 22 SuiteCRM modules with full CRUD, calendar, activity, and relationship management.

## Features

- **Identity Passthrough** — Extracts the `Authorization: Bearer <token>` header from incoming HTTP requests and forwards it to the SuiteCRM API without server-side authentication.
- **Multi-Tenancy** — Uses Python `contextvars` to maintain thread-safe user identity isolation, ensuring all AI-driven actions are scoped to the authenticated user's permissions.
- **Full SuiteCRM Coverage** — 120 tools mapped to SuiteCRM V8 API endpoints across 22 modules (Accounts, Contacts, Leads, Opportunities, Cases, Notes, Calls, Meetings, Tasks, Emails, Documents, Project, Prospects, Campaigns, Bugs, Products, Contracts, Invoices, Quotes, Knowledge Base, Events, Reports).
- **TOON Optimization** — Bulk list responses are automatically compressed using TOON (Token-Optimized Object Notation) to reduce token consumption and maximize context window efficiency.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUITECRM_BASE_URL` | Yes | Docker-internal URL of the SuiteCRM API (e.g. `http://suitecrm-web:80/Api/V8`) |
| `MCP_SERVER_PORT` | Yes | Port number the MCP server listens on |

## Installation & Local Development

1. Ensure you have Python 3.12+ installed.
2. Install dependencies:
   ```bash
   pip install fastmcp httpx pydantic uvicorn toon-mcp-server
   ```
3. Run the server:
   ```bash
   export SUITECRM_BASE_URL=http://your-suitecrm:80/Api/V8
   export MCP_SERVER_PORT=80
   python -m src.main
   ```

## Docker Deployment

Build and run the server using Docker:

```bash
docker build -t suitecrm-mcp:latest .
docker run -d --name suitecrm-mcp --network dock-ext \
    -e SUITECRM_BASE_URL="http://suitecrm-web:80/Api/V8" \
    -e MCP_SERVER_PORT=80 \
    suitecrm-mcp:latest
```

The MCP server serves at `http://suitecrm-mcp:80/mcp` (Streamable HTTP).

## Important Notes

- **`include_all_fields`** — The `include_all_fields` parameter (available on all `get_*` and `list_*` tools) controls whether Studio-defined custom fields are included in responses. Defaults to `False` for performance; set to `True` only when custom fields are needed.
- **TOON Compression** — All bulk list responses are automatically compressed using TOON (Token-Optimized Object Notation) to reduce token consumption by 30-60%.
- **Required Fields & Defaults** — Each `create_*` tool requires specific key fields (e.g. `name` for Accounts, `first_name`/`last_name` for Contacts, `last_name` for Leads). All other fields default to empty strings or reasonable values. The `assigned_user_id` is automatically set to the authenticated user for most modules (excluded for Documents, Products, Contracts, Invoices, Quotes, Knowledge Base, Events, and Reports).

## API Tool Mapping

The server implements 120 MCP tools organized into the following categories:

### 📊 Accounts (5)
- `get_all_accounts` — List all account records
- `get_account_by_id` — Get a single account by ID
- `create_account` — Create a new account
- `update_account` — Update an existing account
- `delete_account_by_id` — Delete an account by ID

### 👤 Contacts (5)
- `get_all_contacts` — List all contact records
- `get_contact_by_id` — Get a single contact by ID
- `create_contact` — Create a new contact
- `update_contact` — Update an existing contact
- `delete_contact_by_id` — Delete a contact by ID

### 🎯 Leads (5)
- `get_all_leads` — List all lead records
- `get_lead_by_id` — Get a single lead by ID
- `create_lead` — Create a new lead
- `update_lead` — Update an existing lead
- `delete_lead_by_id` — Delete a lead by ID

### 💰 Opportunities (5)
- `get_all_opportunities` — List all opportunity records
- `get_opportunity_by_id` — Get a single opportunity by ID
- `create_opportunity` — Create a new opportunity
- `update_opportunity` — Update an existing opportunity
- `delete_opportunity_by_id` — Delete an opportunity by ID

### 🔧 Cases (5)
- `get_all_cases` — List all case records
- `get_case_by_id` — Get a single case by ID
- `create_case` — Create a new case
- `update_case` — Update an existing case
- `delete_case_by_id` — Delete a case by ID

### 📝 Notes (5)
- `get_all_notes` — List all note records
- `get_note_by_id` — Get a single note by ID
- `create_note` — Create a new note
- `update_note` — Update an existing note
- `delete_note_by_id` — Delete a note by ID

### 📞 Calls (5)
- `get_all_calls` — List all call records
- `get_call_by_id` — Get a single call by ID
- `create_call` — Create a new call
- `update_call` — Update an existing call
- `delete_call_by_id` — Delete a call by ID

### 📅 Meetings (5)
- `get_all_meetings` — List all meeting records
- `get_meeting_by_id` — Get a single meeting by ID
- `create_meeting` — Create a new meeting
- `update_meeting` — Update an existing meeting
- `delete_meeting_by_id` — Delete a meeting by ID

### ✅ Tasks (5)
- `get_all_tasks` — List all task records
- `get_task_by_id` — Get a single task by ID
- `create_task` — Create a new task
- `update_task` — Update an existing task
- `delete_task_by_id` — Delete a task by ID

### ✉️ Emails (5)
- `get_all_emails` — List all email records
- `get_email_by_id` — Get a single email by ID
- `create_email` — Create a new email
- `update_email` — Update an existing email
- `delete_email_by_id` — Delete an email by ID

### 📄 Documents (5)
- `get_all_documents` — List all document records
- `get_document_by_id` — Get a single document by ID
- `create_document` — Create a new document
- `update_document` — Update an existing document
- `delete_document_by_id` — Delete a document by ID

### 📋 Project (5)
- `get_all_projects` — List all project records
- `get_project_by_id` — Get a single project by ID
- `create_project` — Create a new project
- `update_project` — Update an existing project
- `delete_project_by_id` — Delete a project by ID

### 🎯 Prospects (5)
- `get_all_prospects` — List all prospect records
- `get_prospect_by_id` — Get a single prospect by ID
- `create_prospect` — Create a new prospect
- `update_prospect` — Update an existing prospect
- `delete_prospect_by_id` — Delete a prospect by ID

### 📢 Campaigns (5)
- `get_all_campaigns` — List all campaign records
- `get_campaign_by_id` — Get a single campaign by ID
- `create_campaign` — Create a new campaign
- `update_campaign` — Update an existing campaign
- `delete_campaign_by_id` — Delete a campaign by ID

### 🐛 Bugs (5)
- `get_all_bugs` — List all bug records
- `get_bug_by_id` — Get a single bug by ID
- `create_bug` — Create a new bug
- `update_bug` — Update an existing bug
- `delete_bug_by_id` — Delete a bug by ID

### 📦 Products (5)
- `get_all_products` — List all product records
- `get_product_by_id` — Get a single product by ID
- `create_product` — Create a new product
- `update_product` — Update an existing product
- `delete_product_by_id` — Delete a product by ID

### 📑 Contracts (5)
- `get_all_contracts` — List all contract records
- `get_contract_by_id` — Get a single contract by ID
- `create_contract` — Create a new contract
- `update_contract` — Update an existing contract
- `delete_contract_by_id` — Delete a contract by ID

### 🧾 Invoices (5)
- `get_all_invoices` — List all invoice records
- `get_invoice_by_id` — Get a single invoice by ID
- `create_invoice` — Create a new invoice
- `update_invoice` — Update an existing invoice
- `delete_invoice_by_id` — Delete an invoice by ID

### 💬 Quotes (5)
- `get_all_quotes` — List all quote records
- `get_quote_by_id` — Get a single quote by ID
- `create_quote` — Create a new quote
- `update_quote` — Update an existing quote
- `delete_quote_by_id` — Delete a quote by ID

### 📚 Knowledge Base (5)
- `get_all_knowledgebase` — List all knowledge base articles
- `get_knowledgebase_by_id` — Get a single knowledge base article by ID
- `create_knowledgebase` — Create a new knowledge base article
- `update_knowledgebase` — Update an existing knowledge base article
- `delete_knowledgebase_by_id` — Delete a knowledge base article by ID

### 🎪 Events (5)
- `get_all_events` — List all event records
- `get_event_by_id` — Get a single event by ID
- `create_event` — Create a new event
- `update_event` — Update an existing event
- `delete_event_by_id` — Delete an event by ID

### 📊 Reports (5)
- `get_all_reports` — List all report records
- `get_report_by_id` — Get a single report by ID
- `create_report` — Create a new report
- `update_report` — Update an existing report
- `delete_report_by_id` — Delete a report by ID

### 🗓️ Calendar & Activities (5)
- `get_calendar_events` — Retrieve calendar events (Calls, Meetings, Tasks) within a date range
- `get_calendar_event_by_id` — Look up a single calendar event by ID across modules
- `get_activities_related_to_record` — Get open activities linked to a specific record
- `get_history_related_to_record` — Get completed or closed activities linked to a record
- `get_activity_history_by_id` — Look up an activity by ID across activity modules

### 🔗 Relationships (3)
- `get_record_relationships` — List records linked via a relationship
- `create_record_relationship` — Link two records together
- `delete_record_relationship` — Unlink two records

### ⚙️ System (2)
- `get_current_user` — Retrieve the currently authenticated user's profile
- `check_server_status` — Verify connectivity to the SuiteCRM backend

"""
End-to-end test harness for SuiteCRM MCP Server.

Connects via Streamable HTTP (JSON-RPC POST), tests all 120 tools,
and prints a Markdown report. No branches, no try/catch, no SKIP.
"""

import json
import os
import sys
import time
import uuid
from typing import Any

import httpx

MCP_SERVER_PORT = os.environ.get("MCP_SERVER_PORT", "8020")
API_KEY = os.environ.get("API_KEY", "obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC")
MCP_URL = f"http://localhost:{MCP_SERVER_PORT}/mcp"

MCP_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
}

rid = uuid.uuid4().hex[:8]

results: list[dict[str, Any]] = []
_created_ids: dict[str, str] = {}


class MCPSession:
    """MCP Streamable HTTP client using JSON-RPC over HTTP POST."""

    def __init__(self, url: str, headers: dict[str, str]):
        self.url = url
        self.base_headers = {**headers, "Content-Type": "application/json", "Accept": "application/json"}
        self.session_headers = dict(self.base_headers)
        self.client = httpx.AsyncClient(timeout=120.0)
        self._request_id = 0
        self._session_id: str | None = None

    async def __aenter__(self):
        await self._initialize()
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def _send_notification(self, method: str) -> None:
        response = await self.client.post(
            self.url, headers=self.session_headers,
            json={"jsonrpc": "2.0", "method": method}
        )
        response.raise_for_status()

    async def _send(self, method: str, params: dict = {}) -> dict:
        self._request_id += 1
        payload = {"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params}
        response = await self.client.post(self.url, headers=self.session_headers, json=payload)
        response.raise_for_status()

        sid = response.headers.get("mcp-session-id")
        self._session_id = sid or self._session_id
        self.session_headers = {**self.base_headers, "mcp-session-id": self._session_id}

        data = response.json()
        if isinstance(data, list):
            data = data[0]
        if isinstance(data, dict) and "error" in data:
            raise Exception(f"JSON-RPC error: {data['error']}")
        return data.get("result", {})

    async def _initialize(self) -> dict:
        result = await self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "suitecrm-test-runner", "version": "1.0"},
        })
        await self._send_notification("notifications/initialized")
        return result

    async def call_tool(self, name: str, arguments: dict = {}) -> dict:
        return await self._send("tools/call", {"name": name, "arguments": arguments})

    async def list_tools(self) -> list[dict]:
        result = await self._send("tools/list")
        return result.get("tools", result)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


async def run_test(label: str, tool: str, params: dict[str, Any] = {}, expect_error: bool = False) -> dict:
    result = await session.call_tool(tool, params)
    is_error = result.get("isError", False)
    passed = (not is_error, is_error)[expect_error]
    status = ("FAILED", "PASSED")[bool(passed)]
    results.append({"label": label, "tool": tool, "status": status, "result": result})
    log(f"  {status} {label}")
    return result


def make_name(base: str) -> str:
    return f"t{rid}-{base}"


MODULE_TESTS = [
    ("Accounts", "create_account", {"name": make_name("Account"), "account_type": "Customer"},
     "get_all_accounts", "get_account_by_id",
     "update_account", {"name": make_name("Account-upd")},
     "delete_account_by_id"),
    ("Contacts", "create_contact", {"first_name": f"Test{rid}", "last_name": "Contact"},
     "get_all_contacts", "get_contact_by_id",
     "update_contact", {"last_name": "Contact-upd"},
     "delete_contact_by_id"),
    ("Leads", "create_lead", {"first_name": f"Test{rid}", "last_name": "Lead", "status": "New"},
     "get_all_leads", "get_lead_by_id",
     "update_lead", {"status": "Assigned"},
     "delete_lead_by_id"),
    ("Opportunities", "create_opportunity",
     {"name": make_name("Opp"), "amount": 1000.0, "date_closed": "2026-12-31", "sales_stage": "Prospecting"},
     "get_all_opportunities", "get_opportunity_by_id",
     "update_opportunity", {"sales_stage": "Needs Analysis"},
     "delete_opportunity_by_id"),
    ("Cases", "create_case", {"name": make_name("Case"), "description": "Test case"},
     "get_all_cases", "get_case_by_id",
     "update_case", {"priority": "P2"},
     "delete_case_by_id"),
    ("Notes", "create_note", {"name": make_name("Note"), "description": "Test note"},
     "get_all_notes", "get_note_by_id",
     "update_note", {"description": "Updated note"},
     "delete_note_by_id"),
    ("Calls", "create_call", {"name": make_name("Call"), "date_start": "2026-06-20", "duration_hours": 1, "status": "Planned"},
     "get_all_calls", "get_call_by_id",
     "update_call", {"duration_hours": 2},
     "delete_call_by_id"),
    ("Meetings", "create_meeting", {"name": make_name("Meeting"), "date_start": "2026-06-20", "duration_hours": 1},
     "get_all_meetings", "get_meeting_by_id",
     "update_meeting", {"status": "Held"},
     "delete_meeting_by_id"),
    ("Tasks", "create_task", {"name": make_name("Task"), "status": "Not Started", "date_due": "2026-06-30"},
     "get_all_tasks", "get_task_by_id",
     "update_task", {"priority": "High"},
     "delete_task_by_id"),
    ("Emails", "create_email", {"name": make_name("Email"), "description": "Test email"},
     "get_all_emails", "get_email_by_id",
     "update_email", {"type": "archived"},
     "delete_email_by_id"),
    ("Documents", "create_document",
     {"document_name": make_name("Doc"), "filename": "test.txt", "active_date": "2026-06-20", "description": "Test doc"},
     "get_all_documents", "get_document_by_id",
     "update_document", {"revision": "2"},
     "delete_document_by_id"),
    ("Project", "create_project",
     {"name": make_name("Project"), "estimated_start_date": "2026-06-20", "estimated_end_date": "2026-12-31", "status": "Underway"},
     "get_all_projects", "get_project_by_id",
     "update_project", {"priority": "High"},
     "delete_project_by_id"),
    ("Prospects", "create_prospect", {"first_name": f"Test{rid}", "last_name": "Prospect"},
     "get_all_prospects", "get_prospect_by_id",
     "update_prospect", {"title": "Updated Title"},
     "delete_prospect_by_id"),
    ("Campaigns", "create_campaign",
     {"name": make_name("Campaign"), "campaign_type": "Email", "status": "Active", "start_date": "2026-06-20", "end_date": "2026-12-31"},
     "get_all_campaigns", "get_campaign_by_id",
     "update_campaign", {"budget": 5000.0},
     "delete_campaign_by_id"),
    ("Bugs", "create_bug", {"name": make_name("Bug"), "description": "Test bug"},
     "get_all_bugs", "get_bug_by_id",
     "update_bug", {"priority": "High"},
     "delete_bug_by_id"),
    ("Products", "create_product",
     {"name": make_name("Product"), "cost": 10.0, "price": 25.0, "type": "Good"},
     "get_all_products", "get_product_by_id",
     "update_product", {"price": 30.0},
     "delete_product_by_id"),
    ("Contracts", "create_contract",
     {"name": make_name("Contract"), "status": "Active", "contract_account": "Test Account", "total_contract_value": 5000.0},
     "get_all_contracts", "get_contract_by_id",
     "update_contract", {"total_contract_value": 6000.0},
     "delete_contract_by_id"),
    ("Invoices", "create_invoice",
     {"name": make_name("Invoice"), "number": f"INV-{rid}", "status": "Unpaid", "total_amount": 1000.0, "due_date": "2026-07-31"},
     "get_all_invoices", "get_invoice_by_id",
     "update_invoice", {"status": "Paid"},
     "delete_invoice_by_id"),
    ("Quotes", "create_quote",
     {"name": make_name("Quote"), "stage": "Draft", "total_amount": 1000.0},
     "get_all_quotes", "get_quote_by_id",
     "update_quote", {"stage": "Negotiation"},
     "delete_quote_by_id"),
    ("KnowledgeBase", "create_knowledgebase",
     {"name": make_name("KB"), "author": "TestAuthor", "status": "published_public", "description": "Test KB article"},
     "get_all_knowledgebase", "get_knowledgebase_by_id",
     "update_knowledgebase", {"revision": "2"},
     "delete_knowledgebase_by_id"),
    ("Events", "create_event",
     {"name": make_name("Event"), "date_start": "2026-06-20", "duration_hours": 2, "description": "Test event"},
     "get_all_events", "get_event_by_id",
     "update_event", {"location": "Main Hall"},
     "delete_event_by_id"),
    ("Reports", "create_report",
     {"name": make_name("Report"), "report_module": "Accounts"},
     "get_all_reports", "get_report_by_id",
     "update_report", {"graphs_per_row": 3},
     "delete_report_by_id"),
]


async def main():
    global session

    print(f"# Test Report — SuiteCRM MCP Server")
    print(f"\n**Date**: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    print(f"**Server**: {MCP_URL}")
    print(f"**Run ID**: {rid}")
    print()

    async with MCPSession(MCP_URL, MCP_HEADERS) as session:

        # Phase 0: Initialize session and discover tools
        log("\n=== Phase 0: Session Init & Tool Discovery ===")
        tools_list = await session.list_tools()
        tool_names = [t["name"] for t in tools_list]
        print(f"**Discovered**: {len(tool_names)} tools")
        print()

        # Phase 1: Read-only tools
        log("\n=== Phase 1: Status & User Tools ===")
        await run_test("A1 check_server_status", "check_server_status")
        await run_test("A2 get_current_user", "get_current_user")

        # Phase 2: List tools (get_all for each module)
        log("\n=== Phase 2: List Tools ===")
        for mod_conf in MODULE_TESTS:
            api_mod = mod_conf[0]
            list_tool_name = mod_conf[3]
            await run_test(f"B2 list_{api_mod.lower()}", list_tool_name)

        # Phase 3: Create + Get + Update + Delete + Verify Delete
        log("\n=== Phase 3: Module CRUD Cycle ===")
        for mod_conf in MODULE_TESTS:
            api_mod, create_tool, create_params, _, get_tool, update_tool, update_params, delete_tool = mod_conf
            mod_key = api_mod.lower()

            _create_result = await run_test(f"C1 create_{mod_key}", create_tool, create_params)
            _raw = _create_result.get("content", [{}])[0].get("text", "{}")
            _start = _raw.find("{")
            _end = _raw.rfind("}") + 1
            _data = json.loads(_raw[max(0, _start):max(0, _end)] or "{}")
            _cid = _data.get("id")
            _created_ids[mod_key] = _cid

            await run_test(f"C2 get_{mod_key}_by_id", get_tool, {"id": _cid})
            _upd = dict(update_params)
            _upd["id"] = _cid
            await run_test(f"C3 update_{mod_key}", update_tool, _upd)
            await run_test(f"C4 delete_{mod_key}_by_id", delete_tool, {"id": _cid})
            await run_test(f"C5 verify_delete_{mod_key}", get_tool, {"id": _cid}, expect_error=True)

        # Phase 4: Calendar Tools
        log("\n=== Phase 4: Calendar Tools ===")
        await run_test("D1 get_calendar_events", "get_calendar_events",
                       {"start_date": "2026-01-01", "end_date": "2026-12-31"})

        # Phase 5: Relationship Tools
        log("\n=== Phase 5: Relationship Tools ===")
        _rel_acct = await run_test("E1 create_rel_account", "create_account",
                                   {"name": make_name("RelAccount"), "account_type": "Customer"})
        _rel_acct_raw = _rel_acct.get("content", [{}])[0].get("text", "{}")
        _rel_acct_start = _rel_acct_raw.find("{")
        _rel_acct_end = _rel_acct_raw.rfind("}") + 1
        _rel_acct_data = json.loads(_rel_acct_raw[max(0, _rel_acct_start):max(0, _rel_acct_end)] or "{}")
        _rel_acct_id = _rel_acct_data.get("id")

        _rel_cont = await run_test("E2 create_rel_contact", "create_contact",
                                   {"first_name": f"Rel{rid}", "last_name": "Contact"})
        _rel_cont_raw = _rel_cont.get("content", [{}])[0].get("text", "{}")
        _rel_cont_start = _rel_cont_raw.find("{")
        _rel_cont_end = _rel_cont_raw.rfind("}") + 1
        _rel_cont_data = json.loads(_rel_cont_raw[max(0, _rel_cont_start):max(0, _rel_cont_end)] or "{}")
        _rel_cont_id = _rel_cont_data.get("id")

        await run_test("E3 create_rel", "create_record_relationship", {
            "module": "Accounts", "id": _rel_acct_id,
            "related_module": "Contacts", "related_id": _rel_cont_id,
        })
        await run_test("E4 get_rel", "get_record_relationships", {
            "module": "Accounts", "id": _rel_acct_id,
            "link_field_name": "contacts"
        })
        await run_test("E5 delete_rel", "delete_record_relationship", {
            "module": "Accounts", "id": _rel_acct_id,
            "link_field_name": "contacts", "related_id": _rel_cont_id
        })
        await run_test("E6 cleanup_rel_account", "delete_account_by_id", {"id": _rel_acct_id})
        await run_test("E7 cleanup_rel_contact", "delete_contact_by_id", {"id": _rel_cont_id})

        # Phase 6: Activity/History
        log("\n=== Phase 6: Activity & History ===")
        _call_id = _created_ids.get("calls")
        await run_test("F1 activity_history_by_id", "get_activity_history_by_id", {"id": _call_id})
        _note_id = _created_ids.get("notes")
        await run_test("F2 activities_related", "get_activities_related_to_record", {
            "module": "Notes", "id": _note_id
        })
        _acc_id = _created_ids.get("accounts")
        await run_test("G1 history_related", "get_history_related_to_record", {
            "module": "Accounts", "id": _acc_id
        })
        await run_test("H1 calendar_event_by_id", "get_calendar_event_by_id", {"id": _call_id})

    # Generate Report
    passed = 0
    failed = 0
    for r in results:
        passed = passed + (r["status"] == "PASSED")
        failed = failed + (r["status"] == "FAILED")

    print(f"\n## Summary\n")
    print(f"| Status | Count |")
    print(f"|--------|-------|")
    print(f"| PASSED | {passed} |")
    print(f"| FAILED | {failed} |")

    print(f"\n## Results\n")
    for r in results:
        print(f"- `{r['tool']}` — {r['label']} — {r['status']}")

    print(f"\n---\n**Total tests:** {len(results)} | **PASSED:** {passed} | **FAILED:** {failed}")

    _all_pass = (failed == 0)
    _verdict = ("TESTS FAILING", "ALL TESTS PASS")[_all_pass]
    print(f"\n**{_verdict}**")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

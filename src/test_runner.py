"""
End-to-end test harness for SuiteCRM MCP Server.

Connects via Streamable HTTP (JSON-RPC POST), tests all 120 tools,
and prints a Markdown report.
"""

import json
import os
import sys
import time
import uuid
from typing import Any, Optional

import httpx

MCP_SERVER_PORT = os.environ.get("MCP_SERVER_PORT", "8020")
API_KEY = os.environ.get("API_KEY", "obrWw16WzXQBW3mHGCNaTfjd7AwqrjKC")
MCP_URL = f"http://localhost:{MCP_SERVER_PORT}/mcp"

MCP_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
}

rid = uuid.uuid4().hex[:8]

results: list[dict[str, Any]] = []
store: dict[str, Any] = {}
created: dict[str, str] = {}
iteration = 1


class MCPSession:
    """MCP Streamable HTTP client using JSON-RPC over HTTP POST (stateful sessions)."""

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

    async def _send_notification(self, method: str, params: dict | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params:
            payload["params"] = params
        response = await self.client.post(self.url, headers=self.session_headers, json=payload)
        if response.status_code not in (200, 202):
            response.raise_for_status()

    async def _send(self, method: str, params: dict | None = None) -> dict:
        self._request_id += 1
        payload = {"jsonrpc": "2.0", "id": self._request_id, "method": method}
        if params:
            payload["params"] = params
        response = await self.client.post(self.url, headers=self.session_headers, json=payload)
        if response.status_code == 202:
            return {}
        response.raise_for_status()

        sid = response.headers.get("mcp-session-id")
        if sid:
            self._session_id = sid
            self.session_headers = {**self.base_headers, "mcp-session-id": sid}

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

    async def list_tools(self) -> list[dict]:
        result = await self._send("tools/list")
        return result.get("tools", result)

    async def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        return await self._send("tools/call", params)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


async def call_tool_fn(
    session: MCPSession,
    tool: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    return await session.call_tool(tool, params)


async def list_tools_fn(
    session: MCPSession,
) -> list[dict]:
    return await session.list_tools()


def is_error(result: dict[str, Any]) -> Optional[str]:
    if "error" in result:
        err = result["error"]
        return err.get("message", str(err))
    if result.get("isError"):
        content = result.get("content", [])
        for c in content:
            if c.get("type") == "text":
                txt = c["text"]
                if txt.startswith("Error calling tool"):
                    return txt.split(":", 1)[1].strip() if ":" in txt else txt
                try:
                    data = json.loads(txt)
                except json.JSONDecodeError:
                    return txt
                if isinstance(data, dict):
                    return data.get("error", txt)
    return None


def extract_content(result: dict[str, Any]) -> Any:
    if result.get("isError"):
        return {}
    content = result.get("content", [])
    for c in content:
        if c.get("type") == "text":
            try:
                return json.loads(c["text"])
            except json.JSONDecodeError:
                return c["text"]
    return result.get("_meta", {})


async def run_test(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any] = None,
    prereq: Optional[str] = None,
) -> bool:
    if params is None:
        params = {}
    if prereq and prereq not in created:
        results.append({
            "label": label, "tool": tool, "status": "SKIPPED",
            "reason": f"Missing prerequisite: {prereq}"
        })
        log(f"  SKIP {label}: missing {prereq}")
        return False
    try:
        result = await call_tool_fn(session, tool, params)
        err = is_error(result)
        if err:
            results.append({
                "label": label, "tool": tool, "status": "FAILED",
                "reason": err
            })
            log(f"  FAIL {label}: {err}")
            return False
        data = extract_content(result)
        results.append({
            "label": label, "tool": tool, "status": "PASSED", "data": data
        })
        log(f"  PASS {label}")
        return True
    except Exception as e:
        results.append({
            "label": label, "tool": tool, "status": "FAILED",
            "reason": str(e)
        })
        log(f"  FAIL {label}: {e}")
        return False


async def run_test_with_store(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any] = None,
    store_key: str = None,
    prereq: Optional[str] = None,
) -> bool:
    ok = await run_test(session, label, tool, params, prereq)
    if ok and store_key:
        for r in results:
            if r["label"] == label and r["status"] == "PASSED":
                store[store_key] = r.get("data")
                break
    return ok


def pick_id(key: str) -> Optional[str]:
    entry = store.get(key, {})
    if isinstance(entry, dict):
        return entry.get("id")
    return None


def make_name(base: str) -> str:
    return f"t{rid}-{base}"


async def run_verify_delete(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any] = None,
) -> bool:
    if params is None:
        params = {}
    try:
        result = await call_tool_fn(session, tool, params)
        err = is_error(result)
        if err:
            if "not found" in err.lower():
                results.append({
                    "label": label, "tool": tool, "status": "PASSED",
                    "data": {"verified": "deleted"}
                })
                log(f"  PASS {label} (confirmed deleted)")
                return True
            results.append({
                "label": label, "tool": tool, "status": "FAILED",
                "reason": err
            })
            log(f"  FAIL {label}: {err}")
            return False
        results.append({
            "label": label, "tool": tool, "status": "FAILED",
            "reason": "Record still exists after delete"
        })
        log(f"  FAIL {label}: record still exists")
        return False
    except Exception as e:
        results.append({
            "label": label, "tool": tool, "status": "FAILED",
            "reason": str(e)
        })
        log(f"  FAIL {label}: {e}")
        return False


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
     "update_email", {"type": "sent"},
     "delete_email_by_id"),
    ("Documents", "create_document",
     {"document_name": make_name("Doc"), "filename": "test.txt", "active_date": "2026-06-20", "description": "Test doc"},
     "get_all_documents", "get_document_by_id",
     "update_document", {"revision": "2"},
     "delete_document_by_id"),
    ("Project", "create_project",
     {"name": make_name("Project"), "estimated_start_date": "2026-06-20", "estimated_end_date": "2026-12-31", "status": "Active"},
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
     "update_bug", {"priority": "P2"},
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
     {"name": make_name("KB"), "author": "TestAuthor", "status": "Published", "description": "Test KB article"},
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
    global iteration

    print(f"# Test Report — SuiteCRM MCP Server")
    print(f"\n**Date**: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    print(f"**Server**: {MCP_URL}")
    print(f"**Run ID**: {rid}")
    print()

    async with MCPSession(MCP_URL, MCP_HEADERS) as session:
        # Phase 0: Initialize session and discover tools
        log("\n=== Phase 0: Session Init & Tool Discovery ===")
        tools_list = await list_tools_fn(session)
        tool_names = [t["name"] for t in tools_list]
        print(f"**Discovered**: {len(tool_names)} tools")
        if len(tool_names) != 120:
            log(f"WARNING: Expected 120 tools, found {len(tool_names)}")

        # Phase 1: Read-only tools
        log("\n=== Phase 1: Status & User Tools ===")
        await run_test(session, "A1 check_server_status", "check_server_status")
        await run_test_with_store(session, "A2 get_current_user", "get_current_user", store_key="current_user")

        # Phase 2: List tools (get_all for each module)
        log("\n=== Phase 2: List Tools ===")
        for mod_conf in MODULE_TESTS:
            api_mod = mod_conf[0]
            list_tool_name = mod_conf[3]
            await run_test(session, f"B2 list_{api_mod.lower()}", list_tool_name)

        # Phase 3: Create + Verify + Update + Verify + Delete
        log("\n=== Phase 3: Module CRUD Cycle ===")
        for mod_conf in MODULE_TESTS:
            api_mod, create_tool, create_params, _, get_tool, update_tool, update_params, delete_tool = mod_conf
            mod_key = api_mod.lower()

            ok = await run_test_with_store(
                session, f"C1 create_{mod_key}", create_tool, create_params,
                store_key=f"create_{mod_key}"
            )
            if ok:
                cid = pick_id(f"create_{mod_key}")
                if cid:
                    created[f"create_{mod_key}"] = cid

            cid = created.get(f"create_{mod_key}")
            if cid:
                await run_test_with_store(
                    session, f"C2 get_{mod_key}_by_id", get_tool,
                    {"id": cid}, store_key=f"get_{mod_key}"
                )
                upd_params = dict(update_params)
                upd_params["id"] = cid
                await run_test_with_store(
                    session, f"C3 update_{mod_key}", update_tool, upd_params,
                    store_key=f"update_{mod_key}"
                )
                await run_test(
                    session, f"C4 delete_{mod_key}_by_id", delete_tool, {"id": cid}
                )
                await run_verify_delete(
                    session, f"C5 verify_delete_{mod_key}", get_tool, {"id": cid}
                )
            else:
                results.append({
                    "label": f"C2 get_{mod_key}_by_id", "tool": get_tool,
                    "status": "SKIPPED", "reason": "No ID from create"
                })
                results.append({
                    "label": f"C3 update_{mod_key}", "tool": update_tool,
                    "status": "SKIPPED", "reason": "No ID from create"
                })
                results.append({
                    "label": f"C4 delete_{mod_key}_by_id", "tool": delete_tool,
                    "status": "SKIPPED", "reason": "No ID from create"
                })
                results.append({
                    "label": f"C5 verify_delete_{mod_key}", "tool": get_tool,
                    "status": "SKIPPED", "reason": "No ID from create"
                })

        # Phase 4: Calendar Tools
        log("\n=== Phase 4: Calendar Tools ===")
        await run_test(session, "D1 get_calendar_events", "get_calendar_events",
                       {"start_date": "2026-01-01", "end_date": "2026-12-31"})

        # Phase 5: Relationship Tools
        log("\n=== Phase 5: Relationship Tools ===")
        await run_test_with_store(
            session, "E1 create_rel_account", "create_account",
            {"name": make_name("RelAccount"), "account_type": "Customer"},
            store_key="rel_account"
        )
        rel_account_id = pick_id("rel_account")
        if rel_account_id:
            created["rel_account"] = rel_account_id

        await run_test_with_store(
            session, "E2 create_rel_contact", "create_contact",
            {"first_name": f"Rel{rid}", "last_name": "Contact"},
            store_key="rel_contact"
        )
        rel_contact_id = pick_id("rel_contact")
        if rel_contact_id:
            created["rel_contact"] = rel_contact_id

        if rel_account_id and rel_contact_id:
            await run_test(session, "E3 create_rel", "create_record_relationship", {
                "module": "Accounts", "id": rel_account_id,
                "related_module": "Contacts", "related_id": rel_contact_id,
            })
            await run_test(session, "E4 get_rel", "get_record_relationships", {
                "module": "Accounts", "id": rel_account_id,
                "link_field_name": "contacts"
            })
            await run_test(session, "E5 delete_rel", "delete_record_relationship", {
                "module": "Accounts", "id": rel_account_id,
                "link_field_name": "contacts", "related_id": rel_contact_id
            })

        if rel_account_id:
            await run_test(session, "E6 cleanup_rel_account", "delete_account_by_id",
                          {"id": rel_account_id})
        if rel_contact_id:
            await run_test(session, "E7 cleanup_rel_contact", "delete_contact_by_id",
                          {"id": rel_contact_id})

        # Phase 6: Activity/History
        log("\n=== Phase 6: Activity & History ===")
        call_id = created.get("create_calls")
        if call_id:
            await run_test(session, "F1 activity_history_by_id", "get_activity_history_by_id",
                          {"id": call_id})
        else:
            results.append({
                "label": "F1 activity_history_by_id", "tool": "get_activity_history_by_id",
                "status": "SKIPPED", "reason": "No call ID available"
            })

        note_id = created.get("create_notes")
        if note_id:
            await run_test(session, "F2 activities_related", "get_activities_related_to_record", {
                "module": "Notes", "id": note_id
            })
        else:
            results.append({
                "label": "F2 activities_related", "tool": "get_activities_related_to_record",
                "status": "SKIPPED", "reason": "No note ID"
            })

        acc_id = created.get("create_accounts")
        if acc_id:
            await run_test(session, "G1 history_related", "get_history_related_to_record", {
                "module": "Accounts", "id": acc_id
            })
        else:
            results.append({
                "label": "G1 history_related", "tool": "get_history_related_to_record",
                "status": "SKIPPED", "reason": "No account ID"
            })

        if call_id:
            await run_test(session, "H1 calendar_event_by_id", "get_calendar_event_by_id",
                          {"id": call_id})
        else:
            results.append({
                "label": "H1 calendar_event_by_id", "tool": "get_calendar_event_by_id",
                "status": "SKIPPED", "reason": "No call ID"
            })

    # Generate Report
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")

    print(f"\n## Summary\n")
    print(f"| Status | Count |")
    print(f"|--------|-------|")
    print(f"| PASSED | {passed} |")
    print(f"| FAILED | {failed} |")
    print(f"| SKIPPED | {skipped} |")

    if passed:
        print(f"\n## PASSED ({passed})\n")
        for r in results:
            if r["status"] == "PASSED":
                print(f"- `{r['tool']}` — {r['label']}")

    if failed:
        print(f"\n## FAILED ({failed})\n")
        for r in results:
            if r["status"] == "FAILED":
                print(f"### {r['label']}")
                print(f"- **Error**: {r['reason']}")
                print()

    if skipped:
        print(f"\n## SKIPPED ({skipped})\n")
        for r in results:
            if r["status"] == "SKIPPED":
                print(f"- `{r['tool']}` — {r['reason']}")

    print(f"\n## Iteration History\n")
    print(f"| Iteration | Passed | Failed | Skipped | Fixes Applied |")
    print(f"|-----------|--------|--------|---------|---------------|")
    print(f"| {iteration} | {passed} | {failed} | {skipped} | Initial run |")

    total = len(results)
    print(f"\n---\n**Total tests:** {total} | **PASSED:** {passed} | **FAILED:** {failed} | **SKIPPED:** {skipped}")

    if failed == 0 and skipped == 0:
        print(f"\n**ALL TESTS PASS**")
    else:
        print(f"\n**TESTS FAILING** — see above for details")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

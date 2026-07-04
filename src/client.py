import datetime as dt
import json as json_mod
import os
import re
import sys
from typing import Any, Optional

import httpx


def _normalize_datetime(value: str) -> str:
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$', value):
        parsed = dt.datetime.fromisoformat(value)
        parsed = parsed.astimezone(dt.timezone.utc)
        return parsed.strftime('%Y-%m-%d %H:%M:%S')
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
        raise ValueError(
            f"Invalid datetime: {value}. Timezone offset is required. "
            "Must use format: 2026-06-22T15:00:00-04:00"
        )
    return value


# NOTE: The base URL already includes /Api/V8, so all paths
# here must be RELATIVE to the V8 route group (no /V8 prefix).

COMMON_FIELDS: dict[str, str] = {
    "Accounts": "name,description,account_type,industry,phone_office,billing_address_city",
    "Contacts": "name,description,first_name,last_name,title,phone_work,email1",
    "Leads": "name,description,first_name,last_name,title,status,phone_work,email1",
    "Opportunities": "name,description,amount,date_closed,sales_stage,probability",
    "Cases": "name,description,case_number,status,priority,type",
    "Notes": "name,description,filename,parent_name",
    "Calls": "name,description,date_start,status,parent_name",
    "Meetings": "name,description,date_start,status,location,parent_name",
    "Tasks": "name,description,status,date_due,priority,parent_name",
    "Emails": "name,description,type,status,parent_name",
    "Documents": "name,description,document_name,status,latest_revision_name",
    "Project": "name,description,estimated_start_date,estimated_end_date,status",
    "Prospects": "name,description,first_name,last_name,title,phone_work,email1",
    "Campaigns": "name,description,campaign_type,status,start_date,end_date",
    "Bugs": "name,description,bug_number,status,priority",
    "AOS_Products": "name,description,part_number,cost,price",
    "AOS_Contracts": "name,description,status,contract_account,total_contract_value",
    "AOS_Invoices": "name,description,number,status,total_amount,due_date",
    "AOS_Quotes": "name,description,number,stage,total_amount,expiration",
    "AOK_KnowledgeBase": "name,description,author,status,revision",
    "FP_events": "name,description,date_start,date_end",
    "AOR_Reports": "name,description,report_module",
}

NO_ASSIGNED_USER: set[str] = {
    "Documents", "AOS_Products", "AOS_Contracts", "AOS_Invoices",
    "AOS_Quotes", "AOK_KnowledgeBase", "FP_events", "AOR_Reports",
}

LINK_TO_MODULE: dict[str, str] = {
    "accounts": "Accounts", "contacts": "Contacts", "leads": "Leads",
    "opportunities": "Opportunities", "cases": "Cases", "notes": "Notes",
    "calls": "Calls", "meetings": "Meetings", "tasks": "Tasks",
    "emails": "Emails", "documents": "Documents", "project": "Project",
    "prospects": "Prospects", "campaigns": "Campaigns", "bugs": "Bugs",
    "aos_products": "AOS_Products", "aos_contracts": "AOS_Contracts",
    "aos_invoices": "AOS_Invoices", "aos_quotes": "AOS_Quotes",
    "aok_knowledgebase": "AOK_KnowledgeBase", "fp_events": "FP_events",
    "aor_reports": "AOR_Reports",
}


class SuiteCRMClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("SUITECRM_BASE_URL", "")).rstrip("/")
        if not self.base_url:
            raise ValueError(
                "SuiteCRM URL required. Set SUITECRM_BASE_URL env var "
                "or pass base_url."
            )

    def _get_headers(self, token: Optional[str] = None) -> dict[str, str]:
        headers = {
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def request(
        self, method: str, path: str, token: Optional[str] = None, **kwargs: Any
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._get_headers(token)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            if response.status_code >= 400:
                detail = response.text[:500] if response.text else "no body"
                raise httpx.HTTPStatusError(
                    f"{response.status_code} {response.reason_phrase}: {detail}",
                    request=response.request,
                    response=response,
                )
            if response.status_code == 204:
                return {}
            try:
                return response.json()
            except json_mod.JSONDecodeError:
                # SuiteCRM may append PHP warning HTML after JSON
                text = response.text
                start = text.find("{")
                depth = 0
                for i in range(start, len(text)):
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                        if depth == 0:
                            return json_mod.loads(text[start : i + 1])
                raise

    async def get(self, path: str, token: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("GET", path, token, **kwargs)

    async def post(self, path: str, token: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("POST", path, token, **kwargs)

    async def patch(self, path: str, token: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("PATCH", path, token, **kwargs)

    async def put(self, path: str, token: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("PUT", path, token, **kwargs)

    async def delete(self, path: str, token: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("DELETE", path, token, **kwargs)

    def _flatten_single(self, data: dict, include_relationships: bool = False) -> dict[str, Any]:
        if "errors" in data:
            err = data["errors"]
            return {"error": err.get("detail", str(err))}
        d = data.get("data", {})
        result: dict[str, Any] = {"id": d.get("id"), "type": d.get("type")}
        result.update(d.get("attributes", {}))
        if include_relationships:
            rels = d.get("relationships")
            if rels:
                result["relationships"] = rels
        return result

    def _flatten_list(self, data: dict, include_relationships: bool = False) -> list[dict[str, Any]]:
        items = data.get("data", [])
        return [self._flatten_single({"data": item}, include_relationships) for item in items]

    async def get_current_user(self, token: Optional[str], include_all_fields: bool = False) -> dict[str, Any]:
        data = await self.get("/current-user", token)
        return self._flatten_single(data, include_all_fields)

    async def get_all_records(
        self,
        module: str,
        token: Optional[str],
        include_all_fields: bool = False,
        filters: Optional[dict[str, str]] = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if not include_all_fields and module in COMMON_FIELDS:
            params[f"fields[{module}]"] = COMMON_FIELDS[module]
        if filters:
            params.update(filters)
        data = await self.get(f"/module/{module}", token, params=params or None)
        return self._flatten_list(data, include_all_fields)

    async def get_record_by_id(
        self,
        module: str,
        record_id: str,
        token: Optional[str],
        include_all_fields: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, str] = {}
        if not include_all_fields and module in COMMON_FIELDS:
            params[f"fields[{module}]"] = COMMON_FIELDS[module]
        data = await self.get(f"/module/{module}/{record_id}", token, params=params or None)
        result = self._flatten_single(data, include_all_fields)
        if "error" in result:
            raise RuntimeError(result["error"])
        return result

    async def create_record(
        self,
        module: str,
        attributes: dict[str, Any],
        token: Optional[str],
        inject_assigned: bool = True,
    ) -> dict[str, Any]:
        user_id = None
        if inject_assigned and module not in NO_ASSIGNED_USER:
            user = await self.get_current_user(token)
            attributes["assigned_user_id"] = user.get("id")
            user_id = user.get("id")
        attributes = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in attributes.items()}
        payload = {"data": {"type": module, "attributes": attributes}}
        data = await self.post("/module", token, json=payload)
        result = self._flatten_single(data)
        mid = result.get("id")
        if user_id and module in ("Meetings", "Calls") and mid:
            await self.create_record_relationship(
                token, module, mid, "Users", user_id, "users"
            )
        return result

    async def update_record(
        self,
        module: str,
        record_id: str,
        attributes: dict[str, Any],
        token: Optional[str],
    ) -> dict[str, Any]:
        attributes = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in attributes.items()}
        payload = {"data": {"type": module, "id": record_id, "attributes": attributes}}
        data = await self.patch("/module", token, json=payload)
        return self._flatten_single(data)

    async def delete_record(
        self, module: str, record_id: str, token: Optional[str]
    ) -> dict[str, Any]:
        data = await self.delete(f"/module/{module}/{record_id}", token)
        if not data:
            return {"message": "Deleted"}
        meta = data.get("meta", {})
        return {"message": meta.get("message", "Deleted")}

    async def get_calendar_events(
        self,
        token: Optional[str],
        start_date: str,
        end_date: str,
        user_id: str = "",
        include_all_fields: bool = False,
    ) -> list[dict[str, Any]]:
        modules_to_check = ["Calls", "Meetings", "Tasks"]
        results: list[dict[str, Any]] = []
        norm_start = _normalize_datetime(start_date)
        norm_end = _normalize_datetime(end_date)
        for mod in modules_to_check:
            filters = {"filter[date_start][gte]": norm_start, "filter[date_start][lte]": norm_end}
            if user_id:
                filters["filter[assigned_user_id][eq]"] = user_id
            records = await self.get_all_records(mod, token, include_all_fields, filters)
            for r in records:
                r["_module"] = mod
            results.extend(records)
        results.sort(key=lambda x: x.get("date_start", ""))
        return results

    async def get_calendar_event_by_id(
        self,
        token: Optional[str],
        event_id: str,
        include_all_fields: bool = False,
    ) -> Optional[dict[str, Any]]:
        modules_to_check = ["Calls", "Meetings", "Tasks"]
        for mod in modules_to_check:
            try:
                return await self.get_record_by_id(mod, event_id, token, include_all_fields)
            except Exception:
                continue
        return None

    async def get_activities_related_to_record(
        self,
        token: Optional[str],
        module: str,
        record_id: str,
        activity_types: Optional[list[str]] = None,
        include_all_fields: bool = False,
    ) -> list[dict[str, Any]]:
        link_map = {
            "calls": "Calls",
            "meetings": "Meetings",
            "tasks": "Tasks",
            "notes": "Notes",
            "emails": "Emails",
        }
        if activity_types:
            links = [t for t in activity_types if t in link_map]
        else:
            links = list(link_map.keys())
        results: list[dict[str, Any]] = []
        for link in links:
            try:
                data = await self.get(
                    f"/module/{module}/{record_id}/relationships/{link}", token
                )
                items = self._flatten_list(data, include_all_fields)
                rel_module = link_map[link]
                if not include_all_fields and rel_module in COMMON_FIELDS:
                    keep = set(COMMON_FIELDS[rel_module].split(",")) | {"_link"}
                    items = [{k: v for k, v in it.items() if k in keep} for it in items]
                for item in items:
                    item["_link"] = link
                results.extend(items)
            except Exception:
                continue
        return results

    async def get_history_related_to_record(
        self,
        token: Optional[str],
        module: str,
        record_id: str,
        include_all_fields: bool = False,
    ) -> list[dict[str, Any]]:
        all_activities = await self.get_activities_related_to_record(
            token, module, record_id, None, include_all_fields
        )
        completed_statuses = {"Held", "Completed", "Closed"}
        return [
            a for a in all_activities
            if a.get("status") in completed_statuses
        ]

    async def get_activity_history_by_id(
        self,
        token: Optional[str],
        activity_id: str,
        include_all_fields: bool = False,
    ) -> Optional[dict[str, Any]]:
        modules_to_check = ["Calls", "Meetings", "Tasks", "Notes", "Emails"]
        for mod in modules_to_check:
            try:
                return await self.get_record_by_id(mod, activity_id, token, include_all_fields)
            except Exception:
                continue
        return None

    async def get_record_relationships(
        self,
        token: Optional[str],
        module: str,
        record_id: str,
        link_field_name: str,
        include_all_fields: bool = False,
    ) -> list[dict[str, Any]]:
        data = await self.get(
            f"/module/{module}/{record_id}/relationships/{link_field_name}", token
        )
        items = self._flatten_list(data, include_all_fields)
        if not include_all_fields:
            rel_module = LINK_TO_MODULE.get(link_field_name.lower())
            if rel_module and rel_module in COMMON_FIELDS:
                keep = set(COMMON_FIELDS[rel_module].split(","))
                items = [{k: v for k, v in it.items() if k in keep} for it in items]
        return items

    async def create_record_relationship(
        self,
        token: Optional[str],
        module: str,
        record_id: str,
        related_module: str,
        related_id: str,
        link_field_name: str = "",
    ) -> dict[str, Any]:
        if not link_field_name:
            name_to_link = {
                "Accounts": "accounts", "Contacts": "contacts", "Leads": "leads",
                "Opportunities": "opportunities", "Cases": "cases", "Notes": "notes",
                "Calls": "calls", "Meetings": "meetings", "Tasks": "tasks",
                "Emails": "emails", "Documents": "documents", "Project": "project",
                "Prospects": "prospects", "Campaigns": "campaigns", "Bugs": "bugs",
                "AOS_Products": "aos_products", "AOS_Contracts": "aos_contracts",
                "AOS_Invoices": "aos_invoices", "AOS_Quotes": "aos_quotes",
                "AOK_KnowledgeBase": "aok_knowledgebase", "FP_events": "fp_events",
                "AOR_Reports": "aor_reports",
            }
            link_field_name = name_to_link.get(related_module, related_module.lower())
        payload = {
            "data": {
                "type": related_module,
                "id": related_id,
            }
        }
        data = await self.post(
            f"/module/{module}/{record_id}/relationships/{link_field_name}",
            token,
            json=payload,
        )
        return {"message": "Relationship created", "link": link_field_name}

    async def delete_record_relationship(
        self,
        token: Optional[str],
        module: str,
        record_id: str,
        link_field_name: str,
        related_id: str,
    ) -> dict[str, Any]:
        path = f"/module/{module}/{record_id}/relationships/{link_field_name}/{related_id}"
        data = await self.delete(path, token)
        if not data:
            return {"message": "Relationship deleted"}
        meta = data.get("meta", {})
        return {"message": meta.get("message", "Relationship deleted")}

import os
import sys
from contextvars import ContextVar
from typing import Any, Literal, Optional

import httpx as httpx_mod
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from toon_mcp import json_to_toon

from.client import SuiteCRMClient

_current_user_token: ContextVar[Optional[str]] = ContextVar("current_user_token", default=None)

ALLOW_ALL_AGGREGATE = os.getenv("ALLOW_ALL_AGGREGATE", "false").lower() in ("true", "1", "yes")
IS_STATEFUL = os.getenv("IS_STATEFUL", "false").lower() in ("true", "1", "yes")


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                token_val = auth_header[7:]
                _current_user_token.set(token_val)
        await self.app(scope, receive, send)


mcp = FastMCP("SuiteCRM-mcp-server")

_client: Optional[SuiteCRMClient] = None


def get_client() -> SuiteCRMClient:
    global _client
    if _client is None:
        _client = SuiteCRMClient()
    return _client


def get_user_token() -> Optional[str]:
    return _current_user_token.get()


# =============================================================================
# Pydantic Contract Models (22 Create + 22 Update)
# =============================================================================

class CreateAccountParam(BaseModel):
    name: str
    account_type: str
    description: str = ""
    industry: str = ""
    phone_office: str = ""
    website: str = ""
    billing_address_street: str = ""
    billing_address_city: str = ""
    billing_address_state: str = ""
    billing_address_postalcode: str = ""
    billing_address_country: str = ""


class UpdateAccountParam(BaseModel):
    name: Optional[str] = None
    account_type: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    phone_office: Optional[str] = None
    website: Optional[str] = None
    billing_address_street: Optional[str] = None
    billing_address_city: Optional[str] = None
    billing_address_state: Optional[str] = None
    billing_address_postalcode: Optional[str] = None
    billing_address_country: Optional[str] = None


class CreateContactParam(BaseModel):
    first_name: str
    last_name: str
    description: str = ""
    title: str = ""
    department: str = ""
    phone_work: str = ""
    phone_mobile: str = ""
    phone_home: str = ""
    phone_fax: str = ""
    email1: str = ""
    primary_address_street: str = ""
    primary_address_city: str = ""
    primary_address_state: str = ""
    primary_address_postalcode: str = ""
    primary_address_country: str = ""
    account_id: str = ""
    reports_to_id: str = ""


class UpdateContactParam(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    phone_work: Optional[str] = None
    phone_mobile: Optional[str] = None
    phone_home: Optional[str] = None
    phone_fax: Optional[str] = None
    email1: Optional[str] = None
    primary_address_street: Optional[str] = None
    primary_address_city: Optional[str] = None
    primary_address_state: Optional[str] = None
    primary_address_postalcode: Optional[str] = None
    primary_address_country: Optional[str] = None
    account_id: Optional[str] = None
    reports_to_id: Optional[str] = None


class CreateLeadParam(BaseModel):
    first_name: str
    last_name: str
    status: str
    description: str = ""
    title: str = ""
    department: str = ""
    phone_work: str = ""
    phone_mobile: str = ""
    phone_fax: str = ""
    email1: str = ""
    primary_address_street: str = ""
    primary_address_city: str = ""
    primary_address_state: str = ""
    primary_address_postalcode: str = ""
    primary_address_country: str = ""
    account_name: str = ""
    lead_source: str = ""


class UpdateLeadParam(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    phone_work: Optional[str] = None
    phone_mobile: Optional[str] = None
    phone_fax: Optional[str] = None
    email1: Optional[str] = None
    primary_address_street: Optional[str] = None
    primary_address_city: Optional[str] = None
    primary_address_state: Optional[str] = None
    primary_address_postalcode: Optional[str] = None
    primary_address_country: Optional[str] = None
    account_name: Optional[str] = None
    lead_source: Optional[str] = None


class CreateOpportunityParam(BaseModel):
    name: str
    amount: float
    date_closed: str
    sales_stage: str
    description: str = ""
    lead_source: str = ""
    account_id: str = ""
    probability: str = ""
    campaign_id: str = ""


class UpdateOpportunityParam(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    date_closed: Optional[str] = None
    sales_stage: Optional[str] = None
    description: Optional[str] = None
    lead_source: Optional[str] = None
    account_id: Optional[str] = None
    probability: Optional[str] = None
    campaign_id: Optional[str] = None


class CreateCaseParam(BaseModel):
    name: str
    description: str
    status: str = "New"
    priority: str = "P3"
    type: str = ""
    account_id: str = ""


class UpdateCaseParam(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    type: Optional[str] = None
    account_id: Optional[str] = None


class CreateNoteParam(BaseModel):
    name: str
    description: str
    portal_flag: bool = False
    parent_type: str = ""
    parent_id: str = ""


class UpdateNoteParam(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    filename: Optional[str] = None
    portal_flag: Optional[bool] = None
    parent_type: Optional[str] = None
    parent_id: Optional[str] = None


class CreateCallParam(BaseModel):
    name: str
    date_start: str
    duration_hours: int
    status: str
    description: str = ""
    duration_minutes: int = 0
    date_end: str = ""
    parent_type: str = ""
    parent_id: str = ""
    direction: str = ""
    reminder_time: int = -1


class UpdateCallParam(BaseModel):
    name: Optional[str] = None
    date_start: Optional[str] = None
    duration_hours: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    date_end: Optional[str] = None
    parent_type: Optional[str] = None
    parent_id: Optional[str] = None
    direction: Optional[str] = None
    reminder_time: Optional[int] = None


class CreateMeetingParam(BaseModel):
    name: str
    date_start: str
    duration_hours: int
    description: str = ""
    duration_minutes: int = 0
    date_end: str = ""
    status: str = "Planned"
    parent_type: str = ""
    parent_id: str = ""
    reminder_time: int = -1


class UpdateMeetingParam(BaseModel):
    name: Optional[str] = None
    date_start: Optional[str] = None
    duration_hours: Optional[int] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    date_end: Optional[str] = None
    status: Optional[str] = None
    parent_type: Optional[str] = None
    parent_id: Optional[str] = None
    reminder_time: Optional[int] = None


class CreateTaskParam(BaseModel):
    name: str
    status: str
    date_due: str
    description: str = ""
    date_start: str = ""
    parent_type: str = ""
    parent_id: str = ""
    priority: str = "Medium"


class UpdateTaskParam(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    date_due: Optional[str] = None
    description: Optional[str] = None
    date_start: Optional[str] = None
    parent_type: Optional[str] = None
    parent_id: Optional[str] = None
    priority: Optional[str] = None


class CreateEmailParam(BaseModel):
    name: str
    description: str
    parent_type: str = ""
    parent_id: str = ""
    type: str = "draft"
    status: str = "draft"


class UpdateEmailParam(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    date_sent: Optional[str] = None
    parent_type: Optional[str] = None
    parent_id: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None


class CreateDocumentParam(BaseModel):
    document_name: str
    filename: str
    active_date: str
    description: str
    category_id: str = ""
    revision: str = "1"


class UpdateDocumentParam(BaseModel):
    document_name: Optional[str] = None
    filename: Optional[str] = None
    active_date: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    subcategory: Optional[str] = None
    revision: Optional[str] = None


class CreateProjectParam(BaseModel):
    name: str
    estimated_start_date: str
    estimated_end_date: str
    status: str
    description: str = ""
    priority: str = ""
    total_estimated_effort: int = 0
    total_actual_effort: int = 0


class UpdateProjectParam(BaseModel):
    name: Optional[str] = None
    estimated_start_date: Optional[str] = None
    estimated_end_date: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    total_estimated_effort: Optional[int] = None
    total_actual_effort: Optional[int] = None


class CreateProspectParam(BaseModel):
    first_name: str
    last_name: str
    description: str = ""
    title: str = ""
    department: str = ""
    phone_work: str = ""
    phone_mobile: str = ""
    email1: str = ""
    primary_address_street: str = ""
    primary_address_city: str = ""
    primary_address_state: str = ""
    primary_address_postalcode: str = ""
    primary_address_country: str = ""


class UpdateProspectParam(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    phone_work: Optional[str] = None
    phone_mobile: Optional[str] = None
    email1: Optional[str] = None
    primary_address_street: Optional[str] = None
    primary_address_city: Optional[str] = None
    primary_address_state: Optional[str] = None
    primary_address_postalcode: Optional[str] = None
    primary_address_country: Optional[str] = None


class CreateCampaignParam(BaseModel):
    name: str
    campaign_type: str
    status: str
    start_date: str
    end_date: str
    description: str = ""
    budget: float = 0.0
    expected_cost: float = 0.0
    actual_cost: float = 0.0
    expected_revenue: float = 0.0
    objective: str = ""
    content: str = ""


class UpdateCampaignParam(BaseModel):
    name: Optional[str] = None
    campaign_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    expected_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    expected_revenue: Optional[float] = None
    objective: Optional[str] = None
    content: Optional[str] = None


class CreateBugParam(BaseModel):
    name: str
    description: str
    bug_number: str = ""
    status: str = "New"
    priority: str = "P3"
    type: str = ""
    resolution: str = ""
    found_in_release: str = ""
    fixed_in_release: str = ""


class UpdateBugParam(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bug_number: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    type: Optional[str] = None
    severity: Optional[str] = None
    resolution: Optional[str] = None
    found_in_release: Optional[str] = None
    fixed_in_release: Optional[str] = None


class CreateProductParam(BaseModel):
    name: str
    cost: float
    price: float
    type: str
    description: str = ""
    part_number: str = ""
    category: str = ""
    url: str = ""
    contact_id: str = ""
    currency_id: str = ""


class UpdateProductParam(BaseModel):
    name: Optional[str] = None
    cost: Optional[float] = None
    price: Optional[float] = None
    type: Optional[str] = None
    description: Optional[str] = None
    part_number: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    contact_id: Optional[str] = None
    pricing_formula: Optional[str] = None
    currency_id: Optional[str] = None


class CreateContractParam(BaseModel):
    name: str
    status: str
    contract_account: str
    total_contract_value: float
    description: str = ""
    start_date: str = ""
    end_date: str = ""
    currency_id: str = ""


class UpdateContractParam(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    contract_account: Optional[str] = None
    total_contract_value: Optional[float] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    currency_id: Optional[str] = None


class CreateInvoiceParam(BaseModel):
    name: str
    number: str
    status: str
    total_amount: float
    due_date: str
    description: str = ""
    billing_account: str = ""
    billing_contact: str = ""
    currency_id: str = ""
    quote_number: str = ""


class UpdateInvoiceParam(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None
    status: Optional[str] = None
    total_amount: Optional[float] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    billing_account: Optional[str] = None
    billing_contact: Optional[str] = None
    currency_id: Optional[str] = None
    quote_number: Optional[str] = None


class CreateQuoteParam(BaseModel):
    name: str
    stage: str
    total_amount: float
    description: str = ""
    number: str = ""
    currency_id: str = ""
    billing_account: str = ""


class UpdateQuoteParam(BaseModel):
    name: Optional[str] = None
    stage: Optional[str] = None
    total_amount: Optional[float] = None
    valid_until: Optional[str] = None
    description: Optional[str] = None
    number: Optional[str] = None
    currency_id: Optional[str] = None
    billing_account: Optional[str] = None


class CreateKnowledgeBaseParam(BaseModel):
    name: str
    author: str
    status: str
    description: str
    revision: str = ""
    additional_info: str = ""


class UpdateKnowledgeBaseParam(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    revision: Optional[str] = None
    additional_info: Optional[str] = None


class CreateEventParam(BaseModel):
    name: str
    date_start: str
    duration_hours: int
    description: str
    duration_minutes: int = 0
    date_end: str = ""
    location: str = ""
    budget: float = 0.0


class UpdateEventParam(BaseModel):
    name: Optional[str] = None
    date_start: Optional[str] = None
    duration_hours: Optional[int] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    date_end: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[float] = None
    expected_revenue: Optional[float] = None


class CreateReportParam(BaseModel):
    name: str
    report_module: str
    description: str = ""
    graphs_per_row: int = 2


class UpdateReportParam(BaseModel):
    name: Optional[str] = None
    report_module: Optional[str] = None
    description: Optional[str] = None
    graphs_per_row: Optional[int] = None


# =============================================================================
# Internal helpers
# =============================================================================

async def _list_tool(module: str, include_all_fields: bool) -> dict[str, Any]:
    data = await get_client().get_all_records(
        module, get_user_token(), include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False
    )
    return {"items": json_to_toon(data)}


async def _get_tool(module: str, record_id: str, include_all_fields: bool) -> dict[str, Any]:
    return await get_client().get_record_by_id(
        module, record_id, get_user_token(), include_all_fields=include_all_fields
    )


async def _delete_tool(module: str, record_id: str) -> dict[str, Any]:
    return await get_client().delete_record(module, record_id, get_user_token())


# =============================================================================
# Accounts (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'basic', 'suitecrm'})
async def get_all_accounts(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all account records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Accounts", include_all_fields)


@mcp.tool(tags={'read', 'basic', 'suitecrm'})
async def get_account_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single account record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Accounts", id, include_all_fields)


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def create_account(
    name: str,
    account_type: Literal["", "Analyst", "Competitor", "Customer", "Integrator", "Investor", "Partner", "Press", "Prospect", "Reseller", "Other"] = "",
    description: str = "",
    industry: str = "",
    phone_office: str = "",
    website: str = "",
    billing_address_street: str = "",
    billing_address_city: str = "",
    billing_address_state: str = "",
    billing_address_postalcode: str = "",
    billing_address_country: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new account record.

    Args:
        name: The account name.
        account_type: Valid values: Analyst, Competitor, Customer, Integrator, Investor, Partner, Press, Prospect, Reseller, Other (or empty for none).
        description: A description of the account.
        industry: The industry the account belongs to.
        phone_office: The office phone number.
        website: The account's website URL.
        billing_address_street: The billing address street.
        billing_address_city: The billing address city.
        billing_address_state: The billing address state.
        billing_address_postalcode: The billing address postal code.
        billing_address_country: The billing address country.
    """
    params = CreateAccountParam(
        name=name, account_type=account_type, description=description,
        industry=industry, phone_office=phone_office, website=website,
        billing_address_street=billing_address_street,
        billing_address_city=billing_address_city,
        billing_address_state=billing_address_state,
        billing_address_postalcode=billing_address_postalcode,
        billing_address_country=billing_address_country,
    )
    return await get_client().create_record(
        "Accounts", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def update_account(
    id: str,
    name: str = None,
    account_type: Optional[Literal["", "Analyst", "Competitor", "Customer", "Integrator", "Investor", "Partner", "Press", "Prospect", "Reseller", "Other"]] = None,
    description: str = None,
    industry: str = None,
    phone_office: str = None,
    website: str = None,
    billing_address_street: str = None,
    billing_address_city: str = None,
    billing_address_state: str = None,
    billing_address_postalcode: str = None,
    billing_address_country: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing account record.

    Args:
        id: The record ID to update.
        name: The account name.
        account_type: Valid values: Analyst, Competitor, Customer, Integrator, Investor, Partner, Press, Prospect, Reseller, Other (or empty for none).
        description: A description of the account.
        industry: The industry the account belongs to.
        phone_office: The office phone number.
        website: The account's website URL.
        billing_address_street: The billing address street.
        billing_address_city: The billing address city.
        billing_address_state: The billing address state.
        billing_address_postalcode: The billing address postal code.
        billing_address_country: The billing address country.
    """
    params = UpdateAccountParam(
        name=name, account_type=account_type, description=description,
        industry=industry, phone_office=phone_office, website=website,
        billing_address_street=billing_address_street,
        billing_address_city=billing_address_city,
        billing_address_state=billing_address_state,
        billing_address_postalcode=billing_address_postalcode,
        billing_address_country=billing_address_country,
    )
    return await get_client().update_record(
        "Accounts", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def delete_account_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete an account record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Accounts", id)


# =============================================================================
# Contacts (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'basic', 'suitecrm'})
async def get_all_contacts(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all contact records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Contacts", include_all_fields)


@mcp.tool(tags={'read', 'basic', 'suitecrm'})
async def get_contact_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single contact record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Contacts", id, include_all_fields)


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def create_contact(
    first_name: str,
    last_name: str,
    description: str = "",
    title: str = "",
    department: str = "",
    phone_work: str = "",
    phone_mobile: str = "",
    phone_home: str = "",
    phone_fax: str = "",
    email1: str = "",
    primary_address_street: str = "",
    primary_address_city: str = "",
    primary_address_state: str = "",
    primary_address_postalcode: str = "",
    primary_address_country: str = "",
    account_id: str = "",
    reports_to_id: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new contact record.

    Args:
        first_name: The contact's first name.
        last_name: The contact's last name.
        description: A description of the contact.
        title: The contact's job title.
        department: The department the contact works in.
        phone_work: The work phone number.
        phone_mobile: The mobile phone number.
        phone_home: The home phone number.
        phone_fax: The fax number.
        email1: The primary email address.
        primary_address_street: The primary address street.
        primary_address_city: The primary address city.
        primary_address_state: The primary address state.
        primary_address_postalcode: The primary address postal code.
        primary_address_country: The primary address country.
        account_id: The ID of the related account.
        reports_to_id: The ID of the contact this contact reports to.
    """
    params = CreateContactParam(
        first_name=first_name, last_name=last_name, description=description,
        title=title, department=department, phone_work=phone_work,
        phone_mobile=phone_mobile, phone_home=phone_home, phone_fax=phone_fax,
        email1=email1, primary_address_street=primary_address_street,
        primary_address_city=primary_address_city,
        primary_address_state=primary_address_state,
        primary_address_postalcode=primary_address_postalcode,
        primary_address_country=primary_address_country,
        account_id=account_id, reports_to_id=reports_to_id,
    )
    return await get_client().create_record(
        "Contacts", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def update_contact(
    id: str,
    first_name: str = None,
    last_name: str = None,
    description: str = None,
    title: str = None,
    department: str = None,
    phone_work: str = None,
    phone_mobile: str = None,
    phone_home: str = None,
    phone_fax: str = None,
    email1: str = None,
    primary_address_street: str = None,
    primary_address_city: str = None,
    primary_address_state: str = None,
    primary_address_postalcode: str = None,
    primary_address_country: str = None,
    account_id: str = None,
    reports_to_id: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing contact record.

    Args:
        id: The record ID to update.
        first_name: The contact's first name.
        last_name: The contact's last name.
        description: A description of the contact.
        title: The contact's job title.
        department: The department the contact works in.
        phone_work: The work phone number.
        phone_mobile: The mobile phone number.
        phone_home: The home phone number.
        phone_fax: The fax number.
        email1: The primary email address.
        primary_address_street: The primary address street.
        primary_address_city: The primary address city.
        primary_address_state: The primary address state.
        primary_address_postalcode: The primary address postal code.
        primary_address_country: The primary address country.
        account_id: The ID of the related account.
        reports_to_id: The ID of the contact this contact reports to.
    """
    params = UpdateContactParam(
        first_name=first_name, last_name=last_name, description=description,
        title=title, department=department, phone_work=phone_work,
        phone_mobile=phone_mobile, phone_home=phone_home, phone_fax=phone_fax,
        email1=email1, primary_address_street=primary_address_street,
        primary_address_city=primary_address_city,
        primary_address_state=primary_address_state,
        primary_address_postalcode=primary_address_postalcode,
        primary_address_country=primary_address_country,
        account_id=account_id, reports_to_id=reports_to_id,
    )
    return await get_client().update_record(
        "Contacts", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def delete_contact_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a contact record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Contacts", id)


# =============================================================================
# Leads (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'basic', 'suitecrm'})
async def get_all_leads(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all lead records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Leads", include_all_fields)


@mcp.tool(tags={'read', 'basic', 'suitecrm'})
async def get_lead_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single lead record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Leads", id, include_all_fields)


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def create_lead(
    first_name: str,
    last_name: str,
    status: Literal["New", "Assigned", "In Process", "Converted", "Recycled", "Dead"],
    description: str = "",
    title: str = "",
    department: str = "",
    phone_work: str = "",
    phone_mobile: str = "",
    phone_fax: str = "",
    email1: str = "",
    primary_address_street: str = "",
    primary_address_city: str = "",
    primary_address_state: str = "",
    primary_address_postalcode: str = "",
    primary_address_country: str = "",
    account_name: str = "",
    lead_source: Literal["", "Cold Call", "Existing Customer", "Self Generated", "Employee", "Partner", "Public Relations", "Direct Mail", "Conference", "Trade Show", "Web Site", "Word of mouth", "Email", "Campaign", "Other"] = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new lead record.

    Args:
        first_name: The lead's first name.
        last_name: The lead's last name.
        status: Valid values: New, Assigned, In Process, Converted, Recycled, Dead.
        description: A description of the lead.
        title: The lead's job title.
        department: The department the lead works in.
        phone_work: The work phone number.
        phone_mobile: The mobile phone number.
        phone_fax: The fax number.
        email1: The primary email address.
        primary_address_street: The primary address street.
        primary_address_city: The primary address city.
        primary_address_state: The primary address state.
        primary_address_postalcode: The primary address postal code.
        primary_address_country: The primary address country.
        account_name: The name of the related account.
        lead_source: Valid values: Cold Call, Existing Customer, Self Generated, Employee, Partner, Public Relations, Direct Mail, Conference, Trade Show, Web Site, Word of mouth, Email, Campaign, Other (or empty for none).
    """
    params = CreateLeadParam(
        first_name=first_name, last_name=last_name, status=status,
        description=description, title=title, department=department,
        phone_work=phone_work, phone_mobile=phone_mobile, phone_fax=phone_fax,
        email1=email1, primary_address_street=primary_address_street,
        primary_address_city=primary_address_city,
        primary_address_state=primary_address_state,
        primary_address_postalcode=primary_address_postalcode,
        primary_address_country=primary_address_country,
        account_name=account_name, lead_source=lead_source,
    )
    return await get_client().create_record(
        "Leads", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def update_lead(
    id: str,
    first_name: str = None,
    last_name: str = None,
    status: Optional[Literal["New", "Assigned", "In Process", "Converted", "Recycled", "Dead"]] = None,
    description: str = None,
    title: str = None,
    department: str = None,
    phone_work: str = None,
    phone_mobile: str = None,
    phone_fax: str = None,
    email1: str = None,
    primary_address_street: str = None,
    primary_address_city: str = None,
    primary_address_state: str = None,
    primary_address_postalcode: str = None,
    primary_address_country: str = None,
    account_name: str = None,
    lead_source: Optional[Literal["", "Cold Call", "Existing Customer", "Self Generated", "Employee", "Partner", "Public Relations", "Direct Mail", "Conference", "Trade Show", "Web Site", "Word of mouth", "Email", "Campaign", "Other"]] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing lead record.

    Args:
        id: The record ID to update.
        first_name: The lead's first name.
        last_name: The lead's last name.
        status: Valid values: New, Assigned, In Process, Converted, Recycled, Dead.
        description: A description of the lead.
        title: The lead's job title.
        department: The department the lead works in.
        phone_work: The work phone number.
        phone_mobile: The mobile phone number.
        phone_fax: The fax number.
        email1: The primary email address.
        primary_address_street: The primary address street.
        primary_address_city: The primary address city.
        primary_address_state: The primary address state.
        primary_address_postalcode: The primary address postal code.
        primary_address_country: The primary address country.
        account_name: The name of the related account.
        lead_source: Valid values: Cold Call, Existing Customer, Self Generated, Employee, Partner, Public Relations, Direct Mail, Conference, Trade Show, Web Site, Word of mouth, Email, Campaign, Other (or empty for none).
    """
    params = UpdateLeadParam(
        first_name=first_name, last_name=last_name, status=status,
        description=description, title=title, department=department,
        phone_work=phone_work, phone_mobile=phone_mobile, phone_fax=phone_fax,
        email1=email1, primary_address_street=primary_address_street,
        primary_address_city=primary_address_city,
        primary_address_state=primary_address_state,
        primary_address_postalcode=primary_address_postalcode,
        primary_address_country=primary_address_country,
        account_name=account_name, lead_source=lead_source,
    )
    return await get_client().update_record(
        "Leads", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'basic', 'suitecrm'})
async def delete_lead_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a lead record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Leads", id)


# =============================================================================
# Opportunities (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_opportunities(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all opportunity records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Opportunities", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_opportunity_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single opportunity record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Opportunities", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_opportunity(
    name: str,
    amount: float,
    date_closed: str,
    sales_stage: Literal["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", "Id. Decision Makers", "Perception Analysis", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"],
    description: str = "",
    lead_source: str = "",
    account_id: str = "",
    probability: str = "",
    campaign_id: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new opportunity record.

    Args:
        name: The opportunity name.
        amount: The opportunity amount.
        date_closed: YYYY-MM-DD format (2026-12-31).
        sales_stage: Valid values: Prospecting, Qualification, Needs Analysis, Value Proposition, Id. Decision Makers, Perception Analysis, Proposal/Price Quote, Negotiation/Review, Closed Won, Closed Lost.
        description: A description of the opportunity.
        lead_source: The lead source.
        account_id: The ID of the related account.
        probability: The probability of closing (percentage).
        campaign_id: The ID of the related campaign.
    """
    params = CreateOpportunityParam(
        name=name, amount=amount, date_closed=date_closed,
        sales_stage=sales_stage, description=description,
        lead_source=lead_source, account_id=account_id,
        probability=probability, campaign_id=campaign_id,
    )
    return await get_client().create_record(
        "Opportunities", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_opportunity(
    id: str,
    name: str = None,
    amount: float = None,
    date_closed: str = None,
    sales_stage: Optional[Literal["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", "Id. Decision Makers", "Perception Analysis", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]] = None,
    description: str = None,
    lead_source: str = None,
    account_id: str = None,
    probability: str = None,
    campaign_id: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing opportunity record.

    Args:
        id: The record ID to update.
        name: The opportunity name.
        amount: The opportunity amount.
        date_closed: YYYY-MM-DD format (2026-12-31).
        sales_stage: Valid values: Prospecting, Qualification, Needs Analysis, Value Proposition, Id. Decision Makers, Perception Analysis, Proposal/Price Quote, Negotiation/Review, Closed Won, Closed Lost.
        description: A description of the opportunity.
        lead_source: The lead source.
        account_id: The ID of the related account.
        probability: The probability of closing (percentage).
        campaign_id: The ID of the related campaign.
    """
    params = UpdateOpportunityParam(
        name=name, amount=amount, date_closed=date_closed,
        sales_stage=sales_stage, description=description,
        lead_source=lead_source, account_id=account_id,
        probability=probability, campaign_id=campaign_id,
    )
    return await get_client().update_record(
        "Opportunities", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_opportunity_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete an opportunity record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Opportunities", id)


# =============================================================================
# Cases (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_cases(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all case records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Cases", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_case_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single case record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Cases", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_case(
    name: str,
    description: str,
    status: str = "New",
    priority: Literal["P1", "P2", "P3"] = "P3",
    type: str = "",
    account_id: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new case record.

    Args:
        name: The case name.
        description: A description of the case.
        status: The case status. Defaults to "New".
        priority: Valid values: P1, P2, P3. Defaults to "P3".
        type: The case type.
        account_id: The ID of the related account.
    """
    params = CreateCaseParam(
        name=name, description=description, status=status,
        priority=priority, type=type, account_id=account_id,
    )
    return await get_client().create_record(
        "Cases", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_case(
    id: str,
    name: str = None,
    description: str = None,
    status: str = None,
    priority: Optional[Literal["P1", "P2", "P3"]] = None,
    type: str = None,
    account_id: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing case record.

    Args:
        id: The record ID to update.
        name: The case name.
        description: A description of the case.
        status: The case status.
        priority: Valid values: P1 (High), P2 (Medium), P3 (Low).
        type: The case type.
        account_id: The ID of the related account.
    """
    params = UpdateCaseParam(
        name=name, description=description, status=status,
        priority=priority, type=type, account_id=account_id,
    )
    return await get_client().update_record(
        "Cases", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_case_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a case record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Cases", id)


# =============================================================================
# Notes (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_notes(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all note records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Notes", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_note_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single note record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Notes", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_note(
    name: str,
    description: str,
    portal_flag: bool = False,
    parent_type: str = "",
    parent_id: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new note record.

    Args:
        name: The note name.
        description: The note body text.
        portal_flag: Whether the note is visible in the portal.
        parent_type: The parent module type (e.g. Accounts, Contacts).
        parent_id: The ID of the parent record.
    """
    params = CreateNoteParam(
        name=name, description=description,
        portal_flag=portal_flag, parent_type=parent_type, parent_id=parent_id,
    )
    return await get_client().create_record(
        "Notes", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_note(
    id: str,
    name: str = None,
    description: str = None,
    filename: str = None,
    portal_flag: bool = None,
    parent_type: str = None,
    parent_id: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing note record.

    Args:
        id: The record ID to update.
        name: The note name.
        description: The note body text.
        filename: The filename of an attached file.
        portal_flag: Whether the note is visible in the portal.
        parent_type: The parent module type.
        parent_id: The ID of the parent record.
    """
    params = UpdateNoteParam(
        name=name, description=description, filename=filename,
        portal_flag=portal_flag, parent_type=parent_type, parent_id=parent_id,
    )
    return await get_client().update_record(
        "Notes", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_note_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a note record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Notes", id)


# =============================================================================
# Calls (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_calls(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all call records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Calls", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_call_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single call record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Calls", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_call(
    name: str,
    date_start: str,
    duration_hours: int,
    status: Literal["Planned", "Held", "Not Held"],
    description: str = "",
    duration_minutes: int = 0,
    date_end: str = "",
    parent_type: str = "",
    parent_id: str = "",
    direction: str = "",
    reminder_time: int = -1,
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new call record. The current user is automatically linked.

    Args:
        name: The call subject.
        date_start: ISO 8601 format (2026-06-22T15:00:00-04:00)
        duration_hours: The call duration in hours.
        status: Valid values: Planned, Held, Not Held.
        description: A description of the call.
        duration_minutes: Additional duration in minutes.
        date_end: ISO 8601 format (2026-06-22T15:00:00-04:00)
        parent_type: The parent module type (e.g. Accounts, Contacts).
        parent_id: The ID of the parent record.
        direction: The call direction (Inbound or Outbound).
        reminder_time: Reminder time in seconds before the call.
    """
    params = CreateCallParam(
        name=name, date_start=date_start, duration_hours=duration_hours,
        status=status, description=description,
        duration_minutes=duration_minutes, date_end=date_end,
        parent_type=parent_type, parent_id=parent_id,
        direction=direction, reminder_time=reminder_time,
    )
    return await get_client().create_record(
        "Calls", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_call(
    id: str,
    name: str = None,
    date_start: str = None,
    duration_hours: int = None,
    status: str = None,
    description: str = None,
    duration_minutes: int = None,
    date_end: str = None,
    parent_type: str = None,
    parent_id: str = None,
    direction: str = None,
    reminder_time: int = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing call record.

    Args:
        id: The record ID to update.
        name: The call subject.
        date_start: ISO 8601 format (2026-06-22T15:00:00-04:00)
        duration_hours: The call duration in hours.
        status: The call status.
        description: A description of the call.
        duration_minutes: Additional duration in minutes.
        date_end: ISO 8601 format (2026-06-22T15:00:00-04:00)
        parent_type: The parent module type.
        parent_id: The ID of the parent record.
        direction: The call direction.
        reminder_time: Reminder time in seconds before the call.
    """
    params = UpdateCallParam(
        name=name, date_start=date_start, duration_hours=duration_hours,
        status=status, description=description,
        duration_minutes=duration_minutes, date_end=date_end,
        parent_type=parent_type, parent_id=parent_id,
        direction=direction, reminder_time=reminder_time,
    )
    return await get_client().update_record(
        "Calls", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_call_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a call record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Calls", id)


# =============================================================================
# Meetings (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_meetings(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all meeting records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Meetings", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_meeting_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single meeting record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Meetings", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_meeting(
    name: str,
    date_start: str,
    duration_hours: int,
    description: str = "",
    duration_minutes: int = 0,
    date_end: str = "",
    status: str = "Planned",
    parent_type: str = "",
    parent_id: str = "",
    reminder_time: int = -1,
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new meeting record. The current user is automatically linked.

    Args:
        name: The meeting subject.
        date_start: ISO 8601 format (2026-06-22T15:00:00-04:00)
        duration_hours: The meeting duration in hours.
        description: A description of the meeting.
        duration_minutes: Additional duration in minutes.
        date_end: ISO 8601 format (2026-06-22T15:00:00-04:00)
        status: The meeting status. Defaults to "Planned".
        parent_type: The parent module type (e.g. Accounts, Contacts).
        parent_id: The ID of the parent record.
        reminder_time: Reminder time in seconds before the meeting.
    """
    params = CreateMeetingParam(
        name=name, date_start=date_start, duration_hours=duration_hours,
        description=description, duration_minutes=duration_minutes,
        date_end=date_end, status=status, parent_type=parent_type,
        parent_id=parent_id, reminder_time=reminder_time,
    )
    return await get_client().create_record(
        "Meetings", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_meeting(
    id: str,
    name: str = None,
    date_start: str = None,
    duration_hours: int = None,
    description: str = None,
    duration_minutes: int = None,
    date_end: str = None,
    status: str = None,
    parent_type: str = None,
    parent_id: str = None,
    reminder_time: int = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing meeting record.

    Args:
        id: The record ID to update.
        name: The meeting subject.
        date_start: ISO 8601 format (2026-06-22T15:00:00-04:00)
        duration_hours: The meeting duration in hours.
        description: A description of the meeting.
        duration_minutes: Additional duration in minutes.
        date_end: ISO 8601 format (2026-06-22T15:00:00-04:00)
        status: The meeting status.
        parent_type: The parent module type.
        parent_id: The ID of the parent record.
        reminder_time: Reminder time in seconds before the meeting.
    """
    params = UpdateMeetingParam(
        name=name, date_start=date_start, duration_hours=duration_hours,
        description=description, duration_minutes=duration_minutes,
        date_end=date_end, status=status, parent_type=parent_type,
        parent_id=parent_id, reminder_time=reminder_time,
    )
    return await get_client().update_record(
        "Meetings", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_meeting_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a meeting record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Meetings", id)


# =============================================================================
# Tasks (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_tasks(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all task records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Tasks", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_task_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single task record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Tasks", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_task(
    name: str,
    status: Literal["Not Started", "In Progress", "Completed", "Pending Input", "Deferred"],
    date_due: str,
    description: str = "",
    date_start: str = "",
    parent_type: str = "",
    parent_id: str = "",
    priority: Literal["High", "Medium", "Low"] = "Medium",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new task record.

    Args:
        name: The task subject.
        status: Valid values: Not Started, In Progress, Completed, Pending Input, Deferred.
        date_due: YYYY-MM-DD format (2026-12-31).
        description: A description of the task.
        date_start: YYYY-MM-DD format (2026-12-31).
        parent_type: The parent module type (e.g. Accounts, Contacts).
        parent_id: The ID of the parent record.
        priority: Valid values: High, Medium, Low. Defaults to "Medium".
    """
    params = CreateTaskParam(
        name=name, status=status, date_due=date_due,
        description=description, date_start=date_start,
        parent_type=parent_type, parent_id=parent_id, priority=priority,
    )
    return await get_client().create_record(
        "Tasks", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_task(
    id: str,
    name: str = None,
    status: Optional[Literal["Not Started", "In Progress", "Completed", "Pending Input", "Deferred"]] = None,
    date_due: str = None,
    description: str = None,
    date_start: str = None,
    parent_type: str = None,
    parent_id: str = None,
    priority: Optional[Literal["High", "Medium", "Low"]] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing task record.

    Args:
        id: The record ID to update.
        name: The task subject.
        status: Valid values: Not Started, In Progress, Completed, Pending Input, Deferred.
        date_due: YYYY-MM-DD format (2026-12-31).
        description: A description of the task.
        date_start: YYYY-MM-DD format (2026-12-31).
        parent_type: The parent module type.
        parent_id: The ID of the parent record.
        priority: Valid values: High, Medium, Low.
    """
    params = UpdateTaskParam(
        name=name, status=status, date_due=date_due,
        description=description, date_start=date_start,
        parent_type=parent_type, parent_id=parent_id, priority=priority,
    )
    return await get_client().update_record(
        "Tasks", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_task_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a task record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Tasks", id)


# =============================================================================
# Emails (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_emails(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all email records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Emails", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_email_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single email record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Emails", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_email(
    name: str,
    description: str,
    parent_type: str = "",
    parent_id: str = "",
    type: Literal["out", "archived", "draft", "inbound", "campaign"] = "draft",
    status: Literal["archived", "closed", "draft", "read", "replied", "sent", "send_error", "unread"] = "draft",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new email record.

    Args:
        name: The email subject.
        description: The email body text.
        parent_type: The parent module type (e.g. Accounts, Contacts).
        parent_id: The ID of the parent record.
        type: Valid values: out (Sent), archived (Archived), draft (Draft), inbound (Inbound), campaign (Campaign). Defaults to "draft".
        status: Valid values: archived, closed, draft, read, replied, sent, send_error, unread. Defaults to "draft".
    """
    params = CreateEmailParam(
        name=name, description=description,
        parent_type=parent_type, parent_id=parent_id,
        type=type, status=status,
    )
    return await get_client().create_record(
        "Emails", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_email(
    id: str,
    name: str = None,
    description: str = None,
    date_sent: str = None,
    parent_type: str = None,
    parent_id: str = None,
    type: Optional[Literal["out", "archived", "draft", "inbound", "campaign"]] = None,
    status: Optional[Literal["archived", "closed", "draft", "read", "replied", "sent", "send_error", "unread"]] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing email record.

    Args:
        id: The record ID to update.
        name: The email subject.
        description: The email body text.
        date_sent: YYYY-MM-DD format (2026-12-31).
        parent_type: The parent module type.
        parent_id: The ID of the parent record.
        type: Valid values: out (Sent), archived (Archived), draft (Draft), inbound (Inbound), campaign (Campaign).
        status: Valid values: archived, closed, draft, read, replied, sent, send_error, unread.
    """
    params = UpdateEmailParam(
        name=name, description=description, date_sent=date_sent,
        parent_type=parent_type, parent_id=parent_id,
        type=type, status=status,
    )
    return await get_client().update_record(
        "Emails", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_email_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete an email record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Emails", id)


# =============================================================================
# Documents (5 tools) — no assigned_user_id
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_documents(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all document records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Documents", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_document_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single document record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Documents", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_document(
    document_name: str,
    filename: str,
    active_date: str,
    description: str,
    category_id: str = "",
    revision: str = "1",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new document record.

    Args:
        document_name: The document name.
        filename: The filename of the uploaded document.
        active_date: YYYY-MM-DD format (2026-12-31).
        description: A description of the document.
        category_id: The document category ID.
        revision: The document revision number. Defaults to "1".
    """
    params = CreateDocumentParam(
        document_name=document_name, filename=filename, active_date=active_date,
        description=description, category_id=category_id,
        revision=revision,
    )
    return await get_client().create_record(
        "Documents", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE, inject_assigned=False
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_document(
    id: str,
    document_name: str = None,
    filename: str = None,
    active_date: str = None,
    description: str = None,
    category_id: str = None,
    subcategory: str = None,
    revision: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing document record.

    Args:
        id: The record ID to update.
        document_name: The document name.
        filename: The filename of the uploaded document.
        active_date: YYYY-MM-DD format (2026-12-31).
        description: A description of the document.
        category_id: The document category ID.
        subcategory: The document subcategory.
        revision: The document revision number.
    """
    params = UpdateDocumentParam(
        document_name=document_name, filename=filename, active_date=active_date,
        description=description, category_id=category_id,
        subcategory=subcategory, revision=revision,
    )
    return await get_client().update_record(
        "Documents", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_document_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a document record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Documents", id)


# =============================================================================
# Project (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_projects(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all project records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Project", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_project_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single project record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Project", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_project(
    name: str,
    estimated_start_date: str,
    estimated_end_date: str,
    status: Literal["Draft", "In Review", "Underway", "On_Hold", "Completed"],
    description: str = "",
    priority: str = "",
    total_estimated_effort: int = 0,
    total_actual_effort: int = 0,
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new project record.

    Args:
        name: The project name.
        estimated_start_date: YYYY-MM-DD format (2026-12-31).
        estimated_end_date: YYYY-MM-DD format (2026-12-31).
        status: Valid values: Draft, In Review, Underway, On_Hold, Completed.
        description: A description of the project.
        priority: The project priority.
        total_estimated_effort: The total estimated effort in hours.
        total_actual_effort: The total actual effort in hours.
    """
    params = CreateProjectParam(
        name=name, estimated_start_date=estimated_start_date,
        estimated_end_date=estimated_end_date, status=status,
        description=description, priority=priority,
        total_estimated_effort=total_estimated_effort,
        total_actual_effort=total_actual_effort,
    )
    return await get_client().create_record(
        "Project", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_project(
    id: str,
    name: str = None,
    estimated_start_date: str = None,
    estimated_end_date: str = None,
    status: Optional[Literal["Draft", "In Review", "Underway", "On_Hold", "Completed"]] = None,
    description: str = None,
    priority: str = None,
    total_estimated_effort: int = None,
    total_actual_effort: int = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing project record.

    Args:
        id: The record ID to update.
        name: The project name.
        estimated_start_date: YYYY-MM-DD format (2026-12-31).
        estimated_end_date: YYYY-MM-DD format (2026-12-31).
        status: Valid values: Draft, In Review, Underway, On_Hold, Completed.
        description: A description of the project.
        priority: The project priority.
        total_estimated_effort: The total estimated effort in hours.
        total_actual_effort: The total actual effort in hours.
    """
    params = UpdateProjectParam(
        name=name, estimated_start_date=estimated_start_date,
        estimated_end_date=estimated_end_date, status=status,
        description=description, priority=priority,
        total_estimated_effort=total_estimated_effort,
        total_actual_effort=total_actual_effort,
    )
    return await get_client().update_record(
        "Project", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_project_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a project record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Project", id)


# =============================================================================
# Prospects (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_prospects(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all prospect records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Prospects", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_prospect_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single prospect record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Prospects", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_prospect(
    first_name: str,
    last_name: str,
    description: str = "",
    title: str = "",
    department: str = "",
    phone_work: str = "",
    phone_mobile: str = "",
    email1: str = "",
    primary_address_street: str = "",
    primary_address_city: str = "",
    primary_address_state: str = "",
    primary_address_postalcode: str = "",
    primary_address_country: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new prospect record.

    Args:
        first_name: The prospect's first name.
        last_name: The prospect's last name.
        description: A description of the prospect.
        title: The prospect's job title.
        department: The department the prospect works in.
        phone_work: The work phone number.
        phone_mobile: The mobile phone number.
        email1: The primary email address.
        primary_address_street: The primary address street.
        primary_address_city: The primary address city.
        primary_address_state: The primary address state.
        primary_address_postalcode: The primary address postal code.
        primary_address_country: The primary address country.
    """
    params = CreateProspectParam(
        first_name=first_name, last_name=last_name, description=description,
        title=title, department=department, phone_work=phone_work,
        phone_mobile=phone_mobile, email1=email1,
        primary_address_street=primary_address_street,
        primary_address_city=primary_address_city,
        primary_address_state=primary_address_state,
        primary_address_postalcode=primary_address_postalcode,
        primary_address_country=primary_address_country,
    )
    return await get_client().create_record(
        "Prospects", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_prospect(
    id: str,
    first_name: str = None,
    last_name: str = None,
    description: str = None,
    title: str = None,
    department: str = None,
    phone_work: str = None,
    phone_mobile: str = None,
    email1: str = None,
    primary_address_street: str = None,
    primary_address_city: str = None,
    primary_address_state: str = None,
    primary_address_postalcode: str = None,
    primary_address_country: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing prospect record.

    Args:
        id: The record ID to update.
        first_name: The prospect's first name.
        last_name: The prospect's last name.
        description: A description of the prospect.
        title: The prospect's job title.
        department: The department the prospect works in.
        phone_work: The work phone number.
        phone_mobile: The mobile phone number.
        email1: The primary email address.
        primary_address_street: The primary address street.
        primary_address_city: The primary address city.
        primary_address_state: The primary address state.
        primary_address_postalcode: The primary address postal code.
        primary_address_country: The primary address country.
    """
    params = UpdateProspectParam(
        first_name=first_name, last_name=last_name, description=description,
        title=title, department=department, phone_work=phone_work,
        phone_mobile=phone_mobile, email1=email1,
        primary_address_street=primary_address_street,
        primary_address_city=primary_address_city,
        primary_address_state=primary_address_state,
        primary_address_postalcode=primary_address_postalcode,
        primary_address_country=primary_address_country,
    )
    return await get_client().update_record(
        "Prospects", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_prospect_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a prospect record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Prospects", id)


# =============================================================================
# Campaigns (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_campaigns(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all campaign records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Campaigns", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_campaign_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single campaign record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Campaigns", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_campaign(
    name: str,
    campaign_type: Literal["Telesales", "Mail", "Email", "Print", "Web", "Radio", "Television", "NewsLetter", "Survey"],
    status: Literal["Planning", "Active", "Inactive", "Complete"],
    start_date: str,
    end_date: str,
    description: str = "",
    budget: float = 0.0,
    expected_cost: float = 0.0,
    actual_cost: float = 0.0,
    expected_revenue: float = 0.0,
    objective: str = "",
    content: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new campaign record.

    Args:
        name: The campaign name.
        campaign_type: Valid values: Telesales, Mail, Email, Print, Web, Radio, Television, NewsLetter, Survey.
        status: Valid values: Planning, Active, Inactive, Complete.
        start_date: YYYY-MM-DD format (2026-12-31).
        end_date: YYYY-MM-DD format (2026-12-31).
        description: A description of the campaign.
        budget: The campaign budget.
        expected_cost: The expected cost of the campaign.
        actual_cost: The actual cost of the campaign.
        expected_revenue: The expected revenue from the campaign.
        objective: The campaign objective.
        content: The campaign content.
    """
    params = CreateCampaignParam(
        name=name, campaign_type=campaign_type, status=status,
        start_date=start_date, end_date=end_date, description=description,
        budget=budget, expected_cost=expected_cost, actual_cost=actual_cost,
        expected_revenue=expected_revenue, objective=objective, content=content,
    )
    return await get_client().create_record(
        "Campaigns", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_campaign(
    id: str,
    name: str = None,
    campaign_type: Optional[Literal["Telesales", "Mail", "Email", "Print", "Web", "Radio", "Television", "NewsLetter", "Survey"]] = None,
    status: Optional[Literal["Planning", "Active", "Inactive", "Complete"]] = None,
    start_date: str = None,
    end_date: str = None,
    description: str = None,
    budget: float = None,
    expected_cost: float = None,
    actual_cost: float = None,
    expected_revenue: float = None,
    objective: str = None,
    content: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing campaign record.

    Args:
        id: The record ID to update.
        name: The campaign name.
        campaign_type: Valid values: Telesales, Mail, Email, Print, Web, Radio, Television, NewsLetter, Survey.
        status: Valid values: Planning, Active, Inactive, Complete.
        start_date: YYYY-MM-DD format (2026-12-31).
        end_date: YYYY-MM-DD format (2026-12-31).
        description: A description of the campaign.
        budget: The campaign budget.
        expected_cost: The expected cost.
        actual_cost: The actual cost.
        expected_revenue: The expected revenue.
        objective: The campaign objective.
        content: The campaign content.
    """
    params = UpdateCampaignParam(
        name=name, campaign_type=campaign_type, status=status,
        start_date=start_date, end_date=end_date, description=description,
        budget=budget, expected_cost=expected_cost, actual_cost=actual_cost,
        expected_revenue=expected_revenue, objective=objective, content=content,
    )
    return await get_client().update_record(
        "Campaigns", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_campaign_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a campaign record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Campaigns", id)


# =============================================================================
# Bugs (5 tools)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_bugs(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all bug records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("Bugs", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_bug_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single bug record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("Bugs", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_bug(
    name: str,
    description: str,
    bug_number: str = "",
    status: str = "New",
    priority: Literal["Urgent", "High", "Medium", "Low"] = "Medium",
    type: Literal["Defect", "Feature"] = "Defect",
    resolution: Literal["", "Accepted", "Duplicate", "Fixed", "Out of Date", "Invalid", "Later"] = "",
    found_in_release: str = "",
    fixed_in_release: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new bug record.

    Args:
        name: The bug name/summary.
        description: A description of the bug.
        bug_number: The bug tracking number.
        status: The bug status. Defaults to "New".
        priority: Valid values: Urgent, High, Medium, Low. Defaults to "Medium".
        type: Valid values: Defect, Feature. Defaults to "Defect".
        resolution: Valid values: Accepted, Duplicate, Fixed, Out of Date, Invalid, Later (or empty for none).
        found_in_release: The release version where the bug was found.
        fixed_in_release: The release version where the bug was fixed.
    """
    params = CreateBugParam(
        name=name, description=description, bug_number=bug_number,
        status=status, priority=priority, type=type,
        resolution=resolution, found_in_release=found_in_release,
        fixed_in_release=fixed_in_release,
    )
    return await get_client().create_record(
        "Bugs", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_bug(
    id: str,
    name: str = None,
    description: str = None,
    bug_number: str = None,
    status: str = None,
    priority: Optional[Literal["Urgent", "High", "Medium", "Low"]] = None,
    type: Optional[Literal["Defect", "Feature"]] = None,
    severity: str = None,
    resolution: Optional[Literal["", "Accepted", "Duplicate", "Fixed", "Out of Date", "Invalid", "Later"]] = None,
    found_in_release: str = None,
    fixed_in_release: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing bug record.

    Args:
        id: The record ID to update.
        name: The bug name/summary.
        description: A description of the bug.
        bug_number: The bug tracking number.
        status: The bug status.
        priority: Valid values: Urgent, High, Medium, Low.
        type: Valid values: Defect, Feature.
        severity: The bug severity.
        resolution: Valid values: Accepted, Duplicate, Fixed, Out of Date, Invalid, Later (or empty for none).
        found_in_release: The release where the bug was found.
        fixed_in_release: The release where the bug was fixed.
    """
    params = UpdateBugParam(
        name=name, description=description, bug_number=bug_number,
        status=status, priority=priority, type=type, severity=severity,
        resolution=resolution, found_in_release=found_in_release,
        fixed_in_release=fixed_in_release,
    )
    return await get_client().update_record(
        "Bugs", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_bug_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a bug record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("Bugs", id)


# =============================================================================
# Products (5 tools) — no assigned_user_id
# =============================================================================

@mcp.tool(tags={'read', 'advanced', 'suitecrm'})
async def get_all_products(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all product records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("AOS_Products", include_all_fields)


@mcp.tool(tags={'read', 'advanced', 'suitecrm'})
async def get_product_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single product record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("AOS_Products", id, include_all_fields)


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def create_product(
    name: str,
    cost: float,
    price: float,
    type: str,
    description: str = "",
    part_number: str = "",
    category: str = "",
    url: str = "",
    contact_id: str = "",
    currency_id: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new product record.

    Args:
        name: The product name.
        cost: The product cost.
        price: The product price.
        type: The product type.
        description: A description of the product.
        part_number: The product part number.
        category: The product category.
        url: The product URL.
        contact_id: The ID of the related contact.
        currency_id: The currency ID.
    """
    params = CreateProductParam(
        name=name, cost=cost, price=price, type=type,
        description=description, part_number=part_number, category=category,
        url=url, contact_id=contact_id,
        currency_id=currency_id,
    )
    return await get_client().create_record(
        "AOS_Products", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE, inject_assigned=False
    )


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def update_product(
    id: str,
    name: str = None,
    cost: float = None,
    price: float = None,
    type: str = None,
    description: str = None,
    part_number: str = None,
    category: str = None,
    url: str = None,
    contact_id: str = None,
    pricing_formula: str = None,
    currency_id: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing product record.

    Args:
        id: The record ID to update.
        name: The product name.
        cost: The product cost.
        price: The product price.
        type: The product type.
        description: A description of the product.
        part_number: The product part number.
        category: The product category.
        url: The product URL.
        contact_id: The ID of the related contact.
        pricing_formula: The pricing formula.
        currency_id: The currency ID.
    """
    params = UpdateProductParam(
        name=name, cost=cost, price=price, type=type,
        description=description, part_number=part_number, category=category,
        url=url, contact_id=contact_id, pricing_formula=pricing_formula,
        currency_id=currency_id,
    )
    return await get_client().update_record(
        "AOS_Products", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def delete_product_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a product record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("AOS_Products", id)


# =============================================================================
# Contracts (5 tools) — no assigned_user_id
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_contracts(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all contract records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("AOS_Contracts", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_contract_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single contract record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("AOS_Contracts", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_contract(
    name: str,
    status: str,
    contract_account: str,
    total_contract_value: float,
    description: str = "",
    start_date: str = "",
    end_date: str = "",
    currency_id: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new contract record.

    Args:
        name: The contract name.
        status: The contract status.
        contract_account: The ID of the related account.
        total_contract_value: The total contract value.
        description: A description of the contract.
        start_date: YYYY-MM-DD format (2026-12-31).
        end_date: YYYY-MM-DD format (2026-12-31).
        currency_id: The currency ID.
    """
    params = CreateContractParam(
        name=name, status=status, contract_account=contract_account,
        total_contract_value=total_contract_value, description=description,
        start_date=start_date, end_date=end_date, currency_id=currency_id,
    )
    return await get_client().create_record(
        "AOS_Contracts", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE, inject_assigned=False
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_contract(
    id: str,
    name: str = None,
    status: str = None,
    contract_account: str = None,
    total_contract_value: float = None,
    description: str = None,
    start_date: str = None,
    end_date: str = None,
    currency_id: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing contract record.

    Args:
        id: The record ID to update.
        name: The contract name.
        status: The contract status.
        contract_account: The ID of the related account.
        total_contract_value: The total contract value.
        description: A description of the contract.
        start_date: YYYY-MM-DD format (2026-12-31).
        end_date: YYYY-MM-DD format (2026-12-31).
        currency_id: The currency ID.
    """
    params = UpdateContractParam(
        name=name, status=status, contract_account=contract_account,
        total_contract_value=total_contract_value, description=description,
        start_date=start_date, end_date=end_date, currency_id=currency_id,
    )
    return await get_client().update_record(
        "AOS_Contracts", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_contract_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a contract record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("AOS_Contracts", id)


# =============================================================================
# Invoices (5 tools) — no assigned_user_id
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_invoices(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all invoice records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _list_tool("AOS_Invoices", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_invoice_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a single invoice record by its ID.

    Args:
        id: The record ID to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await _get_tool("AOS_Invoices", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_invoice(
    name: str,
    number: str,
    status: str,
    total_amount: float,
    due_date: str,
    description: str = "",
    billing_account: str = "",
    billing_contact: str = "",
    currency_id: str = "",
    quote_number: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new invoice record.

    Args:
        name: The invoice name.
        number: The invoice number.
        status: The invoice status.
        total_amount: The invoice total amount.
        due_date: YYYY-MM-DD format (2026-12-31).
        description: A description of the invoice.
        billing_account: The ID of the billing account.
        billing_contact: The ID of the billing contact.
        currency_id: The currency ID.
        quote_number: The related quote number.
    """
    params = CreateInvoiceParam(
        name=name, number=number, status=status, total_amount=total_amount,
        due_date=due_date, description=description,
        billing_account=billing_account, billing_contact=billing_contact,
        currency_id=currency_id, quote_number=quote_number,
    )
    return await get_client().create_record(
        "AOS_Invoices", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE, inject_assigned=False
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_invoice(
    id: str,
    name: str = None,
    number: str = None,
    status: str = None,
    total_amount: float = None,
    due_date: str = None,
    description: str = None,
    billing_account: str = None,
    billing_contact: str = None,
    currency_id: str = None,
    quote_number: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing invoice record.

    Args:
        id: The record ID to update.
        name: The invoice name.
        number: The invoice number.
        status: The invoice status.
        total_amount: The invoice total amount.
        due_date: YYYY-MM-DD format (2026-12-31).
        description: A description of the invoice.
        billing_account: The ID of the billing account.
        billing_contact: The ID of the billing contact.
        currency_id: The currency ID.
        quote_number: The related quote number.
    """
    params = UpdateInvoiceParam(
        name=name, number=number, status=status, total_amount=total_amount,
        due_date=due_date, description=description,
        billing_account=billing_account, billing_contact=billing_contact,
        currency_id=currency_id, quote_number=quote_number,
    )
    return await get_client().update_record(
        "AOS_Invoices", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_invoice_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete an invoice record by its ID.

    Args:
        id: The record ID to delete.
    """
    return await _delete_tool("AOS_Invoices", id)


# =============================================================================
# Quotes (5 tools) — no assigned_user_id
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_all_quotes(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve all quote records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the list of quotes.
    """
    return await _list_tool("AOS_Quotes", include_all_fields)


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_quote_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve a specific quote record by ID.

    Args:
        id: The ID of the quote record to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the quote record data.
    """
    return await _get_tool("AOS_Quotes", id, include_all_fields)


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_quote(
    name: str,
    stage: Literal["Draft", "Negotiation", "Delivered", "On Hold", "Confirmed", "Closed Accepted", "Closed Lost", "Closed Dead"],
    total_amount: float,
    description: str = "",
    number: str = "",
    currency_id: str = "",
    billing_account: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new quote record.

    Args:
        name: Name of the quote.
        stage: Valid values: Draft, Negotiation, Delivered, On Hold, Confirmed, Closed Accepted, Closed Lost, Closed Dead.
        total_amount: Total monetary amount of the quote.
        description: Description of the quote.
        number: Quote number identifier.
        currency_id: ID of the currency used for the quote.
        billing_account: ID of the billing account associated with the quote.

    Returns:
        Dictionary containing the created quote data.
    """
    params = CreateQuoteParam(
        name=name, stage=stage, total_amount=total_amount,
        description=description, number=number,
        currency_id=currency_id, billing_account=billing_account,
    )
    return await get_client().create_record(
        "AOS_Quotes", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE, inject_assigned=False
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def update_quote(
    id: str,
    name: str = None,
    stage: Optional[Literal["Draft", "Negotiation", "Delivered", "On Hold", "Confirmed", "Closed Accepted", "Closed Lost", "Closed Dead"]] = None,
    total_amount: float = None,
    valid_until: str = None,
    description: str = None,
    number: str = None,
    currency_id: str = None,
    billing_account: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing quote record.

    Args:
        id: The ID of the quote record to update.
        name: New name for the quote.
        stage: Valid values: Draft, Negotiation, Delivered, On Hold, Confirmed, Closed Accepted, Closed Lost, Closed Dead.
        total_amount: New total monetary amount.
        valid_until: YYYY-MM-DD format (2026-12-31).
        description: New description for the quote.
        number: New quote number.
        currency_id: New currency ID.
        billing_account: New billing account ID.

    Returns:
        Dictionary containing the updated quote data.
    """
    params = UpdateQuoteParam(
        name=name, stage=stage, total_amount=total_amount,
        valid_until=valid_until, description=description, number=number,
        currency_id=currency_id, billing_account=billing_account,
    )
    return await get_client().update_record(
        "AOS_Quotes", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_quote_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a quote record by ID.

    Args:
        id: The ID of the quote record to delete.

    Returns:
        Dictionary containing the deletion result.
    """
    return await _delete_tool("AOS_Quotes", id)


# =============================================================================
# Knowledge Base (5 tools) — no assigned_user_id
# =============================================================================

@mcp.tool(tags={'read', 'advanced', 'suitecrm'})
async def get_all_knowledgebase(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve all knowledge base articles.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the list of knowledge base articles.
    """
    return await _list_tool("AOK_KnowledgeBase", include_all_fields)


@mcp.tool(tags={'read', 'advanced', 'suitecrm'})
async def get_knowledgebase_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve a specific knowledge base article by ID.

    Args:
        id: The ID of the knowledge base article to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the knowledge base article data.
    """
    return await _get_tool("AOK_KnowledgeBase", id, include_all_fields)


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def create_knowledgebase(
    name: str,
    author: str,
    status: Literal["Draft", "Expired", "In_Review", "published_private", "published_public"],
    description: str,
    revision: str = "",
    additional_info: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new knowledge base article.

    Args:
        name: Title of the knowledge base article.
        author: Author of the article.
        status: Valid values: Draft, Expired, In_Review, published_private, published_public.
        description: Content/body of the knowledge base article.
        revision: Revision number or identifier.
        additional_info: Additional information or notes.

    Returns:
        Dictionary containing the created knowledge base article data.
    """
    params = CreateKnowledgeBaseParam(
        name=name, author=author, status=status, description=description,
        revision=revision, additional_info=additional_info,
    )
    return await get_client().create_record(
        "AOK_KnowledgeBase", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE, inject_assigned=False
    )


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def update_knowledgebase(
    id: str,
    name: str = None,
    author: str = None,
    status: Optional[Literal["Draft", "Expired", "In_Review", "published_private", "published_public"]] = None,
    description: str = None,
    revision: str = None,
    additional_info: str = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing knowledge base article.

    Args:
        id: The ID of the knowledge base article to update.
        name: New title for the article.
        author: New author for the article.
        status: Valid values: Draft, Expired, In_Review, published_private, published_public.
        description: New content/body for the article.
        revision: New revision number.
        additional_info: New additional information.
        description: New content/body for the article.
        revision: New revision number.
        additional_info: New additional information.

    Returns:
        Dictionary containing the updated knowledge base article data.
    """
    params = UpdateKnowledgeBaseParam(
        name=name, author=author, status=status, description=description,
        revision=revision, additional_info=additional_info,
    )
    return await get_client().update_record(
        "AOK_KnowledgeBase", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def delete_knowledgebase_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a knowledge base article by ID.

    Args:
        id: The ID of the knowledge base article to delete.

    Returns:
        Dictionary containing the deletion result.
    """
    return await _delete_tool("AOK_KnowledgeBase", id)


# =============================================================================
# Events (5 tools) — no assigned_user_id
# =============================================================================

@mcp.tool(tags={'read', 'advanced', 'suitecrm'})
async def get_all_events(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve all event records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the list of events.
    """
    return await _list_tool("FP_events", include_all_fields)


@mcp.tool(tags={'read', 'advanced', 'suitecrm'})
async def get_event_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve a specific event record by ID.

    Args:
        id: The ID of the event record to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the event record data.
    """
    return await _get_tool("FP_events", id, include_all_fields)


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def create_event(
    name: str,
    date_start: str,
    duration_hours: int,
    description: str,
    duration_minutes: int = 0,
    date_end: str = "",
    location: str = "",
    budget: float = 0.0,
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new event record.

    Args:
        name: Name of the event.
        date_start: ISO 8601 format (2026-06-22T15:00:00-04:00)
        duration_hours: Duration of the event in hours.
        description: Description of the event.
        duration_minutes: Additional duration in minutes.
        date_end: ISO 8601 format (2026-06-22T15:00:00-04:00)
        location: Location of the event.
        budget: Budget allocated for the event.

    Returns:
        Dictionary containing the created event data.
    """
    params = CreateEventParam(
        name=name, date_start=date_start, duration_hours=duration_hours,
        description=description, duration_minutes=duration_minutes,
        date_end=date_end, location=location,
        budget=budget,
    )
    return await get_client().create_record(
        "FP_events", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE, inject_assigned=False
    )


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def update_event(
    id: str,
    name: str = None,
    date_start: str = None,
    duration_hours: int = None,
    description: str = None,
    duration_minutes: int = None,
    date_end: str = None,
    status: Optional[Literal["active", "inactive"]] = None,
    location: str = None,
    budget: float = None,
    expected_revenue: float = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing event record.

    Args:
        id: The ID of the event record to update.
        name: New name for the event.
        date_start: ISO 8601 format (2026-06-22T15:00:00-04:00)
        duration_hours: New duration in hours.
        description: New description for the event.
        duration_minutes: New additional duration in minutes.
        date_end: ISO 8601 format (2026-06-22T15:00:00-04:00)
        status: Valid values: active, inactive.
        location: New location for the event.
        budget: New budget amount.
        expected_revenue: New expected revenue amount.

    Returns:
        Dictionary containing the updated event data.
    """
    params = UpdateEventParam(
        name=name, date_start=date_start, duration_hours=duration_hours,
        description=description, duration_minutes=duration_minutes,
        date_end=date_end, status=status, location=location,
        budget=budget, expected_revenue=expected_revenue,
    )
    return await get_client().update_record(
        "FP_events", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def delete_event_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete an event record by ID.

    Args:
        id: The ID of the event record to delete.

    Returns:
        Dictionary containing the deletion result.
    """
    return await _delete_tool("FP_events", id)


# =============================================================================
# Reports (5 tools) — no assigned_user_id
# =============================================================================

@mcp.tool(tags={'read', 'advanced', 'suitecrm'})
async def get_all_reports(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve all report records.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the list of reports.
    """
    return await _list_tool("AOR_Reports", include_all_fields)


@mcp.tool(tags={'read', 'advanced', 'suitecrm'})
async def get_report_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve a specific report record by ID.

    Args:
        id: The ID of the report record to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the report record data.
    """
    return await _get_tool("AOR_Reports", id, include_all_fields)


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def create_report(
    name: str,
    report_module: str,
    description: str = "",
    graphs_per_row: int = 2,
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new report record.

    Args:
        name: Name of the report.
        report_module: The SuiteCRM module the report is based on.
        description: Description of the report.
        graphs_per_row: Number of graphs to display per row (default 2).

    Returns:
        Dictionary containing the created report data.
    """
    params = CreateReportParam(
        name=name, report_module=report_module, description=description,
        graphs_per_row=graphs_per_row,
    )
    return await get_client().create_record(
        "AOR_Reports", params.model_dump(exclude_unset=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE, inject_assigned=False
    )


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def update_report(
    id: str,
    name: str = None,
    report_module: str = None,
    description: str = None,
    graphs_per_row: int = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update an existing report record.

    Args:
        id: The ID of the report record to update.
        name: New name for the report.
        report_module: New module the report is based on.
        description: New description for the report.
        graphs_per_row: New number of graphs per row.

    Returns:
        Dictionary containing the updated report data.
    """
    params = UpdateReportParam(
        name=name, report_module=report_module, description=description,
        graphs_per_row=graphs_per_row,
    )
    return await get_client().update_record(
        "AOR_Reports", id, params.model_dump(exclude_none=True), get_user_token(), include_all_fields=ALLOW_ALL_AGGREGATE
    )


@mcp.tool(tags={'write', 'advanced', 'suitecrm'})
async def delete_report_by_id(
    id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a report record by ID.

    Args:
        id: The ID of the report record to delete.

    Returns:
        Dictionary containing the deletion result.
    """
    return await _delete_tool("AOR_Reports", id)


# =============================================================================
# Additional Tools (7)
# =============================================================================

@mcp.tool(tags={'read', 'basic', 'suitecrm'})
async def get_current_user(
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve the currently authenticated user's information.

    Args:
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the current user data.
    """
    return await get_client().get_current_user(get_user_token(), include_all_fields)


@mcp.tool(tags={'read', 'basic', 'suitecrm'})
async def check_server_status(ctx: Context = None) -> dict[str, Any]:
    """Check the connection status of the SuiteCRM backend server.

    Returns:
        Dictionary containing the connection status and backend response code.
    """
    client = get_client()
    token = get_user_token()
    try:
        async with httpx_mod.AsyncClient(timeout=5.0) as http_client:
            url = f"{client.base_url}/current-user"
            headers = {"Authorization": f"Bearer {token}"}
            response = await http_client.get(url, headers=headers)
            return {"status": "connected", "backend_response": response.status_code}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_calendar_events(
    start_date: str,
    end_date: str,
    user_id: str = "",
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve calendar events within a date range.

    Args:
        start_date: ISO 8601 format (2026-06-22T15:00:00-04:00)
        end_date: ISO 8601 format (2026-06-22T15:00:00-04:00)
        user_id: Filter events by specific user ID.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the list of calendar events.
    """
    data = await get_client().get_calendar_events(
        get_user_token(), start_date, end_date, user_id, include_all_fields if ALLOW_ALL_AGGREGATE else False
    )
    return {"items": json_to_toon(data)}


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_calendar_event_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve a specific calendar event by ID.

    Args:
        id: The ID of the calendar event to retrieve.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the calendar event data, or an error if not found.
    """
    result = await get_client().get_calendar_event_by_id(
        get_user_token(), id, include_all_fields
    )
    if result is None:
        return {"error": "Event not found in any calendar module"}
    return result


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_activities_related_to_record(
    module: str,
    id: str,
    activity_types: list[str] = [],
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve activities related to a specific record.

    Args:
        module: The module name of the record (e.g. Accounts, Contacts).
        id: The ID of the record to find related activities for.
        activity_types: Activity types to include. Valid values: Call, Meeting, Task, Email, Note.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the list of related activities.
    """
    data = await get_client().get_activities_related_to_record(
        get_user_token(), module, id, activity_types, include_all_fields if ALLOW_ALL_AGGREGATE else False
    )
    return {"items": json_to_toon(data)}


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_history_related_to_record(
    module: str,
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve history items related to a specific record.

    Args:
        module: The module name of the record (e.g. Accounts, Contacts).
        id: The ID of the record to find history for.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the list of history items.
    """
    data = await get_client().get_history_related_to_record(
        get_user_token(), module, id, include_all_fields if ALLOW_ALL_AGGREGATE else False if ALLOW_ALL_AGGREGATE else False
    )
    return {"items": json_to_toon(data)}


@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_activity_history_by_id(
    id: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve activity history for a specific record by ID.

    Args:
        id: The ID of the record to retrieve activity history for.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the activity history, or an error if not found.
    """
    result = await get_client().get_activity_history_by_id(
        get_user_token(), id, include_all_fields
    )
    if result is None:
        return {"error": "Activity not found in any module"}
    return result


# =============================================================================
# Relationship Tools (3)
# =============================================================================

@mcp.tool(tags={'read', 'primary', 'suitecrm'})
async def get_record_relationships(
    module: str,
    id: str,
    link_field_name: str,
    include_all_fields: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Retrieve relationships for a specific record.

    Args:
        module: The module name of the record (e.g. Accounts, Contacts).
        id: The ID of the record to retrieve relationships for.
        link_field_name: The link field name defining the relationship.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.

    Returns:
        Dictionary containing the list of related records.
    """
    data = await get_client().get_record_relationships(
        get_user_token(), module, id, link_field_name, include_all_fields if ALLOW_ALL_AGGREGATE else False if ALLOW_ALL_AGGREGATE else False
    )
    return {"items": json_to_toon(data)}


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def create_record_relationship(
    module: str,
    id: str,
    related_module: str,
    related_id: str,
    link_field_name: str = "",
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new relationship between two records.

    Args:
        module: The module name of the primary record.
        id: The ID of the primary record.
        related_module: The module name of the related record.
        related_id: The ID of the related record.
        link_field_name: The link field name defining the relationship.

    Returns:
        Dictionary containing the result of the relationship creation.
    """
    return await get_client().create_record_relationship(
        get_user_token(), module, id, related_module, related_id, link_field_name
    )


@mcp.tool(tags={'write', 'primary', 'suitecrm'})
async def delete_record_relationship(
    module: str,
    id: str,
    link_field_name: str,
    related_id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete a relationship between two records.

    Args:
        module: The module name of the primary record.
        id: The ID of the primary record.
        link_field_name: The link field name defining the relationship.
        related_id: The ID of the related record to disconnect.

    Returns:
        Dictionary containing the result of the relationship deletion.
    """
    return await get_client().delete_record_relationship(
        get_user_token(), module, id, link_field_name, related_id
    )


# =============================================================================
# Entry Point
# =============================================================================

def main():
    base_url = os.getenv("SUITECRM_BASE_URL")
    if not base_url:
        print("ERROR: SUITECRM_BASE_URL environment variable is required", file=sys.stderr)
        print("Example: export SUITECRM_BASE_URL=http://suitecrm-nginx:80/Api/V8", file=sys.stderr)
        sys.exit(1)

    port_env = os.getenv("MCP_SERVER_PORT")
    if not port_env:
        print("ERROR: MCP_SERVER_PORT environment variable is required", file=sys.stderr)
        print("Example: export MCP_SERVER_PORT=80", file=sys.stderr)
        sys.exit(1)

    host = "0.0.0.0"
    port = int(port_env)
    path = "/mcp"
    if IS_STATEFUL:
        app = mcp.http_app(path=path, json_response=True)
    else:
        app = mcp.http_app(path=path, json_response=True, stateless_http=True)
    app = AuthMiddleware(app)
    print(f"Starting SuiteCRM MCP server on http://{host}:{port}{path}")

    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

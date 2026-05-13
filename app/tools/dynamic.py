import json
import logging
import re
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from controller import ACIController
from models import CreateToolInput, GroupToolInput, NonFilterableToolInput

logger = logging.getLogger("ACIMCPServer")


def load_urls(file_path: str = "urls.json") -> List[Dict[str, Any]]:
    """Load and flatten endpoint definitions from urls.json."""
    try:
        with open(file_path, "r") as f:
            raw = json.load(f)
        endpoints: List[Dict[str, Any]] = []
        for item in raw:
            if "Group" in item:
                for ep in item["Endpoints"]:
                    ep["Group"] = item["Group"]
                    endpoints.append(ep)
            else:
                item["Group"] = "ungrouped"
                endpoints.append(item)
        return endpoints
    except Exception as e:
        logger.error(f"Failed to load urls.json: {e}")
        return []


def register_dynamic_tools(
    mcp: FastMCP,
    controller: ACIController,
    urls: List[Dict[str, Any]],
) -> None:
    """Register all tools derived from urls.json onto the mcp server."""
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    ungrouped: List[Dict[str, Any]] = []

    for entry in urls:
        group = entry.get("Group", "ungrouped")
        if group == "ungrouped":
            ungrouped.append(entry)
        else:
            grouped.setdefault(group, []).append(entry)

    _register_grouped(mcp, controller, grouped)
    _register_ungrouped(mcp, controller, ungrouped)


# ── Private helpers ────────────────────────────────────────────────────────────

def _register_grouped(
    mcp: FastMCP,
    controller: ACIController,
    grouped: Dict[str, List[Dict[str, Any]]],
) -> None:
    for group, endpoints in grouped.items():
        choices = [e["URL"] for e in endpoints if e.get("URL")]

        def _make_tool(valid_endpoints: List[str], group_name: str):
            def group_tool(input: GroupToolInput) -> dict:
                if input.endpoint not in valid_endpoints:
                    raise ToolError(
                        f"Invalid endpoint for group '{group_name}'. "
                        f"Must be one of: {valid_endpoints}"
                    )
                args: Dict[str, Any] = {}
                if input.filter_expression:
                    args["query-target-filter"] = input.filter_expression
                if input.query_params:
                    args.update(input.query_params)
                return controller.get(input.endpoint, args)
            return group_tool

        tool_base = re.sub(r"[^a-z0-9_-]", "_", group.replace(" ", "_").lower())
        fn = _make_tool(choices, group)
        fn.__name__ = f"{tool_base}_get"
        fn.__doc__ = f"GET any endpoint from group '{group}' ({len(choices)} endpoints)."
        mcp.add_tool(fn)
        logger.info(f"Registered grouped tool: {fn.__name__} ({len(choices)} endpoints)")


def _register_ungrouped(
    mcp: FastMCP,
    controller: ACIController,
    ungrouped: List[Dict[str, Any]],
) -> None:
    for entry in ungrouped:
        name = entry.get("Name", "") or entry["URL"].split("/")[-1]
        endpoint = entry.get("URL")
        if not endpoint:
            logger.warning(f"Skipping entry with missing URL: {name}")
            continue

        tool_base = re.sub(r"[^a-z0-9_-]", "_", name.replace(" ", "_").lower())

        def _read(ep: str):
            def tool(params: NonFilterableToolInput = Field(default_factory=NonFilterableToolInput)) -> dict:
                return controller.get(ep, params.query_params or {})
            return tool

        def _post(ep: str):
            def tool(input: CreateToolInput) -> dict:
                return controller.post(ep, input.payload)
            return tool

        def _delete(ep: str):
            def tool(
                dn: Optional[str] = Field(
                    default=None,
                    description=(
                        "Distinguished name of the specific object to delete, "
                        "e.g. 'uni/tn-MyTenant/ap-MyAP/epg-MyEPG'. "
                        "When provided the request targets /api/node/mo/{dn}.json. "
                        "Omit only if deleting at the class-level endpoint."
                    ),
                )
            ) -> dict:
                target = f"/api/node/mo/{dn}.json" if dn else ep
                return controller.delete(target)
            return tool

        for suffix, factory in [("get", _read), ("post", _post), ("delete", _delete)]:
            fn = factory(endpoint)
            fn.__name__ = f"{tool_base}_{suffix}"
            fn.__doc__ = {
                "get": f"GET {name or endpoint} from ACI.",
                "post": f"POST (create) {name or endpoint} in ACI.",
                "delete": f"DELETE {name or endpoint} in ACI.",
            }[suffix]
            mcp.add_tool(fn)

        logger.info(f"Registered GET/POST/DELETE for: {name or endpoint}")

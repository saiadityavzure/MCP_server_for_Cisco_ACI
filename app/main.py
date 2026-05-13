from fastmcp import FastMCP

from config import APIC_URL, MCP_PORT, PASSWORD, URLS_PATH, USERNAME, setup_logging
from controller import ACIController
from tools.crud import register_crud_tools
from tools.dynamic import load_urls, register_dynamic_tools

logger = setup_logging()

if not APIC_URL or not USERNAME or not PASSWORD:
    logger.error("Missing required env vars: APIC_URL, USERNAME, PASSWORD")

controller = ACIController(APIC_URL, USERNAME, PASSWORD)

mcp = FastMCP(
    name="ACI MCP Server",
    instructions="Tools for full CRUD access to Cisco ACI API.",
)

urls = load_urls(URLS_PATH)
register_dynamic_tools(mcp, controller, urls)
register_crud_tools(mcp, controller)

if __name__ == "__main__":
    if not urls:
        logger.error("No tools registered — check URLS_PATH.")
    else:
        logger.info(f"Starting ACI MCP Server on SSE http://0.0.0.0:{MCP_PORT}/sse")
        mcp.run(transport="sse")

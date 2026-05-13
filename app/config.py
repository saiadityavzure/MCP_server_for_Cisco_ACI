import logging
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

APIC_URL: str = os.getenv("APIC_URL", "")
USERNAME: str = os.getenv("USERNAME", "")
PASSWORD: str = os.getenv("PASSWORD", "")
URLS_PATH: str = os.getenv("URLS_PATH", "urls.json")
MCP_PORT: int = int(os.getenv("MCP_PORT", "9050"))

# Third-party loggers that produce noise — kept at WARNING or above only
_SILENT_LOGGERS = [
    "httpcore", "httpx", "urllib3", "urllib3.connectionpool",
    "asyncio", "uvicorn", "uvicorn.access", "uvicorn.error",
    "starlette", "mcp", "mcp.server", "mcp.server.sse",
    "fastmcp", "multipart",
]


def setup_logging() -> logging.Logger:
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)

    debug_file = logging.FileHandler(os.path.join(log_dir, "aci_mcp_debug.log"))
    debug_file.setLevel(logging.DEBUG)
    debug_file.setFormatter(fmt)

    error_file = logging.FileHandler(os.path.join(log_dir, "aci_mcp_error.log"))
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(fmt)

    # Silence third-party loggers — must be done before any basicConfig call
    for name in _SILENT_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    # Root logger stays at WARNING so any unsilenced lib doesn't sneak through
    logging.getLogger().setLevel(logging.WARNING)

    # Our logger gets its own handlers and does NOT propagate to root
    logger = logging.getLogger("ACIMCPServer")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers.clear()
    logger.addHandler(console)
    logger.addHandler(debug_file)
    logger.addHandler(error_file)

    return logger

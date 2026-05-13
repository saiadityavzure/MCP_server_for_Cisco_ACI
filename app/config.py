import os
import logging
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

APIC_URL: str = os.getenv("APIC_URL", "")
USERNAME: str = os.getenv("USERNAME", "")
PASSWORD: str = os.getenv("PASSWORD", "")
URLS_PATH: str = os.getenv("URLS_PATH", "urls.json")
MCP_PORT: int = int(os.getenv("MCP_PORT", "9050"))


def setup_logging() -> logging.Logger:
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)

    debug_file = logging.FileHandler(os.path.join(log_dir, "aci_mcp_debug.log"))
    debug_file.setLevel(logging.DEBUG)
    debug_file.setFormatter(fmt)

    error_file = logging.FileHandler(os.path.join(log_dir, "aci_mcp_error.log"))
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(fmt)

    logging.basicConfig(level=logging.DEBUG, handlers=[console, debug_file, error_file])
    return logging.getLogger("ACIMCPServer")

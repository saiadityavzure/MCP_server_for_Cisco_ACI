import logging

from fastmcp import FastMCP

from controller import ACIController

logger = logging.getLogger("ACIMCPServer")


def register_crud_tools(mcp: FastMCP, controller: ACIController) -> None:
    """Register dedicated, human-friendly CRUD tools for common ACI objects."""

    @mcp.tool()
    def create_tenant(name: str, description: str = "") -> dict:
        """
        Create a new ACI tenant.

        Args:
            name: Tenant name (e.g. 'my-tenant')
            description: Optional description
        """
        payload = {
            "fvTenant": {
                "attributes": {
                    "name": name,
                    "descr": description,
                    "rn": f"tn-{name}",
                    "status": "created,modified",
                }
            }
        }
        logger.debug(f"Creating tenant '{name}'")
        result = controller.post("/api/node/mo/uni.json", payload)
        logger.info(f"Tenant '{name}' created")
        return result

    @mcp.tool()
    def delete_tenant(name: str) -> dict:
        """
        Delete an ACI tenant by name.

        Args:
            name: Tenant name to delete (e.g. 'my-tenant')
        """
        logger.debug(f"Deleting tenant '{name}'")
        result = controller.delete(f"/api/node/mo/uni/tn-{name}.json")
        logger.info(f"Tenant '{name}' deleted")
        return result

    @mcp.tool()
    def create_vrf(tenant_name: str, vrf_name: str, description: str = "") -> dict:
        """
        Create a VRF (context) inside an ACI tenant.

        Args:
            tenant_name: Name of the parent tenant
            vrf_name: VRF name
            description: Optional description
        """
        payload = {
            "fvCtx": {
                "attributes": {
                    "name": vrf_name,
                    "descr": description,
                    "rn": f"ctx-{vrf_name}",
                    "status": "created,modified",
                }
            }
        }
        logger.debug(f"Creating VRF '{vrf_name}' in tenant '{tenant_name}'")
        result = controller.post(f"/api/node/mo/uni/tn-{tenant_name}.json", payload)
        logger.info(f"VRF '{vrf_name}' created in tenant '{tenant_name}'")
        return result

    @mcp.tool()
    def create_bridge_domain(
        tenant_name: str,
        bd_name: str,
        vrf_name: str = "",
        description: str = "",
    ) -> dict:
        """
        Create a Bridge Domain inside an ACI tenant.

        Args:
            tenant_name: Name of the parent tenant
            bd_name: Bridge Domain name
            vrf_name: Optional VRF to associate with
            description: Optional description
        """
        children = []
        if vrf_name:
            children.append({
                "fvRsCtx": {
                    "attributes": {"tnFvCtxName": vrf_name, "status": "created,modified"}
                }
            })
        payload = {
            "fvBD": {
                "attributes": {
                    "name": bd_name,
                    "descr": description,
                    "rn": f"BD-{bd_name}",
                    "status": "created,modified",
                },
                "children": children,
            }
        }
        logger.debug(f"Creating BD '{bd_name}' in tenant '{tenant_name}'")
        result = controller.post(f"/api/node/mo/uni/tn-{tenant_name}.json", payload)
        logger.info(f"Bridge Domain '{bd_name}' created in tenant '{tenant_name}'")
        return result

    @mcp.tool()
    def create_application_profile(
        tenant_name: str,
        ap_name: str,
        description: str = "",
    ) -> dict:
        """
        Create an Application Profile inside an ACI tenant.

        Args:
            tenant_name: Name of the parent tenant
            ap_name: Application Profile name
            description: Optional description
        """
        payload = {
            "fvAp": {
                "attributes": {
                    "name": ap_name,
                    "descr": description,
                    "rn": f"ap-{ap_name}",
                    "status": "created,modified",
                }
            }
        }
        logger.debug(f"Creating AP '{ap_name}' in tenant '{tenant_name}'")
        result = controller.post(f"/api/node/mo/uni/tn-{tenant_name}.json", payload)
        logger.info(f"Application Profile '{ap_name}' created in tenant '{tenant_name}'")
        return result

    @mcp.tool()
    def create_epg(
        tenant_name: str,
        ap_name: str,
        epg_name: str,
        bd_name: str = "",
        description: str = "",
    ) -> dict:
        """
        Create an Endpoint Group (EPG) inside an Application Profile.

        Args:
            tenant_name: Name of the parent tenant
            ap_name: Application Profile name
            epg_name: EPG name
            bd_name: Optional Bridge Domain to bind to
            description: Optional description
        """
        children = []
        if bd_name:
            children.append({
                "fvRsBd": {
                    "attributes": {"tnFvBDName": bd_name, "status": "created,modified"}
                }
            })
        payload = {
            "fvAEPg": {
                "attributes": {
                    "name": epg_name,
                    "descr": description,
                    "rn": f"epg-{epg_name}",
                    "status": "created,modified",
                },
                "children": children,
            }
        }
        logger.debug(f"Creating EPG '{epg_name}' in AP '{ap_name}' tenant '{tenant_name}'")
        result = controller.post(
            f"/api/node/mo/uni/tn-{tenant_name}/ap-{ap_name}.json", payload
        )
        logger.info(f"EPG '{epg_name}' created in AP '{ap_name}' tenant '{tenant_name}'")
        return result

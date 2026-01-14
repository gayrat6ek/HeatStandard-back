import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from app.config import settings
from app.utils.exceptions import IikoAPIError


logger = logging.getLogger(__name__)


class IikoService:
    """Service for interacting with iiko Cloud API."""
    
    def __init__(self):
        self.base_url = settings.iiko_api_base_url
        self.transport_key = settings.iiko_transport_key
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
    async def _get_access_token(self) -> str:
        """
        Get access token from iiko API.
        Caches token and refreshes when expired.
        
        Returns:
            str: Access token
            
        Raises:
            IikoAPIError: If authentication fails
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        url = f"{self.base_url}/api/1/access_token"
        payload = {"apiLogin": self.transport_key}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                
                if response.status_code != 200:
                    raise IikoAPIError(
                        f"Failed to get access token: {response.text}",
                        status_code=response.status_code
                    )
                
                data = response.json()
                self._access_token = data.get("token")
                
                if not self._access_token:
                    raise IikoAPIError("No token in response")
                
                # Set token expiration (typically 60 minutes, we'll use 50 to be safe)
                self._token_expires_at = datetime.utcnow() + timedelta(minutes=50)
                
                logger.info("Successfully obtained iiko access token")
                return self._access_token
                
        except httpx.RequestError as e:
            logger.error(f"Request error while getting access token: {e}")
            raise IikoAPIError(f"Request failed: {str(e)}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to iiko API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Dict: Response data
            
        Raises:
            IikoAPIError: If request fails
        """
        token = await self._get_access_token()
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=60.0
                )
                
                if response.status_code not in [200, 201]:
                    raise IikoAPIError(
                        f"API request failed: {response.text}",
                        status_code=response.status_code
                    )
                
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise IikoAPIError(f"Request failed: {str(e)}")
    
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """
        Get all organizations accessible to the API user.
        
        Returns:
            List[Dict]: List of organizations
        """
        logger.info("Fetching organizations from iiko")
        
        data = await self._make_request(
            method="POST",
            endpoint="/api/1/organizations",
            data={"returnAdditionalInfo": True}
        )
        
        organizations = data.get("organizations", [])
        logger.info(f"Retrieved {len(organizations)} organizations")
        return organizations
    
    async def get_nomenclature(self, organization_id: str) -> Dict[str, Any]:
        """
        Get nomenclature (products/menu) for a single organization.
        
        Args:
            organization_id: Single organization ID
            
        Returns:
            Dict: Nomenclature data with groups and products
        """
        logger.info(f"Fetching nomenclature for organization {organization_id}")
        
        data = await self._make_request(
            method="POST",
            endpoint="/api/1/nomenclature",
            data={"organizationId": organization_id}
        )
        
        logger.info("Successfully retrieved nomenclature")
        return data
    
    async def get_terminal_groups(self, organization_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get terminal groups for organizations (includes restaurant sections).
        
        Args:
            organization_ids: List of organization IDs
            
        Returns:
            List[Dict]: Terminal groups data
        """
        logger.info(f"Fetching terminal groups for {len(organization_ids)} organizations")
        
        data = await self._make_request(
            method="POST",
            endpoint="/api/1/terminal_groups",
            data={"organizationIds": organization_ids}
        )
        
        terminal_groups = data.get("terminalGroups", [])
        logger.info(f"Retrieved {len(terminal_groups)} terminal groups")
        return terminal_groups
    
    async def get_available_restaurant_sections(
        self,
        terminal_group_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get available restaurant sections (tables) for terminal groups.
        
        Args:
            terminal_group_ids: List of terminal group IDs
            
        Returns:
            List[Dict]: Restaurant sections with table information
        """
        logger.info(f"Fetching restaurant sections for {len(terminal_group_ids)} terminal groups")
        
        payload = {
            "terminalGroupIds": terminal_group_ids
        }
        
        data = await self._make_request(
            method="POST",
            endpoint="/api/1/reserve/available_restaurant_sections",
            data=payload
        )
        
        sections = data.get("restaurantSections", [])
        logger.info(f"Retrieved {len(sections)} restaurant sections")
        return sections
    
    async def create_delivery_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create delivery order in iiko.
        
        Args:
            order_data: Order data in iiko format
            
        Returns:
            Dict: Created order response
        """
        logger.info("Creating delivery order in iiko")
        
        response = await self._make_request(
            method="POST",
            endpoint="/api/1/deliveries/create",
            data=order_data
        )
        
        logger.info(f"Successfully created order: {response.get('orderInfo', {}).get('id')}")
        return response


# Global service instance
iiko_service = IikoService()

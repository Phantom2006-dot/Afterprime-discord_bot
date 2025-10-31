from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BasePlatform(ABC):
    @abstractmethod
    def get_auth_url(self, state: str) -> str:
        pass
    
    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def publish_post(
        self, 
        access_token: str, 
        content: str, 
        media_urls: Optional[list] = None,
        platform_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_post_metrics(self, access_token: str, post_id: str) -> Dict[str, Any]:
        pass

from typing import Dict, Optional

from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(self, tokenUrl: str, scheme_name: Optional[str] = None, scopes: Optional[Dict[str, str]] = None, auto_error: bool = True):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str] | None:
        # Get the `token` from the request's cookies:
        token: str = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(token)

        if not token or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Not authorized",
                    headers={},
                )
            else:
                return None
        return param

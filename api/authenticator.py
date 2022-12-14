from http import HTTPStatus

from fastapi import Depends
from fastapi.security import HTTPBasicCredentials, HTTPBearer

from modules.exceptions import APIResponse
from modules.models import models

security = HTTPBearer()


async def offline_has_access(token: HTTPBasicCredentials = Depends(security)) -> None:
    """Validates the token if mentioned as a dependency.

    Args:
        token: Takes the authorization header token as an argument.
    """
    auth = token.dict().get('credentials', '')
    if auth.startswith('\\'):
        auth = bytes(auth, "utf-8").decode(encoding="unicode_escape")
    if auth == models.env.offline_pass:
        return
    raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real, detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])


async def robinhood_has_access(token: HTTPBasicCredentials = Depends(security)) -> None:
    """Validates the token if mentioned as a dependency.

    Args:
        token: Takes the authorization header token as an argument.
    """
    auth = token.dict().get('credentials')
    if auth.startswith('\\'):
        auth = bytes(auth, "utf-8").decode(encoding="unicode_escape")
    if auth == models.env.robinhood_endpoint_auth:
        return
    raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real, detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])

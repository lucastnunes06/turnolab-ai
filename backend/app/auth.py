import hmac
import os
from dataclasses import dataclass
from typing import Annotated
from fastapi import Depends, Header, HTTPException

@dataclass(frozen=True)
class Principal:
    actor: str
    restaurants: frozenset[int]
    reviewer: bool = False

async def authenticate(authorization: Annotated[str | None, Header()]=None):
    tokens = [(os.getenv('DEMO_TOKEN', 'turnolab-demo'), Principal('demo-operator', frozenset(range(1, 21)), True)), (os.getenv('DEMO_OTHER_TOKEN', 'turnolab-other'), Principal('tenant-2', frozenset([2]), True)), (os.getenv('ADMIN_TOKEN', 'turnolab-reviewer'), Principal('human-reviewer', frozenset(range(1, 21)), True))]
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Bearer token required')
    value = authorization.removeprefix('Bearer ')
    if not value:
        raise HTTPException(401, 'Bearer token required')
    for token, principal in tokens:
        if hmac.compare_digest(value.encode(), token.encode()):
            return principal
    raise HTTPException(401, 'Invalid token')
User = Annotated[Principal, Depends(authenticate)]

def authorize(user: Principal, restaurant_id: int):
    if restaurant_id not in user.restaurants:
        raise HTTPException(403, 'Restaurant outside authorized scope')

from synology_api.universal_search import UniversalSearch

from .config import settings
from .auth import require_token_auth
from fastapi.routing import APIRouter
from fastapi import Depends

search_router = APIRouter(
    prefix="/search",
    tags=["搜索管理"],
    dependencies=[Depends(require_token_auth)]  # 全局应用 Token 鉴权
)


search = UniversalSearch(settings.dsm_host,settings.dsm_port,settings.nas_user, settings.nas_password)

@search_router.get("/")
async def search_items(query: str):
    return search.search(query)
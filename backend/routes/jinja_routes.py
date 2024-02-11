from fastapi import APIRouter, Request, status
from fastapi.templating import Jinja2Templates

from backend.config.constants import API_PREFIX

jinja_router = APIRouter(
    prefix=f"/jinja",
    tags=["jinja2-template test routes"],
)

templates = Jinja2Templates(directory="frontend/templates")

MA_LIST = [
    {
        "name": "Lemon Sour Diesel",
        "terps": "TOM",
    },
    {
        "name": "Cherry Do-Si-Dos",
        "terps": "CLH",
    },
]


@jinja_router.get("/")
async def name(request: Request, name: str = "Sample Person"):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "name": name,
        "buds": MA_LIST,
    })

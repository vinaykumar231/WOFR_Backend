from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from db.session import Base, engine,get_db
from api.v1.models import rbac
from api.v1.models import tenants
from api.v1.models import user
from api.v1.endpoints.user import user_router, google_router
from api.v1.endpoints.settings import setting_router
from api.v1.endpoints.rbac import module_router
from api.v1.endpoints.rbac import action_router
from api.v1.endpoints.rbac import role_router
from api.v1.endpoints.rbac import role_module_action_mapping_router
from api.v1.endpoints.rbac import user_role_assignment_router
from api.v1.endpoints.tenants import tenant_router
Base.metadata.create_all(bind=engine)

app = FastAPI()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = FastAPI.openapi(app)  
    openapi_schema["info"]["title"] = "WOFR Backend"
    openapi_schema["info"]["version"] = "1.1.0"
    openapi_schema["info"]["description"] = "This API serves as the backend for WOFR."
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(setting_router, prefix="/api", tags=["Settings"])
app.include_router(user_router, prefix="/api", tags=["User Auth"])
app.include_router(google_router, prefix="/api", tags=["Google Auth"])
app.include_router(tenant_router, prefix="/api", tags=["tenant management"])
app.include_router(module_router, prefix="/api", tags=["Module management"])
app.include_router(action_router, prefix="/api", tags=["Actions management"])
app.include_router(role_router, prefix="/api", tags=["Roles management"])
app.include_router(role_module_action_mapping_router, prefix="/api", tags=["Role module action mapping management"])
app.include_router(user_role_assignment_router, prefix="/api", tags=["User role assignment management"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8001, reload= True, host="0.0.0.0")
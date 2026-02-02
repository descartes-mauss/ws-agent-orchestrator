from fastapi import APIRouter, Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from database.manager import get_all
from database.models.public_models import Client
from database.models.tenant_models import SOW
from jwt_validator import validate_jwt

app = FastAPI()

router = APIRouter(prefix="/api", dependencies=[Depends(validate_jwt)])


@app.get("/")
def read_root():
    clients: list[Client] = get_all(Client)
    print(f"Total number of clients {len(clients)}")
    return JSONResponse(status_code=200, content=jsonable_encoder({"clients": clients}))


@app.get("/api/error")
def base():
    return JSONResponse(status_code=500, content={"status": "Error endpoint"})


@app.post("/api/protected")
def protected(authorization: dict = Depends(validate_jwt)):
    org_id = authorization.get("orgId")
    clients: list[Client] = get_all(Client)
    print(f"Total number of clients {len(clients)}")
    sows: list[SOW] = get_all(SOW, tenant_schema=org_id)
    print(f"Total number of SOWs {len(sows)}")
    return JSONResponse(
        status_code=200, content=jsonable_encoder({"clients": clients, "sows": sows})
    )

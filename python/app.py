from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routes import router
from openapi import register_openapi


def create_app():
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url="/openapi.json")

    # CORS: 모든 출처 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # startup: init db
    app.add_event_handler("startup", init_db)

    # register openapi routes and custom schema
    register_openapi(app)

    return app

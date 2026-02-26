import os
import yaml
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import PlainTextResponse, HTMLResponse

BASE_DIR = os.path.dirname(__file__)
OPENAPI_YAML = os.path.abspath(os.path.join(BASE_DIR, "..", "openapi.yaml"))


def load_openapi_schema():
    with open(OPENAPI_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def register_openapi(app):
    _openapi_schema = {"schema": None}

    @app.get("/openapi.yaml", response_class=PlainTextResponse)
    def openapi_yaml():
        with open(OPENAPI_YAML, "r", encoding="utf-8") as f:
            return f.read()

    @app.get("/", response_class=HTMLResponse)
    def root_swagger():
        return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")

    def custom_openapi():
        if _openapi_schema["schema"] is not None:
            return _openapi_schema["schema"]
        _openapi_schema["schema"] = load_openapi_schema()
        return _openapi_schema["schema"]

    app.openapi = custom_openapi

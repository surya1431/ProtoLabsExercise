from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="3D Box Packing Service",
        description="Calculates shipping boxes required for rectangular packages.",
        version="1.0.0",
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_request",
                    "message": "Request payload failed validation.",
                    "details": exc.errors(),
                }
            },
        )

    app.include_router(router)
    return app


app = create_app()
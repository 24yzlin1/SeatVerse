from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.scope.common import error_handler, ok
from app.types.common import ResponsePayload

app = FastAPI(title="SeatVerse")
app.add_exception_handler(Exception, error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()


@router.get("/")
def health() -> ResponsePayload[str]:
    return ok("Hello from SeatVerse!")


app.include_router(router)


def main():
    print("Hello from seat-verse!")


if __name__ == "__main__":
    main()

from contextlib import asynccontextmanager
import dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.common import AppError
from app.scope.common import error_handler, ok
from app.types.common import ResponsePayload
from app.scope.authentication import router as authentication_router
from app.scope.bookings import router as bookings_router
from app.scope.events import router as events_router
from app.scope.seats import router as seats_router
from app.scope.venues import router as venues_router
from app.repos.database import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


dotenv.load_dotenv()
router = APIRouter()
app = FastAPI(title="SeatVerse", lifespan=lifespan)
app.add_exception_handler(AppError, error_handler)
app.add_exception_handler(Exception, error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@router.get("/")
def health() -> ResponsePayload[str]:
    return ok("Hello from SeatVerse!")


api_router = APIRouter(prefix="/api")
api_router.include_router(router, tags=["health"])
api_router.include_router(authentication_router, tags=["authentication"])
api_router.include_router(events_router, tags=["events"])
api_router.include_router(bookings_router, tags=["bookings"])
api_router.include_router(seats_router, tags=["seats"])
api_router.include_router(venues_router, tags=["venues"])
app.include_router(api_router)


def main():
    print("Hello from seat-verse!")


if __name__ == "__main__":
    main()

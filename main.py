from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from database import engine, Base
from routers import auth, users, admin, mock_resources

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Custom Authentication & Authorization System",
    description="""
    Собственная система аутентификации и авторизации на FastAPI.
    
    Основные возможности:
    
    Аутентификация**: Регистрация, вход, выход из системы
    Управление пользователями**: Обновление профиля, удаление аккаунта
    Авторизация на основе ролей (RBAC)**: Гибкая система разграничения прав доступа
    Управление разрешениями**: API для администраторов
    Демонстрационные ресурсы**: Mock объекты для тестирования системы прав
    
    Аутентификация
    
    Система использует JWT токены для аутентификации. После входа токен должен 
    передаваться в заголовке Authorization: Bearer {token}
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"}
    )


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(mock_resources.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Custom Authentication & Authorization System API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


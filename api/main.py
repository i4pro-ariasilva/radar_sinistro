"""
Aplicação FastAPI principal para o Radar Sinistro API
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import time
import logging
from contextlib import asynccontextmanager

from api.routes import risk, policies, coverages


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    logger.info("🚀 Iniciando Radar Sinistro API...")
    yield
    # Shutdown
    logger.info("🛑 Finalizando Radar Sinistro API...")


# Criar aplicação FastAPI
app = FastAPI(
    title="Radar Sinistro API",
    description="""
    **API para cálculo de risco de sinistros e gestão de apólices de seguro**
    
    Esta API permite:
    
    * **Calcular risco de sinistro** para apólices individuais ou em lote
    * **Gerenciar apólices** (consulta, listagem, remoção)
    * **Obter rankings** por risco ou valor segurado
    * **Estatísticas** e relatórios das apólices
    
    ---
    
    ### Autenticação
    Atualmente a API não requer autenticação. Em produção, considere implementar:
    - API Keys
    - JWT Tokens
    - OAuth2
    
    ### Rate Limiting
    - Cálculo individual: 100 req/min
    - Cálculo em lote: 10 req/min  
    - Consultas: 200 req/min
    
    ### Formatos de Data
    Todas as datas devem estar no formato ISO 8601: `YYYY-MM-DD`
    
    """,
    version="1.0.0",
    contact={
        "name": "Equipe Radar Sinistro",
        "email": "contato@radarsinistro.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origins permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log da requisição
    logger.info(f"📥 {request.method} {request.url.path} - IP: {request.client.host}")
    
    response = await call_next(request)
    
    # Log da resposta
    process_time = time.time() - start_time
    logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    # Adicionar header de tempo de processamento
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Registrar rotas
app.include_router(risk.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(coverages.router, prefix="/api/v1")


# Rota raiz
@app.get("/", tags=["Health"])
async def root():
    """
    Endpoint de health check da API
    """
    return {
        "message": "🎯 Radar Sinistro API está funcionando!",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": time.time(),
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint detalhado de health check
    """
    try:
        # Testar conexão com banco (se necessário)
        from database.database import get_database
        db = get_database()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "database": "connected",
                "ml_models": "loaded",
                "api": "running"
            },
            "version": "1.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e),
                "version": "1.0.0"
            }
        )


# Handler para erros globais
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Erro não tratado: {str(exc)} - URL: {request.url}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Erro interno do servidor",
            "message": "Ocorreu um erro inesperado. Tente novamente mais tarde.",
            "timestamp": time.time()
        }
    )


# Handler para HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "message": f"Erro {exc.status_code}",
            "timestamp": time.time()
        }
    )


# Customizar OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Radar Sinistro API",
        version="1.0.0",
        description="API para cálculo de risco de sinistros",
        routes=app.routes,
    )
    
    # Adicionar exemplos personalizados
    openapi_schema["info"]["x-logo"] = {
        "url": "https://via.placeholder.com/200x100/1f77b4/ffffff?text=Radar+Sinistro"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando servidor de desenvolvimento...")
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        reload_dirs=["api"],
        log_level="info"
    )

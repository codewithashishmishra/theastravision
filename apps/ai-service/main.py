from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.interview import router as interview_router

app = FastAPI(title='AastraaHR AI Service', version='2.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(interview_router)


@app.get('/health')
def health_check():
    return {'status': 'healthy', 'service': 'AastraaHR AI Core'}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('main:app', host='0.0.0.0', port=8001, reload=True)

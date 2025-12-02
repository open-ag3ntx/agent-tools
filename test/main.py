from fastapi import FastAPI

app = FastAPI()

@app.get("/greet")
async def greet():
    return {"message": "Hello, World!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

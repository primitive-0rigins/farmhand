from fastapi import FastAPI

app = FastAPI(title="Farmhand")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

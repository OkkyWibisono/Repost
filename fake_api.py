from fastapi import FastAPI, HTTPException

app = FastAPI()
TASK_QUEUE = []


@app.post("/tasks")
def queue_task(task: dict):
    task.setdefault("enabled", True)
    TASK_QUEUE.append(task)
    print(f"[QUEUED] {task}")
    return {"status": "queued"}


@app.get("/tasks")
def get_task():
    if TASK_QUEUE:
        return TASK_QUEUE.pop(0)
    raise HTTPException(404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8888)

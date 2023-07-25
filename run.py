import uvicorn

if __name__ == '__main__':
    # Start with reloading enabled (must be string to work)
    uvicorn.run("abotcore:create_coreapp", host='localhost',
                port=8000, factory=True, reload=True)

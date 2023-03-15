import uvicorn

if __name__ == '__main__':
    # Start with reloading enabled (must be string to work)
    uvicorn.run("rasabackend:create_app", host='localhost', port=8000, reload=True)

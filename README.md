# Abot backend server

## Usage

1. Install requirements

```bash
pip install -r requirements.txt
```

2. Set environments (.env method)
```env
ENDPOINTS_FILE=endpoints.dev.yml
MODEL_PATH=<Path to the trained model, only set when endpoints does not set the path.>
CREDENTIALS_FILE=credentials.yml
TELEGRAM_BOT_TOKEN=<Your Telegram bot token (if enabled in credentials)>
```

3. Run development server:
```bash
python run.py
```

## Docker deployment

1. Build docker image
  - Development server
  ```bash
  docker build -t abot/backend .
  ```

  - Production
  ```bash
  docker build -t abot/backend -f Dockerfile.prod .
  ```

2. Run the image
```bash
docker run --name abot_backend_1 -d -p 8080:8080 abot/backend
```

*Note*: Optionally, you can set the environment variables `PORT` and `LOG_LEVEL` before running the image.

# Run the Abot backend server
FROM python:3.9

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

# Endpoints config file to use
ENV ENDPOINTS_FILE=endpoints.prod.yml

CMD ["uvicorn", "abotcore:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
# Run the Abot backend server
FROM python:3.9

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

CMD ["uvicorn", "abotcore:create_coreapp", "--host", "0.0.0.0", "--port", "8000", "--factory"]

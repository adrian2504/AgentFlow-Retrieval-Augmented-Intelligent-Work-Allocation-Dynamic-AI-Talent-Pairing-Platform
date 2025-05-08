FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy code into a real package directory
COPY . /app/backend

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# run as package
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.10-slim

WORKDIR /code

COPY requirements.txt /code/

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
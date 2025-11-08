FROM python:3.12-slim

WORKDIR /app

# Sistema
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Fonte
COPY . .

EXPOSE 3000

CMD ["python", "manage.py", "runserver", "0.0.0.0:3000"]

FROM python:3.13-slim

WORKDIR /app

# Copia solo requirements primero (aprovecha cache de Docker en rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto (app, alembic, tests, etc.)
COPY . .

# Comando por defecto: abre una shell dentro del contenedor
CMD ["bash"]

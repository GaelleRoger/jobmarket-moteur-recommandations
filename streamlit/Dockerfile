FROM python:3.12-slim

WORKDIR /app

# Installation des dépendances système légères
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements spécifiques à l'interface
COPY streamlit/requirements_streamlit.txt .

# Installation des packages (streamlit, pandas, plotly, requests) 
RUN pip install --no-cache-dir -r requirements_streamlit.txt

# Copie du code source nécessaire
# On remonte d'un cran pour prendre le dossier src global
COPY src ./src

EXPOSE 8501

# L'URL de l'API pointera vers le nom du service défini dans docker-compose
ENV API_BASE_URL=http://api:8000
ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "src/api/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
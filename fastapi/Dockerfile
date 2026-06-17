# Stage 1: Build
FROM python:3.12 as builder
WORKDIR /app
COPY fastapi/requirements_api.txt .
# Install PyTorch CPU wheel from the official PyTorch index first (torch+cpu isn't on PyPI)
RUN pip install --user --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1+cpu \
    && pip install --user --no-cache-dir -r requirements_api.txt

# Stage 2: Runtime (léger)
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
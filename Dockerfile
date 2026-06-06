# Dockerfile

# --------------------------------------------------
# 1. Base image — slim = smaller size, no extras
# --------------------------------------------------
FROM python:3.11-slim

# --------------------------------------------------
# 2. Set working directory inside container
#    all commands run from here
# --------------------------------------------------
WORKDIR /app

# --------------------------------------------------
# 3. Install UV inside container
# --------------------------------------------------
RUN pip install uv

# --------------------------------------------------
# 4. Copy dependency files FIRST
#    Docker caches this layer — if pyproject.toml
#    doesn't change, deps are not reinstalled on rebuild
#    This saves huge time during development
# --------------------------------------------------
COPY pyproject.toml uv.lock ./

# --------------------------------------------------
# 5. Install dependencies using UV
#    --system = install into system python, not venv
#    --frozen = use exact versions from uv.lock
# --------------------------------------------------
RUN uv sync --frozen --no-dev

# --------------------------------------------------
# 6. Copy rest of the project code
#    done after deps so code changes don't
#    trigger full dependency reinstall
# --------------------------------------------------
COPY . .

# --------------------------------------------------
# 7. Expose port 8000 for FastAPI
# --------------------------------------------------
EXPOSE 8000

# --------------------------------------------------
# 8. Start FastAPI server
#    host 0.0.0.0 = accessible outside container
#    reload = auto restart on code changes
# --------------------------------------------------
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
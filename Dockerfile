# =========================
# Build stage
# =========================
FROM python:3.12.3 AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    patchelf \
    && rm -rf /var/lib/apt/lists/*

# Clone application
RUN git clone https://github.com/yanufo/RoW-App.git.

COPY requirements.txt .

# Install all application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Nuitka
RUN pip install --no-cache-dir nuitka


# =========================
# Compile application modules
# =========================

RUN mkdir -p /build/compiled/ui
RUN mkdir -p /build/compiled/sql_tool
RUN mkdir -p /build/compiled/services


# -------------------------
# UI
# -------------------------

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/ui \
    ui/upload.py

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/ui \
    ui/download.py

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/ui \
    ui/ui_tools.py

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/ui \
    ui/preview.py

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/ui \
    ui/drone_model.py

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/ui \
    ui/usagi_model.py


# -------------------------
# SQL
# -------------------------

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/sql_tool \
    sql_tool/connection.py

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/sql_tool \
    sql_tool/queries.py


# -------------------------
# Services
# -------------------------

RUN python -m nuitka \
    --module \
    --output-dir=/build/compiled/services \
    services/report_service.py


# =========================
# Runtime stage
# =========================
FROM python:3.12.3-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*


# =========================
# Python dependencies
# =========================

COPY --from=builder /build/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# =========================
# 3D Models
# =========================

COPY --from=builder /build/models /app/models


# =========================
# Streamlit entrypoint
# =========================

COPY --from=builder /build/app_prototype.py /app/app_prototype.py

COPY --from=builder /build/pages /app/pages

COPY --from=builder /build/.streamlit /app/.streamlit




# =========================
# Application assets
# =========================

COPY --from=builder /build/images /app/images

RUN mkdir -p /app/inspection

COPY --from=builder /build/inspection/config.yml /app/inspection/config.yml

# =========================
# Compiled UI modules
# =========================

RUN mkdir -p /app/ui

COPY --from=builder /build/compiled/ui/ /app/ui/


# =========================
# Compiled SQL modules
# =========================

RUN mkdir -p /app/sql_tool

COPY --from=builder /build/compiled/sql_tool/ /app/sql_tool/


# =========================
# Compiled services
# =========================

RUN mkdir -p /app/services

COPY --from=builder /build/compiled/services/ /app/services/


# =========================
# Package markers
# =========================

RUN touch /app/ui/__init__.py
RUN touch /app/sql_tool/__init__.py
RUN touch /app/services/__init__.py


# =========================
# Streamlit
# =========================

EXPOSE 8501

HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=30s \
    --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "/app/app_prototype.py", "--server.port=8501", "--server.address=0.0.0.0"]
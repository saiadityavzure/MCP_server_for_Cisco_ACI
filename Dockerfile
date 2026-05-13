FROM python:3.13-slim-bookworm
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
ENV PYTHONUNBUFFERED=1
ARG MCP_PORT=9050
EXPOSE ${MCP_PORT}
CMD ["python", "-u", "main.py"]

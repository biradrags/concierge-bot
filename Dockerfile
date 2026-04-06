FROM python:3.12 as builder
WORKDIR /app
COPY pyproject.toml .
COPY bali_concierge bali_concierge
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --no-cache-dir -e .

FROM python:3.12-slim
WORKDIR /app
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=builder /app/bali_concierge bali_concierge
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
CMD ["python3", "-m", "bali_concierge"]

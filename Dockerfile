FROM python:3.11-slim

WORKDIR /app

# 1. Устанавливаем системные инструменты и Node.js (пока мы ROOT)
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 2. Обновляем пип
RUN pip install --upgrade pip

# 3. Копируем файлы проекта
COPY pyproject.toml ./
COPY src/ ./src/
COPY modules/ ./modules/

# 4. Устанавливаем зависимости Python
RUN pip install -e .

# 5. Создаем пользователя и настраиваем права
RUN addgroup --system --gid 1001 ytaimbot \
 && adduser  --system --uid 1001 --ingroup ytaimbot --no-create-home ytaimbot \
 && mkdir -p /data \
 && chown -R ytaimbot:ytaimbot /app /data

# Переключаемся на обычного пользователя для безопасности
USER ytaimbot

ENTRYPOINT ["python", "-m", "modules.orchestrator"]
FROM python:3.11-slim

WORKDIR /app

# 1. РЈСЃС‚Р°РЅР°РІР»РёРІР°РµРј СЃРёСЃС‚РµРјРЅС‹Рµ РёРЅСЃС‚СЂСѓРјРµРЅС‚С‹ Рё Node.js (РїРѕРєР° РјС‹ ROOT)
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 2. РћР±РЅРѕРІР»СЏРµРј РїРёРї
RUN pip install --upgrade pip

# 3. РљРѕРїРёСЂСѓРµРј С„Р°Р№Р»С‹ РїСЂРѕРµРєС‚Р°
COPY pyproject.toml ./
COPY src/ ./src/
COPY modules/ ./modules/

# 4. РЈСЃС‚Р°РЅР°РІР»РёРІР°РµРј Р·Р°РІРёСЃРёРјРѕСЃС‚Рё Python
RUN pip install -e ".[dev]"

# 5. РЎРѕР·РґР°РµРј РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ Рё РЅР°СЃС‚СЂР°РёРІР°РµРј РїСЂР°РІР°
RUN addgroup --system --gid 1001 ytaimbot \
 && adduser  --system --uid 1001 --ingroup ytaimbot --no-create-home ytaimbot \
 && mkdir -p /data \
 && chown -R ytaimbot:ytaimbot /app /data

# РџРµСЂРµРєР»СЋС‡Р°РµРјСЃСЏ РЅР° РѕР±С‹С‡РЅРѕРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РґР»СЏ Р±РµР·РѕРїР°СЃРЅРѕСЃС‚Рё
USER ytaimbot

ENTRYPOINT ["python", "-m", "modules.orchestrator"]

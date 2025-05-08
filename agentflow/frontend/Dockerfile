FROM node:20-bullseye-slim
WORKDIR /app

# ---------- copy source ----------
COPY . .

# ---------- install (with a bug‑free npm) ----------
RUN npm install -g npm@11.3.0  \   
 && npm ci --no-audit --no-fund \
 && npm rebuild esbuild

# ---------- build ----------
RUN npm run build

EXPOSE 4173
CMD ["npm","run","preview","--","--port","4173","--host","0.0.0.0"]

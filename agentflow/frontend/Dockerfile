FROM node:20-bullseye-slim
WORKDIR /app

COPY package.json ./

# single install; --omit=optional skips native rollup binaries
RUN npm install --omit=optional

# force pure‑JS rollup and remove any native folders
RUN npm install --save-dev rollup@4 \
 && find node_modules -type d -name "@rollup" -path "*-linux-*-*" -prune -exec rm -rf {} +

RUN npm rebuild esbuild
COPY . .
RUN npm run build

EXPOSE 4173
CMD ["npm","run","preview","--","--port","4173","--host","0.0.0.0"]

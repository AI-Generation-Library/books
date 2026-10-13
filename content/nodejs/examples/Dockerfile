FROM node:24.18.0-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts && mkdir -p /app/var/uploads && chown node:node /app/var/uploads
COPY --chown=node:node src ./src
COPY --chown=node:node migrations ./migrations
ENV NODE_ENV=production HOST=0.0.0.0
USER node
EXPOSE 3000
CMD ["node", "src/main.mjs"]

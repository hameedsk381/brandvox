FROM oven/bun:1.2 AS base

WORKDIR /app

COPY package*.json ./
RUN bun install

COPY . .
RUN bun run build

FROM oven/bun:1.2 AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

COPY --from=base /app/.next/standalone ./
COPY --from=base /app/.next/static ./.next/static
COPY --from=base /app/public ./public

EXPOSE 3000

CMD ["bun", "server.js"]

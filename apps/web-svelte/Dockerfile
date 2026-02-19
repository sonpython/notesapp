FROM oven/bun:1 AS builder
WORKDIR /app

# Copy package files
COPY package.json bun.lock* ./

# Install dependencies
RUN bun install

# Copy source
COPY . .

# Build the app (uses relative URLs, no env vars needed)
RUN bun run build

# Production image
FROM oven/bun:1-slim
WORKDIR /app

# Copy built app
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./

# Install only production deps
RUN bun install --production

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Run the app
ENV NODE_ENV=production
CMD ["bun", "./build"]

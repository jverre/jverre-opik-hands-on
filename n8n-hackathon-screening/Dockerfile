# n8n plus the Opik OpenTelemetry hooks.
#
# n8n-observability registers lifecycle hooks (EXTERNAL_HOOK_FILES) that turn
# every workflow execution into one OTel trace and every node run into a span.
# docker-compose.yml tells the exporter where Opik's OTLP endpoint is.
FROM n8nio/n8n:2.41.7

USER root
RUN npm install -g n8n-observability@1.0.3

# Opik: this is the only wiring n8n needs. Without it, executions run fine but
# nothing is exported, so the Opik project stays empty.
ENV EXTERNAL_HOOK_FILES=/usr/local/lib/node_modules/n8n-observability/dist/hooks.cjs

USER node

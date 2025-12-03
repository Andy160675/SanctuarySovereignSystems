# OPA Policy Gate
FROM openpolicyagent/opa:latest-static

COPY policies/ /policies/

EXPOSE 8181

ENTRYPOINT ["opa", "run", "--server", "--addr", "0.0.0.0:8181", "/policies"]

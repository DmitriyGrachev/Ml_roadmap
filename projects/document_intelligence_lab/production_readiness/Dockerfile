# Optional deployment wrapper. Base: existing service/Dockerfile, built from repo root.
# Configuration supplied in an external NEW build context; no learner data in git.
# Build/run NOT_RUN in the implementation environment.
FROM document-service:local
COPY --chown=10001:10001 bundle /runtime/bundle
COPY --chown=10001:10001 service.json /runtime/service.json
ENV ROADMAP_SERVICE_CONFIG=/runtime/service.json

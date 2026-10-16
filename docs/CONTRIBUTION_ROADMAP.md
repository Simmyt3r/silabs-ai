# Silabs AI Contribution Roadmap

This roadmap keeps contributors aligned on what is complete, what is still in progress, and what should be worked on next.

## Phase 1 — Foundation ✅

- Project structure
- Base AI model setup
- API setup
- Training and evaluation tools

## Phase 2 — Data & Knowledge ✅

- Training datasets prepared
- Knowledge sources collected and cleaned
- Verified knowledge base completed

## Phase 3 — Model Training 🟡

- Initial training experiments completed
- Best training approach selected
- Full training still pending

## Phase 4 — Evaluation & Safety 🟡

- Capability testing
- Safety checks
- Guardrails
- Regression testing
- Final manual review still pending

## Phase 5 — RAG / Knowledge Retrieval ✅

- Knowledge retrieval completed
- Source citations added
- Citation validation added
- Retrieval accuracy is strong and stable

## Phase 6 — Product Integration 🟢 CURRENT

Completed:

- API authentication
- Rate limiting
- Usage monitoring
- Request tracking
- Streaming responses
- JavaScript and Python client SDKs

Current task:

**UniXpress staging integration**

Temporary remote staging through Colab + ngrok has now passed authentication, warm inference, usage telemetry, true streaming, RAG retrieval and citation tests. The current task is now UniXpress staging integration. Persistent always-on hosting remains a later deployment requirement.

## Phase 7 — Deployment & Optimization ⏳

- Performance testing
- Model optimization
- Hosting decisions
- Load testing
- Production deployment

## Phase 8 — Future Improvements ⏳

- Better training
- More capabilities
- Language expansion
- Tools and advanced AI features

## Contribution Rule

Before starting anything, check the current phase.

Every contribution should clearly answer:

1. Which phase does this belong to?
2. What task does it complete?
3. How do we know it works?
4. What should come next?

## Current Position

**Foundation ✅ → Data ✅ → Training 🟡 → Evaluation 🟡 → RAG ✅ → Product Integration 🟢 → Deployment ⏳ → Future Improvements ⏳**

Right now, the main focus is **Phase 6: UniXpress staging integration**.

Finish each stage properly before jumping ahead.

# Optional Review Inbox

Placeholder for a lightweight React dashboard that surfaces:

- **Inbox / Quarantine**: manually confirm client emails vs. spam.
- **Client profile**: preferences, interactions, tone profile, auto-send toggle.
- **Draft approval**: preview CMA PDF + email body before sending.
- **Deal desk**: acknowledge or annotate undervalued property alerts.

To scaffold quickly:

```bash
npx create-react-app apps/web --template typescript
```

Expose API base URL via Vite/CRA env vars and authenticate with JWT when you wire auth.

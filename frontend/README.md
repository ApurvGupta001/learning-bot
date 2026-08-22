# Frontend — Next.js

Chat UI + progress dashboard for the Personalized Learning Bot. App Router +
TypeScript. Talks to the FastAPI backend via `lib/api.ts`.

## Run locally

```bash
cd frontend
npm install
cp .env.local.example .env.local     # points at http://localhost:8000
npm run dev                          # http://localhost:3000
```

The backend should be running on :8000 (see ../backend).

## Layout

```
frontend/
├── app/
│   ├── layout.tsx        # root layout + global styles
│   ├── page.tsx          # topic picker (home)
│   ├── chat/page.tsx     # streaming chat UI
│   └── globals.css
├── lib/
│   └── api.ts            # fetch-based API client + SSE stream reader
├── package.json
└── tsconfig.json
```

## Notes

- Streaming uses `fetch` + a `ReadableStream` reader (not `EventSource`) so we
  can POST a message and still stream tokens back.
- The chat page currently posts to `/sessions/{id}/message`, which is added in
  the agent-loop step; until then it shows a friendly placeholder on error.

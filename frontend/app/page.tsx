import Link from "next/link";

// Topic picker stub. Topics will come from GET /topics once that route lands.
const TOPICS = [{ slug: "cuda", title: "CUDA" }];

export default function Home() {
  return (
    <main className="container">
      <h1>Personalized Learning Bot</h1>
      <p className="muted">
        Pick a topic and learn it step by step, grounded in real docs via MCP.
      </p>

      <div className="card" style={{ marginTop: 24 }}>
        <h2 style={{ marginTop: 0 }}>Topics</h2>
        <ul>
          {TOPICS.map((t) => (
            <li key={t.slug}>
              <Link href={`/chat?topic=${t.slug}`}>{t.title}</Link>
            </li>
          ))}
        </ul>
        <p className="muted" style={{ fontSize: 14 }}>
          More topics appear here once the backend <code>/topics</code> route and
          MCP registry are wired.
        </p>
      </div>
    </main>
  );
}

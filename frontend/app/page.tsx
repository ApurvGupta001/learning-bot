import TopicList from "./TopicList";

export default function Home() {
  return (
    <main className="container">
      <h1>Personalized Learning Bot</h1>
      <p className="muted">
        Pick a topic and learn it step by step, grounded in real docs via MCP.
      </p>

      <div className="card" style={{ marginTop: 24 }}>
        <h2 style={{ marginTop: 0 }}>Topics</h2>
        <TopicList />
      </div>
    </main>
  );
}

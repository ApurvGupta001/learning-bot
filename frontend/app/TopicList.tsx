"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTopics, type Topic } from "@/lib/api";

// Shown if the backend isn't reachable, so the page always renders something.
const FALLBACK: Topic[] = [{ id: 0, slug: "cuda", title: "CUDA" }];

export default function TopicList() {
  const [topics, setTopics] = useState<Topic[]>(FALLBACK);
  const [live, setLive] = useState(false);

  useEffect(() => {
    getTopics()
      .then((t) => {
        if (t.length) {
          setTopics(t);
          setLive(true);
        }
      })
      .catch(() => {
        /* keep fallback */
      });
  }, []);

  return (
    <div>
      <ul>
        {topics.map((t) => (
          <li key={t.slug}>
            <Link href={`/chat?topic=${t.slug}`}>{t.title}</Link>
          </li>
        ))}
      </ul>
      {!live && (
        <p className="muted" style={{ fontSize: 14 }}>
          Showing a default list. Start the backend and seed the database
          (<code>make seed</code>) to load the full topic catalog.
        </p>
      )}
    </div>
  );
}

import { useState } from "react";
import Experiment from "./components/Experiment";
import { Card } from "./components/ui";
import { joinExperiment } from "./lib/api";
import { tokenStore } from "./lib/tokenStore";

const STEPS = [
  { title: "Discuss", text: "Chat with your group for about a minute." },
  { title: "Vote", text: "Pick who should be the Decision Maker." },
  { title: "Repeat", text: "A second round of chat and voting." },
  { title: "Result", text: "See who the group selected." },
];

export default function App() {
  const [token, setToken] = useState<string | null>(tokenStore.get);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const join = async () => {
    setJoining(true);
    setError(null);
    try {
      const newToken = await joinExperiment();
      tokenStore.set(newToken);
      setToken(newToken);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not join");
    } finally {
      setJoining(false);
    }
  };

  const leave = () => {
    tokenStore.clear();
    setToken(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50/60 to-sky-50 text-slate-800">
      <header className="sticky top-0 z-10 border-b border-slate-200/70 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 text-white shadow-md shadow-indigo-500/30">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="size-5">
              <path d="M17 20h5v-2a3 3 0 0 0-5.36-1.86M17 20H7m10 0v-2c0-.66-.13-1.28-.36-1.86M7 20H2v-2a3 3 0 0 1 5.36-1.86M7 20v-2c0-.66.13-1.28.36-1.86m0 0a5 5 0 0 1 9.28 0M15 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </div>
          <div className="leading-tight">
            <p className="font-semibold">Group Decision Study</p>
            <p className="text-xs text-slate-500">Research experiment</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8">
        {token ? (
          <Experiment key={token} token={token} onLeave={leave} />
        ) : (
          <Card className="space-y-6 p-8">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                Choose a Decision Maker together
              </h1>
              <p className="text-slate-600">
                You will be grouped with two other participants. Over two short rounds of chat, the
                group decides who should be the <strong>Decision Maker</strong> in a follow-up task.
              </p>
            </div>

            <ol className="grid gap-3 sm:grid-cols-4">
              {STEPS.map((step, i) => (
                <li key={step.title} className="rounded-xl bg-slate-50 p-4 ring-1 ring-slate-200/70">
                  <span className="mb-2 flex size-7 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
                    {i + 1}
                  </span>
                  <p className="font-semibold">{step.title}</p>
                  <p className="text-sm text-slate-500">{step.text}</p>
                </li>
              ))}
            </ol>

            <div className="flex flex-wrap items-center gap-4">
              <button className="btn px-6 py-3 text-base" onClick={join} disabled={joining}>
                {joining ? "Joining…" : "Join the study →"}
              </button>
              <p className="text-sm text-slate-500">
                Everyone is shown only as Player A, B or C.
              </p>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </Card>
        )}
      </main>
    </div>
  );
}

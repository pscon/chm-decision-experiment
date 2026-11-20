import { useState } from "react";
import Experiment from "./components/Experiment";
import { joinExperiment, tokenStore } from "./useExperiment";

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
    <main className="page">
      <h1>Group Decision Study</h1>
      {token ? (
        <Experiment key={token} token={token} onLeave={leave} />
      ) : (
        <section className="card">
          <p>
            You will be grouped with two other participants. Over two short rounds of chat, the group
            decides who should be the <strong>Decision Maker</strong> in a follow-up task. After each
            round, everyone votes.
          </p>
          <p className="muted">Participants are only identified as Player A, B or C.</p>
          <button onClick={join} disabled={joining}>
            {joining ? "Joining…" : "Join the study"}
          </button>
          {error && <p className="error">{error}</p>}
        </section>
      )}
    </main>
  );
}

interface Props {
  active: boolean;
  listening: boolean;
  speaking: boolean;
  processing: boolean;
  connected: boolean;
  supported: boolean;
  ttsError: string | null;
  onStart: () => void;
  onStop: () => void;
}

export function VoiceDock({
  active,
  listening,
  speaking,
  processing,
  connected,
  supported,
  ttsError,
  onStart,
  onStop,
}: Props) {
  let hint = "Einmal tippen — danach nur noch sprechen";
  if (!supported) hint = "Spracheingabe wird in diesem Browser nicht unterstützt";
  else if (!connected) hint = "Verbindung wird aufgebaut…";
  else if (!active) hint = "Tippen zum Starten — kein Tippen nötig";
  else if (speaking) hint = "Jürgen spricht…";
  else if (processing) hint = "Jürgen denkt…";
  else if (listening) hint = "Hört zu — sag z. B. „Hallo Jürgen“ oder „Wie spät ist es?“";
  else hint = "Mikro wird neu gestartet…";

  return (
    <div className="voice-dock">
      <p className="voice-hint">{ttsError ? `Stimme: ${ttsError}` : hint}</p>
      {!active ? (
        <button
          type="button"
          className="voice-orb start holo-ring"
          onClick={onStart}
          disabled={!supported || !connected}
          aria-label="Sprachsteuerung starten"
        >
          <span className="orb-inner holo" />
          <span className="orb-label">Start</span>
        </button>
      ) : (
        <button
          type="button"
          className={`voice-orb holo-ring ${listening ? "listen" : ""} ${speaking ? "speak" : ""}`}
          onClick={onStop}
          aria-label="Sprachsteuerung beenden"
        >
          <span className="orb-inner holo" />
          <span className="orb-label">{speaking ? "…" : listening ? "◉" : "…"}</span>
        </button>
      )}
    </div>
  );
}

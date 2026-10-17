import { useCallback, useEffect, useRef, useState } from "react";
import { ArcReactor } from "./components/ArcReactor";
import { DevicePanel } from "./components/DevicePanel";
import { InstallBanner } from "./components/InstallBanner";
import { SecureContextHint } from "./components/SecureContextHint";
import { useAssistantSocket } from "./hooks/useAssistantSocket";
import { useSpeech } from "./hooks/useSpeech";
import type { AssistantStatus, ChatMessage, Device, WsEvent } from "./types";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceBusy, setDeviceBusy] = useState<string | null>(null);
  const [toolActivity, setToolActivity] = useState<string | null>(null);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const streamIdRef = useRef<string | null>(null);
  const assistantBufferRef = useRef("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  const { supported, listening, wakeEnabled, speak, unlockAudio, startListening, stop, toggleWake } =
    useSpeech("de-DE", status);

  const refreshDevices = useCallback(async () => {
    try {
      const res = await fetch("/api/devices");
      const data = await res.json();
      setDevices(data.devices ?? []);
    } catch {
      /* backend offline */
    }
  }, []);

  useEffect(() => {
    fetch("/api/status")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => null);
    refreshDevices();
  }, [refreshDevices]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, toolActivity]);

  const sendMessageRef = useRef<(text: string) => void>(() => {});

  const handleWsEvent = useCallback(
    (event: WsEvent) => {
      if (event.type === "text") {
        assistantBufferRef.current += event.content;
        const sid = streamIdRef.current;
        if (!sid) return;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === sid ? { ...m, content: assistantBufferRef.current } : m,
          ),
        );
      } else if (event.type === "tool_start") {
        setToolActivity(event.name);
        refreshDevices();
      } else if (event.type === "tool_end") {
        setToolActivity(null);
        refreshDevices();
      } else if (event.type === "done") {
        const sid = streamIdRef.current;
        const finalText = assistantBufferRef.current;
        if (sid) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === sid ? { ...m, streaming: false, content: finalText || m.content } : m,
            ),
          );
        }
        streamIdRef.current = null;
        setToolActivity(null);
        if (autoSpeak && finalText) speak(finalText);
      } else if (event.type === "error") {
        setMessages((m) => [
          ...m.filter((x) => !x.streaming),
          { id: uid(), role: "assistant", content: event.content },
        ]);
        streamIdRef.current = null;
      } else if (event.type === "cleared") {
        setMessages([]);
      }
    },
    [autoSpeak, refreshDevices, speak],
  );

  const { connected, sendMessage, clearSession } = useAssistantSocket(handleWsEvent);
  sendMessageRef.current = sendMessage;

  const submit = useCallback((text: string) => {
    sendMessageRef.current(text);
  }, []);

  const onSend = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      setMessages((m) => [...m, { id: uid(), role: "user", content: trimmed }]);
      streamIdRef.current = uid();
      assistantBufferRef.current = "";
      setMessages((m) => [
        ...m,
        { id: streamIdRef.current!, role: "assistant", content: "", streaming: true },
      ]);
      submit(trimmed);
    },
    [submit],
  );

  const toggleDevice = useCallback(
    async (device: Device) => {
      const action =
        device.type === "cover"
          ? device.state === "open"
            ? "close"
            : "open"
          : device.state === "on"
            ? "off"
            : "on";
      const mapped = action === "close" ? "off" : action === "open" ? "on" : action;
      setDeviceBusy(device.id);
      try {
        await fetch(`/api/devices/${encodeURIComponent(device.id)}/control`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: mapped }),
        });
        await refreshDevices();
      } finally {
        setDeviceBusy(null);
      }
    },
    [refreshDevices],
  );

  const handleForm = (e: React.FormEvent) => {
    e.preventDefault();
    unlockAudio();
    onSend(input);
    setInput("");
  };

  const handleMic = () => {
    unlockAudio();
    if (listening) {
      stop();
      return;
    }
    startListening((text) => onSend(text), false);
  };

  const handleSendClick = () => {
    unlockAudio();
  };

  const haLabel =
    status?.smart_home_provider === "homeassistant"
      ? status.homeassistant_connected
        ? " · Home Assistant verbunden"
        : " · Home Assistant offline"
      : " · Demo-Geräte";

  return (
    <div className="app">
      <div className="grid-bg" aria-hidden />
      <InstallBanner />
      <SecureContextHint />
      <header className="top-bar">
        <div className="brand">
          <ArcReactor active={connected} listening={listening || !!toolActivity} />
          <div>
            <h1>{status?.name ?? "J.Ü.R.G.E.N."}</h1>
            <p className="subtitle acronym">
              {status?.acronym ??
                "Joint Überwachungs-Regelungs-Gebäude-Energie-Navigator"}
            </p>
            <p className="subtitle">
              {connected ? "Systeme online" : "Verbindung wird aufgebaut…"}
              {!status?.llm_configured && " · Demo-KI (LLM nicht konfiguriert)"}
              {haLabel}
            </p>
          </div>
        </div>
        <div className="top-actions">
          <label className="toggle">
            <input
              type="checkbox"
              checked={autoSpeak}
              onChange={(e) => setAutoSpeak(e.target.checked)}
            />
            Sprache
          </label>
          <button
            type="button"
            className={`btn ${wakeEnabled ? "active" : ""}`}
            onClick={() => toggleWake((t) => onSend(t))}
            disabled={!supported}
            title={supported ? "Wake: Hey Jürgen" : "Sprache nicht verfügbar"}
          >
            Wake
          </button>
          <button type="button" className="btn ghost" onClick={() => clearSession()}>
            Reset
          </button>
        </div>
      </header>

      <main className="layout">
        <section className="panel chat-panel">
          <div className="chat-log">
            {messages.length === 0 && (
              <div className="empty-state">
                <p>Tippe oder halte das Mikro — Jürgen hört auf dem iPad im Browser.</p>
                <ul>
                  <li>Wie spät ist es?</li>
                  <li>Wetter in München</li>
                  <li>Liste alle Geräte</li>
                  <li>Schalte light.wohnzimmer an (Home Assistant)</li>
                </ul>
              </div>
            )}
            {messages.map((m) => (
              <article key={m.id} className={`bubble ${m.role}`}>
                <span className="role-label">{m.role === "user" ? "Du" : "Jürgen"}</span>
                <p>{m.content || (m.streaming ? "…" : "")}</p>
              </article>
            ))}
            {toolActivity && <p className="tool-hint">Tool: {toolActivity} …</p>}
            <div ref={chatEndRef} />
          </div>

          <form className="composer" onSubmit={handleForm}>
            <button
              type="button"
              className={`mic ${listening ? "on" : ""}`}
              onClick={handleMic}
              disabled={!supported}
              aria-label="Mikrofon"
            >
              ◉
            </button>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Befehl oder Frage…"
              autoComplete="off"
              enterKeyHint="send"
            />
            <button
              type="submit"
              className="btn primary"
              disabled={!connected}
              onClick={handleSendClick}
            >
              Senden
            </button>
          </form>
        </section>

        <aside className="side">
          <DevicePanel devices={devices} onToggle={toggleDevice} busyId={deviceBusy} />
          <section className="panel info-panel">
            <h2>Status</h2>
            <dl>
              <dt>Modell</dt>
              <dd>{status?.model ?? "—"}</dd>
              <dt>TTS</dt>
              <dd>{status?.tts_provider ?? "browser"}</dd>
              <dt>Smart Home</dt>
              <dd>{status?.smart_home_provider ?? "mock"}</dd>
              <dt>LLM</dt>
              <dd>{status?.llm_backend ?? (status?.llm_configured ? "API" : "Fallback")}</dd>
            </dl>
          </section>
        </aside>
      </main>
    </div>
  );
}

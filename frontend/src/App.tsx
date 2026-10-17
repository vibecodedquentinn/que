import { useCallback, useEffect, useRef, useState } from "react";
import { DevicePanel } from "./components/DevicePanel";
import { InstallBanner } from "./components/InstallBanner";
import { SecureContextHint } from "./components/SecureContextHint";
import { VoiceDock } from "./components/VoiceDock";
import { VoiceHologramButton } from "./components/VoiceHologramButton";
import { useAssistantSocket } from "./hooks/useAssistantSocket";
import { useSpeech } from "./hooks/useSpeech";
import type { AssistantStatus, ChatMessage, Device, WsEvent } from "./types";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceBusy, setDeviceBusy] = useState<string | null>(null);
  const [toolActivity, setToolActivity] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [showDevices, setShowDevices] = useState(false);
  const streamIdRef = useRef<string | null>(null);
  const assistantBufferRef = useRef("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const pendingResumeRef = useRef(false);

  const {
    supported,
    listening,
    speaking,
    voiceSession,
    speakAsync,
    startVoiceSession,
    resumeListening,
    pauseListening,
    endVoiceSession,
    primeAudio,
    ttsError,
    unlockAudio,
  } = useSpeech("de-DE", status);

  const refreshDevices = useCallback(async () => {
    try {
      const res = await fetch("/api/devices");
      const data = await res.json();
      setDevices(data.devices ?? []);
    } catch {
      /* offline */
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

  const onSend = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setProcessing(true);
    pauseListening();
    setMessages((m) => [...m, { id: uid(), role: "user", content: trimmed }]);
    streamIdRef.current = uid();
    assistantBufferRef.current = "";
    setMessages((m) => [
      ...m,
      { id: streamIdRef.current!, role: "assistant", content: "", streaming: true },
    ]);
    sendMessageRef.current(trimmed);
  }, [pauseListening]);

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
        setProcessing(false);

        if (voiceSession && finalText) {
          pendingResumeRef.current = true;
          void speakAsync(finalText).then(() => {
            if (pendingResumeRef.current) resumeListening();
          });
        } else if (voiceSession) {
          resumeListening();
        }
      } else if (event.type === "error") {
        setMessages((m) => [
          ...m.filter((x) => !x.streaming),
          { id: uid(), role: "assistant", content: event.content },
        ]);
        streamIdRef.current = null;
        setProcessing(false);
        if (voiceSession) resumeListening();
      } else if (event.type === "cleared") {
        setMessages([]);
      }
    },
    [refreshDevices, resumeListening, speakAsync, voiceSession],
  );

  const { connected, sendMessage, clearSession } = useAssistantSocket(handleWsEvent);
  sendMessageRef.current = sendMessage;

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

  const handleVoiceToggle = () => {
    if (voiceSession) {
      pendingResumeRef.current = false;
      endVoiceSession();
      return;
    }
    void (async () => {
      unlockAudio();
      await primeAudio();
      startVoiceSession(onSend);
      await speakAsync("Hier ist Jürgen. Wie kann ich helfen?");
    })();
  };

  const handleReset = () => {
    pendingResumeRef.current = false;
    clearSession();
    if (voiceSession) resumeListening();
  };

  let hint = "Auf Jürgen tippen — dann sprechen";
  if (!supported) hint = "Spracheingabe wird in diesem Browser nicht unterstützt";
  else if (!connected) hint = "Verbindung wird aufgebaut…";
  else if (ttsError) hint = `Stimme: ${ttsError}`;
  else if (speaking) hint = "Jürgen spricht…";
  else if (processing) hint = "Jürgen denkt…";
  else if (listening) hint = "Sag z. B. „Wie spät ist es?“ oder „Wetter in Berlin“";
  else if (voiceSession) hint = "Nochmal tippen zum Beenden";

  const visibleMessages = messages.slice(-6);

  return (
    <div className="app voice-only ipad-shell">
      <div className="grid-bg" aria-hidden />
      <InstallBanner />
      <SecureContextHint />
      <header className="top-bar top-bar--compact">
        <div className="brand brand--text">
          <h1>{status?.name ?? "J.Ü.R.G.E.N."}</h1>
          <p className="subtitle status-line">
            <span className={`dot ${connected ? "on" : ""}`} aria-hidden />
            {connected ? "Online" : "Verbinden…"}
            {voiceSession ? " · Sprache an" : ""}
          </p>
        </div>
        <div className="top-actions">
          <button
            type="button"
            className="btn ghost small"
            onClick={() => setShowDevices((v) => !v)}
          >
            Geräte
          </button>
          <button type="button" className="btn ghost small" onClick={handleReset}>
            Reset
          </button>
        </div>
      </header>

      <main className="ipad-main">
        <VoiceHologramButton
          active={voiceSession}
          listening={listening}
          speaking={speaking}
          processing={processing || !!toolActivity}
          connected={connected}
          supported={supported}
          onPress={handleVoiceToggle}
        />

        <VoiceDock hint={hint} />

        <section className="chat-strip panel">
          <div className="chat-log">
            {visibleMessages.length === 0 && (
              <p className="empty-state compact">
                Kein Tippen — nur die Kugel antippen und sprechen.
              </p>
            )}
            {visibleMessages.map((m) => (
              <article key={m.id} className={`bubble ${m.role} compact`}>
                <p>{m.content || (m.streaming ? "…" : "")}</p>
              </article>
            ))}
            {toolActivity && <p className="tool-hint">… {toolActivity}</p>}
            <div ref={chatEndRef} />
          </div>
        </section>

        {showDevices && (
          <aside className="side-drawer panel">
            <DevicePanel devices={devices} onToggle={toggleDevice} busyId={deviceBusy} />
          </aside>
        )}
      </main>
    </div>
  );
}

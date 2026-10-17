import { useCallback, useEffect, useRef, useState } from "react";
import type { JarvisStatus } from "../types";

type SpeechRecognitionCtor = new () => SpeechRecognition;

function getRecognition(): SpeechRecognition | null {
  const w = window as Window &
    typeof globalThis & {
      SpeechRecognition?: SpeechRecognitionCtor;
      webkitSpeechRecognition?: SpeechRecognitionCtor;
    };
  const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export function useSpeech(lang = "de-DE", status: JarvisStatus | null) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const [wakeEnabled, setWakeEnabled] = useState(false);
  const recRef = useRef<SpeechRecognition | null>(null);
  const onResultRef = useRef<(text: string) => void>(() => {});
  const wakeRef = useRef(wakeEnabled);
  wakeRef.current = wakeEnabled;
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    setSupported(!!getRecognition());
  }, []);

  const stop = useCallback(() => {
    recRef.current?.stop();
    setListening(false);
  }, []);

  const speakBrowser = useCallback(
    (text: string) => {
      if (!("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang;
      u.rate = 1.02;
      u.pitch = 0.95;
      const voices = window.speechSynthesis.getVoices();
      const preferred =
        voices.find((v) => v.lang.startsWith("de") && /Anna|Google|Premium/i.test(v.name)) ||
        voices.find((v) => v.lang.startsWith("de")) ||
        voices[0];
      if (preferred) u.voice = preferred;
      window.speechSynthesis.speak(u);
    },
    [lang],
  );

  const speakServer = useCallback(async (text: string) => {
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) {
      speakBrowser(text);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    if (audioRef.current) {
      audioRef.current.pause();
      URL.revokeObjectURL(audioRef.current.src);
    }
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.onended = () => URL.revokeObjectURL(url);
    await audio.play();
  }, [speakBrowser]);

  const speak = useCallback(
    (text: string) => {
      const provider = status?.tts_provider ?? "browser";
      if (provider === "piper" || provider === "elevenlabs") {
        void speakServer(text);
      } else {
        speakBrowser(text);
      }
    },
    [speakBrowser, speakServer, status?.tts_provider],
  );

  const startListening = useCallback(
    (onFinal: (text: string) => void, continuous = false) => {
      const rec = getRecognition();
      if (!rec) {
        setSupported(false);
        return;
      }
      onResultRef.current = onFinal;
      recRef.current = rec;
      rec.lang = lang;
      rec.continuous = continuous;
      rec.interimResults = !continuous;

      rec.onresult = (ev: SpeechRecognitionEvent) => {
        let transcript = "";
        for (let i = ev.resultIndex; i < ev.results.length; i++) {
          transcript += ev.results[i][0].transcript;
        }
        const trimmed = transcript.trim();
        if (!trimmed) return;

        if (wakeRef.current && continuous) {
          const lower = trimmed.toLowerCase();
          if (lower.includes("jarvis") || lower.includes("hey jarvis")) {
            const after = trimmed.split(/jarvis/i).pop()?.trim() || "";
            if (after.length > 2) onResultRef.current(after);
          }
          return;
        }

        if (ev.results[ev.results.length - 1].isFinal) {
          onResultRef.current(trimmed);
          if (!continuous) stop();
        }
      };

      rec.onend = () => {
        if (wakeRef.current && continuous) {
          try {
            rec.start();
          } catch {
            setListening(false);
          }
        } else {
          setListening(false);
        }
      };

      rec.onerror = () => setListening(false);

      try {
        rec.start();
        setListening(true);
      } catch {
        setListening(false);
      }
    },
    [lang, stop],
  );

  const toggleWake = useCallback(
    (onWakeCommand: (text: string) => void) => {
      if (wakeEnabled) {
        setWakeEnabled(false);
        stop();
        return;
      }
      setWakeEnabled(true);
      startListening(onWakeCommand, true);
    },
    [wakeEnabled, startListening, stop],
  );

  return {
    supported,
    listening,
    wakeEnabled,
    speak,
    startListening,
    stop,
    toggleWake,
  };
}

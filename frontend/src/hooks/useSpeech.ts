import { useCallback, useEffect, useRef, useState } from "react";
import type { AssistantStatus } from "../types";

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

function pickGermanVoice(): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis.getVoices();
  const score = (v: SpeechSynthesisVoice): number => {
    let s = 0;
    if (!v.lang.toLowerCase().startsWith("de")) return -1;
    if (/thorsten|hans|markus|stefan|michael|google deutsch/i.test(v.name)) s += 4;
    if (/male|männlich/i.test(v.name)) s += 3;
    if (/premium|enhanced|natural/i.test(v.name)) s += 1;
    if (v.localService) s += 1;
    return s;
  };
  return voices
    .map((v) => ({ v, s: score(v) }))
    .filter((x) => x.s >= 0)
    .sort((a, b) => b.s - a.s)[0]?.v;
}

function normalizeWake(text: string): string {
  return text
    .toLowerCase()
    .replace(/ü/g, "u")
    .replace(/ä/g, "a")
    .replace(/ö/g, "o")
    .replace(/ß/g, "ss");
}

export function useSpeech(lang = "de-DE", status: AssistantStatus | null) {
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
    if ("speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
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
      u.rate = 0.96;
      u.pitch = 0.88;
      const preferred = pickGermanVoice();
      if (preferred) u.voice = preferred;
      window.speechSynthesis.speak(u);
    },
    [lang],
  );

  const speakServer = useCallback(
    async (text: string) => {
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
      audio.setAttribute("playsinline", "true");
      audioRef.current = audio;
      audio.onended = () => URL.revokeObjectURL(url);
      await audio.play();
    },
    [speakBrowser],
  );

  const speak = useCallback(
    (text: string) => {
      const provider = status?.tts_provider ?? "browser";
      if (
        provider === "gtts" ||
        provider === "edge" ||
        provider === "piper" ||
        provider === "elevenlabs"
      ) {
        void speakServer(text);
      } else {
        speakBrowser(text);
      }
    },
    [speakBrowser, speakServer, status?.tts_provider],
  );

  const unlockedRef = useRef(false);
  const unlockAudio = useCallback(() => {
    if (unlockedRef.current) return;
    unlockedRef.current = true;
    const Ctx =
      window.AudioContext ||
      (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (Ctx) {
      const ctx = new Ctx();
      void ctx.resume();
    }
  }, []);

  const extractAfterWake = (trimmed: string): string | null => {
    const norm = normalizeWake(trimmed);
    const triggers = ["hey jürgen", "hey juergen", "jürgen", "juergen"];
    for (const t of triggers) {
      const nt = normalizeWake(t);
      const idx = norm.indexOf(nt);
      if (idx >= 0) {
        const after = trimmed.slice(idx + t.length).trim();
        return after.length > 1 ? after : null;
      }
    }
    return null;
  };

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
          const after = extractAfterWake(trimmed);
          if (after) onResultRef.current(after);
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
    unlockAudio,
    startListening,
    stop,
    toggleWake,
  };
}

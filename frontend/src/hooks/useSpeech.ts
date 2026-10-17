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

export function useSpeech(lang = "de-DE", status: AssistantStatus | null) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const [voiceSession, setVoiceSession] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const recRef = useRef<SpeechRecognition | null>(null);
  const onResultRef = useRef<(text: string) => void>(() => {});
  const voiceSessionRef = useRef(false);
  const pauseListenRef = useRef(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    voiceSessionRef.current = voiceSession;
  }, [voiceSession]);

  useEffect(() => {
    setSupported(!!getRecognition());
    if ("speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
  }, []);

  const stop = useCallback(() => {
    recRef.current?.stop();
    recRef.current = null;
    setListening(false);
  }, []);

  const pauseListening = useCallback(() => {
    pauseListenRef.current = true;
    stop();
  }, [stop]);

  const speakBrowserAsync = useCallback(
    (text: string) =>
      new Promise<void>((resolve) => {
        if (!("speechSynthesis" in window)) {
          resolve();
          return;
        }
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        u.rate = 0.96;
        u.pitch = 0.88;
        const preferred = pickGermanVoice();
        if (preferred) u.voice = preferred;
        u.onend = () => resolve();
        u.onerror = () => resolve();
        window.speechSynthesis.speak(u);
      }),
    [lang],
  );

  const speakServerAsync = useCallback(
    async (text: string) => {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        await speakBrowserAsync(text);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.pause();
        URL.revokeObjectURL(audioRef.current.src);
      }
      await new Promise<void>((resolve) => {
        const audio = new Audio(url);
        audio.setAttribute("playsinline", "true");
        audioRef.current = audio;
        audio.onended = () => {
          URL.revokeObjectURL(url);
          resolve();
        };
        audio.onerror = () => {
          URL.revokeObjectURL(url);
          resolve();
        };
        void audio.play().catch(() => resolve());
      });
    },
    [speakBrowserAsync],
  );

  const speakAsync = useCallback(
    async (text: string) => {
      setSpeaking(true);
      try {
        const provider = status?.tts_provider ?? "browser";
        if (
          provider === "gtts" ||
          provider === "edge" ||
          provider === "piper" ||
          provider === "elevenlabs"
        ) {
          await speakServerAsync(text);
        } else {
          await speakBrowserAsync(text);
        }
      } finally {
        setSpeaking(false);
      }
    },
    [speakBrowserAsync, speakServerAsync, status?.tts_provider],
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

  const beginCapture = useCallback(() => {
    const rec = getRecognition();
    if (!rec || pauseListenRef.current || !voiceSessionRef.current) return;

    rec.lang = lang;
    rec.continuous = true;
    rec.interimResults = true;

    rec.onresult = (ev: SpeechRecognitionEvent) => {
      if (pauseListenRef.current) return;
      const last = ev.results[ev.results.length - 1];
      if (!last?.isFinal) return;
      const trimmed = last[0].transcript.trim();
      if (trimmed.length > 0) {
        onResultRef.current(trimmed);
      }
    };

    rec.onend = () => {
      if (pauseListenRef.current || !voiceSessionRef.current) {
        setListening(false);
        return;
      }
      try {
        rec.start();
        setListening(true);
      } catch {
        setListening(false);
      }
    };

    rec.onerror = () => {
      if (!voiceSessionRef.current) setListening(false);
    };

    try {
      rec.start();
      recRef.current = rec;
      setListening(true);
    } catch {
      setListening(false);
    }
  }, [lang]);

  const startVoiceSession = useCallback(
    (onFinal: (text: string) => void) => {
      unlockAudio();
      onResultRef.current = (text) => {
        pauseListenRef.current = true;
        stop();
        onFinal(text);
      };
      pauseListenRef.current = false;
      setVoiceSession(true);
      voiceSessionRef.current = true;
      beginCapture();
    },
    [beginCapture, stop, unlockAudio],
  );

  const resumeListening = useCallback(() => {
    if (!voiceSessionRef.current) return;
    pauseListenRef.current = false;
    beginCapture();
  }, [beginCapture]);

  const endVoiceSession = useCallback(() => {
    voiceSessionRef.current = false;
    setVoiceSession(false);
    pauseListenRef.current = true;
    stop();
  }, [stop]);

  return {
    supported,
    listening,
    speaking,
    voiceSession,
    speakAsync,
    unlockAudio,
    startVoiceSession,
    resumeListening,
    pauseListening,
    endVoiceSession,
  };
}

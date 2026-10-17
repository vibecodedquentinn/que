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

function isAppleDevice(): boolean {
  return (
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
  );
}

function pickGermanMaleVoice(): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis.getVoices();
  const female = /anna|petra|helena|marlene|victoria|female|frau|woman|karen/i;
  const maleBoost =
    /markus|martin|hans|michael|stefan|jan|thorsten|helmut|conrad|klaus|thomas|google deutsch/i;

  let best: SpeechSynthesisVoice | undefined;
  let bestScore = -1;
  for (const v of voices) {
    if (!v.lang.toLowerCase().startsWith("de")) continue;
    if (female.test(v.name)) continue;
    let s = 1;
    if (maleBoost.test(v.name)) s += 5;
    if (v.localService) s += 1;
    if (s > bestScore) {
      bestScore = s;
      best = v;
    }
  }
  return best ?? voices.find((v) => v.lang.toLowerCase().startsWith("de"));
}

export function useSpeech(lang = "de-DE", status: AssistantStatus | null) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const [voiceSession, setVoiceSession] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [ttsError, setTtsError] = useState<string | null>(null);
  const recRef = useRef<SpeechRecognition | null>(null);
  const onResultRef = useRef<(text: string) => void>(() => {});
  const voiceSessionRef = useRef(false);
  const pauseListenRef = useRef(false);
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    voiceSessionRef.current = voiceSession;
  }, [voiceSession]);

  useEffect(() => {
    setSupported(!!getRecognition());
    const loadVoices = () => window.speechSynthesis?.getVoices();
    loadVoices();
    window.speechSynthesis && (window.speechSynthesis.onvoiceschanged = loadVoices);
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

  const ensureAudioContext = useCallback(async () => {
    const Ctx =
      window.AudioContext ||
      (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctx) return null;
    if (!audioCtxRef.current) {
      audioCtxRef.current = new Ctx();
    }
    if (audioCtxRef.current.state === "suspended") {
      await audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }, []);

  const speakBrowserMaleAsync = useCallback(
    (text: string) =>
      new Promise<void>((resolve) => {
        if (!("speechSynthesis" in window)) {
          resolve();
          return;
        }
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        u.rate = 0.92;
        u.pitch = 0.78;
        const voice = pickGermanMaleVoice();
        if (voice) u.voice = voice;
        u.onend = () => resolve();
        u.onerror = () => resolve();
        window.speechSynthesis.speak(u);
      }),
    [lang],
  );

  const playArrayBuffer = useCallback(
    async (data: ArrayBuffer) => {
      const ctx = await ensureAudioContext();
      if (!ctx) throw new Error("Kein AudioContext");
      const buffer = await ctx.decodeAudioData(data.slice(0));
      await new Promise<void>((resolve, reject) => {
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(ctx.destination);
        source.onended = () => resolve();
        source.onerror = () => reject(new Error("Wiedergabe fehlgeschlagen"));
        try {
          source.start(0);
        } catch (e) {
          reject(e);
        }
      });
    },
    [ensureAudioContext],
  );

  const speakServerAsync = useCallback(
    async (text: string) => {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        throw new Error(`TTS HTTP ${res.status}`);
      }
      const data = await res.arrayBuffer();
      await playArrayBuffer(data);
    },
    [playArrayBuffer],
  );

  const speakAsync = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      setSpeaking(true);
      setTtsError(null);
      try {
        const provider = status?.tts_provider ?? "espeak";
        const serverTts =
          provider === "piper" ||
          provider === "piper_http" ||
          provider === "espeak" ||
          provider === "gtts" ||
          provider === "edge" ||
          provider === "elevenlabs";

        if (isAppleDevice()) {
          try {
            if (serverTts) await speakServerAsync(text);
            else await speakBrowserMaleAsync(text);
          } catch {
            await speakBrowserMaleAsync(text);
          }
        } else if (serverTts) {
          try {
            await speakServerAsync(text);
          } catch {
            await speakBrowserMaleAsync(text);
          }
        } else {
          await speakBrowserMaleAsync(text);
        }
      } catch (e) {
        setTtsError(e instanceof Error ? e.message : "Stimme fehlgeschlagen");
        await speakBrowserMaleAsync(text);
      } finally {
        setSpeaking(false);
      }
    },
    [speakBrowserMaleAsync, speakServerAsync, status?.tts_provider],
  );

  const primeAudio = useCallback(async () => {
    const ctx = await ensureAudioContext();
    if (!ctx) return;
    const buffer = ctx.createBuffer(1, 1, 22050);
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);
    source.start(0);
  }, [ensureAudioContext]);

  const unlockAudio = useCallback(() => {
    void ensureAudioContext();
  }, [ensureAudioContext]);

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
      if (trimmed.length > 0) onResultRef.current(trimmed);
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
    ttsError,
    speakAsync,
    primeAudio,
    unlockAudio,
    startVoiceSession,
    resumeListening,
    pauseListening,
    endVoiceSession,
  };
};

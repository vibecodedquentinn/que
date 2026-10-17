import { useEffect, useState } from "react";

function isIOS(): boolean {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

function isStandalone(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

export function InstallBanner() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (isStandalone()) return;
    if (isIOS()) {
      setShow(true);
      return;
    }
    const handler = (e: Event) => {
      e.preventDefault();
      setShow(true);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (!show) return null;

  return (
    <aside className="install-banner" role="note">
      {isIOS() ? (
        <p>
          <strong>iPad:</strong> Teilen → <em>Zum Home-Bildschirm</em> — dann startet JARVIS wie eine App.
          Für das Mikrofon brauchst du <strong>HTTPS</strong> (siehe README).
        </p>
      ) : (
        <p>
          Diese Seite kann als App installiert werden (Browser-Menü → App installieren / Zum Home-Bildschirm).
        </p>
      )}
      <button type="button" className="btn ghost small" onClick={() => setShow(false)}>
        OK
      </button>
    </aside>
  );
}

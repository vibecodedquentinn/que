export function SecureContextHint() {
  if (window.isSecureContext) return null;
  return (
    <aside className="secure-hint" role="alert">
      Mikrofon auf dem iPad funktioniert nur über <strong>HTTPS</strong>. Starte J.Ü.R.G.E.N. mit{" "}
      <code>docker compose --profile https up</code> und öffne die HTTPS-URL.
    </aside>
  );
}

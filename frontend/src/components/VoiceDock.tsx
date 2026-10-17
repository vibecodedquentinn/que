interface Props {
  hint: string;
}

/** Nur Statuszeile — der Hologramm-Button sitzt darüber. */
export function VoiceDock({ hint }: Props) {
  return (
    <div className="voice-dock voice-dock--hint-only">
      <p className="voice-hint">{hint}</p>
    </div>
  );
}

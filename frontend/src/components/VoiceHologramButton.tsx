import { JuergenHologram } from "./JuergenHologram";

interface Props {
  active: boolean;
  listening: boolean;
  speaking: boolean;
  processing: boolean;
  connected: boolean;
  supported: boolean;
  onPress: () => void;
}

export function VoiceHologramButton({
  active,
  listening,
  speaking,
  processing,
  connected,
  supported,
  onPress,
}: Props) {
  const disabled = !supported || !connected;

  let caption = "Tippen zum Start";
  if (disabled && !connected) caption = "Verbinden…";
  else if (disabled) caption = "Nicht unterstützt";
  else if (active && speaking) caption = "Spricht";
  else if (active && processing) caption = "Denkt nach";
  else if (active && listening) caption = "Hört zu";
  else if (active) caption = "Tippen zum Beenden";
  else caption = "Tippen zum Start";

  return (
    <button
      type="button"
      className={`voice-holo-button ${active ? "active" : ""} ${listening ? "listen" : ""} ${
        speaking ? "speak" : ""
      } ${processing ? "think" : ""}`}
      onClick={onPress}
      disabled={disabled}
      aria-label={active ? "Sprachsteuerung beenden" : "Sprachsteuerung starten"}
    >
      <div className="voice-holo-button__sphere">
        <JuergenHologram
          variant="stage"
          online={connected}
          active={active}
          listening={listening}
          speaking={speaking}
          processing={processing}
        />
      </div>
      <span className="voice-holo-button__caption">{caption}</span>
    </button>
  );
}

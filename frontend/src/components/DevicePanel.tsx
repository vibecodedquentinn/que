import type { Device } from "../types";

interface Props {
  devices: Device[];
  onToggle: (device: Device) => void;
  busyId: string | null;
}

function stateLabel(d: Device): string {
  if (d.type === "climate") return `${d.target ?? d.temperature}°C`;
  if (d.type === "light" && d.state === "on") return `${d.brightness ?? 100}%`;
  if (d.type === "cover") return d.position != null ? `${d.position}%` : d.state;
  return d.state;
}

export function DevicePanel({ devices, onToggle, busyId }: Props) {
  return (
    <section className="panel devices-panel">
      <header>
        <h2>Smart Home</h2>
        <span className="badge">{devices.length} Geräte</span>
      </header>
      <ul className="device-list">
        {devices.map((d) => (
          <li key={d.id}>
            <button
              type="button"
              className={`device-btn ${d.state} ${busyId === d.id ? "busy" : ""}`}
              onClick={() => onToggle(d)}
              disabled={busyId === d.id}
            >
              <div>
                <strong>{d.name}</strong>
                <span className="room">{d.room}</span>
              </div>
              <span className="device-state">{stateLabel(d)}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

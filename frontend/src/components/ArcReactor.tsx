interface Props {
  active: boolean;
  listening: boolean;
}

export function ArcReactor({ active, listening }: Props) {
  return (
    <div
      className={`arc-reactor ${active ? "online" : ""} ${listening ? "listening" : ""}`}
      aria-hidden
    >
      <div className="arc-ring ring-outer" />
      <div className="arc-ring ring-mid" />
      <div className="arc-ring ring-inner" />
      <div className="arc-core" />
    </div>
  );
}

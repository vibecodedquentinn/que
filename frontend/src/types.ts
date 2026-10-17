export type Role = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  streaming?: boolean;
}

export interface Device {
  id: string;
  name: string;
  type: string;
  room: string;
  state: string;
  brightness?: number;
  temperature?: number;
  target?: number;
  position?: number;
}

export interface JarvisStatus {
  name: string;
  llm_configured: boolean;
  model: string;
  language: string;
}

export type WsEvent =
  | { type: "session"; session_id: string }
  | { type: "text"; content: string }
  | { type: "tool_start"; name: string }
  | { type: "tool_end"; name: string; result: string }
  | { type: "done" }
  | { type: "error"; content: string }
  | { type: "pong" }
  | { type: "cleared" };

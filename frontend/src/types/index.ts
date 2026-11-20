export type Player = "A" | "B" | "C";
export type Phase = "waiting" | "discussion" | "voting" | "results";

export interface ChatMessage {
  id: number;
  player: Player;
  round: number;
  text: string;
  ts: number;
}

export interface Result {
  decision_maker: Player;
  totals: Record<Player, number>;
  by_round: Record<string, Record<Player, number>>;
  tie_break: "final_round" | "player_order" | null;
}

export interface SessionState {
  you: Player;
  server_time: number;
  phase: Phase;
  round: number;
  total_rounds: number;
  deadline: number | null;
  players: Player[];
  messages: ChatMessage[];
  my_vote: Player | null;
  result: Result | null;
}

export type ServerEvent =
  | ({ type: "state" } & SessionState)
  | { type: "chat"; message: ChatMessage }
  | { type: "error"; message: string };

export type ClientAction = { type: "chat"; text: string } | { type: "vote"; target: Player };

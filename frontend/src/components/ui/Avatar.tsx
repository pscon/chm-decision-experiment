import type { Player } from "../../types";

// One colour per neutral label. Colours depend only on the letter, so they
// reveal nothing about who is human.
const PLAYER_COLORS: Record<Player, string> = {
  A: "bg-violet-500",
  B: "bg-amber-500",
  C: "bg-teal-500",
};

const SIZES = { sm: "size-8 text-sm", md: "size-10 text-base", lg: "size-16 text-2xl" };

export function Avatar({ player, size = "md" }: { player: Player; size?: keyof typeof SIZES }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-bold text-white shadow-sm ${PLAYER_COLORS[player]} ${SIZES[size]}`}
    >
      {player}
    </span>
  );
}

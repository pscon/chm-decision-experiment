import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section
      className={`rounded-2xl border border-slate-200/70 bg-white p-6 shadow-lg shadow-slate-200/60 ${className}`}
    >
      {children}
    </section>
  );
}

import type { ReactNode } from "react";
import type { SceneMeta } from "../scenes/meta";

export function Header({ meta, index, children, title }: { meta: SceneMeta; index: number; children?: ReactNode; title?: ReactNode }) {
  return (
    <header>
      <div className="kicker"><span className="num">{String(index + 1).padStart(2, "0")}</span>{meta.section}</div>
      <h1 className="title">{title ?? meta.title}</h1>
      {children && <p className="lead">{children}</p>}
    </header>
  );
}

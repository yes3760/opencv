// Python kodunu basitçe renklendirir (yorum, metin, anahtar sözcük, sayı).
import type { ReactNode } from "react";
const KW = new Set(["def", "class", "return", "if", "elif", "else", "for", "while", "in", "not", "and", "or", "with",
  "as", "import", "from", "try", "finally", "is", "None", "True", "False", "self", "break", "continue", "lambda"]);

export function highlight(code: string) {
  const out: ReactNode[] = [];
  const re = /(#[^\n]*)|(f?"[^"\n]*"|'[^'\n]*')|(\b\d+(?:\.\d+)?\b)|([A-Za-z_][A-Za-z0-9_]*)|(\s+|.)/g;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(code))) {
    if (m[1]) out.push(<span key={k++} className="c">{m[1]}</span>);
    else if (m[2]) out.push(<span key={k++} className="s">{m[2]}</span>);
    else if (m[3]) out.push(<span key={k++} className="n">{m[3]}</span>);
    else if (m[4]) out.push(KW.has(m[4]) ? <span key={k++} className="k">{m[4]}</span> : m[4]);
    else out.push(m[5]);
  }
  return out;
}

export function CodeBlock({ code }: { code: string }) {
  return <pre className="code">{highlight(code)}</pre>;
}

export type SceneMeta = {
  id: string;
  section: string;
  session: string;
  minutes: number;
  title: string;
  camera?: boolean;
  notes: string[];
  code?: { file: string; run: string; snippet: string };
};
export declare const SECTIONS: string[];
export declare const SCENES: SceneMeta[];
export type SessionFlow = {
  session: string; title: string; outcome: string;
  slots: [string, string, number, string[], string][];
};
export declare const SESSION_FLOW: SessionFlow[];

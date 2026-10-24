/*
  saleFlow.ts  ->  put in frontend/lib/saleFlow.ts   (NEW file)

  The "what should the chat ask next?" logic, plus the small on-device log of recent sales.
  Nothing here talks to the backend, so no schema or API changes are needed.
*/

export type PaymentMethod = "cash" | "digital";
export type Evidence = "typed" | "bank_screenshot" | "receipt";

export type Question =
  | "amount_options"
  | "amount"
  | "payment"
  | "is_sale"
  | "match"
  | "item"
  | "quantity";

export type RecentSale = {
  client_txn_id: string;
  amount_zar: number;
  payment_method: PaymentMethod;
  offering_name: string | null;
  evidence: Evidence;
  corroborated: boolean; // another upload or entry was linked to this sale
  status: "recorded" | "waiting";
  created_at: string;
};

export type SaleDraft = {
  amount_zar: number | null;
  payment_method: PaymentMethod | null;
  offering_name: string | null;
  quantity: number | null;
  // Everything below is optional so older code that builds a SaleDraft keeps working.
  evidence?: Evidence;
  transaction_date?: string | null;
  evidence_hash?: string | null;
  amount_options?: number[];
  is_sale?: boolean | null; // bank messages only: was it payment for a sale?
  item_skipped?: boolean;
  quantity_skipped?: boolean;
  match?: RecentSale | null; // undefined = not checked yet, null = nothing similar found
  match_checked?: boolean;
  match_confirmed?: boolean;
};

export const EVIDENCE_LABEL: Record<Evidence, string> = {
  typed: "typed",
  bank_screenshot: "bank message",
  receipt: "receipt",
};

/* ------------------------------ Chat wording ------------------------------ */

export const CHAT = {
  greeting:
    "Hi! I’m here to record your sales. Tell me what you sold, like “2 shirts, R300, cash”, or tap + to add a bank screenshot, receipt or SMS.",
  scope:
    "I’m only here to record your sales, so I can’t help with that one. Tell me what you sold, like “2 shirts, R300, cash”, or tap + to add a screenshot, receipt or SMS.",
  noAmount:
    "I couldn’t find a sale total in that. Try something like “2 shirts, R300, cash”. I can record amounts up to R100 000.",
  moneyOut:
    "That sounds like money going out. I only record money coming in from sales, so I’ve left it out.",
  notUnderstood: "Sorry, I didn’t catch that. I’m only here to record sales, so I just need an answer to this:",
  notSale: "No problem, I’ve left that out. I only record money that came from sales.",
  linked: "Linked to that sale, so it isn’t counted twice.",
  duplicate: "You’ve already added that one, so I haven’t added it again.",
} as const;

/* --------------------------- What to ask next ----------------------------- */

export function nextQuestion(d: SaleDraft): Question | null {
  if (d.amount_zar === null) return (d.amount_options?.length ?? 0) > 1 ? "amount_options" : "amount";
  if (d.payment_method === null) return "payment";
  if (d.evidence === "bank_screenshot" && (d.is_sale === undefined || d.is_sale === null)) return "is_sale";
  if (d.match && !d.match_checked) return "match";
  if (!d.offering_name && !d.item_skipped) return "item";
  if (d.offering_name && d.quantity === null && !d.quantity_skipped) return "quantity";
  return null;
}

export function questionText(q: Question, d: SaleDraft, fmt: (amount: number) => string): string {
  switch (q) {
    case "amount_options":
      return "I found more than one amount. Which one did the customer pay?";
    case "amount":
      return d.payment_method === null
        ? "What was the total, and was it paid in cash or digitally?"
        : "What was the total amount for that sale?";
    case "payment":
      return "Was that paid in cash or digitally?";
    case "is_sale":
      return `I see ${fmt(d.amount_zar ?? 0)} coming in. Was it payment for a sale?`;
    case "match": {
      const m = d.match;
      return m
        ? `This looks like the ${fmt(m.amount_zar)} ${m.payment_method} sale you recorded ${ago(m.created_at)}. Is it the same sale?`
        : "Is this the same sale as one you recorded earlier?";
    }
    case "item":
      return "What did you sell? You can skip this.";
    case "quantity":
      return `How many ${d.offering_name ?? "items"}? You can skip this.`;
  }
}

export function chipsFor(
  q: Question,
  d: SaleDraft,
  fmt: (amount: number) => string,
): { label: string; text: string }[] {
  switch (q) {
    case "amount_options":
      return (d.amount_options ?? []).map((amount) => ({ label: fmt(amount), text: String(amount) }));
    case "payment":
      return [
        { label: "Cash", text: "cash" },
        { label: "Digital", text: "digital" },
      ];
    case "is_sale":
      return [
        { label: "Yes, a sale", text: "yes" },
        { label: "No, something else", text: "no" },
      ];
    case "match":
      return [
        { label: "Yes, same sale", text: "yes" },
        { label: "No, a different sale", text: "no" },
      ];
    case "item":
      return [{ label: "Skip", text: "skip" }];
    case "quantity":
      return [
        { label: "1", text: "1" },
        { label: "Skip", text: "skip" },
      ];
    default:
      return [];
  }
}

/* ----------------------------- Typed-message guards ----------------------- */

const MONEY_OUT_WORDS = /\b(bought|spent|paid (?:for|to|the|my)|expenses?|refund(?:ed)?|rent|wages?|salary|salaries|supplier invoice|restock(?:ed)?)\b/i;
const SALE_WORDS = /\b(sold|sale|sales|customer|client|received|paid me|payment from)\b/i;

export function looksLikeMoneyOut(text: string): boolean {
  return MONEY_OUT_WORDS.test(text) && !SALE_WORDS.test(text);
}

export function isGreeting(text: string): boolean {
  return text.trim().length < 30 && /^\s*(hi|hello|hey|howzit|sawubona|molo|dumela|good (morning|afternoon|evening))\b/i.test(text);
}

/* --------------------------- Same-sale matching --------------------------- */

const MATCH_WINDOW_MS = 24 * 60 * 60 * 1000;

// A new entry might be the same sale as something already recorded, but only when the
// evidence is different (a typed sale and a bank SMS), the amount matches, and the
// payment type doesn't contradict. Two typed R50 haircuts are genuinely two sales.
export function findSameSale(d: SaleDraft, recent: RecentSale[], now = Date.now()): RecentSale | null {
  const amount = d.amount_zar;
  if (amount === null) return null;
  const evidence = d.evidence ?? "typed";
  return (
    recent.find(
      (r) =>
        !r.corroborated &&
        r.evidence !== evidence &&
        Math.abs(r.amount_zar - amount) < 0.01 &&
        (d.payment_method === null || r.payment_method === d.payment_method) &&
        now - Date.parse(r.created_at) < MATCH_WINDOW_MS,
    ) ?? null
  );
}

export function ago(iso: string, now = Date.now()): string {
  const minutes = Math.max(1, Math.round((now - Date.parse(iso)) / 60000));
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return `${hours} hour${hours > 1 ? "s" : ""} ago`;
}

/* ----------------------- On-device recent sales + hashes ------------------- */

const RECENT_PREFIX = "zakascore-pwa-recent:";
const HASH_PREFIX = "zakascore-pwa-hashes:";
const MAX_RECENT = 50;
const MAX_HASHES = 200;

function isRecentSale(value: unknown): value is RecentSale {
  if (!value || typeof value !== "object") return false;
  const sale = value as Partial<RecentSale>;
  return (
    typeof sale.client_txn_id === "string" &&
    typeof sale.amount_zar === "number" &&
    (sale.payment_method === "cash" || sale.payment_method === "digital") &&
    (sale.evidence === "typed" || sale.evidence === "bank_screenshot" || sale.evidence === "receipt") &&
    typeof sale.corroborated === "boolean" &&
    (sale.status === "recorded" || sale.status === "waiting") &&
    typeof sale.created_at === "string"
  );
}

export function loadRecent(storeId: string): RecentSale[] {
  try {
    const raw = window.localStorage.getItem(`${RECENT_PREFIX}${storeId}`);
    if (!raw) return [];
    const value: unknown = JSON.parse(raw);
    return Array.isArray(value) ? value.filter(isRecentSale).slice(0, MAX_RECENT) : [];
  } catch {
    return [];
  }
}

export function saveRecent(storeId: string, list: RecentSale[]) {
  try {
    window.localStorage.setItem(`${RECENT_PREFIX}${storeId}`, JSON.stringify(list.slice(0, MAX_RECENT)));
  } catch {
    return; // Not critical: the sale itself is already safe in the queue or the backend.
  }
}

export function loadHashes(storeId: string): string[] {
  try {
    const raw = window.localStorage.getItem(`${HASH_PREFIX}${storeId}`);
    const value: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

export function rememberHash(storeId: string, hash: string) {
  try {
    const next = [hash, ...loadHashes(storeId).filter((item) => item !== hash)].slice(0, MAX_HASHES);
    window.localStorage.setItem(`${HASH_PREFIX}${storeId}`, JSON.stringify(next));
  } catch {
    return; // Not critical.
  }
}
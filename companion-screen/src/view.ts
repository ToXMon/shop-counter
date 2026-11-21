// State -> card view. Pure, so it is the test seam. Shapes: docs/INTERFACES.md 1.3 and 1.5.
export interface Candidate {
  product_id: string;
  title: string;
  price_minor: number;
  currency: string;
  image_url?: string;
  seller: { name: string; domain: string };
  is_pick: boolean;
}

export interface SessionState {
  session_id: string;
  phase: string;
  candidates: Candidate[];
  pick: { product_id: string; reasons: string[]; offer_id?: string } | null;
  handoff?: Handoff | null;
}

export interface Handoff {
  status: string;
  continue_url?: string;
  merchant: string | null;
  total_minor: number | null;
  currency: string;
  offer_id?: string;
}

export interface Health {
  ok: boolean;
  catalog: string;
  gemini: string;
}

export interface CardView {
  title: string;
  priceText: string;
  sellerName: string;
  imageUrl?: string;
  reason: string | null; // one short reason; the screen is a display, not a spec sheet
}

export interface View {
  card: CardView | null;
  fixtureMode: boolean;
}

// Minor units are cents: 19900 -> $199.00. Never divide anywhere else.
export function formatPrice(minor: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(minor / 100);
}

// The stub backend reports "stub". Unknown health (offline) counts as live, so we fail closed.
export function isFixtureMode(health: Health | null): boolean {
  return health?.catalog === "stub" || health?.gemini === "stub";
}

export function cardView(state: SessionState | null, health: Health | null): View {
  const fixtureMode = isFixtureMode(health);
  const pick = state?.candidates.find((c) => c.is_pick) ?? null;
  if (!state || !pick) return { card: null, fixtureMode };
  return {
    fixtureMode,
    card: {
      title: pick.title,
      priceText: formatPrice(pick.price_minor, pick.currency),
      sellerName: pick.seller.name,
      imageUrl: pick.image_url,
      reason: state.pick?.reasons[0] ?? null,
    },
  };
}

export interface HandoffView {
  merchant: string;
  totalText: string;
  continueUrl: string; // goes to the QR encoder only; never render or log it
}

export function handoffView(state: SessionState | null, health: Health | null): HandoffView | null {
  const h = state?.handoff;
  if (!h || h.status !== "ready" || !h.continue_url?.startsWith("https://")) return null;
  if (h.merchant === null || h.total_minor === null) return null;
  const pick = state?.candidates.find((c) => c.is_pick);
  if (!pick) return null;

  const pickOffer = state?.pick?.offer_id;
  if (pickOffer && h.offer_id) {
    // Bound to the displayed offer. This also catches a same-seller item change.
    if (pickOffer !== h.offer_id) return null;
  } else if (!isFixtureMode(health)) {
    // Live checkout needs both IDs. Never show a QR we cannot tie to the displayed offer.
    return null;
  } else if (pick.seller.name !== h.merchant) {
    // Legacy fixture payloads have no offer_id. Fixture mode only: match on merchant. Price is not
    // compared because a real checkout total includes tax.
    return null;
  }
  return { merchant: h.merchant, totalText: formatPrice(h.total_minor, h.currency), continueUrl: h.continue_url };
}

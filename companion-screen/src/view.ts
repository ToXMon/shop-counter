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
  pick: { product_id: string; reasons: string[] } | null;
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
  reasons: string[];
}

export interface View {
  card: CardView | null;
  fixtureMode: boolean;
}

// Minor units are cents: 19900 -> $199.00. Never divide anywhere else.
export function formatPrice(minor: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(minor / 100);
}

export function cardView(state: SessionState | null, health: Health | null): View {
  // The stub backend reports "stub". Say so on screen, so nobody mistakes fixtures for live data.
  const fixtureMode = health?.catalog === "stub" || health?.gemini === "stub";
  const pick = state?.candidates.find((c) => c.is_pick) ?? null;
  if (!state || !pick) return { card: null, fixtureMode };
  return {
    fixtureMode,
    card: {
      title: pick.title,
      priceText: formatPrice(pick.price_minor, pick.currency),
      sellerName: pick.seller.name,
      imageUrl: pick.image_url,
      reasons: state.pick?.reasons ?? [],
    },
  };
}

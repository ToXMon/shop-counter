// Pure view of the companion screen: props in, markup out. No fetch, no effects,
// so tests can render it with react-dom/server. Uses createElement (not JSX) because
// `node --test` strips types but cannot parse JSX.
import { createElement as h, type FormEvent } from "react";
import { cardView, type Health, type SessionState } from "./view.ts";

export interface ScreenProps {
  state: SessionState | null;
  health: Health | null;
  text: string;
  onText: (value: string) => void;
  onSend: (e: FormEvent) => void;
}

export function Screen({ state, health, text, onText, onSend }: ScreenProps) {
  const { card, fixtureMode } = cardView(state, health);
  return h("main", null,
    h("header", null,
      h("h1", null, "Shop Counter"),
      fixtureMode && h("span", { className: "badge", "data-testid": "fixture-badge" }, "FIXTURE MODE: stub data, not live"),
      !health && h("span", { className: "badge offline" }, "backend offline"),
    ),
    card
      ? h("article", { className: "card", "data-testid": "product-card" },
          card.imageUrl && h("img", { src: card.imageUrl, alt: "" }),
          h("div", null,
            h("h2", { className: "title" }, card.title),
            h("p", { className: "price", "data-testid": "price" }, card.priceText),
            h("p", { className: "seller" }, card.sellerName),
            card.reasons.map((r) => h("p", { className: "reason", key: r }, r)),
          ),
        )
      : h("p", { className: "empty" }, "Tell me what you are looking for."),
    h("form", { onSubmit: onSend },
      h("input", { value: text, onChange: (e) => onText(e.target.value), placeholder: "Type a request", "aria-label": "Request" }),
      h("button", { type: "submit" }, "Send"),
    ),
  );
}

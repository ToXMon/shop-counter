// Pure view of the companion screen: props in, markup out. No fetch, no effects,
// so tests can render it with react-dom/server. Uses createElement (not JSX) because
// `node --test` strips types but cannot parse JSX.
import { createElement as h, type FormEvent } from "react";
import { qrSvg } from "./qr.ts";
import { cardView, handoffView, type Health, type SessionState } from "./view.ts";

export interface ScreenProps {
  state: SessionState | null;
  health: Health | null;
  text: string;
  onText: (value: string) => void;
  onSend: (e: FormEvent) => void;
  onClear: () => void;
}

export function Screen({ state, health, text, onText, onSend, onClear }: ScreenProps) {
  const { card, fixtureMode } = cardView(state, health);
  const handoff = handoffView(state);
  const qr = handoff && qrSvg(handoff.continueUrl);
  return h("main", null,
    h("header", null,
      h("h1", null, "Shop Counter"),
      fixtureMode && h("span", { className: "badge", "data-testid": "fixture-badge" }, "FIXTURE MODE: stub data, not live"),
      !health && h("span", { className: "badge offline" }, "backend offline"),
      state && h("button", { type: "button", className: "clear", onClick: onClear }, "Clear session"),
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
    handoff && qr && h("section", { className: "handoff", "data-testid": "handoff" },
      h("svg", {
          className: "qr", "data-testid": "handoff-qr", role: "img", "aria-label": "QR code to review and pay on your phone",
          viewBox: `-4 -4 ${qr.size + 8} ${qr.size + 8}`, shapeRendering: "crispEdges",
        },
        h("rect", { x: -4, y: -4, width: qr.size + 8, height: qr.size + 8, fill: "#fff" }),
        h("path", { d: qr.path, fill: "#000" }),
      ),
      h("div", null,
        h("p", { className: "scan" }, "Scan to review and pay on your phone"),
        h("p", { className: "seller" }, `${handoff.merchant} · ${handoff.totalText}`),
      ),
    ),
    h("form", { onSubmit: onSend },
      h("input", { value: text, onChange: (e) => onText(e.target.value), placeholder: "Type a request", "aria-label": "Request" }),
      h("button", { type: "submit" }, "Send"),
    ),
  );
}

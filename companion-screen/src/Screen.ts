// Pure view of the companion screen: props in, markup out. No fetch, no effects,
// so tests can render it with react-dom/server. Uses createElement (not JSX) because
// `node --test` strips types but cannot parse JSX.
import { createElement as h, type FormEvent } from "react";
import { qrSvg } from "./qr.ts";
import { cardView, handoffView, type CardView, type Health, type SessionState } from "./view.ts";

export interface ScreenProps {
  state: SessionState | null;
  health: Health | null;
  text: string;
  onText: (value: string) => void;
  onSend: (e: FormEvent) => void;
  onClear: () => void;
  devControls: boolean;
}

function productView(card: CardView) {
  return h("article", { className: "product", "data-testid": "product-card" },
    card.imageUrl && h("img", { className: "art", src: card.imageUrl, alt: "" }),
    h("div", { className: "info" },
      h("h1", { className: "title" }, card.title),
      h("p", { className: "price", "data-testid": "price" }, card.priceText),
      h("p", { className: "seller" }, card.sellerName),
      card.reason && h("p", { className: "reason" }, card.reason),
      h("p", { className: "hint" }, "Tap the center of the device screen to open checkout."),
    ),
  );
}

function scanView(card: CardView | null, merchant: string, totalText: string, qr: { size: number; path: string }) {
  return h("section", { className: "scan", "data-testid": "handoff" },
    h("div", { className: "qrframe" },
      h("svg", {
          className: "qr", "data-testid": "handoff-qr", role: "img", "aria-label": "QR code to review and pay on your phone",
          // 4-module quiet zone on white, drawn inside the SVG so the margin scales with the code.
          viewBox: `-4 -4 ${qr.size + 8} ${qr.size + 8}`, shapeRendering: "crispEdges",
        },
        h("rect", { x: -4, y: -4, width: qr.size + 8, height: qr.size + 8, fill: "#fff" }),
        h("path", { d: qr.path, fill: "#000" }),
      ),
    ),
    h("div", { className: "scaninfo" },
      h("h1", { className: "scan-title" }, "Scan to review and pay on your phone."),
      h("p", { className: "scan-merchant" }, `${merchant} · ${totalText}`),
      h("p", { className: "scan-note" }, "Check the merchant and total before you pay."),
      card && h("div", { className: "summary", "data-testid": "offer-summary" },
        card.imageUrl && h("img", { className: "thumb", src: card.imageUrl, alt: "" }),
        h("span", null, `${card.title} · ${card.priceText}`),
      ),
    ),
  );
}

export function Screen({ state, health, text, onText, onSend, onClear, devControls }: ScreenProps) {
  const { card, fixtureMode } = cardView(state, health);
  const handoff = handoffView(state, health);
  const qr = handoff && qrSvg(handoff.continueUrl);
  return h("main", { className: "stage" },
    h("header", { className: "bar" },
      h("span", { className: "brand" }, "Shop Counter"),
      fixtureMode && h("span", { className: "chip", "data-testid": "fixture-badge" }, "Fixture mode · stub data, not live"),
      !health && h("span", { className: "chip offline" }, "Backend offline"),
      state && h("button", { type: "button", className: "clear", onClick: onClear }, "Clear session"),
    ),
    handoff && qr
      ? scanView(card, handoff.merchant, handoff.totalText, qr)
      : card
        ? productView(card)
        : h("p", { className: "empty" }, "Tell me what you are looking for."),
    // Test and fallback input only (?dev). The shopper talks and taps on the device.
    devControls && h("form", { className: "dev", onSubmit: onSend },
      h("input", { value: text, onChange: (e) => onText(e.target.value), placeholder: "Type a request", "aria-label": "Request" }),
      h("button", { type: "submit" }, "Send"),
    ),
  );
}

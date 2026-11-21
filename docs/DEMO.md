# Shop Counter demo runbook

2026-11-21 · Owner: Tolu · Freeze 16:15 ET. Submit by 17:00 ET.

**The judge talks and taps on the CoreS3, looks at the Mac, and reviews checkout on their phone.** The Mac is a companion display, not a second set of shopping controls. The QR is a pull handoff, not a push notification. A tap requests checkout. It does not authorize payment.

## Three-minute live demo

1. Before the judge arrives, connect the CoreS3 on the private network and pair it to the Mac's fresh session. Open the live companion screen full-screen. Verify the frontend proxy reaches the real backend, not the stub, and ensure there is no leftover QR.
2. Say: “Hold the bottom-left of the screen and tell it what you’re looking for. Release when you’re done.” The draft firmware caps a clip at five seconds. You can seed the demo with “Find me something from Monday Cartoons under fifty dollars.” Let the judge give an unrehearsed follow-up; “Actually, something digital under a dollar” is a rehearsal example.
3. The recommendation should be spoken aloud. Point to the Mac for the item, seller and current price. The CoreS3 is for short status and actions. The current draft displays the reply as text; playback still needs proving. Say where the audio comes from if you use Mac playback.
4. Once the judge sees the offer they want, say: “Tap bottom-center to open a checkout QR on the Mac.” Use the touch control by default. Use an RFID demo tag only if it works end to end. No one needs to tap a payment card.
5. The Mac displays “Scan to review and pay on your phone” and a QR. The judge opens their phone camera, scans, and opens the merchant checkout. Ask them to verify Monday Cartoons, Digital Sticker, quantity one, and the actual total. Stop before payment for the demo. Any real purchase is their choice on the phone.
6. If there is time, show measured evidence from unrehearsed inputs. Name Hydrogen, Neon and the Decisions API only for calls actually exercised. Claim a hosted Managed Agent run only if it completed.

Do not promise $0.99. The product page last showed $0.50; a test checkout returned $0.54 with tax. Recheck after any merchant change. The Digital Sticker is a verified merchant storefront variant; do not describe it as a Global Catalog search result.

## One-minute submission video

Film landscape with a second phone or ask someone to film; use your phone as the shopper phone. Silence notifications. Capture the real device audio or the real fallback audio. Do not film checkout URLs, a readable checkout QR, contact details, or payment fields. Frame the scan from the side or mask the QR before upload. The point of the simulation is to stop before money moves, not to fake the handoff.

| Time | Shot and sound |
| --- | --- |
| 0–5 s | CoreS3 and Mac in one frame. “Shop Counter lets you shop by voice and pay on your own phone.” |
| 5–19 s | Hold bottom-left and speak the first request. Keep the real spoken reply and laptop card in the shot. |
| 19–32 s | Say “Actually, something digital under a dollar.” Show the recommendation change to the Digital Sticker. |
| 32–45 s | Close up on the bottom-center tap. Cut to the Mac’s scan instruction and the phone in position. “That tap asks for checkout. It doesn’t charge me.” |
| 45–55 s | Show the phone's actual merchant checkout summary. Keep the item and live price legible. No payment. |
| 55–60 s | “Talk at the counter. Review on your phone. You decide whether to pay.” |

Aim for 58–59 seconds. If cutting a long wait, mark the cut as shortened rather than implying that latency was real-time. A fixture rehearsal is useful for framing, not evidence of a working live checkout. If a feature is still missing, label the limitation and show the portion that actually works.

## Build checkpoints

- **Backend / Antigravity:** Get a committed build running separately from the stub. Prove the same session across audio, pick, tap and QR. Agree one offer identifier or revision with both lanes. For live checkout, require the tap to reference that offer and reject missing or stale references. Keep checkout-bearing state on the Mac, invalidate it on offer change or clear, and never log the URL. Verify the two Gemini 4 roles, Decisions API, and real audio.
- **Screen / Claude Code:** `e9b3479` has QR and Clear. Mac build and nine tests passed. Fixture browser smoke was reported by Claude. Prioritize browser push-to-talk and playback fallback. Coordinate offer binding with backend; same-seller changes currently rely on backend invalidation. Verify a late response cannot redisplay the old QR. Do not restart the shared stub.
- **Device / Codex:** The touch intent checkpoint worked against the stub. Draft audio capture was in an uncommitted diff at the last check. Confirm bottom-left hold/release, bottom-center tap, and reply audio on the flashed board. Bind the tap to the displayed offer with backend. If hardware audio slips, keep the device tap and use the Mac mic/speaker. State which hardware path actually ran.
- **Integration / Tolu:** First prove laptop request → live sticker → explicit intent → phone checkout. Then prove hardware tap, then live voice. Rehearse twice from a fresh session. Change or clear an offer and check that the old QR disappears. Scan a fresh QR on a phone before filming. Leave RFID and styling until the working loop is recorded.

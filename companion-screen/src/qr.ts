// Local QR generation. The link goes into the encoder and nowhere else:
// no network, no canvas, no text output. Returns an SVG path of dark modules.
import QRCode from "qrcode";

export interface QrSvg {
  size: number; // modules per side
  path: string; // one unit square per dark module
}

export function qrSvg(text: string): QrSvg {
  const { modules } = QRCode.create(text, { errorCorrectionLevel: "M" });
  const size = modules.size;
  let path = "";
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      if (modules.get(row, col)) path += `M${col},${row}h1v1h-1z`;
    }
  }
  return { size, path };
}

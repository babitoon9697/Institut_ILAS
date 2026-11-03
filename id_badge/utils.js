/**
 * utils.js — Génération QR + Barcode (helpers pure, sans rendu).
 */
import QRCode from "qrcode.react";
import JsBarcode from "jsbarcode";

/**
 * Retourne un composant QRCode React configuré pour la carte.
 */
export function makeQR(data, size = 100) {
  return (
    <QRCode
      value={data}
      size={size}
      bgColor="#ffffff"
      fgColor="#1B3D8F"
      level="M"
      includeMargin={false}
    />
  );
}

/**
 * Rend un barcode CODE128 dans un élément SVG.
 * @param {SVGElement} el - cible (ref)
 * @param {string} data
 */
export function renderBarcode(el, data) {
  if (!el || !data) return;
  try {
    JsBarcode(el, data, {
      format: "CODE128",
      displayValue: false,
      width: 1.2,
      height: 42,
      margin: 0,
      lineColor: "#1B3D8F",
      background: "#ffffff",
    });
  } catch (e) {
    console.warn("Barcode invalide :", data);
  }
}

/**
 * Construit les données QR par défaut d'un élève/enseignant.
 */
export function badgeQRData(person) {
  const role = person?.role === "teacher" ? "INSTRUCTOR" : "STUDENT";
  return `ILAS|${role}|${person?.id || ""}|${person?.fullName || ""}`;
}

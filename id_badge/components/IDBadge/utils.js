import React from "react";
import JsBarcode from "jsbarcode";

/**
 * Renders a CODE128 barcode into an SVG DOM element using JsBarcode
 * @param {SVGElement} svgEl Target SVG DOM node
 * @param {string} code Data string to encode
 */
export function renderBarcode(svgEl, code) {
  if (!svgEl || !code) return;
  try {
    JsBarcode(svgEl, code, {
      format: "CODE128",
      displayValue: false, // No text below barcode as specified
      margin: 0,
      width: 1.5,
      height: 48,
      lineColor: "#1B3D8F",
      background: "#ffffff",
    });
  } catch (err) {
    console.warn("Invalid barcode data:", code, err);
  }
}

/**
 * Circular vector SVG flag components (UK, Belgium, France, Spain)
 * 24px circular diameter, high quality print-ready vector renderings
 */
export const VectorFlags = {
  uk: (
    <svg viewBox="0 0 60 60" width="24" height="24" style={{ borderRadius: "50%" }}>
      <clipPath id="uk-circle"><circle cx="30" cy="30" r="30"/></clipPath>
      <g clipPath="url(#uk-circle)">
        <rect width="60" height="60" fill="#00247D"/>
        <path d="M0,0 L60,60 M60,0 L0,60" stroke="#FFFFFF" strokeWidth="10"/>
        <path d="M0,0 L60,60 M60,0 L0,60" stroke="#CF142B" strokeWidth="6"/>
        <path d="M30,0 V60 M0,30 H60" stroke="#FFFFFF" strokeWidth="14"/>
        <path d="M30,0 V60 M0,30 H60" stroke="#CF142B" strokeWidth="8"/>
      </g>
    </svg>
  ),
  be: (
    <svg viewBox="0 0 60 60" width="24" height="24" style={{ borderRadius: "50%" }}>
      <clipPath id="be-circle"><circle cx="30" cy="30" r="30"/></clipPath>
      <g clipPath="url(#be-circle)">
        <rect x="0" y="0" width="20" height="60" fill="#000000"/>
        <rect x="20" y="0" width="20" height="60" fill="#FDDA24"/>
        <rect x="40" y="0" width="20" height="60" fill="#EF3340"/>
      </g>
    </svg>
  ),
  fr: (
    <svg viewBox="0 0 60 60" width="24" height="24" style={{ borderRadius: "50%" }}>
      <clipPath id="fr-circle"><circle cx="30" cy="30" r="30"/></clipPath>
      <g clipPath="url(#fr-circle)">
        <rect x="0" y="0" width="20" height="60" fill="#002654"/>
        <rect x="20" y="0" width="20" height="60" fill="#FFFFFF"/>
        <rect x="40" y="0" width="20" height="60" fill="#CE1126"/>
      </g>
    </svg>
  ),
  es: (
    <svg viewBox="0 0 60 60" width="24" height="24" style={{ borderRadius: "50%" }}>
      <clipPath id="es-circle"><circle cx="30" cy="30" r="30"/></clipPath>
      <g clipPath="url(#es-circle)">
        <rect x="0" y="0" width="60" height="15" fill="#AA1529"/>
        <rect x="0" y="15" width="60" height="30" fill="#F1BF00"/>
        <rect x="0" y="45" width="60" height="15" fill="#AA1529"/>
      </g>
    </svg>
  ),
};

export const EMOJI_FLAGS = {
  uk: "🇬🇧",
  be: "🇧🇪",
  fr: "🇫🇷",
  es: "🇪🇸",
};

import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";

/**
 * Exports card DOM element as high-res 300 DPI PNG image
 * @param {HTMLElement} cardEl - Target ID badge card element
 * @param {string} name - File label (e.g. person's full name)
 */
export async function exportBadgePNG(cardEl, name = "badge") {
  if (!cardEl) return;
  try {
    const canvas = await html2canvas(cardEl, {
      scale: 3, // 3x scaling for ~300 DPI print quality
      backgroundColor: null,
      useCORS: true,
      logging: false,
      allowTaint: true,
    });
    const dataUrl = canvas.toDataURL("image/png");
    const link = document.createElement("a");
    link.download = `${slugify(name)}-id-badge.png`;
    link.href = dataUrl;
    link.click();
  } catch (err) {
    console.error("Error exporting PNG:", err);
  }
}

/**
 * Exports card DOM element as exact CR80 size PDF (85.6mm x 54mm)
 * @param {HTMLElement} cardEl - Target ID badge card element
 * @param {string} name - File label
 */
export async function exportBadgePDF(cardEl, name = "badge") {
  if (!cardEl) return;
  try {
    const canvas = await html2canvas(cardEl, {
      scale: 3,
      backgroundColor: null,
      useCORS: true,
      logging: false,
      allowTaint: true,
    });
    const imgData = canvas.toDataURL("image/png");

    // Standard CR80 Dimensions in mm
    const CARD_WIDTH_MM = 85.6;
    const CARD_HEIGHT_MM = 54;

    const pdf = new jsPDF({
      orientation: "landscape",
      unit: "mm",
      format: [CARD_WIDTH_MM, CARD_HEIGHT_MM],
      compress: true,
    });

    pdf.addImage(imgData, "PNG", 0, 0, CARD_WIDTH_MM, CARD_HEIGHT_MM);
    pdf.save(`${slugify(name)}-id-badge.pdf`);
  } catch (err) {
    console.error("Error exporting PDF:", err);
  }
}

function slugify(str) {
  return String(str || "badge")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
}

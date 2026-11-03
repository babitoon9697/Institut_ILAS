import React, { useRef, useEffect, useState } from "react";
import QRCode from "qrcode.react";
import { Phone, Mail, Download, FileText, Printer, Star, RotateCw, ShieldCheck } from "lucide-react";
import styles from "./IDBadge.module.css";
import { renderBarcode, VectorFlags } from "./utils.js";
import { exportBadgePNG, exportBadgePDF } from "../../utils/exportBadge.js";

/**
 * IDBadge — Flagship Dual-Tone ILAS Modern Card (Recto & Verso)
 * Dynamic website pulled from system settings!
 */
export default function IDBadge({
  photo = "",
  fullName = "SARA ALAOUI",
  role = "LANGUAGE INSTRUCTOR",
  id = "1234567890",
  phone = "+33 6 12 34 56 78",
  email = "info@ilas-ecole.com",
  website = "www.institut.ma",
  schoolYear = "2025/2026",
  qrCodeData = "1234567890",
  barcodeData = "1234567890",
  flags = ["uk", "be", "fr", "es"],
  conditions = [
    "1. Cette carte est strictly personnelle, nominative et incessible.",
    "2. Obligatoire pour accéder aux salles de cours et événements de l'institut.",
    "3. En cas de perte ou vol, signaler immédiatement à l'administration.",
    "4. Demeure la propriété exclusive de l'INSTITUT ILAS.",
  ],
  showActions = true,
}) {
  const cardRef = useRef(null);
  const barcodeRef = useRef(null);
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    if (barcodeRef.current && barcodeData) {
      renderBarcode(barcodeRef.current, barcodeData);
    }
  }, [barcodeData, flipped]);

  const initial = (fullName || "U").trim().charAt(0).toUpperCase();

  return (
    <div className={styles.wrapper}>
      {/* ===== 3D FLIPPABLE BADGE CARD ===== */}
      <div className={`${styles.cardContainer} ${flipped ? styles.isFlipped : ""}`}>
        
        {/* RECTO (FRONT SIDE) */}
        <div ref={cardRef} className={`${styles.card} ${styles.cardFront}`}>
          <div className={styles.cardHeaderBg}></div>
          <div className={styles.accentWave}></div>

          {/* Header */}
          <div className={styles.cardHeader}>
            <div className={styles.brandBox}>
              <Star size={16} fill="#FFD47A" color="#FFD47A" />
              <div className={styles.brandLogoText}>
                <div className={styles.brandName}>INSTITUT <span>ILAS</span></div>
                <div className={styles.brandSub}>LANGUES & FORMATION CONTINUE</div>
              </div>
            </div>
            <div className={styles.yearPill}>{schoolYear}</div>
          </div>

          {/* Body */}
          <div className={styles.cardBody}>
            {/* Photo */}
            <div className={styles.leftCol}>
              <div className={styles.photoFrame}>
                {photo ? (
                  <img src={photo} alt={fullName} className={styles.photo} />
                ) : (
                  <span>{initial}</span>
                )}
              </div>
            </div>

            {/* Details */}
            <div className={styles.rightCol}>
              <div className={styles.personName} title={fullName}>{fullName}</div>

              <div className={styles.roleTagRow}>
                <div className={styles.roleBadge}>{role}</div>
                <div className={styles.idCodeText}>ID: #{id}</div>
              </div>

              <div className={styles.contactGroup}>
                <div className={styles.contactItem} title={phone}>
                  <Phone className={styles.contactIcon} size={10} />
                  <span>{phone}</span>
                </div>
                <div className={styles.contactItem} title={email}>
                  <Mail className={styles.contactIcon} size={10} />
                  <span>{email}</span>
                </div>
              </div>

              <div className={styles.flagsBar}>
                {flags.map((flagKey) => (
                  <div key={flagKey} className={styles.flagSphere} title={flagKey.toUpperCase()}>
                    {VectorFlags[flagKey] || <span>🌐</span>}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className={styles.cardFooter}>
            <div className={styles.footerLeft}>
              <div className={styles.qrBox}>
                <QRCode value={qrCodeData || id} bgColor="#ffffff" fgColor="#0B3D6E" level="M" renderAs="svg" />
              </div>
              <div className={styles.footerText}>
                <div className={styles.footerId}>ID: {id}</div>
                <div className={styles.footerSub}>ILAS CARTE OFFICIELLE</div>
              </div>
            </div>

            <div className={styles.barcodeBox}>
              <svg ref={barcodeRef} className={styles.barcodeSvg} />
            </div>
          </div>
        </div>

        {/* VERSO (BACK SIDE) */}
        <div className={`${styles.card} ${styles.cardBack}`}>
          <div className={styles.cardHeaderBg}></div>
          <div className={styles.accentWave}></div>

          {/* Header */}
          <div className={styles.cardHeader}>
            <div className={styles.brandBox}>
              <ShieldCheck size={16} color="#FFD47A" />
              <div className={styles.brandLogoText}>
                <div className={styles.brandName}>INSTITUT <span>ILAS</span></div>
                <div className={styles.brandSub}>RÈGLEMENT INTÉRIEUR & CONDITIONS</div>
              </div>
            </div>
            <div className={styles.yearPill}>{schoolYear}</div>
          </div>

          {/* Body */}
          <div className={styles.backBody}>
            <div className={styles.conditionsBox}>
              <div className={styles.condTitle}>Conditions Générales d'Utilisation :</div>
              <div className={styles.condList}>
                {Array.isArray(conditions)
                  ? conditions.map((c, i) => (
                      <div key={i} className={styles.condItem}>
                        <span>{c}</span>
                      </div>
                    ))
                  : String(conditions)
                      .split("\n")
                      .map((c, i) => (
                        <div key={i} className={styles.condItem}>
                          <span>• {c}</span>
                        </div>
                      ))}
              </div>
            </div>

            <div className={styles.backBottom}>
              <div className={styles.stampBox}>
                <div className={styles.stampTitle}>Cachet & Signature</div>
                <div className={styles.stampArea}>Direction ILAS</div>
              </div>
              <div className={styles.noticePill}>
                ⚠️ Si trouvée, merci de retourner cette carte à l'accueil de l'INSTITUT ILAS.
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className={styles.backFooter}>
            <div>📞 {phone}</div>
            <div>🌐 <span>{website}</span></div>
          </div>
        </div>

      </div>

      {/* Toolbar */}
      {showActions && (
        <div className={styles.actionsBar}>
          <button className={styles.actionBtn} onClick={() => setFlipped(!flipped)}>
            <RotateCw size={16} /> Flip Card ({flipped ? "Show Front" : "Show Back"})
          </button>
          <button className={styles.actionBtn} onClick={() => exportBadgePNG(cardRef.current, fullName)}>
            <Download size={16} /> Download PNG
          </button>
          <button className={styles.actionBtn} onClick={() => exportBadgePDF(cardRef.current, fullName)}>
            <FileText size={16} /> Download PDF
          </button>
          <button className={`${styles.actionBtn} ${styles.actionBtnSecondary}`} onClick={() => window.print()}>
            <Printer size={16} /> Print Badge
          </button>
        </div>
      )}
    </div>
  );
}

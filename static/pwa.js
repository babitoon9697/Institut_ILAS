/**
 * Institut ILAS - PWA Progressive Web App Controller
 * Enables seamless mobile installation (Android/iOS) for teachers and staff.
 */
(function() {
  'use strict';

  let deferredPrompt = null;
  const STORAGE_KEY_DISMISSED = 'ilas_pwa_dismissed_until';
  const STORAGE_KEY_INSTALLED = 'ilas_pwa_installed';

  // Check if app is running in standalone mode (already installed on home screen)
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || 
                       window.navigator.standalone === true ||
                       document.referrer.includes('android-app://');

  // Check device OS
  const ua = navigator.userAgent || '';
  const isIos = /iPad|iPhone|iPod/.test(ua) && !window.MSStream;
  const isAndroid = /Android/i.test(ua);
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua) || (window.innerWidth <= 768);

  // Detect in-app browsers (WhatsApp, Facebook, Instagram, etc.)
  const isInApp = /FBAN|FBAV|Instagram|WhatsApp|Line|Twitter|Snapchat/i.test(ua);

  // 1. On desktop localhost / 127.0.0.1: unregister SW and purge cache so local work is direct and never intercepted
  const isLocalHost = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  if (isLocalHost) {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations().then(function(regs) {
        for (var i = 0; i < regs.length; i++) {
          regs[i].unregister();
        }
      });
    }
    if ('caches' in window) {
      caches.keys().then(function(names) {
        for (var j = 0; j < names.length; j++) {
          caches.delete(names[j]);
        }
      });
    }
  } else if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('/sw.js', { scope: '/' })
        .then(function(reg) {
          // SW registered successfully
        })
        .catch(function(err) {
          console.warn('[PWA] Service Worker registration failed:', err);
        });
    });
  }

  // 2. If running standalone, remember it and hide install prompts
  if (isStandalone) {
    try {
      localStorage.setItem(STORAGE_KEY_INSTALLED, 'true');
    } catch(e) {}
    document.documentElement.classList.add('pwa-standalone');
    // Hide any on-page install cards
    window.addEventListener('DOMContentLoaded', function() {
      const cards = document.querySelectorAll('#pwaLoginInstallCard, #pwaInstallBtn, .pwa-install-trigger');
      cards.forEach(function(el) { el.style.display = 'none'; });
    });
    return;
  }

  // 3. Helper for snooze
  function isDismissedRecently() {
    try {
      const until = sessionStorage.getItem(STORAGE_KEY_DISMISSED);
      if (!until) return false;
      return Date.now() < parseInt(until, 10);
    } catch(e) {
      return false;
    }
  }

  function dismissBanner(hours) {
    try {
      const expiry = Date.now() + (hours || 2) * 60 * 60 * 1000;
      sessionStorage.setItem(STORAGE_KEY_DISMISSED, expiry.toString());
    } catch(e) {}
    hideInstallBanner();
  }

  // 4. Create and inject PWA Banner & Modals UI
  function createPwaElements() {
    if (document.getElementById('ilas-pwa-container')) return;

    const container = document.createElement('div');
    container.id = 'ilas-pwa-container';
    container.innerHTML = `
      <style>
        #ilas-pwa-banner {
          position: fixed;
          bottom: 14px;
          left: 12px;
          right: 12px;
          max-width: 480px;
          margin: 0 auto;
          background: #ffffff;
          border-radius: 18px;
          box-shadow: 0 16px 40px rgba(11, 61, 110, 0.28), 0 2px 8px rgba(0,0,0,0.1);
          border: 1.5px solid #93c5fd;
          padding: 14px 16px;
          z-index: 99999;
          display: none;
          animation: ilasPwaSlideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1);
          font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
          box-sizing: border-box;
        }
        @keyframes ilasPwaSlideUp {
          from { transform: translateY(120%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .ilas-pwa-header {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .ilas-pwa-icon {
          width: 46px;
          height: 46px;
          border-radius: 12px;
          box-shadow: 0 4px 10px rgba(31,111,235,0.25);
          flex-shrink: 0;
          object-fit: cover;
        }
        .ilas-pwa-text {
          flex: 1;
          min-width: 0;
        }
        .ilas-pwa-title {
          font-size: 13.5px;
          font-weight: 800;
          color: #0B3D6E;
          margin: 0 0 2px 0;
          line-height: 1.25;
        }
        .ilas-pwa-desc {
          font-size: 11px;
          color: #475569;
          margin: 0;
          line-height: 1.35;
        }
        .ilas-pwa-close {
          background: #f1f5f9;
          border: none;
          color: #64748b;
          width: 26px;
          height: 26px;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 13px;
          font-weight: bold;
          flex-shrink: 0;
        }
        .ilas-pwa-actions {
          display: flex;
          gap: 8px;
          margin-top: 10px;
        }
        .ilas-pwa-btn-install {
          flex: 1;
          background: linear-gradient(135deg, #0B3D6E 0%, #1f6feb 100%);
          color: #ffffff;
          border: none;
          border-radius: 10px;
          padding: 10px 14px;
          font-size: 13px;
          font-weight: 800;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          box-shadow: 0 4px 12px rgba(31,111,235,0.3);
        }
        .ilas-pwa-btn-dismiss {
          background: #f8fafc;
          border: 1px solid #cbd5e1;
          color: #475569;
          border-radius: 10px;
          padding: 10px 14px;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
        }

        /* Generic / Android Instruction Modal */
        .ilas-pwa-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(15, 23, 42, 0.7);
          backdrop-filter: blur(4px);
          z-index: 100000;
          display: none;
          align-items: flex-end;
          justify-content: center;
          padding: 14px;
          box-sizing: border-box;
          animation: ilasFadeIn 0.2s ease;
        }
        @keyframes ilasFadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .ilas-pwa-card {
          background: #ffffff;
          border-radius: 24px;
          max-width: 440px;
          width: 100%;
          padding: 22px 18px;
          box-sizing: border-box;
          box-shadow: 0 24px 50px rgba(0,0,0,0.35);
          text-align: center;
          position: relative;
        }
        .ilas-pwa-steps {
          text-align: left;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 14px;
          padding: 14px 16px;
          margin: 14px 0 16px 0;
        }
        .ilas-pwa-step {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          margin-bottom: 12px;
          font-size: 13px;
          color: #1e293b;
          line-height: 1.4;
        }
        .ilas-pwa-step:last-child {
          margin-bottom: 0;
        }
        .ilas-pwa-num {
          background: #0B3D6E;
          color: #fff;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: 800;
          flex-shrink: 0;
        }
      </style>

      <!-- Bottom Install Banner -->
      <div id="ilas-pwa-banner">
        <div class="ilas-pwa-header">
          <img src="/static/icons/icon-192.png" alt="ILAS" class="ilas-pwa-icon">
          <div class="ilas-pwa-text">
            <div class="ilas-pwa-title">📲 Installer l'application Institut ILAS</div>
            <div class="ilas-pwa-desc">Accédez directement à l'émargement & cours sans retaper l'adresse !</div>
          </div>
          <button class="ilas-pwa-close" onclick="window.dismissPwaBanner()" title="Fermer">✕</button>
        </div>
        <div class="ilas-pwa-actions">
          <button class="ilas-pwa-btn-install" onclick="window.triggerPWAInstall()">
            <span>📥</span>
            <span>Installer l'Application</span>
          </button>
          <button class="ilas-pwa-btn-dismiss" onclick="window.dismissPwaBanner()">
            Plus tard
          </button>
        </div>
      </div>

      <!-- Android / Chrome / Generic Modal -->
      <div id="ilas-android-modal" class="ilas-pwa-modal-overlay" onclick="if(event.target===this) window.hideAndroidModal()">
        <div class="ilas-pwa-card">
          <div style="font-size:36px; margin-bottom:6px;">📲</div>
          <h3 style="margin:0 0 6px 0; font-size:17px; font-weight:800; color:#0B3D6E;">
            Installer sur votre téléphone
          </h3>
          <p style="margin:0; font-size:12px; color:#64748b;">
            Ajoutez l'application sur votre écran d'accueil en 2 étapes rapides :
          </p>

          <div class="ilas-pwa-steps">
            ${isInApp ? `
              <div class="ilas-pwa-step" style="background:#fee2e2; padding:8px 10px; border-radius:8px; color:#991b1b; font-weight:600;">
                ⚠️ Vous êtes dans WhatsApp / Messagerie. Touchez les 3 points <strong>(⋮)</strong> en haut et choisissez <strong>« Ouvrir dans Chrome »</strong>.
              </div>
            ` : ''}
            <div class="ilas-pwa-step">
              <span class="ilas-pwa-num">1</span>
              <div>Touchez le menu <strong>(⋮)</strong> avec les 3 petits points verticaux en haut à droite de votre navigateur.</div>
            </div>
            <div class="ilas-pwa-step">
              <span class="ilas-pwa-num">2</span>
              <div>Appuyez sur <strong>« Installer l'application »</strong> ou <strong>« Ajouter à l'écran d'accueil »</strong> 📲.</div>
            </div>
            <div class="ilas-pwa-step">
              <span class="ilas-pwa-num">3</span>
              <div>Validez sur <strong>« Installer »</strong>. L'icône de l'Institut ILAS apparaîtra sur votre écran d'accueil !</div>
            </div>
          </div>

          <button onclick="window.hideAndroidModal()" style="width:100%; background:linear-gradient(135deg, #0B3D6E 0%, #1f6feb 100%); color:#fff; border:none; border-radius:12px; padding:12px; font-size:14px; font-weight:800; cursor:pointer;">
            ✓ J'ai compris
          </button>
        </div>
      </div>

      <!-- iOS Instruction Modal -->
      <div id="ilas-ios-modal" class="ilas-pwa-modal-overlay" onclick="if(event.target===this) window.hideIosModal()">
        <div class="ilas-pwa-card">
          <div style="font-size:36px; margin-bottom:6px;">🍎</div>
          <h3 style="margin:0 0 6px 0; font-size:17px; font-weight:800; color:#0B3D6E;">
            Installer sur iPhone / iPad
          </h3>
          <p style="margin:0; font-size:12px; color:#64748b;">
            Dans Safari, ajoutez l'application à votre écran d'accueil :
          </p>

          <div class="ilas-pwa-steps">
            ${isInApp ? `
              <div class="ilas-pwa-step" style="background:#fee2e2; padding:8px 10px; border-radius:8px; color:#991b1b; font-weight:600;">
                ⚠️ Touchez les 3 points <strong>(⋮)</strong> ou l'icône de boussole pour <strong>« Ouvrir dans Safari »</strong>.
              </div>
            ` : ''}
            <div class="ilas-pwa-step">
              <span class="ilas-pwa-num">1</span>
              <div>Touchez l'icône de <strong>Partage</strong> (<span style="font-size:15px;">⎋</span> ou rectangle avec flèche vers le haut) dans la barre Safari en bas.</div>
            </div>
            <div class="ilas-pwa-step">
              <span class="ilas-pwa-num">2</span>
              <div>Faites défiler le menu et touchez <strong>« Sur l'écran d'accueil »</strong> (icône ➕).</div>
            </div>
            <div class="ilas-pwa-step">
              <span class="ilas-pwa-num">3</span>
              <div>Touchez <strong>« Ajouter »</strong> en haut à droite pour confirmer.</div>
            </div>
          </div>

          <button onclick="window.hideIosModal()" style="width:100%; background:linear-gradient(135deg, #0B3D6E 0%, #1f6feb 100%); color:#fff; border:none; border-radius:12px; padding:12px; font-size:14px; font-weight:800; cursor:pointer;">
            ✓ J'ai compris
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(container);
  }

  function showInstallBanner() {
    if (isStandalone || isDismissedRecently()) return;
    const banner = document.getElementById('ilas-pwa-banner');
    if (banner) {
      banner.style.display = 'block';
    }
  }

  function hideInstallBanner() {
    const banner = document.getElementById('ilas-pwa-banner');
    if (banner) {
      banner.style.display = 'none';
    }
  }

  function showIosModal() {
    const modal = document.getElementById('ilas-ios-modal');
    if (modal) modal.style.display = 'flex';
  }

  function hideIosModal() {
    const modal = document.getElementById('ilas-ios-modal');
    if (modal) modal.style.display = 'none';
  }

  function showAndroidModal() {
    const modal = document.getElementById('ilas-android-modal');
    if (modal) modal.style.display = 'flex';
  }

  function hideAndroidModal() {
    const modal = document.getElementById('ilas-android-modal');
    if (modal) modal.style.display = 'none';
  }

  // Reveal triggers on page
  function revealPageTriggers() {
    if (isStandalone) return;
    const triggers = document.querySelectorAll('#pwaInstallBtn, #pwaLoginInstallCard, .pwa-install-trigger');
    triggers.forEach(function(el) {
      el.style.display = (el.tagName === 'BUTTON' || el.classList.contains('btn')) ? 'inline-flex' : 'block';
    });
  }

  // 5. Intercept beforeinstallprompt (when available)
  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
    revealPageTriggers();
    if (isMobile && !isDismissedRecently()) {
      showInstallBanner();
    }
  });

  // 6. Handle app installed
  window.addEventListener('appinstalled', function() {
    deferredPrompt = null;
    hideInstallBanner();
    hideAndroidModal();
    hideIosModal();
    try {
      localStorage.setItem(STORAGE_KEY_INSTALLED, 'true');
    } catch(e) {}
    const triggers = document.querySelectorAll('#pwaInstallBtn, #pwaLoginInstallCard, .pwa-install-trigger');
    triggers.forEach(function(el) { el.style.display = 'none'; });
    showToast('🎉 Application installée avec succès ! Retrouvez-la sur votre écran d\'accueil.');
  });

  function showToast(msg) {
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed; top:20px; left:50%; transform:translateX(-50%); background:#0f172a; color:#fff; padding:12px 20px; border-radius:12px; font-size:13px; font-weight:700; z-index:999999; box-shadow:0 10px 25px rgba(0,0,0,0.3); text-align:center; max-width:90%; animation:ilasFadeIn 0.3s ease;';
    toast.innerText = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.5s';
      setTimeout(() => toast.remove(), 500);
    }, 4500);
  }

  // Main click handler
  window.triggerPWAInstall = function() {
    if (deferredPrompt) {
      hideInstallBanner();
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function(choiceResult) {
        if (choiceResult.outcome === 'accepted') {
          console.log('[PWA] Installed');
        } else {
          dismissBanner(1);
        }
        deferredPrompt = null;
      });
    } else if (isIos) {
      hideInstallBanner();
      showIosModal();
    } else {
      // Android / other browsers when prompt is blocked on HTTP or not ready
      hideInstallBanner();
      showAndroidModal();
    }
  };

  window.dismissPwaBanner = function() {
    dismissBanner(1);
  };

  window.hideIosModal = hideIosModal;
  window.hideAndroidModal = hideAndroidModal;

  // Auto init
  function initPwa() {
    createPwaElements();
    revealPageTriggers();

    // Show banner on mobile automatically after 800ms
    if (isMobile && !isStandalone && !isDismissedRecently()) {
      setTimeout(showInstallBanner, 800);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPwa);
  } else {
    initPwa();
  }
})();

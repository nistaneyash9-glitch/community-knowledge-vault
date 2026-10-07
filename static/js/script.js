/**
 * COMMUNITY KNOWLEDGE VAULT (CKV)
 * Frontend Interactivity Script
 */

document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initSearchModal();
});

/* ==========================================================================
   HEADER & NAVIGATION
   ========================================================================== */
function initHeader() {
  const header = document.querySelector('.site-header');
  const toggleBtn = document.querySelector('.mobile-nav-toggle');
  const navMenu = document.querySelector('.main-nav');

  // Sticky header background on scroll
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      header?.classList.add('scrolled');
    } else {
      header?.classList.remove('scrolled');
    }
  });

  // Mobile navigation drawer toggle
  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', () => {
      navMenu.classList.toggle('mobile-open');
      const isExpanded = navMenu.classList.contains('mobile-open');
      toggleBtn.setAttribute('aria-expanded', isExpanded);
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!navMenu.contains(e.target) && !toggleBtn.contains(e.target)) {
        navMenu.classList.remove('mobile-open');
      }
    });
  }
}

/* ==========================================================================
   SEARCH MODAL OVERLAY
   ========================================================================== */
function initSearchModal() {
  const searchTriggers = document.querySelectorAll('.search-trigger-btn');
  const searchModal = document.getElementById('searchModal');
  const searchInput = document.getElementById('modalSearchInput');
  const closeBtn = document.getElementById('closeSearchModal');

  if (!searchModal) return;

  function openSearch() {
    searchModal.classList.add('active');
    setTimeout(() => searchInput?.focus(), 100);
  }

  function closeSearch() {
    searchModal.classList.remove('active');
  }

  searchTriggers.forEach(btn => btn.addEventListener('click', openSearch));
  closeBtn?.addEventListener('click', closeSearch);

  // Keyboard shortcut '/' to open, 'Escape' to close
  window.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
      e.preventDefault();
      openSearch();
    }
    if (e.key === 'Escape' && searchModal.classList.contains('active')) {
      closeSearch();
    }
  });

  // Close when clicking modal backdrop
  searchModal.addEventListener('click', (e) => {
    if (e.target === searchModal) {
      closeSearch();
    }
  });
}

/* ==========================================================================
   TOAST NOTIFICATION SYSTEM
   ========================================================================== */
function showToast(message) {
  let toast = document.getElementById('ckvToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'ckvToast';
    toast.className = 'toast-notification';
    toast.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--accent-lime); flex-shrink: 0;">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      <span class="toast-message" style="font-size: 0.88rem; font-weight: 500;"></span>
    `;
    document.body.appendChild(toast);
  }

  const messageSpan = toast.querySelector('.toast-message');
  if (messageSpan) messageSpan.textContent = message;

  toast.classList.add('show');
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}

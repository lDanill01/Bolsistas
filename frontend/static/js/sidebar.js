(function () {
    var SIDEBAR_ID = 'sidebar';
    var WRAPPER_ID = 'content-wrapper';
    var TOGGLE_BTN_ID = 'sidebar-toggle';
    var OVERLAY_ID = 'sidebar-overlay';
    var STORAGE_KEY = 'sb_pinned';

    function getSidebar() { return document.getElementById(SIDEBAR_ID); }
    function getWrapper() { return document.getElementById(WRAPPER_ID); }
    function getToggleBtn() { return document.getElementById(TOGGLE_BTN_ID); }
    function getInnerToggleBtn() { return document.getElementById('btn-toggle'); }
    function getOverlay() { return document.getElementById(OVERLAY_ID); }

    function isMobile() { return window.innerWidth < 768; }

    function isPinned() {
        var sidebar = getSidebar();
        return sidebar && sidebar.classList.contains('pinned');
    }

    function syncInnerToggleIcon() {
        var icon = document.getElementById('btn-toggle-icon');
        if (!icon) return;
        // ">" recolhido (clique para manter aberto) / "<" fixado aberto
        if (isPinned()) {
            icon.classList.remove('ri-arrow-right-s-line');
            icon.classList.add('ri-arrow-left-s-line');
        } else {
            icon.classList.remove('ri-arrow-left-s-line');
            icon.classList.add('ri-arrow-right-s-line');
        }
    }

    function applyState(pinned) {
        var sidebar = getSidebar();
        var wrapper = getWrapper();
        if (!sidebar || !wrapper) return;
        if (pinned) {
            sidebar.classList.add('pinned');
            sidebar.classList.remove('mobile-open');
            wrapper.classList.add('pinned');
            wrapper.classList.remove('expanded');
        } else {
            // Recolhe automaticamente: só ícones (hover expande temporariamente via CSS)
            sidebar.classList.remove('pinned');
            sidebar.classList.remove('collapsed');
            wrapper.classList.remove('pinned');
            wrapper.classList.remove('expanded');
        }
        syncInnerToggleIcon();
    }

    function toggleSidebar() {
        var sidebar = getSidebar();
        if (!sidebar) return;
        if (isMobile()) {
            sidebar.classList.toggle('mobile-open');
            var overlay = getOverlay();
            if (overlay) overlay.classList.toggle('show', sidebar.classList.contains('mobile-open'));
            return;
        }
        var newState = !isPinned();
        applyState(newState);
        try { localStorage.setItem(STORAGE_KEY, newState ? '1' : '0'); } catch (e) {}
    }

    function closeMobileSidebar() {
        var sidebar = getSidebar();
        if (sidebar) sidebar.classList.remove('mobile-open');
        var overlay = getOverlay();
        if (overlay) overlay.classList.remove('show');
    }

    function init() {
        var sidebar = getSidebar();
        var wrapper = getWrapper();
        if (!sidebar || !wrapper) return;

        if (!isMobile()) {
            var saved = null;
            try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
            if (saved === null) {
                // Migra preferência antiga (sb_collapsed): '0' = era aberto -> fixa aberto
                try {
                    var legacy = localStorage.getItem('sb_collapsed');
                    if (legacy === '0') saved = '1';
                    localStorage.removeItem('sb_collapsed');
                } catch (e) {}
            }
            applyState(saved === '1');
        } else {
            applyState(false);
        }

        var toggleBtn = getToggleBtn();
        if (toggleBtn) {
            toggleBtn.addEventListener('click', toggleSidebar);
        }

        var innerToggleBtn = getInnerToggleBtn();
        if (innerToggleBtn) {
            innerToggleBtn.addEventListener('click', toggleSidebar);
        }
        syncInnerToggleIcon();

        var overlay = getOverlay();
        if (overlay) {
            overlay.addEventListener('click', closeMobileSidebar);
        }

        window.addEventListener('resize', function () {
            if (isMobile()) {
                applyState(false);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', init);
})();

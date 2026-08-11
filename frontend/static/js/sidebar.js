(function () {
    var SIDEBAR_ID = 'sidebar';
    var WRAPPER_ID = 'content-wrapper';
    var TOGGLE_BTN_ID = 'sidebar-toggle';
    var OVERLAY_ID = 'sidebar-overlay';
    var STORAGE_KEY = 'sb_collapsed';

    function getSidebar() { return document.getElementById(SIDEBAR_ID); }
    function getWrapper() { return document.getElementById(WRAPPER_ID); }
    function getToggleBtn() { return document.getElementById(TOGGLE_BTN_ID); }
    function getOverlay() { return document.getElementById(OVERLAY_ID); }

    function isMobile() { return window.innerWidth < 768; }

    function isCollapsed() {
        var sidebar = getSidebar();
        return sidebar && sidebar.classList.contains('collapsed');
    }

    function applyState(collapsed) {
        var sidebar = getSidebar();
        var wrapper = getWrapper();
        if (!sidebar || !wrapper) return;
        if (collapsed) {
            sidebar.classList.add('collapsed');
            sidebar.classList.remove('mobile-open');
            wrapper.classList.add('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            wrapper.classList.remove('expanded');
        }
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
        var newState = !isCollapsed();
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
            var saved;
            try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
            applyState(saved === '1');
        } else {
            applyState(false);
        }

        var toggleBtn = getToggleBtn();
        if (toggleBtn) {
            toggleBtn.addEventListener('click', toggleSidebar);
        }

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

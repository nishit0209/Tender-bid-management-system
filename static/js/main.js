document.addEventListener('DOMContentLoaded', function () {
    try {
        lucide.createIcons();
    } catch (e) {
        console.warn("Lucide icons failed to load:", e);
    }

    // ── Notification Dropdown ──────────────────────────────────────
    const notifBtn = document.getElementById('notif-btn');
    const notifDropdown = document.getElementById('notif-dropdown');
    const userMenuBtn = document.getElementById('user-menu-btn');
    const userMenuDropdown = document.getElementById('user-menu-dropdown');

    function closeAllDropdowns() {
        if (notifDropdown) notifDropdown.classList.add('hidden');
        if (userMenuDropdown) userMenuDropdown.classList.add('hidden');
    }

    if (notifBtn && notifDropdown) {
        notifBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isHidden = notifDropdown.classList.contains('hidden');
            closeAllDropdowns();
            if (isHidden) notifDropdown.classList.remove('hidden');
        });
    }

    if (userMenuBtn && userMenuDropdown) {
        userMenuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isHidden = userMenuDropdown.classList.contains('hidden');
            closeAllDropdowns();
            if (isHidden) userMenuDropdown.classList.remove('hidden');
        });
    }

    document.addEventListener('click', closeAllDropdowns);

    // ── Auto-dismiss Toasts ────────────────────────────────────────
    document.querySelectorAll('[data-toast]').forEach(function (toast) {
        setTimeout(function () {
            toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(function () { toast.remove(); }, 400);
        }, 5000);
    });

    // ── Mobile Sidebar Toggle ──────────────────────────────────────
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function openSidebar() {
        if (sidebar) sidebar.classList.add('sidebar-open');
        if (sidebarOverlay) {
            sidebarOverlay.classList.remove('hidden');
            sidebarOverlay.style.opacity = '1';
        }
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('sidebar-open');
        if (sidebarOverlay) {
            sidebarOverlay.style.opacity = '0';
            setTimeout(function() { sidebarOverlay.classList.add('hidden'); }, 300);
        }
        document.body.style.overflow = '';
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            if (sidebar && sidebar.classList.contains('sidebar-open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Sidebar close button (X inside sidebar on mobile)
    const sidebarClose = document.getElementById('sidebar-close');
    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    // Close sidebar on nav link click (mobile)
    if (sidebar) {
        sidebar.querySelectorAll('a.nav-link').forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth < 1024) closeSidebar();
            });
        });
    }

    // ── Theme Toggle ───────────────────────────────────────────────
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                localStorage.theme = 'light';
            } else {
                document.documentElement.classList.add('dark');
                localStorage.theme = 'dark';
            }
        });
    }


    // Handle resize: close mobile sidebar when going to desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 1024) closeSidebar();
    });
});

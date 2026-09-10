document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('navToggle');
    var list = document.getElementById('navList');

    if (!toggle || !list) {
        return;
    }

    toggle.addEventListener('click', function () {
        var isOpen = list.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
});

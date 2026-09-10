<?php
/** @var string $activeNav */
$navItems = [
    'home'        => ['label' => 'Home', 'href' => site_url('/')],
    'about'       => ['label' => 'About Us', 'href' => site_url('about')],
    'gallery'     => ['label' => 'Gallery', 'href' => site_url('gallery')],
    'competition' => ['label' => 'SPE Competition', 'href' => site_url('spe-competition')],
    'petrolida'   => ['label' => 'Petrolida 2027', 'href' => site_url('petrolida-2027')],
    'leaderboard' => ['label' => 'Leaderboard', 'href' => site_url('leaderboard')],
    'blog'        => ['label' => 'SPE Blog', 'href' => site_url('spe-blog')],
    'alumni'      => ['label' => 'Alumni', 'href' => site_url('alumni')],
];
?>
<header class="site-header">
    <div class="site-header__inner">
        <nav class="site-nav" aria-label="Navigasi utama">
            <button type="button" class="site-nav__toggle" id="navToggle" aria-expanded="false" aria-controls="navList">
                <span></span><span></span><span></span>
                <span class="sr-only">Buka menu</span>
            </button>
            <ul class="site-nav__list" id="navList">
                <?php foreach ($navItems as $key => $item) : ?>
                    <li>
                        <a href="<?= esc($item['href']) ?>" class="site-nav__link<?= ($activeNav ?? '') === $key ? ' is-active' : '' ?>">
                            <?= esc($item['label']) ?>
                        </a>
                    </li>
                <?php endforeach; ?>
            </ul>
        </nav>
        <a href="<?= site_url('/') ?>" class="site-header__logo" aria-label="SPE ITS SC">
            <img src="<?= base_url('assets/images/spe-logo-mark.svg') ?>" alt="Logo SPE ITS Student Chapter" width="48" height="48">
        </a>
    </div>
</header>

<?php
/**
 * Marquee ticker banner (muncul berulang di antar-section pada desain Figma).
 *
 * @var string $variant 'blue' | 'red'
 */
$variant = $variant ?? 'blue';
$text    = '★ IgniteTheImpact ';
$repeat  = str_repeat($text, 12);
?>
<div class="ticker ticker--<?= esc($variant) ?>" aria-hidden="true">
    <div class="ticker__track">
        <span class="ticker__text"><?= esc($repeat) ?></span>
        <span class="ticker__text"><?= esc($repeat) ?></span>
    </div>
</div>

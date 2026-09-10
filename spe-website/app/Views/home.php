<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title><?= esc($title ?? 'SPE ITS Student Chapter') ?></title>
    <meta name="description" content="Society of Petroleum Engineers - Institut Teknologi Sepuluh Nopember Student Chapter">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="shortcut icon" type="image/png" href="<?= base_url('favicon.ico') ?>">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,600;0,700;1,400;1,600;1,700&family=Playfair+Display:ital,wght@1,600;1,700&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="<?= base_url('assets/css/main.css') ?>">
    <link rel="stylesheet" href="<?= base_url('assets/css/home.css') ?>">
</head>
<body>

<?= $this->include('partials/header') ?>

<main>
    <!-- ============ HERO (Figma node 2:15 - "SPE Website - Home Page 1") ============ -->
    <section class="hero">
        <div class="hero__bg" style="background-image:url('<?= base_url('assets/images/hero-bg-placeholder.svg') ?>')"></div>
        <div class="hero__overlay"></div>

        <div class="hero__inner">
            <div class="hero-card">
                <img src="<?= base_url('assets/images/spe-logo-mark.svg') ?>" alt="Logo SPE International" class="hero-card__logo" width="140" height="120">
                <div class="hero-card__body">
                    <h2 class="hero-card__title">Institut Teknologi<br>Sepuluh Nopember<br>Student Chapter</h2>
                    <p class="hero-card__text">
                        The largest and the most prestigious student-led organization that encourages
                        students' professional development through engagement in the energy industry.
                    </p>
                </div>
            </div>

            <h1 class="hero-headline">
                <span class="hero-headline__line">Society of</span>
                <span class="hero-headline__line">Petroleum</span>
                <span class="hero-headline__line">Engineers</span>
            </h1>
        </div>

        <div class="hero__cta">
            <div class="hero__cta-left">
                <p class="hero__cta-title">Learn with SPE</p>
                <p class="hero__cta-text">Develop crucial skills and learn with SPE ITS SC through our events</p>
            </div>
            <a href="<?= site_url('membership') ?>" class="hero__cta-link">Become a Member!</a>
        </div>
    </section>

    <?= $this->include('partials/ticker', ['variant' => 'blue']) ?>

    <!-- ============ TESTIMONIALS (Figma node 2:161 - "Home Page 2") ============ -->
    <section class="testimonials">
        <div class="testimonials__bg" style="background-image:url('<?= base_url('assets/images/testimonials-bg-placeholder.svg') ?>')"></div>

        <h2 class="section-title section-title--red">What Do They Say?</h2>

        <div class="testimonial-grid">
            <article class="testimonial-card">
                <p class="testimonial-card__quote">
                    Joining SPE ITS SC provides the opportunity to expand knowledge in the oil and gas
                    industry while building a broader professional network in engineering. As a member,
                    you can engage in events like PETROLEAGUE, Inspect, Exploring, and contribute as staff
                    for PETROLIDA. Competitions such as BOREYES and OGIP offer additional challenges to
                    grow and showcase your skills.
                </p>
                <div class="testimonial-card__footer">
                    <p class="testimonial-card__role">Member</p>
                    <p class="testimonial-card__name">Muhammad Rafi Cikal</p>
                    <p class="testimonial-card__meta">Engineering Physics, 2023</p>
                </div>
            </article>

            <article class="testimonial-card">
                <p class="testimonial-card__quote">
                    Joining SPE ITS SC opened doors to the oil and gas industry while connecting me with a
                    community of like-minded individuals. Through PetroInsight articles and seminars, I
                    gained valuable knowledge across upstream, midstream, and downstream sectors. Competing
                    in Petroleague and Boreyes competitions, along with volunteering for Petrolida 2024 and
                    Energy4Me, helped me grow both academically and professionally, leading to my current
                    role as a staff member of SPE ITS SC 2024/2025.
                </p>
                <div class="testimonial-card__footer">
                    <p class="testimonial-card__role">Member</p>
                    <p class="testimonial-card__name">Exaudi Abetnego Tampubolon</p>
                    <p class="testimonial-card__meta">Chemical Engineering, 2023</p>
                </div>
            </article>

            <article class="testimonial-card">
                <p class="testimonial-card__quote">
                    Joining SPE ITS SC offered a unique opportunity to dive into the oil and gas industry
                    as a new student, providing the perfect platform for self-development. From insightful
                    courses on Upstream, Midstream, and Downstream Science to actively participating in
                    competitions like Petroleague, IPFEST ITB, OGIP UPNVY, and more, the journey has been
                    enriching and rewarding. Through SPE ITS SC, the benefits are endless&mdash;attending
                    expert-led courses, receiving mentorship from industry professionals, and achieving
                    competition success. It's the perfect place to grow and #IgniteTheImpact.
                </p>
                <div class="testimonial-card__footer">
                    <p class="testimonial-card__role">Member</p>
                    <p class="testimonial-card__name">Athallah Al Ghaisan</p>
                    <p class="testimonial-card__meta">Marine Engineering, 2023</p>
                </div>
            </article>
        </div>
    </section>

    <!-- ============ CLOSING BANNER (Figma node 2:184 - "Home Page 3") ============ -->
    <section class="closing-banner">
        <div class="closing-banner__inner">
            <img src="<?= base_url('assets/images/spe-logo-full.svg') ?>" alt="Logo SPE International" class="closing-banner__logo">
            <div class="closing-banner__divider" aria-hidden="true"></div>
            <p class="closing-banner__tagline">Solutions.<br>People.<br>Energy.<sup>SM</sup></p>
        </div>
        <p class="closing-banner__caption">Institut Teknologi Sepuluh Nopember (ITS)<br>SPE Student Chapter</p>

        <?= $this->include('partials/ticker', ['variant' => 'red']) ?>
    </section>
</main>

<script src="<?= base_url('assets/js/main.js') ?>"></script>
</body>
</html>

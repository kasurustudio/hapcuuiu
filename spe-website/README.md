# SPE ITS SC Website (slicing dari Figma)

Slicing UI ke frontend HTML dengan framework **CodeIgniter 4**, dari desain
Figma
[`SPE-WEBSITE`](https://www.figma.com/design/4rdsf0zGg1nMz9iMFfbF23/SPE-WEBSITE--Copy-).

Ini adalah **proyek terpisah** dari aplikasi analisis saham di root repo
(`backend/`, `frontend/`) — tidak berhubungan dan tidak mengikuti roadmap
`SPEC.md` di root. Ditempatkan di `spe-website/` supaya tidak menyentuh
struktur/kode aplikasi saham yang sudah ada.

Desain sumber punya sekitar 17 halaman penuh (Home, About Us x6, SPE
Competition x2, Leaderboard x2, Alumni x2, SPE Blog x2). **Baru Home Page
yang dikerjakan di iterasi ini** sebagai pola kerja awal; halaman lain
menyusul dengan pola yang sama (controller + view + partial nav/ticker yang
sudah dibuat bisa dipakai ulang).

## Menjalankan

```bash
cd spe-website
composer install
php spark serve
```

Buka `http://localhost:8080`.

## Struktur

- `app/Controllers/Home.php` — controller halaman Home.
- `app/Views/home.php` — markup halaman Home (hero, testimonial, closing banner).
- `app/Views/partials/header.php` — nav bar, dipakai ulang di semua halaman.
- `app/Views/partials/ticker.php` — marquee "IgniteTheImpact", dipakai ulang
  (varian warna biru/merah lewat parameter `variant`).
- `public/assets/css/main.css` — design token warna, base style, nav, ticker.
- `public/assets/css/home.css` — style khusus halaman Home.
- `public/assets/js/main.js` — toggle menu mobile.
- `public/assets/images/` — lihat `README-ASSETS.md`: sebagian masih
  placeholder karena sesi ini tidak punya akses jaringan ke figma.com untuk
  mengunduh aset asli.

## Yang belum dikerjakan

- 16 halaman lain (About Us, SPE Competition, Leaderboard, Alumni, SPE
  Blog) — link navbar ke halaman-halaman ini sudah disiapkan
  (`app/Config/Routes.php` perlu ditambah route-nya saat halaman itu dibuat).
- Aset gambar/logo asli (lihat `README-ASSETS.md`).
- Font dekoratif berlisensi (`RL Madena`, `Snell Roundhand`) — saat ini
  pakai fallback `Playfair Display`.

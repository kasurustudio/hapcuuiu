# Aset yang masih placeholder

Slicing ini dibuat dari Figma
`https://www.figma.com/design/4rdsf0zGg1nMz9iMFfbF23/SPE-WEBSITE--Copy-`
(halaman "SPE WEBSITE" > frame "SPE Website - Home Page 1/2/3", node
`2:15`, `2:161`, `2:184`).

Sesi kerja ini **tidak punya akses jaringan ke `www.figma.com`** (diblokir
oleh kebijakan proxy lingkungan), sehingga aset gambar asli (foto, logo SVG)
tidak bisa diunduh otomatis. Sebagai gantinya dipakai placeholder SVG yang
jelas ditandai, supaya halaman tetap render dengan benar tanpa file rusak.

File yang perlu diganti dengan aset asli (unduh manual dari Figma
Desktop/web, lalu ekspor node terkait):

| File saat ini | Ganti dengan ekspor node Figma | Catatan |
| --- | --- | --- |
| `public/assets/images/hero-bg-placeholder.svg` | `2:16` "Gradient-Map" (foto rig minyak/laut) | Background hero, ganti ekstensi rujukan di `home.php` jadi `.jpg`/`.png` sesuai file asli |
| `public/assets/images/testimonials-bg-placeholder.svg` | `2:162` "Gradient-Map" | Background halus section testimonial (opacity 10%) |
| `public/assets/images/spe-logo-mark.svg` | `2:33` "logo spe black 1" / `2:102` "logo spe black 2" | Logo globe SPE International resmi (bukan logo generik di file ini) |
| `public/assets/images/spe-logo-full.svg` | `2:185` "New logo SPE ITS SC 1" | Lock-up logo besar di closing banner |

Font dekoratif pada desain (`RL Madena`, `Snell Roundhand LT Std`) adalah
font berbayar/kustom yang tidak tersedia di Google Fonts maupun di sandbox
ini. Saat ini CSS memakai fallback `Playfair Display` (italic, gratis via
Google Fonts) lewat variabel `--font-script` di
`public/assets/css/main.css`. Kalau tim punya lisensi font aslinya:

1. Taruh file font (`.woff2`) di `public/assets/fonts/`.
2. Tambahkan `@font-face` di `main.css`.
3. Update nilai `--font-script`.

Setelah aset di atas diganti, hapus file placeholder yang tidak lagi
dipakai.

/**
 * Banner disclaimer permanen di footer setiap halaman.
 * SPEC.md Bagian 0 — wajib, jangan dihapus/disembunyikan.
 */
export function DisclaimerFooter() {
  return (
    <footer className="border-t border-white/10 px-4 py-3 text-center text-xs text-neutral-400">
      Aplikasi ini adalah decision support tool, bukan penasihat investasi.
      Semua sinyal, harga beli, dan harga jual adalah hasil kalkulasi
      rule-based terhadap data historis, bukan jaminan hasil di masa depan.
    </footer>
  );
}

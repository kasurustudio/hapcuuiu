/** SPEC.md Bagian 0: label wajib di setiap kartu sinyal. */
export function SignalDisclaimer({ className = "" }: { className?: string }) {
  return (
    <p className={`text-[11px] leading-snug text-neutral-500 ${className}`}>
      Bukan rekomendasi investasi. Hasil kalkulasi teknikal otomatis.
    </p>
  );
}

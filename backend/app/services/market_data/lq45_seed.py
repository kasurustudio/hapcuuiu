"""Seed daftar konstituen LQ45 IDX untuk `sync_instruments`. SPEC.md Fase 1.

yfinance tidak menyediakan daftar emiten (lihat `YFinanceIDXAdapter.list_instruments`),
jadi daftar awal di-seed secara statis di sini. Job `sync_instruments`
(Bagian 6.4) sebaiknya diganti dengan sumber resmi (scraping IDX / vendor)
begitu tersedia; daftar ini adalah titik awal, bukan sumber kebenaran yang
selalu ter-update (konstituen LQ45 dievaluasi ulang tiap semester oleh IDX).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeedInstrument:
    symbol: str
    name: str
    sector: str


LQ45_SEED: list[SeedInstrument] = [
    SeedInstrument("ACES", "Ace Hardware Indonesia Tbk", "Consumer Cyclicals"),
    SeedInstrument("ADRO", "Alamtri Resources Indonesia Tbk", "Energy"),
    SeedInstrument("AKRA", "AKR Corporindo Tbk", "Energy"),
    SeedInstrument("AMMN", "Amman Mineral Internasional Tbk", "Basic Materials"),
    SeedInstrument("AMRT", "Sumber Alfaria Trijaya Tbk", "Consumer Non-Cyclicals"),
    SeedInstrument("ANTM", "Aneka Tambang Tbk", "Basic Materials"),
    SeedInstrument("ARTO", "Bank Jago Tbk", "Financials"),
    SeedInstrument("ASII", "Astra International Tbk", "Consumer Cyclicals"),
    SeedInstrument("BBCA", "Bank Central Asia Tbk", "Financials"),
    SeedInstrument("BBNI", "Bank Negara Indonesia Tbk", "Financials"),
    SeedInstrument("BBRI", "Bank Rakyat Indonesia Tbk", "Financials"),
    SeedInstrument("BBTN", "Bank Tabungan Negara Tbk", "Financials"),
    SeedInstrument("BMRI", "Bank Mandiri Tbk", "Financials"),
    SeedInstrument("BRPT", "Barito Pacific Tbk", "Basic Materials"),
    SeedInstrument("BUKA", "Bukalapak.com Tbk", "Technology"),
    SeedInstrument("CPIN", "Charoen Pokphand Indonesia Tbk", "Consumer Non-Cyclicals"),
    SeedInstrument("ELSA", "Elnusa Tbk", "Energy"),
    SeedInstrument("EMTK", "Elang Mahkota Teknologi Tbk", "Technology"),
    SeedInstrument("ESSA", "ESSA Industries Indonesia Tbk", "Basic Materials"),
    SeedInstrument("EXCL", "XL Axiata Tbk", "Infrastructures"),
    SeedInstrument("GGRM", "Gudang Garam Tbk", "Consumer Non-Cyclicals"),
    SeedInstrument("GOTO", "GoTo Gojek Tokopedia Tbk", "Technology"),
    SeedInstrument("HRUM", "Harum Energy Tbk", "Energy"),
    SeedInstrument("ICBP", "Indofood CBP Sukses Makmur Tbk", "Consumer Non-Cyclicals"),
    SeedInstrument("INCO", "Vale Indonesia Tbk", "Basic Materials"),
    SeedInstrument("INDF", "Indofood Sukses Makmur Tbk", "Consumer Non-Cyclicals"),
    SeedInstrument("INDY", "Indika Energy Tbk", "Energy"),
    SeedInstrument("INKP", "Indah Kiat Pulp & Paper Tbk", "Basic Materials"),
    SeedInstrument("ITMG", "Indo Tambangraya Megah Tbk", "Energy"),
    SeedInstrument("JPFA", "Japfa Comfeed Indonesia Tbk", "Consumer Non-Cyclicals"),
    SeedInstrument("JSMR", "Jasa Marga Tbk", "Infrastructures"),
    SeedInstrument("KLBF", "Kalbe Farma Tbk", "Healthcare"),
    SeedInstrument("MAPI", "Mitra Adiperkasa Tbk", "Consumer Cyclicals"),
    SeedInstrument("MDKA", "Merdeka Copper Gold Tbk", "Basic Materials"),
    SeedInstrument("MEDC", "Medco Energi Internasional Tbk", "Energy"),
    SeedInstrument("MNCN", "Media Nusantara Citra Tbk", "Consumer Cyclicals"),
    SeedInstrument("MYOR", "Mayora Indah Tbk", "Consumer Non-Cyclicals"),
    SeedInstrument("PGAS", "Perusahaan Gas Negara Tbk", "Energy"),
    SeedInstrument("PGEO", "Pertamina Geothermal Energy Tbk", "Infrastructures"),
    SeedInstrument("PTBA", "Bukit Asam Tbk", "Energy"),
    SeedInstrument("PWON", "Pakuwon Jati Tbk", "Properties & Real Estate"),
    SeedInstrument("SIDO", "Industri Jamu & Farmasi Sido Muncul Tbk", "Healthcare"),
    SeedInstrument("SMGR", "Semen Indonesia Tbk", "Basic Materials"),
    SeedInstrument("SMRA", "Summarecon Agung Tbk", "Properties & Real Estate"),
    SeedInstrument("TLKM", "Telkom Indonesia Tbk", "Infrastructures"),
    SeedInstrument("TOWR", "Sarana Menara Nusantara Tbk", "Infrastructures"),
    SeedInstrument("UNTR", "United Tractors Tbk", "Industrials"),
    SeedInstrument("UNVR", "Unilever Indonesia Tbk", "Consumer Non-Cyclicals"),
]

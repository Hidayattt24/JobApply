# Folder `data/`

Folder ini menyimpan semua data lokal aplikasi. **Seluruh isinya di-ignore oleh Git**
(kecuali file `.gitkeep` dan README ini), sehingga file pribadi Anda — CV, profil,
token OAuth, dan database — tidak ikut ter-upload ke repository.

## Struktur

```text
data/
├── attachments/   # File yang dilampirkan ke email (CV, portfolio PDF/DOCX)
│   └── .gitkeep
├── auth/          # Token OAuth Gmail — dibuat otomatis saat `jobapply auth gmail`
│   └── .gitkeep
├── cv/            # CV Anda (PDF/DOCX/TXT) yang diimport via `jobapply profile import`
│   └── .gitkeep
├── db/            # Placeholder — tidak dipakai (database disimpan di data/jobapply.db)
│   └── .gitkeep
├── profile/       # Profil kandidat hasil parsing CV (profile.json, facts.json)
│   └── .gitkeep
├── jobapply.db    # Database SQLite (jobs, applications, history) — dibuat otomatis
└── README.md      # File ini
```

## Catatan

- Semua folder di atas dibuat **otomatis** oleh `jobapply init`.
- Letakkan CV Anda di `data/cv/`, lalu jalankan:
  ```bash
  jobapply profile import data/cv/NamaCV.pdf
  ```
- File CSV lowongan (mis. `data/jobs.csv`) boleh diletakkan di mana saja; cukup
  arahkan path-nya saat import:
  ```bash
  jobapply job import data/jobs.csv
  ```
- `data/jobapply.db` dan `data/auth/gmail_token.json` bersifat **rahasia** — jangan
  pernah di-commit.

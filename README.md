# JobApply AI CLI

JobApply AI CLI adalah aplikasi **command-line (CLI)** untuk mengotomatisasi pembuatan dan
pengiriman email lamaran kerja. Alur kerjanya:

1. **CV** Anda diproses **satu kali** menjadi *candidate profile* terstruktur.
2. AI menganalisis *job description*, mencocokkannya dengan profil Anda, lalu menyusun
   email lamaran yang dipersonalisasi.
3. Anda **me-review / meng-edit / menyetujui** email tersebut.
4. Email dikirim melalui **Gmail API + OAuth 2.0** (langsung atau terjadwal).

> **Prinsip utama:** AI menganalisis dan menulis; **Anda tetap yang memegang kendali** —
> tidak ada email yang terkirim tanpa persetujuan Anda.

### Provider AI Fleksibel

Arsitektur AI memakai *abstraction layer* (`AIService`), sehingga **provider AI bisa
diganti dengan API apa pun** — Gemini, OpenAI, Anthropic, atau model lokal — tanpa
mengubah logika bisnis. Gemini tersedia sebagai provider bawaan; menambahkan provider
lain cukup dengan mengimplementasikan satu kelas `AIService` baru.

---

## Daftar Isi

- [Fitur](#fitur)
- [Persyaratan (Requirements)](#persyaratan-requirements)
- [Instalasi](#instalasi)
- [Konfigurasi `.env`](#konfigurasi-env)
- [Setup API Key AI](#1-mendapatkan-api-key-ai)
- [Setup Gmail OAuth (untuk mengirim email)](#2-setup-gmail-oauth-untuk-mengirim-email)
- [Struktur Folder `data/`](#struktur-folder-data)
- [Penggunaan](#penggunaan)
- [CSV Bulk Import](#csv-bulk-import)
- [Menjalankan Scheduler](#menjalankan-scheduler)
- [Keamanan](#keamanan)
- [Troubleshooting](#troubleshooting)
- [Menjalankan Test](#menjalankan-test)

---

## Fitur

- Provider AI fleksibel (Gemini bawaan, bisa diganti OpenAI/Anthropic/dll).
- Parsing CV (PDF / DOCX / TXT) menjadi profil kandidat terstruktur.
- Analisis *job description* berbasis AI (skills, seniority, responsibilities).
- *Candidate–job matching* dengan *match score*.
- Pembuatan email lamaran yang dipersonalisasi per lowongan.
- Validasi faktualitas: AI **dilarang mengarang** informasi yang tidak ada di CV.
- Review / edit / regenerate email sebelum dikirim.
- Pengiriman via **Gmail API** (bukan password / App Password).
- Kirim sekarang atau jadwalkan (08:00 otomatis atau waktu kustom).
- *Dry-run mode* untuk testing tanpa benar-benar mengirim email.
- Deteksi duplikat + batas jumlah email per batch (anti-spam).
- Riwayat (history) pengiriman tersimpan di database lokal (SQLite).

---

## Persyaratan (Requirements)

| Kebutuhan | Keterangan |
|-----------|------------|
| **Python** | 3.10 atau lebih baru (disarankan 3.12+) |
| **API Key AI** | Wajib, untuk fitur AI (default: Gemini, bisa diganti provider lain) |
| **Google Cloud + Gmail API** | Hanya jika Anda ingin **benar-benar mengirim** email |
| **Sistem Operasi** | Windows / Linux / macOS |

> **Catatan:** Jika Anda hanya ingin *generate* email (tanpa kirim), cukup
> API key AI saja. Kredensial Gmail hanya dibutuhkan saat tahap pengiriman.

---

## Instalasi

### 1. Clone repositori

```bash
git clone https://github.com/Hidayattt24/JobApply.git
cd JobApply
```

### 2. Buat virtual environment

Disarankan agar dependensi tidak bentrok dengan project lain.

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependensi

```bash
pip install -r requirements.txt
pip install -e .
```

Perintah kedua (`pip install -e .`) mendaftarkan perintah `jobapply` agar bisa
dipanggil dari mana saja.

### 4. Verifikasi instalasi

```bash
jobapply version
```

Jika muncul versi (mis. `JobApply AI CLI v1.0.0`), instalasi berhasil.

### 5. Salin file konfigurasi `.env`

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Kemudian edit `.env` sesuai panduan di bawah.

### 6. Inisialisasi project

```bash
jobapply init
```

Perintah ini membuat folder `data/` dan database SQLite. Jika `AI_API_KEY` belum
diisi, akan muncul peringatan (itu normal — isi dulu `.env`).

---

## Konfigurasi `.env`

Semua konfigurasi sensitif (API key, kredensial) disimpan di `.env`.
File ini **JANGAN** di-commit ke Git. Berikut penjelasan **setiap** variabel.

### APPLICATION

| Variabel | Contoh | Wajib | Penjelasan |
|----------|--------|:-----:|------------|
| `APP_ENV` | `development` | Tidak | Lingkungan aplikasi (`development` / `production`). |
| `TIMEZONE` | `Asia/Jakarta` | Tidak | Zona waktu untuk penjadwalan email. Gunakan nama zona IANA, mis. `Asia/Jakarta`, `Asia/Makassar`, `UTC`. |
| `DEFAULT_CV_PATH` | `data/attachments/CV.pdf` | Tidak | Path ke file CV yang dilampirkan otomatis saat mengirim email. Ekstensi didukung: `.pdf`, `.doc`, `.docx` (maks 25MB). |
| `DEFAULT_PORTFOLIO_PATH` | *(kosong)* | Tidak | Path PDF portofolio yang ikut dilampirkan & disebut sekilas di email. Kosongkan untuk menonaktifkan. |

### AI

| Variabel | Contoh | Wajib | Penjelasan |
|----------|--------|:-----:|------------|
| `AI_PROVIDER` | `gemini` | Tidak | Provider AI yang dipakai. Default `gemini`; bisa diganti dengan provider lain (OpenAI, Anthropic, dll) dengan menambahkan kelas `AIService` baru. |
| `AI_API_KEY` | `AIzaSy...` | **Ya** | API key untuk provider AI yang dipilih. Lihat [cara mendapatkannya](#1-mendapatkan-api-key-ai). |
| `AI_MODEL` | `gemini-2.5-flash` | Tidak | Model yang dipakai sesuai provider (mis. `gemini-2.5-flash`, `gpt-4o`, `claude-sonnet-4-5`). |
| `AI_TEMPERATURE` | `0.4` | Tidak | Tingkat kreativitas AI (0.0–1.0). Semakin rendah semakin konsisten/faktual. |

### EMAIL (Gmail API + OAuth 2.0)

| Variabel | Contoh | Wajib | Penjelasan |
|----------|--------|:-----:|------------|
| `EMAIL_PROVIDER` | `gmail` | Tidak | Provider email. Saat ini hanya `gmail` yang didukung. |
| `GMAIL_CLIENT_ID` | `1234...apps.googleusercontent.com` | * | Client ID OAuth dari Google Cloud Console. |
| `GMAIL_CLIENT_SECRET` | `GOCSPX-...` | * | Client Secret OAuth dari Google Cloud Console. |
| `GMAIL_SENDER_EMAIL` | `nama@gmail.com` | * | Akun Gmail yang dipakai **mengirim** email. Harus sama dengan akun yang Anda autentikasi via `jobapply auth gmail`. |
| `GMAIL_TOKEN_FILE` | `data/auth/gmail_token.json` | Tidak | Lokasi token OAuth disimpan lokal (jangan di-commit). |
| `GMAIL_REDIRECT_URI` | `http://localhost` | Tidak | Hanya untuk kompatibilitas; alur OAuth desktop tidak benar-benar memakainya. |
| `EMAIL_DRY_RUN` | `false` | Tidak | Jika `true`, email **tidak benar-benar dikirim** (untuk testing). |

> `*` Wajib hanya jika Anda ingin mengirim email. Lihat [Setup Gmail OAuth](#2-setup-gmail-oauth-untuk-mengirim-email).

### DATABASE

| Variabel | Contoh | Wajib | Penjelasan |
|----------|--------|:-----:|------------|
| `DATABASE_URL` | `sqlite:///data/jobapply.db` | Tidak | Lokasi database SQLite (jobs, applications, history). |

### SCHEDULER

| Variabel | Contoh | Wajib | Penjelasan |
|----------|--------|:-----:|------------|
| `DEFAULT_SCHEDULE_TIME` | `08:00` | Tidak | Jam default untuk penjadwalan otomatis (format `HH:MM`, 24 jam). |

### SAFETY

| Variabel | Contoh | Wajib | Penjelasan |
|----------|--------|:-----:|------------|
| `MAX_EMAILS_PER_BATCH` | `20` | Tidak | Batas maksimal email yang boleh dikirim sekaligus (pengaman anti-spam). |

---

### 1. Mendapatkan API Key AI

Secara bawaan aplikasi memakai **Gemini**, tapi Anda bisa memakai provider lain dengan
menyesuaikan `AI_PROVIDER`, `AI_MODEL`, dan `AI_API_KEY` di `.env`.

#### Contoh: Gemini (default)

1. Buka [Google AI Studio](https://aistudio.google.com/).
2. Login dengan akun Google Anda.
3. Buka menu **Get API key** → **Create API key**.
4. Salin key yang muncul (format `AIzaSy...`).
5. Tempel ke `.env`:

```env
AI_PROVIDER=gemini
AI_API_KEY=AIzaSy...key-anda
AI_MODEL=gemini-2.5-flash
```

#### Contoh: OpenAI / Anthropic

Untuk memakai provider lain, ganti nilai `AI_PROVIDER`, `AI_MODEL`, dan `AI_API_KEY`
dengan milik provider tersebut, lalu pastikan kelas `AIService` untuk provider itu
tersedia di `app/ai/`:

```env
AI_PROVIDER=openai
AI_API_KEY=sk-...key-openai
AI_MODEL=gpt-4o
```

```env
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-...key-anthropic
AI_MODEL=claude-sonnet-4-5
```

### 2. Setup Gmail OAuth (untuk mengirim email)

Aplikasi ini menggunakan **OAuth 2.0** (bukan password / App Password), jadi login
dilakukan lewat browser dan refresh token disimpan lokal.

1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. **Buat project** baru (atau pilih project yang ada).
3. Aktifkan **Gmail API**:
   - Menu **APIs & Services** → **Library** → cari **Gmail API** → **Enable**.
4. Konfigurasi **OAuth consent screen**:
   - **APIs & Services** → **OAuth consent screen**.
   - Pilih tipe **External** (untuk akun pribadi).
   - Isi nama aplikasi dan email kontak (yang lain bisa dikosongkan).
   - Tambahkan akun Gmail Anda sebagai **Test user**.
5. Buat **OAuth Client ID**:
   - **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**.
   - Application type: **Desktop app** (bukan *Web application*).
   - Beri nama lalu klik **Create**.
6. Salin **Client ID** dan **Client Secret** yang muncul ke `.env`:

```env
GMAIL_CLIENT_ID=1234567890-xxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-xxxx
GMAIL_SENDER_EMAIL=nama@gmail.com
```

7. Jalankan autentikasi (membuka browser):

```bash
jobapply auth gmail
```

8. Setujui akses di browser. Refresh token akan disimpan di
   `data/auth/gmail_token.json` (otomatis masuk `.gitignore`).

9. Cek status:

```bash
jobapply auth status
```

---

## Struktur Folder `data/`

Semua data lokal (CV, profil, token, database) disimpan di folder `data/`. Strukturnya:

```text
data/
├── attachments/   # File yang dilampirkan ke email (CV, portfolio PDF/DOCX)
├── auth/          # Token OAuth Gmail (dibuat otomatis oleh `jobapply auth gmail`)
├── cv/            # CV Anda (PDF/DOCX/TXT)
├── db/            # Placeholder (tidak dipakai)
├── profile/       # Profil kandidat hasil parsing CV (profile.json, facts.json)
└── jobapply.db    # Database SQLite (jobs, applications, history)
```

- Semua folder di atas dibuat **otomatis** oleh `jobapply init`, dan tetap terlihat di
  repository lewat file `.gitkeep` (agar user baru tahu nama-nama foldernya).
- Isi folder di-ignore oleh Git; file pribadi Anda tidak ikut ter-upload.
- Lihat `data/README.md` untuk penjelasan lengkap tiap folder.

---

## Penggunaan

Ada dua cara: **menu interaktif** (paling mudah) atau **perintah satu per satu**.

### Cara 1 — Menu Interaktif

```bash
jobapply
```

Muncul menu dengan nomor pilihan (Auth, Import CV, Add jobs, Analyze, Generate,
Review, Schedule, History, dll). Pilih angka lalu tekan Enter, ulangi sampai selesai.

### Cara 2 — End-to-end workflow sekali jalan

```bash
jobapply apply
```

Perintah ini menjalankan alur lengkap: tambah jobs → analyze → generate → review → schedule.

### Perintah Lengkap

#### Inisialisasi & Profil

```bash
jobapply init                       # inisialisasi folder + database
jobapply profile import CV.pdf      # parse CV jadi profil (PDF/DOCX/TXT)
jobapply profile show               # tampilkan profil sebagai JSON
jobapply profile review             # baca ulang profil tersimpan
jobapply profile edit               # edit profil (nama, skill, pengalaman)
```

> Setelah `profile import`, Anda akan ditanya apakah profil disimpan sebagai
> **verified**. Pilih **Yes** agar bisa dipakai untuk generate email.

#### Job / Lowongan

```bash
jobapply job add                    # tambah lowongan secara interaktif
jobapply job import data/jobs.csv   # import banyak lowongan dari CSV
jobapply job list                   # lihat daftar lowongan
jobapply job delete --all           # hapus lowongan (--all atau pilih manual)
```

#### Analisis & Generate

```bash
jobapply analyze                    # analisis job description via AI
jobapply analyze --jobs 1,2,3       # analisis job tertentu
jobapply generate                   # buat email personal (semua job yang belum)
jobapply generate --jobs 1          # generate hanya job ID 1
```

#### Review, Schedule & Send

```bash
jobapply review list                # review / approve / edit / regenerate
jobapply review list --all          # review semua (termasuk yang sudah direview)
jobapply schedule set               # kirim sekarang / jadwal 08:00 / custom
jobapply send now                   # kirim semua email berstatus APPROVED
jobapply send now --all             # sama dengan di atas
jobapply history list               # lihat riwayat & log email
```

#### Autentikasi & Lainnya

```bash
jobapply auth gmail                 # login Gmail (OAuth)
jobapply auth status                # cek status autentikasi
jobapply auth logout                # hapus token lokal
jobapply version                    # tampilkan versi
```

---

## CSV Bulk Import

Untuk memasukkan banyak lowongan sekaligus, buat file CSV seperti contoh
`data/jobs.csv`. Kolom yang **wajib**: `company`, `position`, `email`, `job_description`.
Kolom **opsional**: `recruiter`, `job_url`, `subject`.

```csv
company,position,email,recruiter,job_url,subject,job_description
ABC Indonesia,Frontend Developer,hr@abc.com,Rina,https://abc.com/jobs/1,,Deskripsi pekerjaan...
XYZ Tech,AI Engineer,hr@xyz.com,,https://xyz.com/job/1,Application for AI Engineer,Deskripsi pekerjaan...
DEF Corp,Backend Developer,hr@def.com,Budi,,,Deskripsi pekerjaan...
```

Kemudian import:

```bash
jobapply job import data/jobs.csv
```

---

## Menjalankan Scheduler

Email yang **dijadwalkan** (08:00 / custom) tidak langsung terkirim. Anda perlu
menjalankan *scheduler daemon* agar email terkirim saat waktunya tiba:

```bash
python -m app scheduler-run --interval 30
```

Biarkan proses ini berjalan (interval polling default 30 detik).

---

## Keamanan

- Email **tidak pernah terkirim tanpa persetujuan** Anda (konfirmasi default: **No**).
- `MAX_EMAILS_PER_BATCH` dan deteksi duplikat mencegah pengiriman massal tak terkendali.
- AI dibatasi hanya pada fakta yang terverifikasi dari CV (tidak mengarang).
- API key, kredensial, dan token OAuth **tidak pernah** dicetak / di-log / dikirim ke AI.
- `.env`, `data/auth/`, dan token masuk `.gitignore`.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `AI_API_KEY is not set` | Isi `AI_API_KEY` di `.env`, lalu jalankan ulang perintah. |
| `Unsupported AI provider` | Provider yang diisi di `AI_PROVIDER` belum diimplementasikan. Pakai `gemini` atau tambahkan kelas `AIService` untuk provider tersebut. |
| `No profile found` | Jalankan `jobapply profile import CV.pdf` lalu pilih **Yes** untuk menyimpan. |
| `Gmail OAuth is not configured` | Isi `GMAIL_CLIENT_ID` & `GMAIL_CLIENT_SECRET` di `.env`. |
| `Authentication failed / expired or revoked` | Jalankan ulang `jobapply auth gmail`. |
| `does not match GMAIL_SENDER_EMAIL` | Pastikan `GMAIL_SENDER_EMAIL` sama dengan akun yang di-autentikasi. |
| `Batch contains X emails... Operation blocked` | Naikkan `MAX_EMAILS_PER_BATCH` di `.env` (hati-hati). |
| Email tidak terkirim padahal dijadwalkan | Pastikan scheduler daemon berjalan: `python -m app scheduler-run`. |
| Ingin coba tanpa kirim beneran | Set `EMAIL_DRY_RUN=true` di `.env`. |

---

## Menjalankan Test

```bash
python -m pytest tests/ -q
```

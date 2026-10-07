# TailorBuy

Android app that uses AI to find best-buy products on Romanian e-commerce sites.

---

## Backend Setup

```powershell
# Activate virtual environment
Invoke-Expression (poetry env activate)

# Start backend server
poetry run uvicorn backend.main:app --reload
# Runs on http://127.0.0.1:8000
```

---

## Android Emulator Setup (Windows)

### Prerequisites
- Android Studio (includes the Android SDK and a default virtual device)
- Java 17 — use Microsoft's build: https://aka.ms/download-jdk/microsoft-jdk-17-windows-x64.msi
- Node.js + npm

### One-time Windows configuration (requires admin)

**1. Enable Windows long paths** — open PowerShell as Administrator and run:
```powershell
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
```
Required because React Native's CMake build generates file paths that exceed Windows' default 260-character limit.

**2. Clone the project to a short path** — CMake has its own 250-character internal limit that Windows long path support does NOT override:
```
git clone https://github.com/IonutAIDEng/tailorbuy.git C:\tb
cd C:\tb
git checkout feature/gemini-search
```

### Running the app on the emulator

**1. Start the Android emulator** in Android Studio → Device Manager → press Play.

**2. Start the backend** (Terminal 1):
```
cd C:\tb
poetry run uvicorn backend.main:app --reload
```

**3. Build and install the app** (Terminal 2 — run every session):
```
set JAVA_HOME=C:\Users\<your-username>\AppData\Local\Programs\Microsoft\jdk-17.0.20.101-hotspot
cd C:\tb\frontend
npx expo run:android
```

If you get `SDK location not found`, create `C:\tb\frontend\android\local.properties`:
```
sdk.dir=C\:\\Users\\<your-username>\\AppData\\Local\\Android\\Sdk
```

The first build takes ~8 minutes. Subsequent builds are ~30 seconds.

---

## Known Windows Issues & Solutions

| Error | Cause | Fix |
|---|---|---|
| `JAVA_HOME is not set` | Android Studio's Java 21 is not on PATH | Set `JAVA_HOME` to Java 17 path before building |
| `A restricted method in java.lang.System` | Java 21 incompatibility with React Native native modules | Use Java 17 (see above) |
| `ninja: manifest still dirty after 100 tries` | CMake 250-char path limit exceeded | Clone project to `C:\tb` (short path) |
| `SDK location not found` | `local.properties` missing after prebuild | Create it manually (see above) |
| `newArchEnabled=false` warning | React Native 0.82+ ignores this flag | Safe to ignore, New Architecture is always on |

---

## API

Backend runs on `http://127.0.0.1:8000`. From the Android emulator use `http://10.0.2.2:8000`.

- `GET /health` — health check
- `POST /search` — AI product search
- `GET /preferences/{user_id}` — get user preferences
- `PUT /preferences/{user_id}` — update user preferences

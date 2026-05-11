# Build Commands for supervisor-finder

## Prerequisites

1. **Install Rust**: https://rustup.rs/
2. **Add Windows targets**:
   ```bash
   rustup target add x86_64-pc-windows-msvc
   rustup target add i686-pc-windows-msvc
   ```
3. **Install WiX Toolset v3** (for MSI installers): https://wixtoolset.org/releases/
   - Add to PATH: `C:\Program Files (x86)\WiX Toolset v3.14\bin`
4. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

## Build Commands

## Run Backend API (FastAPI) Before Desktop App

This project uses **FastAPI** (not Flask). The Tauri app now tries to auto-start it,
but for manual troubleshooting run it yourself first:

```bash
cd e:\Repositories\first-tauri\supervisor-finder
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected output:

```json
{"status":"ok"}
```

If `python` cannot import local modules, install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

### x64 (64-bit) — Recommended
```bash
npm run tauri build -- --target x86_64-pc-windows-msvc
```

**Output:**
- Portable `.exe`: `src-tauri/target/x86_64-pc-windows-msvc/release/supervisor-finder.exe`
- NSIS installer: `src-tauri/target/x86_64-pc-windows-msvc/release/bundle/nsis/supervisor-finder_0.1.0_x64-setup.exe`
- MSI installer: `src-tauri/target/x86_64-pc-windows-msvc/release/bundle/msi/supervisor-finder_0.1.0_x64_en-US.msi`

### x86 (32-bit)
```bash
npm run tauri build -- --target i686-pc-windows-msvc
```

**Output:**
- Portable `.exe`: `src-tauri/target/i686-pc-windows-msvc/release/supervisor-finder.exe`
- NSIS installer: `src-tauri/target/i686-pc-windows-msvc/release/bundle/nsis/supervisor-finder_0.1.0_x86-setup.exe`
- MSI installer: `src-tauri/target/i686-pc-windows-msvc/release/bundle/msi/supervisor-finder_0.1.0_x86_en-US.msi`

### Both Architectures
```bash
npx tauri build --target x86_64-pc-windows-msvc --target i686-pc-windows-msvc
```

## Correct Windows Build Flow (Recommended)

1. Install frontend dependencies:

```bash
npm install
```

2. Install Python dependencies used by backend:

```bash
pip install -r requirements.txt
pip install -e .
```

3. Build x64:

```bash
npm run tauri build -- --target x86_64-pc-windows-msvc
```

4. Build x86:

```bash
npm run tauri build -- --target i686-pc-windows-msvc
```

5. Validate artifacts in:

- `src-tauri/target/x86_64-pc-windows-msvc/release/bundle/`
- `src-tauri/target/i686-pc-windows-msvc/release/bundle/`

## macOS Build Guidance

You cannot produce a reliable macOS app bundle from Windows using normal Tauri tooling.
Use one of these approaches:

1. Build on a real macOS machine (recommended)
2. Build on a macOS CI runner (GitHub Actions macos-latest)

Typical macOS targets:

- `aarch64-apple-darwin` (Apple Silicon)
- `x86_64-apple-darwin` (Intel)

On macOS machine/runner:

```bash
npm install
rustup target add aarch64-apple-darwin
rustup target add x86_64-apple-darwin
npm run tauri build -- --target aarch64-apple-darwin
npm run tauri build -- --target x86_64-apple-darwin
```

Optional universal app (run on macOS):

```bash
lipo -create \
   src-tauri/target/aarch64-apple-darwin/release/supervisor-finder \
   src-tauri/target/x86_64-apple-darwin/release/supervisor-finder \
   -output src-tauri/target/universal-macos/supervisor-finder
```

## Notes
- First build takes 10-30 minutes (Rust compiles everything)
- Subsequent builds are faster
- WiX is required for MSI — without it, only NSIS and portable .exe are generated
- For packaged app runtime, Python + backend dependencies must still exist on the target machine

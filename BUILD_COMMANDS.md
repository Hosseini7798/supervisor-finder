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

## Notes
- First build takes 10-30 minutes (Rust compiles everything)
- Subsequent builds are faster
- WiX is required for MSI — without it, only NSIS and portable .exe are generated

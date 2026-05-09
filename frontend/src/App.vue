<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { getCurrentWindow } from '@tauri-apps/api/window';
import { save } from '@tauri-apps/plugin-dialog';
import { writeTextFile } from '@tauri-apps/plugin-fs';
import { WebviewWindow } from '@tauri-apps/api/webviewWindow';

const isDark = ref(false);
const showHelp = ref(false);
const showAbout = ref(false);
const showSplash = ref(true);

type PaperDetail = {
  title: string;
  pmid: string;
  doi: string | null;
  pmc_id: string | null;
  journal_title: string;
  journal_iso: string;
  journal_volume: string;
  journal_issue: string;
  pub_year: string;
  pub_month: string;
  pub_day: string;
  medline_pgn: string;
  language: string;
  publication_status: string;
  publication_types: string[];
  mesh_headings: { descriptor: string; descriptor_ui: string; qualifier: string; qualifier_ui: string }[];
  grants: { grant_id: string; agency: string; country: string }[];
};

type ResultRow = {
  author: string;
  institution: string;
  country: string;
  email: string;
  score: string;
  num_papers: number;
  papers: string[];
  paper_details: PaperDetail[];
  journals: string[];
  keywords: string[];
};

const query = ref('("deep learning"[tiab] OR "machine learning"[tiab]) AND ("medical imaging"[tiab])');
const fromDate = ref("2023/01/01");
const toDate = ref("2024/12/31");

const isLoading = ref(false);

const rows = ref<ResultRow[]>([]);

onMounted(() => {
  const saved = localStorage.getItem('supervisor-finder-theme');
  if (saved === 'dark') {
    isDark.value = true;
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  // Hide splash after a short delay
  setTimeout(() => { showSplash.value = false; }, 1500);
});

function toggleTheme() {
  isDark.value = !isDark.value;
  const theme = isDark.value ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('supervisor-finder-theme', theme);
}

function toggleHelp() {
  showHelp.value = !showHelp.value;
}

function toggleAbout() {
  showAbout.value = !showAbout.value;
}

async function minimizeWindow() {
  try {
    console.log('Minimize clicked');
    const appWindow = getCurrentWindow();
    await appWindow.minimize();
  } catch (err) {
    console.error('Minimize failed:', err);
  }
}

async function maximizeWindow() {
  try {
    console.log('Maximize clicked');
    const appWindow = getCurrentWindow();
    await appWindow.toggleMaximize();
  } catch (err) {
    console.error('Maximize failed:', err);
  }
}

async function closeWindow() {
  try {
    console.log('Close clicked');
    const appWindow = getCurrentWindow();
    console.log('Got window:', appWindow);
    await appWindow.close();
    console.log('Close completed');
  } catch (err) {
    alert('Close failed: ' + err);
  }
}

async function performSearch() {
  if (!query.value) return;
  
  isLoading.value = true;
  try {
    const response = await fetch("http://localhost:8000/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query.value,
        from_date: fromDate.value,
        to_date: toDate.value
      })
    });
    
    if (!response.ok) {
      console.error("Search failed", response.status);
      return;
    }
    
    const data = await response.json();
    rows.value = data.candidates || [];
  } catch (error) {
    console.error("Error during search:", error);
  } finally {
    isLoading.value = false;
  }
}

const csvPreview = computed(() => {
  const header = ["author", "institution", "country", "email", "score", "num_papers", "papers", "journals", "keywords"].join(",");
  const lines = rows.value.map((row) =>
    [
      row.author, 
      row.institution, 
      row.country, 
      row.email, 
      row.score, 
      row.num_papers, 
      (row.papers || []).join(" | "), 
      (row.journals || []).join(" | "),
      (row.keywords || []).join(" | ")
    ]
      .map((value) => `"${String(value).replace(/"/g, '""')}"`)
      .join(","),
  );

  return [header, ...lines].join("\n");
});

async function exportCsv() {
  if (rows.value.length === 0) return;

  try {
    const filePath = await save({
      filters: [{
        name: 'CSV File',
        extensions: ['csv']
      }],
      defaultPath: 'supervisor-finder-results.csv'
    });
    
    if (filePath) {
      await writeTextFile(filePath, csvPreview.value);
    }
  } catch (err) {
    console.warn("Tauri API failed or unavailable, using web fallback", err);
    const blob = new Blob([csvPreview.value], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "supervisor-finder-results.csv";
    link.click();
    URL.revokeObjectURL(url);
  }
}

async function openTableWindow() {
  if (rows.value.length === 0) {
    alert("No data to show. Please search first.");
    return;
  }
  
  localStorage.setItem("supervisor-finder-results", JSON.stringify(rows.value));

  try {
    const webview = new WebviewWindow('table-window', {
      url: '/table.html',
      title: 'Supervisor Finder - Table View',
      width: 1024,
      height: 768,
      center: true
    });
    
    webview.once('tauri://error', function (e) {
      console.warn("Table window error:", e);
      window.open('/table.html', '_blank');
    });
  } catch (err) {
    console.warn("Webview fallback:", err);
    window.open('/table.html', '_blank');
  }
}
</script>

<template>
  <main class="app-shell" :class="{ dark: isDark }">
    <div v-if="showSplash" class="splash-overlay">
      <img src="/splash.webp" alt="Loading..." class="splash-image" />
    </div>

    <section class="window-frame">
      <header class="titlebar">
        <h1>Find your Supervisor</h1>
        <div class="titlebar-right">
          <button class="theme-toggle" type="button" @click="toggleTheme" :title="isDark ? 'Switch to light' : 'Switch to dark'">
            <img :src="isDark ? '/moon.png' : '/sun.png'" :alt="isDark ? 'Dark mode' : 'Light mode'" class="theme-icon" />
          </button>
          <button class="help-toggle" type="button" @click="toggleHelp" :title="'PubMed Search Help'">
            <img :src="isDark ? '/darkq.png' : '/lightq.png'" alt="Help" class="help-icon" />
          </button>
          <button class="about-toggle" type="button" @click="toggleAbout" :title="'About Us'">
            <img :src="isDark ? '/aboutusdark.png' : '/aboutuslight.png'" alt="About" class="about-icon" />
          </button>
          <div class="window-controls">
            <button class="win-btn minimize" @click="minimizeWindow" title="Minimize">−</button>
            <button class="win-btn maximize" @click="maximizeWindow" title="Maximize">□</button>
            <button class="win-btn close" @click="closeWindow" title="Close">×</button>
          </div>
        </div>
      </header>

      <div v-if="showHelp" class="help-overlay" @click="showHelp = false">
        <div class="help-popup" @click.stop>
          <button class="help-close" @click="showHelp = false">×</button>
          <h2>PubMed Search Guide</h2>
          
          <section class="help-section">
            <h3>Search Field Tags</h3>
            <ul>
              <li><code>[tiab]</code> — Title/Abstract (searches both title and abstract text)</li>
              <li><code>[ti]</code> — Title only</li>
              <li><code>[au]</code> — Author name</li>
              <li><code>[ta]</code> — Journal title abbreviation</li>
              <li><code>[pt]</code> — Publication type (e.g., "review", "clinical trial")</li>
              <li><code>[pdat]</code> — Publication date (e.g., "2024[pdat]")</li>
              <li><code>[mesh]</code> — Medical Subject Heading (controlled vocabulary)</li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Boolean Operators</h3>
            <ul>
              <li><strong>AND</strong> — Both terms must appear (narrows results)<br/>
                <em>Example:</em> <code>"machine learning" AND cancer</code></li>
              <li><strong>OR</strong> — Either term can appear (broadens results)<br/>
                <em>Example:</em> <code>"deep learning" OR "neural network"</code></li>
              <li><strong>NOT</strong> — Excludes a term<br/>
                <em>Example:</em> <code>diabetes NOT "type 1"</code></li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Quotes & Parentheses</h3>
            <ul>
              <li><code>"exact phrase"</code> — Searches for the exact phrase in that order</li>
              <li><code>(...)</code> — Groups terms together to control logic<br/>
                <em>Example:</em> <code>("AI" OR "artificial intelligence") AND radiology</code></li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Wildcards</h3>
            <ul>
              <li><code>*</code> — Matches any group of characters<br/>
                <em>Example:</em> <code>cardi*</code> finds cardiology, cardiac, cardiovascular</li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Common Patterns</h3>
            <ul>
              <li><strong>Topic + recent years:</strong><br/>
                <code>("deep learning"[tiab]) AND ("2023"[pdat] OR "2024"[pdat])</code></li>
              <li><strong>Multiple synonyms:</strong><br/>
                <code>("AI"[tiab] OR "artificial intelligence"[tiab] OR "machine learning"[tiab])</code></li>
              <li><strong>Exclude reviews:</strong><br/>
                <code>cancer[tiab] NOT "review"[pt]</code></li>
              <li><strong>Specific journal:</strong><br/>
                <code>"Nature"[ta] AND genomics[tiab]</code></li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Tips</h3>
            <ul>
              <li>Use <strong>OR</strong> for synonyms to capture more results</li>
              <li>Use <strong>AND</strong> to combine different concepts</li>
              <li>Use <code>[tiab]</code> for broad topic searches</li>
              <li>Combine field tags with Boolean operators for precision</li>
            </ul>
          </section>
        </div>
      </div>

      <div v-if="showAbout" class="help-overlay" @click="showAbout = false">
        <div class="help-popup" @click.stop>
          <button class="help-close" @click="showAbout = false">×</button>
          <h2>About Us</h2>
          
          <section class="help-section">
            <h3>Mission</h3>
            <p>Find Your Supervisor is an open-source desktop application designed to help graduate and undergraduate students discover potential academic supervisors by analyzing published research articles from PubMed. Our goal is to simplify the supervisor search process by providing data-driven insights into active researchers in your field of interest.</p>
          </section>

          <section class="help-section">
            <h3>What It Does</h3>
            <p>The application uses an intelligent algorithm to:</p>
            <ul>
              <li>Search PubMed publications in your research domain using recursive date-range splitting to handle large datasets (>10,000 articles)</li>
              <li>Extract comprehensive author information including affiliations, emails, journal details, and publication metrics</li>
              <li>Filter by geography to identify researchers in your target countries or regions</li>
              <li>Assess journal quality by merging results with SCImago rankings to prioritize high-impact publications</li>
              <li>Unify author profiles by aggregating information across multiple papers</li>
              <li>Extract contact information through automated DOI lookup for corresponding authors</li>
              <li>Process data efficiently using parallel multi-threaded fetching</li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Development Team</h3>
            <ul>
              <li><strong>M. Hosseini</strong> – Algorithm Development & Backend Logic</li>
              <li><strong>M. Nematdar</strong> – GUI Development & Frontend Design</li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Project Status</h3>
            <p>This is an alpha release (v0.1.0), meaning the application is in early development. We welcome feedback, bug reports, and feature suggestions as we continue to improve the tool.</p>
          </section>

          <section class="help-section">
            <h3>Technical Details</h3>
            <ul>
              <li><strong>License:</strong> MIT License</li>
              <li><strong>Version:</strong> 0.1.0 (Alpha)</li>
              <li><strong>Repository:</strong> <a href="https://github.com/hosseini7798/supervisor-finder" target="_blank">github.com/hosseini7798/supervisor-finder</a></li>
              <li><strong>Backend:</strong> Python with FastAPI</li>
              <li><strong>Frontend:</strong> Vue 3 + TypeScript</li>
              <li><strong>Framework:</strong> Tauri</li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Contact</h3>
            <ul>
              <li><strong>M. Hosseini:</strong> <a href="mailto:hosseini7798@gmail.com">hosseini7798@gmail.com</a></li>
              <li><strong>M. Nematdar:</strong> <a href="mailto:nematdar.m@gmail.com">nematdar.m@gmail.com</a></li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Disclaimer</h3>
            <p>This tool is provided for research and educational purposes. Users are responsible for verifying all information and complying with PubMed's terms of service and applicable data protection regulations when contacting researchers.</p>
          </section>
        </div>
      </div>

      <section class="panel panel-input">
        <div class="panel-label">Input</div>
        <label class="field">
          <span>Query</span>
          <input v-model="query" type="text" />
        </label>

        <div class="range-row">
          <label class="field compact">
            <input v-model="fromDate" type="text" placeholder="From (YYYY/MM/DD)" />
          </label>
          <span class="range-divider">to</span>
          <label class="field compact">
            <input v-model="toDate" type="text" placeholder="To (YYYY/MM/DD)" />
          </label>
          <button class="primary" type="button" @click="performSearch" :disabled="isLoading">
            {{ isLoading ? 'Searching...' : 'Search' }}
          </button>
        </div>
      </section>

      <section class="panel panel-output">
        <div class="panel-header">
          <div>
            <p class="panel-label">Output</p>
            <h2>output in csv format</h2>
          </div>
          <div class="summary-chip">{{ rows.length }} candidates</div>
        </div>

        <pre class="csv-box">{{ csvPreview }}</pre>
      </section>

      <footer class="actions">
        <button class="secondary" type="button" @click="openTableWindow">Open Advanced Table</button>
        <button class="primary" type="button" @click="exportCsv">Export to CSV</button>
      </footer>
    </section>
  </main>
</template>

<style scoped>
.app-shell {
  --bg-main: linear-gradient(135deg, #f8f2ea 0%, #f3efe6 45%, #e7ece8 100%);
  --bg-radial-a: rgba(247, 204, 146, 0.65);
  --bg-radial-b: rgba(168, 208, 216, 0.7);
  --color-text: #23201d;
  --frame-bg: rgba(255, 251, 246, 0.82);
  --frame-border: rgba(35, 32, 29, 0.88);
  --frame-shadow: rgba(35, 32, 29, 0.16);
  --input-bg: rgba(255, 255, 255, 0.88);
  --chip-bg: rgba(255, 255, 255, 0.8);
  --csv-bg: rgba(255, 255, 255, 0.78);
  --btn-bg: rgba(255, 255, 255, 0.88);
  --btn-shadow: rgba(35, 32, 29, 0.1);
  --btn-primary-from: #f7c66f;
  --btn-primary-to: #f0ae3f;
  --btn-secondary-bg: rgba(255, 255, 255, 0.82);
  --border-dashed: rgba(35, 32, 29, 0.22);
  --row-border: rgba(35, 32, 29, 0.12);
  --th-border: rgba(35, 32, 29, 0.85);
}

.app-shell.dark {
  --bg-main: linear-gradient(135deg, #1a1a2e 0%, #16213e 45%, #0f3460 100%);
  --bg-radial-a: rgba(94, 53, 177, 0.4);
  --bg-radial-b: rgba(30, 136, 229, 0.3);
  --color-text: #e0e0e0;
  --frame-bg: rgba(26, 26, 46, 0.9);
  --frame-border: rgba(224, 224, 224, 0.35);
  --frame-shadow: rgba(0, 0, 0, 0.4);
  --input-bg: rgba(255, 255, 255, 0.08);
  --chip-bg: rgba(255, 255, 255, 0.08);
  --csv-bg: rgba(255, 255, 255, 0.06);
  --btn-bg: rgba(255, 255, 255, 0.1);
  --btn-shadow: rgba(0, 0, 0, 0.25);
  --btn-primary-from: #5e35b1;
  --btn-primary-to: #7c4dff;
  --btn-secondary-bg: rgba(255, 255, 255, 0.08);
  --border-dashed: rgba(224, 224, 224, 0.15);
  --row-border: rgba(224, 224, 224, 0.08);
  --th-border: rgba(224, 224, 224, 0.3);
}

.app-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top left, var(--bg-radial-a), transparent 30%),
    radial-gradient(circle at bottom right, var(--bg-radial-b), transparent 28%),
    var(--bg-main);
  color: var(--color-text);
  transition: background 400ms ease, color 400ms ease;
  overflow: hidden;
  border-radius: 34px;
}

.window-frame {
  width: min(760px, 100%);
  border: 3px solid var(--frame-border);
  border-radius: 34px;
  padding: 18px 18px 20px;
  background: var(--frame-bg);
  box-shadow: 0 30px 60px var(--frame-shadow);
  backdrop-filter: blur(8px);
  transition: background 400ms ease, border-color 400ms ease, box-shadow 400ms ease;
}

.titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  -webkit-app-region: drag;
}

.titlebar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  -webkit-app-region: no-drag;
}

.titlebar h1 {
  -webkit-app-region: drag;
}

.titlebar h1,
.panel h2,
.panel-label,
button,
input,
table {
  font-family: "Comic Sans MS", "Segoe Print", "Bradley Hand", "Trebuchet MS", cursive;
}

.titlebar h1 {
  margin: 0;
  font-size: clamp(2rem, 3vw, 2.5rem);
  line-height: 1;
  letter-spacing: 0.01em;
}

.window-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 100;
  -webkit-app-region: no-drag;
}

.win-btn {
  min-width: unset;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 3px solid var(--frame-border);
  border-radius: 999px;
  background: var(--chip-bg);
  font-size: 20px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 200ms ease, transform 120ms ease, border-color 400ms ease;
  box-shadow: none;
  position: relative;
  z-index: 101;
  -webkit-app-region: no-drag;
}

.win-btn:hover {
  transform: scale(1.05);
}

.win-btn:active {
  transform: scale(0.95);
}

.win-btn.minimize:hover {
  background: var(--btn-primary-from);
}

.win-btn.maximize:hover {
  background: var(--btn-primary-from);
}

.win-btn.close:hover {
  background: #ff5252;
  border-color: #d32f2f;
}

.panel {
  margin-top: 18px;
}

.panel-label {
  margin: 0 0 10px;
  font-size: 1.25rem;
}

.field {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
}

.field span {
  font-size: 1rem;
}

.field input {
  box-sizing: border-box;
  width: 90%;
  border: 3px solid var(--frame-border);
  border-radius: 22px;
  background: var(--input-bg);
  padding: 16px 18px;
  font-size: 1.1rem;
  color: inherit;
  outline: none;
  transition: background 400ms ease, border-color 400ms ease;
}

.range-row {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto;
  align-items: center;
  gap: 12px;
}

.compact {
  margin-bottom: 0;
}

.range-divider {
  font-size: 1.5rem;
  font-weight: 700;
}

.panel-output {
  border-top: 1px dashed var(--border-dashed);
  padding-top: 18px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  text-transform: lowercase;
}

.summary-chip {
  border: 2px solid var(--frame-border);
  border-radius: 999px;
  padding: 8px 14px;
  background: var(--chip-bg);
  font-size: 0.95rem;
  transition: background 400ms ease, border-color 400ms ease;
}

.table-wrap,
.csv-box {
  min-height: 220px;
  border: 3px solid var(--frame-border);
  border-radius: 30px;
  background: var(--csv-bg);
  overflow: hidden;
  transition: background 400ms ease, border-color 400ms ease;
}

.table-wrap {
  padding: 10px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 1rem;
}

th,
td {
  padding: 12px 10px;
  text-align: left;
  vertical-align: top;
}

th {
  border-bottom: 2px solid var(--th-border);
}

tbody tr + tr td {
  border-top: 1px solid var(--row-border);
}

.csv-box {
  margin: 0;
  padding: 18px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.95rem;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 18px;
  flex-wrap: wrap;
}

button {
  min-width: 148px;
  border: 3px solid var(--frame-border);
  border-radius: 20px;
  padding: 14px 18px;
  font-size: 1.05rem;
  background: var(--btn-bg);
  color: inherit;
  cursor: pointer;
  transition:
    transform 120ms ease,
    box-shadow 120ms ease,
    background-color 120ms ease,
    border-color 400ms ease;
  box-shadow: 0 8px 0 var(--btn-shadow);
}

button:hover {
  transform: translateY(-1px);
}

button:active {
  transform: translateY(2px);
  box-shadow: 0 4px 0 var(--btn-shadow);
}

.primary {
  background: linear-gradient(180deg, var(--btn-primary-from) 0%, var(--btn-primary-to) 100%);
}

.secondary {
  background: var(--btn-secondary-bg);
}

@media (max-width: 720px) {
  .window-frame {
    padding: 14px;
  }

  .panel-header,
  .titlebar {
    align-items: flex-start;
    flex-direction: column;
  }

  .actions,
  .range-row {
    align-items: stretch;
  }

  button {
    width: 100%;
  }
}

.theme-toggle {
  min-width: unset;
  width: 40px;
  height: 40px;
  padding: 6px;
  border-radius: 999px;
  border: 3px solid var(--frame-border);
  background: var(--chip-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: none;
  transition: background 400ms ease, border-color 400ms ease, transform 120ms ease;
}

.theme-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
  transition: transform 500ms ease, opacity 300ms ease;
}

.help-toggle {
  min-width: unset;
  width: 40px;
  height: 40px;
  padding: 6px;
  border-radius: 999px;
  border: 3px solid var(--frame-border);
  background: var(--chip-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: none;
  transition: background 400ms ease, border-color 400ms ease, transform 120ms ease;
}

.help-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.about-toggle {
  min-width: unset;
  width: 40px;
  height: 40px;
  padding: 6px;
  border-radius: 999px;
  border: 3px solid var(--frame-border);
  background: var(--chip-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: none;
  transition: background 400ms ease, border-color 400ms ease, transform 120ms ease;
}

.about-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.help-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  animation: fadeIn 200ms ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.help-popup {
  position: relative;
  width: min(680px, 90vw);
  max-height: 85vh;
  background: var(--frame-bg);
  border: 3px solid var(--frame-border);
  border-radius: 24px;
  padding: 28px 32px;
  overflow-y: auto;
  box-shadow: 0 20px 60px var(--frame-shadow);
  animation: slideUp 300ms ease;
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(20px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

.help-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border: 3px solid var(--frame-border);
  border-radius: 999px;
  background: var(--chip-bg);
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 120ms ease, background 400ms ease;
}

.help-close:hover {
  transform: scale(1.1);
}

.help-popup h2 {
  margin: 0 0 20px;
  font-size: 1.8rem;
  font-weight: 700;
  text-transform: lowercase;
}

.help-section {
  margin-bottom: 20px;
}

.help-section h3 {
  margin: 0 0 8px;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--btn-primary-to);
}

.help-section ul {
  margin: 0;
  padding-left: 20px;
  line-height: 1.6;
}

.help-section li {
  margin-bottom: 8px;
}

.help-section code {
  background: var(--csv-bg);
  border: 1px solid var(--frame-border);
  border-radius: 6px;
  padding: 2px 6px;
  font-family: "Courier New", monospace;
  font-size: 0.9em;
}

.help-section em {
  color: var(--meta-color, #666);
  font-style: italic;
}

.help-section p {
  margin: 0 0 12px;
  line-height: 1.6;
}

.help-section a {
  color: var(--btn-primary-to);
  text-decoration: none;
  font-weight: 600;
}

.help-section a:hover {
  text-decoration: underline;
}

.splash-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: var(--frame-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeOut 500ms ease 1s forwards;
}

@keyframes fadeOut {
  to {
    opacity: 0;
    pointer-events: none;
  }
}

.splash-image {
  max-width: 80%;
  max-height: 80%;
  object-fit: contain;
}
</style>

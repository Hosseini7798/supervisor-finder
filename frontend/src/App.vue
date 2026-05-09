<script setup lang="ts">
import { computed, ref } from "vue";
import { save } from '@tauri-apps/plugin-dialog';
import { writeTextFile } from '@tauri-apps/plugin-fs';
import { WebviewWindow } from '@tauri-apps/api/webviewWindow';

type ResultRow = {
  author: string;
  institution: string;
  country: string;
  email: string;
  score: string;
  num_papers: number;
  papers: string[];
  journals: string[];
};

const query = ref('("deep learning"[tiab] OR "machine learning"[tiab]) AND ("medical imaging"[tiab])');
const fromDate = ref("2023/01/01");
const toDate = ref("2024/12/31");

const isLoading = ref(false);

const rows = ref<ResultRow[]>([]);

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
  const header = ["author", "institution", "country", "email", "score", "num_papers", "papers", "journals"].join(",");
  const lines = rows.value.map((row) =>
    [
      row.author, 
      row.institution, 
      row.country, 
      row.email, 
      row.score, 
      row.num_papers, 
      (row.papers || []).join(" | "), 
      (row.journals || []).join(" | ")
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
  <main class="app-shell">
    <section class="window-frame">
      <header class="titlebar">
        <h1>Find your Supervisor</h1>
        <div class="window-controls" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </header>

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
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(247, 204, 146, 0.65), transparent 30%),
    radial-gradient(circle at bottom right, rgba(168, 208, 216, 0.7), transparent 28%),
    linear-gradient(135deg, #f8f2ea 0%, #f3efe6 45%, #e7ece8 100%);
  color: #23201d;
}

.window-frame {
  width: min(760px, 100%);
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 34px;
  padding: 18px 18px 20px;
  background: rgba(255, 251, 246, 0.82);
  box-shadow: 0 30px 60px rgba(35, 32, 29, 0.16);
  backdrop-filter: blur(8px);
}

.titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
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
}

.window-controls span {
  display: block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 999px;
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
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  padding: 16px 18px;
  font-size: 1.1rem;
  color: inherit;
  outline: none;
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
  border-top: 1px dashed rgba(35, 32, 29, 0.22);
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
  border: 2px solid rgba(35, 32, 29, 0.88);
  border-radius: 999px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
}

.table-wrap,
.csv-box {
  min-height: 220px;
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.78);
  overflow: hidden;
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
  border-bottom: 2px solid rgba(35, 32, 29, 0.85);
}

tbody tr + tr td {
  border-top: 1px solid rgba(35, 32, 29, 0.12);
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
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 20px;
  padding: 14px 18px;
  font-size: 1.05rem;
  background: rgba(255, 255, 255, 0.88);
  color: inherit;
  cursor: pointer;
  transition:
    transform 120ms ease,
    box-shadow 120ms ease,
    background-color 120ms ease;
  box-shadow: 0 8px 0 rgba(35, 32, 29, 0.1);
}

button:hover {
  transform: translateY(-1px);
}

button:active {
  transform: translateY(2px);
  box-shadow: 0 4px 0 rgba(35, 32, 29, 0.12);
}

.primary {
  background: linear-gradient(180deg, #f7c66f 0%, #f0ae3f 100%);
}

.secondary {
  background: rgba(255, 255, 255, 0.82);
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
</style>
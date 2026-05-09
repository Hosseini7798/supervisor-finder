<script setup lang="ts">
import { ref, computed, onMounted } from "vue";

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

const isDark = ref(false);

const rows = ref<ResultRow[]>([]);
const searchQuery = ref("");
const selectedCountries = ref<string[]>([]);
const selectedJournals = ref<string[]>([]);
const showCountryDropdown = ref(false);
const showJournalDropdown = ref(false);
const sortBy = ref<"score" | "num_papers">("score");
const sortAscending = ref(false);

onMounted(() => {
  const data = localStorage.getItem("supervisor-finder-results");
  if (data) {
    try {
      rows.value = JSON.parse(data);
      // Initialize filters to select all by default
      selectedCountries.value = [...uniqueCountries.value];
      selectedJournals.value = [...uniqueJournals.value];
    } catch (e) {
      console.error("Failed to parse rows from localStorage", e);
    }
  }
  const savedTheme = localStorage.getItem('supervisor-finder-theme');
  if (savedTheme === 'dark') {
    isDark.value = true;
  }
});

function toggleTheme() {
  isDark.value = !isDark.value;
  const theme = isDark.value ? 'dark' : 'light';
  localStorage.setItem('supervisor-finder-theme', theme);
}

const uniqueCountries = computed(() => {
  const countries = new Set<string>();
  rows.value.forEach(row => {
    if (row.country) countries.add(row.country);
  });
  return Array.from(countries).sort();
});

const uniqueJournals = computed(() => {
  const journals = new Set<string>();
  rows.value.forEach(row => {
    if (row.journals) {
      row.journals.forEach(j => journals.add(j));
    }
  });
  return Array.from(journals).sort();
});

function toggleAllCountries(e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  if (checked) {
    selectedCountries.value = [...uniqueCountries.value];
  } else {
    selectedCountries.value = [];
  }
}

function toggleAllJournals(e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  if (checked) {
    selectedJournals.value = [...uniqueJournals.value];
  } else {
    selectedJournals.value = [];
  }
}

const filteredAndSortedRows = computed(() => {
  let result = [...rows.value];

  // 1. Filter by country
  if (selectedCountries.value.length < uniqueCountries.value.length) {
    result = result.filter(r => selectedCountries.value.includes(r.country));
  }

  // 1.5 Filter by journal
  if (selectedJournals.value.length < uniqueJournals.value.length) {
    result = result.filter(r => {
      if (!r.journals || r.journals.length === 0) return false;
      return r.journals.some(j => selectedJournals.value.includes(j));
    });
  }

  // 2. Filter by search query
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    result = result.filter(r => 
      (r.author && r.author.toLowerCase().includes(q)) ||
      (r.institution && r.institution.toLowerCase().includes(q)) ||
      (r.email && r.email.toLowerCase().includes(q))
    );
  }

  // 3. Sort
  result.sort((a, b) => {
    let valA: string | number = a[sortBy.value] || "";
    let valB: string | number = b[sortBy.value] || "";

    if (sortBy.value === "score") {
      valA = parseFloat(a.score) || 0;
      valB = parseFloat(b.score) || 0;
    } else if (sortBy.value === "num_papers") {
      valA = a.num_papers || 0;
      valB = b.num_papers || 0;
    }

    if (valA < valB) return sortAscending.value ? -1 : 1;
    if (valA > valB) return sortAscending.value ? 1 : -1;
    return 0;
  });

  return result;
});
</script>

<template>
  <div class="table-window" :class="{ dark: isDark }">
    <div v-if="showCountryDropdown || showJournalDropdown" class="dropdown-backdrop" @click="showCountryDropdown = false; showJournalDropdown = false"></div>

    <header class="toolbar">
      <div class="search-box">
        <input v-model="searchQuery" type="text" placeholder="Search author, email, institution..." />
      </div>
      
      <div class="summary-chip">
        {{ filteredAndSortedRows.length }} {{ filteredAndSortedRows.length === 1 ? 'author' : 'authors' }}
      </div>
      
      <div class="filters">
        <button class="theme-toggle" type="button" @click="toggleTheme" :title="isDark ? 'Switch to light' : 'Switch to dark'">
          <img :src="isDark ? '/moon.png' : '/sun.png'" :alt="isDark ? 'Dark mode' : 'Light mode'" class="theme-icon" />
        </button>

        <div class="dropdown-container">
          <button @click="showCountryDropdown = !showCountryDropdown; showJournalDropdown = false" class="dropdown-btn">
            Countries ({{ selectedCountries.length }})
          </button>
          <div v-if="showCountryDropdown" class="dropdown-menu">
            <label>
              <input type="checkbox" @change="toggleAllCountries" :checked="selectedCountries.length === uniqueCountries.length"> 
              <strong>All Countries</strong>
            </label>
            <hr />
            <label v-for="country in uniqueCountries" :key="country">
              <input type="checkbox" v-model="selectedCountries" :value="country"> {{ country }}
            </label>
          </div>
        </div>

        <div class="dropdown-container">
          <button @click="showJournalDropdown = !showJournalDropdown; showCountryDropdown = false" class="dropdown-btn">
            Journals ({{ selectedJournals.length }})
          </button>
          <div v-if="showJournalDropdown" class="dropdown-menu">
            <label>
              <input type="checkbox" @change="toggleAllJournals" :checked="selectedJournals.length === uniqueJournals.length"> 
              <strong>All Journals</strong>
            </label>
            <hr />
            <label v-for="journal in uniqueJournals" :key="journal">
              <input type="checkbox" v-model="selectedJournals" :value="journal"> {{ journal }}
            </label>
          </div>
        </div>

        <select v-model="sortBy">
          <option value="score">Sort by Score</option>
          <option value="num_papers">Sort by Papers (Count)</option>
        </select>

        <button @click="sortAscending = !sortAscending" class="sort-dir-btn">
          {{ sortAscending ? '↑ Asc' : '↓ Desc' }}
        </button>
      </div>
    </header>

    <div class="table-wrap">
      <table v-if="filteredAndSortedRows.length > 0">
        <thead>
          <tr>
            <th>Author</th>
            <th>Institution</th>
            <th>Country</th>
            <th>Email</th>
            <th>Papers</th>
            <th>Journals</th>
            <th>Keywords</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredAndSortedRows" :key="`${row.author}-${row.email}`">
            <td>{{ row.author }}</td>
            <td>{{ row.institution }}</td>
            <td>{{ row.country }}</td>
            <td>{{ row.email }}</td>
            <td>
              <details v-if="row.paper_details && row.paper_details.length > 0">
                <summary>{{ row.num_papers }} Papers</summary>
                <div class="paper-cards">
                  <div v-for="(pd, idx) in row.paper_details" :key="pd.pmid || idx" class="paper-card">
                    <p class="paper-title">{{ pd.title }}</p>
                    <div class="paper-meta">
                      <span v-if="pd.pub_year">{{ pd.pub_year }}<template v-if="pd.pub_month"> {{ pd.pub_month }}</template></span>
                      <span v-if="pd.journal_title" class="meta-sep">{{ pd.journal_title }}</span>
                      <span v-if="pd.journal_volume" class="meta-sep">Vol. {{ pd.journal_volume }}<template v-if="pd.journal_issue">({{ pd.journal_issue }})</template></span>
                      <span v-if="pd.medline_pgn" class="meta-sep">pp. {{ pd.medline_pgn }}</span>
                      <span v-if="pd.language && pd.language !== 'eng'" class="meta-sep">{{ pd.language }}</span>
                    </div>
                    <div class="paper-ids">
                      <span v-if="pd.pmid">PMID: {{ pd.pmid }}</span>
                      <a v-if="pd.doi" :href="'https://doi.org/' + pd.doi" target="_blank" rel="noopener" class="meta-sep">DOI: {{ pd.doi }}</a>
                      <span v-if="pd.pmc_id" class="meta-sep">PMC: {{ pd.pmc_id }}</span>
                    </div>
                    <div v-if="pd.publication_types && pd.publication_types.length" class="paper-types">
                      <span v-for="pt in pd.publication_types" :key="pt" class="tag">{{ pt }}</span>
                    </div>
                    <details v-if="pd.mesh_headings && pd.mesh_headings.length" class="nested-details">
                      <summary>MeSH ({{ pd.mesh_headings.length }})</summary>
                      <div class="mesh-tags">
                        <span v-for="mh in pd.mesh_headings" :key="mh.descriptor_ui || mh.descriptor" class="tag mesh-tag">{{ mh.descriptor }}<template v-if="mh.qualifier"> / {{ mh.qualifier }}</template></span>
                      </div>
                    </details>
                    <details v-if="pd.grants && pd.grants.length" class="nested-details">
                      <summary>Grants ({{ pd.grants.length }})</summary>
                      <ul class="detail-list">
                        <li v-for="g in pd.grants" :key="g.grant_id || g.agency">{{ g.agency }}<template v-if="g.grant_id"> ({{ g.grant_id }})</template><template v-if="g.country"> — {{ g.country }}</template></li>
                      </ul>
                    </details>
                  </div>
                </div>
              </details>
              <span v-else>{{ row.num_papers }}</span>
            </td>
            <td>
              <details v-if="row.journals && row.journals.length > 0">
                <summary>{{ row.journals.length }} Journals</summary>
                <ul class="detail-list">
                  <li v-for="journal in row.journals" :key="journal">{{ journal }}</li>
                </ul>
              </details>
            </td>
            <td>
              <template v-if="row.keywords && row.keywords.length > 0">
                <div class="keyword-tags">
                  <span v-for="kw in row.keywords" :key="kw" class="tag kw-tag">{{ kw }}</span>
                </div>
              </template>
              <span v-else class="muted">—</span>
            </td>
            <td>{{ row.score }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="no-results">
        No results match your filters.
      </div>
    </div>
  </div>
</template>

<style scoped>
.table-window {
  --tw-bg: #fdfbf7;
  --tw-text: #23201d;
  --tw-toolbar-bg: rgba(255, 255, 255, 0.9);
  --tw-border: rgba(35, 32, 29, 0.88);
  --tw-shadow: rgba(35, 32, 29, 0.08);
  --tw-input-bg: #fff;
  --tw-chip-bg: #fdfbf7;
  --tw-table-bg: #fff;
  --tw-th-bg: #f3efe6;
  --tw-row-hover: #fcf9f2;
  --tw-row-border: rgba(35, 32, 29, 0.12);
  --tw-card-bg: #fdfbf7;
  --tw-card-border: rgba(35, 32, 29, 0.15);
  --tw-meta-color: #555;
  --tw-link-color: #2a6fad;
  --tw-tag-bg: rgba(35, 32, 29, 0.07);
  --tw-tag-border: rgba(35, 32, 29, 0.15);
  --tw-kw-bg: rgba(42, 111, 173, 0.1);
  --tw-kw-border: rgba(42, 111, 173, 0.25);
  --tw-muted: #aaa;
  --tw-sort-bg: #f7c66f;
  --tw-dropdown-bg: #fff;
  --tw-dropdown-hover: #fdfbf7;
  --tw-dropdown-shadow: rgba(35, 32, 29, 0.15);
  --tw-accent: #f0ae3f;
  --tw-dashed: rgba(35, 32, 29, 0.2);
  --tw-detail-color: #444;
  --tw-noresult-color: #666;
}

.table-window.dark {
  --tw-bg: #1a1a2e;
  --tw-text: #e0e0e0;
  --tw-toolbar-bg: rgba(26, 26, 46, 0.92);
  --tw-border: rgba(224, 224, 224, 0.35);
  --tw-shadow: rgba(0, 0, 0, 0.25);
  --tw-input-bg: rgba(255, 255, 255, 0.08);
  --tw-chip-bg: rgba(255, 255, 255, 0.08);
  --tw-table-bg: rgba(22, 33, 62, 0.95);
  --tw-th-bg: rgba(15, 52, 96, 0.7);
  --tw-row-hover: rgba(255, 255, 255, 0.04);
  --tw-row-border: rgba(224, 224, 224, 0.08);
  --tw-card-bg: rgba(255, 255, 255, 0.05);
  --tw-card-border: rgba(224, 224, 224, 0.12);
  --tw-meta-color: #aaa;
  --tw-link-color: #7cacf0;
  --tw-tag-bg: rgba(255, 255, 255, 0.08);
  --tw-tag-border: rgba(255, 255, 255, 0.15);
  --tw-kw-bg: rgba(124, 77, 255, 0.15);
  --tw-kw-border: rgba(124, 77, 255, 0.35);
  --tw-muted: #666;
  --tw-sort-bg: #5e35b1;
  --tw-dropdown-bg: #1a1a2e;
  --tw-dropdown-hover: rgba(255, 255, 255, 0.05);
  --tw-dropdown-shadow: rgba(0, 0, 0, 0.4);
  --tw-accent: #7c4dff;
  --tw-dashed: rgba(224, 224, 224, 0.15);
  --tw-detail-color: #aaa;
  --tw-noresult-color: #888;
}

.table-window {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: var(--tw-bg);
  color: var(--tw-text);
  font-family: "Comic Sans MS", "Segoe Print", "Bradley Hand", "Trebuchet MS", cursive;
  transition: background 400ms ease, color 400ms ease;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: var(--tw-toolbar-bg);
  padding: 16px;
  border-radius: 16px;
  border: 3px solid var(--tw-border);
  box-shadow: 0 10px 30px var(--tw-shadow);
  transition: background 400ms ease, border-color 400ms ease;
}

.search-box input, select, button {
  font-family: inherit;
  border: 3px solid var(--tw-border);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 1rem;
  background: var(--tw-input-bg);
  color: inherit;
  outline: none;
  transition: background 400ms ease, border-color 400ms ease;
}

.search-box input {
  min-width: 250px;
}

.summary-chip {
  border: 2px solid var(--tw-border);
  border-radius: 999px;
  padding: 8px 14px;
  background: var(--tw-chip-bg);
  font-size: 0.95rem;
  font-weight: bold;
  transition: background 400ms ease, border-color 400ms ease;
}

.filters {
  display: flex;
  gap: 12px;
  align-items: center;
}

button.sort-dir-btn {
  background: var(--tw-sort-bg);
  cursor: pointer;
  transition: transform 100ms;
}
button.sort-dir-btn:hover {
  transform: translateY(-2px);
}

.table-wrap {
  flex: 1;
  border: 3px solid var(--tw-border);
  border-radius: 20px;
  background: var(--tw-table-bg);
  overflow: auto;
  box-shadow: 0 10px 30px var(--tw-shadow);
  transition: background 400ms ease, border-color 400ms ease;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 14px 16px;
  text-align: left;
}

th {
  background: var(--tw-th-bg);
  position: sticky;
  top: 0;
  border-bottom: 3px solid var(--tw-border);
  font-weight: bold;
}

tbody tr + tr td {
  border-top: 1px solid var(--tw-row-border);
}

tbody tr:hover {
  background: var(--tw-row-hover);
}

.no-results {
  padding: 40px;
  text-align: center;
  color: var(--tw-noresult-color);
  font-size: 1.2rem;
}

.detail-list {
  margin: 5px 0 0 15px;
  padding: 0;
  font-size: 0.9rem;
  color: var(--tw-detail-color);
}

.detail-list li {
  margin-bottom: 4px;
}

.paper-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
}

.paper-card {
  background: var(--tw-card-bg);
  border: 2px solid var(--tw-card-border);
  border-radius: 10px;
  padding: 10px 12px;
  transition: background 400ms ease, border-color 400ms ease;
}

.paper-title {
  margin: 0 0 4px;
  font-weight: bold;
  font-size: 0.95rem;
  line-height: 1.3;
}

.paper-meta,
.paper-ids {
  font-size: 0.85rem;
  color: var(--tw-meta-color);
  margin-bottom: 3px;
}

.paper-ids a {
  color: var(--tw-link-color);
  text-decoration: none;
}

.paper-ids a:hover {
  text-decoration: underline;
}

.meta-sep::before {
  content: " · ";
  color: var(--tw-muted);
}

.tag {
  display: inline-block;
  background: var(--tw-tag-bg);
  border: 1px solid var(--tw-tag-border);
  border-radius: 6px;
  padding: 2px 7px;
  font-size: 0.8rem;
  margin: 2px 3px 2px 0;
  transition: background 400ms ease, border-color 400ms ease;
}

.paper-types {
  margin-top: 4px;
}

.mesh-tags,
.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

.kw-tag {
  background: var(--tw-kw-bg);
  border-color: var(--tw-kw-border);
}

.mesh-tag {
  font-size: 0.78rem;
}

.nested-details {
  margin-top: 5px;
}

.muted {
  color: var(--tw-muted);
}

.dropdown-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 90;
}

.dropdown-container {
  position: relative;
  display: inline-block;
  z-index: 100;
}

.dropdown-btn {
  padding: 10px 14px;
  background: var(--tw-input-bg);
  border: 3px solid var(--tw-border);
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: 1rem;
  transition: background-color 150ms, border-color 400ms ease;
}

.dropdown-btn:hover {
  background: var(--tw-dropdown-hover);
}

.dropdown-menu {
  position: absolute;
  top: 110%;
  left: 0;
  background: var(--tw-dropdown-bg);
  border: 3px solid var(--tw-border);
  border-radius: 12px;
  padding: 12px;
  min-width: 280px;
  max-height: 400px;
  overflow-y: auto;
  box-shadow: 0 10px 30px var(--tw-dropdown-shadow);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dropdown-menu label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 0.95rem;
  word-break: break-word;
}

.dropdown-menu input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--tw-accent);
}

.dropdown-menu hr {
  border: none;
  border-top: 2px dashed var(--tw-dashed);
  margin: 6px 0;
}

.theme-toggle {
  min-width: unset;
  width: 40px;
  height: 40px;
  padding: 6px;
  border-radius: 999px;
  border: 3px solid var(--tw-border);
  background: var(--tw-chip-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: none;
  cursor: pointer;
  transition: background 400ms ease, border-color 400ms ease, transform 120ms ease;
}

.theme-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
  transition: transform 500ms ease, opacity 300ms ease;
}
</style>

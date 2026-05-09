<script setup lang="ts">
import { ref, computed, onMounted } from "vue";

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
});

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
  <div class="table-window">
    <div v-if="showCountryDropdown || showJournalDropdown" class="dropdown-backdrop" @click="showCountryDropdown = false; showJournalDropdown = false"></div>

    <header class="toolbar">
      <div class="search-box">
        <input v-model="searchQuery" type="text" placeholder="Search author, email, institution..." />
      </div>
      
      <div class="summary-chip">
        {{ filteredAndSortedRows.length }} {{ filteredAndSortedRows.length === 1 ? 'author' : 'authors' }}
      </div>
      
      <div class="filters">
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
            <th>Papers (Count)</th>
            <th>Journals</th>
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
              <details v-if="row.papers && row.papers.length > 0">
                <summary>{{ row.num_papers }} Papers</summary>
                <ul class="detail-list">
                  <li v-for="paper in row.papers" :key="paper">{{ paper }}</li>
                </ul>
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
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: #fdfbf7;
  color: #23201d;
  font-family: "Comic Sans MS", "Segoe Print", "Bradley Hand", "Trebuchet MS", cursive;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.9);
  padding: 16px;
  border-radius: 16px;
  border: 3px solid rgba(35, 32, 29, 0.88);
  box-shadow: 0 10px 30px rgba(35, 32, 29, 0.08);
}

.search-box input, select, button {
  font-family: inherit;
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 1rem;
  background: #fff;
  color: inherit;
  outline: none;
}

.search-box input {
  min-width: 250px;
}

.summary-chip {
  border: 2px solid rgba(35, 32, 29, 0.88);
  border-radius: 999px;
  padding: 8px 14px;
  background: #fdfbf7;
  font-size: 0.95rem;
  font-weight: bold;
}

.filters {
  display: flex;
  gap: 12px;
  align-items: center;
}

button.sort-dir-btn {
  background: #f7c66f;
  cursor: pointer;
  transition: transform 100ms;
}
button.sort-dir-btn:hover {
  transform: translateY(-2px);
}

.table-wrap {
  flex: 1;
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 20px;
  background: #fff;
  overflow: auto;
  box-shadow: 0 10px 30px rgba(35, 32, 29, 0.08);
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
  background: #f3efe6;
  position: sticky;
  top: 0;
  border-bottom: 3px solid rgba(35, 32, 29, 0.88);
  font-weight: bold;
}

tbody tr + tr td {
  border-top: 1px solid rgba(35, 32, 29, 0.12);
}

tbody tr:hover {
  background: #fcf9f2;
}

.no-results {
  padding: 40px;
  text-align: center;
  color: #666;
  font-size: 1.2rem;
}

.detail-list {
  margin: 5px 0 0 15px;
  padding: 0;
  font-size: 0.9rem;
  color: #444;
}

.detail-list li {
  margin-bottom: 4px;
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
  background: #fff;
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: 1rem;
  transition: background-color 150ms;
}

.dropdown-btn:hover {
  background: #fdfbf7;
}

.dropdown-menu {
  position: absolute;
  top: 110%;
  left: 0;
  background: #fff;
  border: 3px solid rgba(35, 32, 29, 0.88);
  border-radius: 12px;
  padding: 12px;
  min-width: 280px;
  max-height: 400px;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(35, 32, 29, 0.15);
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
  accent-color: #f0ae3f;
}

.dropdown-menu hr {
  border: none;
  border-top: 2px dashed rgba(35, 32, 29, 0.2);
  margin: 6px 0;
}
</style>

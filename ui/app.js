// ------------------------------------------------
// NAVIGATION — show/hide sections like separate pages
// ------------------------------------------------
function showSection(sectionId) {
  // hide all sections
  document.querySelectorAll(".section").forEach(s => {
    s.classList.add("hidden");
  });

  // show selected section
  document.getElementById(sectionId).classList.remove("hidden");

  // update active nav link
  document.querySelectorAll("nav a").forEach(a => {
    a.classList.remove("active");
  });
  document.querySelector(`nav a[href="#${sectionId}"]`).classList.add("active");
}

// show analyze section by default on load
document.addEventListener("DOMContentLoaded", () => {
  showSection("analyze");
});

// ------------------------------------------------
// API base URL — FastAPI running in Docker
// ------------------------------------------------
const API = "http://localhost:8000";


// ------------------------------------------------
// analyzeMeeting()
// Called when user clicks Analyze button
// POST /analyze → display results
// ------------------------------------------------
async function analyzeMeeting() {
  const title = document.getElementById("meetingTitle").value.trim();
  const transcript = document.getElementById("transcript").value.trim();

  if (!title || !transcript) {
    alert("Please enter both title and transcript.");
    return;
  }

  // show spinner, hide old results
  document.getElementById("loadingSpinner").classList.remove("hidden");
  document.getElementById("results").classList.add("hidden");

  try {
    const response = await fetch(`${API}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, transcript })
    });

    const data = await response.json();

    if (!response.ok) {
      alert("Error: " + (data.detail || "Something went wrong"));
      return;
    }

    displayResults(data);

  } catch (err) {
    alert("Failed to connect to API. Is Docker running?");
  } finally {
    document.getElementById("loadingSpinner").classList.add("hidden");
  }
}


// ------------------------------------------------
// displayResults()
// Renders all data returned from /analyze
// ------------------------------------------------
function displayResults(data) {
  // summary
  document.getElementById("summaryText").textContent = data.summary;

  // action items
  const actionList = document.getElementById("actionItemsList");
  actionList.innerHTML = "";
  data.action_items.forEach(item => {
    const priorityClass = `badge-${item.priority.toLowerCase()}`;
    const reviewBadge = item.needs_review
      ? `<span class="badge badge-review">⚠ Review</span>`
      : "";

    actionList.innerHTML += `
      <div class="action-item">
        <div class="action-item-header">
          <span class="action-item-task">${item.task}</span>
          <span class="badge ${priorityClass}">${item.priority}</span>
          ${reviewBadge}
        </div>
        <div class="action-item-meta">
          <span>👤 ${item.owner || "Unassigned"}</span>
          <span>📅 ${item.deadline || "No deadline"}</span>
          <span>🎯 Confidence: ${(item.confidence_score * 100).toFixed(0)}%</span>
        </div>
      </div>
    `;
  });

  // decisions
  const decisionsList = document.getElementById("decisionsList");
  decisionsList.innerHTML = "";
  (data.decisions || []).forEach(d => {
    decisionsList.innerHTML += `<li>${d}</li>`;
  });

  // risks
  const risksList = document.getElementById("risksList");
  risksList.innerHTML = "";
  (data.risks || []).forEach(r => {
    risksList.innerHTML += `<li>${r}</li>`;
  });

  // email draft
  document.getElementById("emailDraft").textContent = data.email_draft;

  // show results
  document.getElementById("results").classList.remove("hidden");

  // scroll to results
  document.getElementById("results").scrollIntoView({ behavior: "smooth" });
}


// ------------------------------------------------
// copyEmail()
// Copies email draft to clipboard
// ------------------------------------------------
function copyEmail() {
  const email = document.getElementById("emailDraft").textContent;
  navigator.clipboard.writeText(email).then(() => {
    alert("Email copied to clipboard!");
  });
}


// ------------------------------------------------
// loadMeetings()
// GET /meetings → display meeting cards
// ------------------------------------------------
async function loadMeetings() {
  const container = document.getElementById("meetingsList");
  container.innerHTML = "<p style='color:#7a7a8c'>Loading...</p>";

  try {
    const response = await fetch(`${API}/meetings`);
    const meetings = await response.json();

    if (meetings.length === 0) {
      container.innerHTML = "<p style='color:#7a7a8c'>No meetings yet.</p>";
      return;
    }

    container.innerHTML = "";
    meetings.forEach(m => {
      const date = new Date(m.created_at).toLocaleDateString();
      container.innerHTML += `
        <div class="meeting-card" onclick="loadMeetingDetail(${m.id})">
          <h4>${m.title}</h4>
          <p>📅 ${date}</p>
          <p style="margin-top:6px;color:#7c6af7;font-size:0.85rem">Click to view →</p>
        </div>
      `;
    });

  } catch (err) {
    container.innerHTML = "<p style='color:#ff6b6b'>Failed to load meetings.</p>";
  }
}


// ------------------------------------------------
// loadMeetingDetail()
// GET /meetings/{id} → show action items
// ------------------------------------------------
async function loadMeetingDetail(id) {
  try {
    const response = await fetch(`${API}/meetings/${id}`);
    const data = await response.json();

    // switch to analyze section first
    showSection("analyze");

    // fill in the form
    document.getElementById("meetingTitle").value = data.title;
    document.getElementById("transcript").value = data.transcript;

    // display action items
    displayResults({
      summary: `Viewing saved meeting: ${data.title}`,
      email_draft: "Re-analyze to regenerate email.",
      action_items: data.action_items,
      decisions: [],
      risks: []
    });

  } catch (err) {
    alert("Failed to load meeting detail.");
  }
}

// ------------------------------------------------
// searchMeetings()
// POST /search → display matching chunks
// ------------------------------------------------
async function searchMeetings() {
  const query = document.getElementById("searchQuery").value.trim();

  if (!query) {
    alert("Please enter a search query.");
    return;
  }

  const container = document.getElementById("searchResults");
  container.innerHTML = "<p style='color:#7a7a8c'>Searching...</p>";

  try {
    const response = await fetch(`${API}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });

    const data = await response.json();
    const results = data.results || [];

    if (results.length === 0) {
      container.innerHTML = "<p style='color:#7a7a8c'>No results found.</p>";
      return;
    }

    container.innerHTML = "";
    results.forEach(r => {
      container.innerHTML += `
        <div class="search-result">
          <span>Meeting ID: ${r.meeting_id}</span>
          <p>${r.chunk_text}</p>
        </div>
      `;
    });

  } catch (err) {
    container.innerHTML = "<p style='color:#ff6b6b'>Search failed.</p>";
  }
}
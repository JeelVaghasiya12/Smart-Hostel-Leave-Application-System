const leaveForm = document.getElementById("leave-form");
const fromDate = document.getElementById("from-date");
const toDate = document.getElementById("to-date");
const message = document.getElementById("message");

const leaveTable = document.getElementById("leave-table");
const leaveBody = document.getElementById("leave-body");
const leaveEmpty = document.getElementById("leave-empty");

const noteList = document.getElementById("note-list");
const noteEmpty = document.getElementById("note-empty");
const noteCount = document.getElementById("note-count");
const markReadBtn = document.getElementById("mark-read-btn");

// ---------- date inputs ----------
const today = new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in local time
fromDate.min = today;
toDate.min = today;
fromDate.addEventListener("change", () => {
  toDate.min = fromDate.value;
  if (toDate.value && toDate.value < fromDate.value) toDate.value = fromDate.value;
});

// ---------- leave requests ----------
function renderLeaves(leaves) {
  leaveTable.hidden = leaves.length === 0;
  leaveEmpty.hidden = leaves.length > 0;
  leaveBody.innerHTML = leaves.map((l) => `
    <tr>
      <td class="nowrap">${formatDate(l.from_date)} – ${formatDate(l.to_date)}</td>
      <td>${escapeHtml(l.reason)}</td>
      <td><span class="badge ${l.status.toLowerCase()}">${l.status}</span></td>
    </tr>
  `).join("");
}

async function loadLeaves() {
  renderLeaves(await api("/api/leaves"));
}

leaveForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage(message, "");
  const button = leaveForm.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    await api("/api/leaves", "POST", Object.fromEntries(new FormData(leaveForm)));
    leaveForm.reset();
    setMessage(message, "Request submitted. The warden will review it.", "success");
    await loadLeaves();
  } catch (err) {
    setMessage(message, err.message);
  } finally {
    button.disabled = false;
  }
});

// ---------- notifications ----------
function renderNotifications(items) {
  const unread = items.filter((n) => !n.is_read).length;
  noteCount.textContent = unread;
  noteCount.hidden = unread === 0;
  markReadBtn.hidden = unread === 0;
  noteEmpty.hidden = items.length > 0;
  noteList.innerHTML = items.map((n) => `
    <li class="${n.is_read ? "" : "unread"}">
      <p>${escapeHtml(n.message)}</p>
      <time>${formatDateTime(n.created_at)}</time>
    </li>
  `).join("");
}

async function loadNotifications() {
  renderNotifications(await api("/api/notifications"));
}

markReadBtn.addEventListener("click", async () => {
  await api("/api/notifications/read", "POST");
  await loadNotifications();
});

// ---------- start ----------
function loadAll() {
  loadLeaves();
  loadNotifications();
}
loadAll();
setInterval(loadAll, 30000); // pick up the warden's decisions without a page refresh

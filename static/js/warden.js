const leaveTable = document.getElementById("leave-table");
const leaveBody = document.getElementById("leave-body");
const leaveEmpty = document.getElementById("leave-empty");
const statusFilter = document.getElementById("status-filter");
const pendingCount = document.getElementById("pending-count");
const message = document.getElementById("message");

let allLeaves = [];

function render() {
  const wanted = statusFilter.value;
  const rows = wanted === "All" ? allLeaves : allLeaves.filter((l) => l.status === wanted);

  const pending = allLeaves.filter((l) => l.status === "Pending").length;
  pendingCount.textContent = pending ? `(${pending} pending)` : "";

  leaveTable.hidden = rows.length === 0;
  leaveEmpty.hidden = rows.length > 0;

  leaveBody.innerHTML = rows.map((l) => `
    <tr>
      <td>${escapeHtml(l.student_name)}</td>
      <td class="nowrap">${formatDate(l.from_date)} – ${formatDate(l.to_date)}</td>
      <td>${escapeHtml(l.reason)}</td>
      <td><span class="badge ${l.status.toLowerCase()}">${l.status}</span></td>
      <td>${l.status === "Pending" ? `
        <div class="actions-row">
          <button class="btn small" data-id="${l.id}" data-action="approve">Approve</button>
          <button class="btn small ghost danger" data-id="${l.id}" data-action="reject">Reject</button>
        </div>` : ""}
      </td>
    </tr>
  `).join("");
}

async function loadLeaves() {
  allLeaves = await api("/api/leaves");
  render();
}

// One click handler for every Approve / Reject button.
leaveBody.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  button.disabled = true;
  setMessage(message, "");
  try {
    await api(`/api/leaves/${button.dataset.id}/${button.dataset.action}`, "POST");
  } catch (err) {
    setMessage(message, err.message);
  }
  await loadLeaves();
});

statusFilter.addEventListener("change", render);

loadLeaves();
setInterval(loadLeaves, 30000); // show new requests without a page refresh

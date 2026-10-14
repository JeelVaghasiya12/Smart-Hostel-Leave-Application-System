// Shared helpers used by every page.

async function api(url, method = "GET", body = null) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));

  if (res.status === 401) {
    window.location.href = "/login"; // session expired
    throw new Error("Please log in");
  }
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

// Always escape user-written text before putting it into innerHTML.
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function formatDateTime(iso) {
  return new Date(iso).toLocaleString("en-IN", {
    day: "numeric", month: "short", hour: "numeric", minute: "2-digit",
  });
}

function setMessage(el, text, type = "error") {
  el.textContent = text;
  el.className = "message " + (type === "success" ? "success" : "");
}

const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    await api("/api/logout", "POST");
    window.location.href = "/login";
  });
}

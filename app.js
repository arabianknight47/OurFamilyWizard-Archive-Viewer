const archive = window.OFW_ARCHIVE_DATA || { meta: {}, messages: [] };
const PAGE_SIZE = 50;

const state = {
  query: "",
  folder: "Inbox",
  page: 0,
  selectedThreadId: null,
  threadStars: new Set(loadList("ofw.threadStars")),
  messageStars: new Set(loadList("ofw.messageStars")),
};

const els = {
  inboxView: document.querySelector("#inboxView"),
  detailView: document.querySelector("#detailView"),
  searchInput: document.querySelector("#searchInput"),
  archiveSummary: document.querySelector("#archiveSummary"),
  archiveFooterText: document.querySelector("#archiveFooterText"),
  favoritesCount: document.querySelector("#favoritesCount"),
  threadRows: document.querySelector("#threadRows"),
  rangeText: document.querySelector("#rangeText"),
  prevPageBtn: document.querySelector("#prevPageBtn"),
  nextPageBtn: document.querySelector("#nextPageBtn"),
  backBtn: document.querySelector("#backBtn"),
  threadDetail: document.querySelector("#threadDetail"),
  prevThreadBtn: document.querySelector("#prevThreadBtn"),
  nextThreadBtn: document.querySelector("#nextThreadBtn"),
  folderButtons: Array.from(document.querySelectorAll("[data-folder]")),
};

function loadList(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "[]");
  } catch {
    return [];
  }
}

function saveList(key, list) {
  localStorage.setItem(key, JSON.stringify(Array.from(list)));
}

function byDate(a, b) {
  return (a.sentAt || a.sentAtRaw).localeCompare(b.sentAt || b.sentAtRaw);
}

function buildThreads() {
  const map = new Map();
  archive.messages.forEach((message) => {
    if (!map.has(message.threadId)) {
      map.set(message.threadId, {
        id: message.threadId,
        subject: message.threadSubject || message.subject,
        messages: [],
      });
    }
    map.get(message.threadId).messages.push(message);
  });

  return Array.from(map.values())
    .map((thread) => {
      thread.messages.sort(byDate);
      thread.latest = thread.messages[thread.messages.length - 1];
      thread.participants = Array.from(
        new Set(thread.messages.flatMap((msg) => [msg.from, ...(msg.to || [])]).filter(Boolean))
      );
      return thread;
    })
    .sort((a, b) => byDate(b.latest, a.latest));
}

const allThreads = buildThreads();

function matchesFolder(thread) {
  if (state.folder === "All Messages") return true;
  if (state.folder === "Favorites") return isFavoriteThread(thread);
  if (state.folder === "Sent") return thread.messages.some((message) => message.folder === "Sent");
  if (state.folder === "Inbox") return true;
  return false;
}

function rowMessageForThread(thread) {
  if (state.folder !== "Sent") return thread.latest;
  return [...thread.messages].reverse().find((message) => message.folder === "Sent") || thread.latest;
}

function matchesSearch(thread) {
  const query = state.query.trim().toLowerCase();
  if (!query) return true;
  const haystack = [
    thread.subject,
    thread.participants.join(" "),
    ...thread.messages.flatMap((msg) => [msg.subject, msg.from, (msg.to || []).join(" "), msg.body]),
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
}

function isFavoriteThread(thread) {
  return state.threadStars.has(thread.id) || thread.messages.some((msg) => state.messageStars.has(msg.id));
}

function filteredThreads() {
  return allThreads.filter((thread) => matchesFolder(thread) && matchesSearch(thread));
}

function formatRowDate(message) {
  if (!message.sentAt) return message.sentAtRaw || "";
  const date = new Date(message.sentAt);
  const today = new Date();
  if (
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
  ) {
    return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  }
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

function formatFooterDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleDateString([], { month: "long", day: "numeric", year: "numeric" });
}

function renderArchiveFooter() {
  const datedMessages = archive.messages.filter((message) => message.sentAt);
  if (!datedMessages.length) return;
  const sorted = [...datedMessages].sort(byDate);
  const start = formatFooterDate(sorted[0].sentAt);
  const end = formatFooterDate(sorted[sorted.length - 1].sentAt);
  const participants = archive.meta.participants || inferParticipants();
  const participantText = participants.length ? ` between ${participants.join(" and ")}` : "";
  els.archiveFooterText.textContent = `This is a local OurFamilyWizard message archive${participantText} from ${start} through ${end}.`;
}

function inferParticipants() {
  return Array.from(new Set(archive.messages.flatMap((message) => [message.from, ...(message.to || [])]).filter(Boolean)));
}

function initials(name) {
  return (name || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function preview(text) {
  return (text || "").replace(/\s+/g, " ").trim();
}

function renderRows() {
  const threads = filteredThreads();
  const maxPage = Math.max(0, Math.ceil(threads.length / PAGE_SIZE) - 1);
  state.page = Math.min(state.page, maxPage);
  const pageStart = state.page * PAGE_SIZE;
  const pageThreads = threads.slice(pageStart, pageStart + PAGE_SIZE);
  const rangeStart = threads.length ? pageStart + 1 : 0;
  const rangeEnd = pageStart + pageThreads.length;

  els.rangeText.textContent = threads.length ? `${rangeStart} - ${rangeEnd} of ${threads.length}` : "0 - 0";
  els.prevPageBtn.disabled = state.page === 0;
  els.nextPageBtn.disabled = state.page >= maxPage;
  els.favoritesCount.textContent = allThreads.filter(isFavoriteThread).length;
  els.archiveSummary.textContent = `${archive.meta.messageCount || archive.messages.length} messages in ${
    archive.meta.threadCount || allThreads.length
  } threads`;
  els.threadRows.innerHTML = "";

  if (!threads.length) {
    els.threadRows.innerHTML = `<div class="empty-state">No messages match this view.</div>`;
    return;
  }

  pageThreads.forEach((thread) => {
    const latest = rowMessageForThread(thread);
    const row = document.createElement("div");
    row.className = `thread-row${thread.id === state.selectedThreadId ? " selected" : ""}`;
    row.tabIndex = 0;
    row.setAttribute("role", "row");
    row.innerHTML = `
      <span class="check-box" aria-hidden="true"></span>
      <span class="from-cell">
        <span class="reply-icon" aria-hidden="true">&larrhk;</span>
        <span class="sender-name">${escapeHtml(latest.from)}</span>
      </span>
      <span>
        <button class="thread-star ${state.threadStars.has(thread.id) ? "is-starred" : ""}" type="button" aria-label="Favorite thread">&#9733;</button>
      </span>
      <span class="subject-line">
        <span class="subject-title">${escapeHtml(thread.subject)}</span>
        <span class="preview">${escapeHtml(preview(latest.body))}</span>
        <span class="count-pill">${thread.messages.length}</span>
      </span>
      <span class="date-cell">${escapeHtml(formatRowDate(latest))}</span>
    `;

    row.addEventListener("click", () => openThread(thread.id));
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openThread(thread.id);
      }
    });
    row.querySelector(".thread-star").addEventListener("click", (event) => {
      event.stopPropagation();
      toggleThreadStar(thread.id);
    });
    els.threadRows.appendChild(row);
  });
}

function openThread(threadId) {
  state.selectedThreadId = threadId;
  els.inboxView.classList.remove("active-view");
  els.detailView.classList.add("active-view");
  renderDetail();
  renderRows();
}

function closeThread() {
  els.detailView.classList.remove("active-view");
  els.inboxView.classList.add("active-view");
}

function selectedThread() {
  return allThreads.find((thread) => thread.id === state.selectedThreadId) || filteredThreads()[0] || allThreads[0];
}

function renderDetail() {
  const thread = selectedThread();
  if (!thread) return;
  state.selectedThreadId = thread.id;
  const latest = thread.latest;
  const previous = thread.messages.slice(0, -1).reverse();

  els.threadDetail.innerHTML = `
    <div class="detail-heading">
      <h1>${escapeHtml(latest.subject)}</h1>
      <span class="folder-pill">${escapeHtml(latest.folder || "Inbox")}</span>
      <span class="count-pill">${thread.messages.length} messages</span>
      <div class="detail-actions">
        <button class="thread-star ${state.threadStars.has(thread.id) ? "is-starred" : ""}" type="button" id="detailThreadStar" aria-label="Favorite thread">&#9733;</button>
      </div>
    </div>
    ${renderMessage(latest, true)}
    ${previous.map((msg) => renderMessage(msg, false)).join("")}
  `;

  document.querySelector("#detailThreadStar").addEventListener("click", () => toggleThreadStar(thread.id));
  els.threadDetail.querySelectorAll("[data-message-star]").forEach((button) => {
    button.addEventListener("click", () => toggleMessageStar(button.dataset.messageStar));
  });
}

function renderMessage(message, latest) {
  const to = (message.to || []).join(", ");
  const page =
    message.source.pageStart === message.source.pageEnd
      ? `PDF page ${message.source.pageStart}`
      : `PDF pages ${message.source.pageStart}-${message.source.pageEnd}`;
  const source = `${message.source.reportFile}, ${page}, message ${message.source.messageNumber}`;
  const avatarClass = message.folder === "Sent" ? "sent" : "";

  if (latest) {
    return `
      <section class="message-card latest">
        <div class="message-header">
          <span class="avatar ${avatarClass}">${escapeHtml(initials(message.from))}</span>
          <div>
            <div class="sender-title">${escapeHtml(message.from)}</div>
            <div class="sent-line">Sent ${escapeHtml(message.sentAtDisplay || message.sentAtRaw)}</div>
          </div>
          <button class="message-star ${state.messageStars.has(message.id) ? "is-starred" : ""}" type="button" data-message-star="${message.id}" aria-label="Favorite message">&#9733;</button>
        </div>
        <div class="to-line">To: <strong>${escapeHtml(to)}</strong> ${message.viewedAtDisplay ? `(${escapeHtml(message.viewedAtDisplay)})` : ""}</div>
        <div class="source-line"><span class="source-pill">${escapeHtml(source)}</span></div>
        <div class="message-body">${escapeHtml(message.body)}</div>
      </section>
    `;
  }

  return `
    <section class="message-card">
      <hr class="message-separator">
      <div class="history-meta">
        <div><strong>From:</strong> ${escapeHtml(message.from)} on ${escapeHtml(message.sentAtDisplay || message.sentAtRaw)}</div>
        <div><strong>To:</strong> ${escapeHtml(to)}</div>
        <div><strong>Subject:</strong> ${escapeHtml(message.subject)}</div>
        <div><span class="source-pill">${escapeHtml(source)}</span></div>
      </div>
      <button class="message-star ${state.messageStars.has(message.id) ? "is-starred" : ""}" type="button" data-message-star="${message.id}" aria-label="Favorite message">&#9733;</button>
      <div class="message-body">${escapeHtml(message.body)}</div>
    </section>
  `;
}

function toggleThreadStar(threadId) {
  if (state.threadStars.has(threadId)) {
    state.threadStars.delete(threadId);
  } else {
    state.threadStars.add(threadId);
  }
  saveList("ofw.threadStars", state.threadStars);
  els.favoritesCount.textContent = allThreads.filter(isFavoriteThread).length;
  renderRows();
  if (els.detailView.classList.contains("active-view")) renderDetail();
}

function toggleMessageStar(messageId) {
  if (state.messageStars.has(messageId)) {
    state.messageStars.delete(messageId);
  } else {
    state.messageStars.add(messageId);
  }
  saveList("ofw.messageStars", state.messageStars);
  els.favoritesCount.textContent = allThreads.filter(isFavoriteThread).length;
  renderRows();
  renderDetail();
}

function moveThread(offset) {
  const threads = filteredThreads();
  const currentIndex = threads.findIndex((thread) => thread.id === state.selectedThreadId);
  const next = threads[currentIndex + offset];
  if (next) openThread(next.id);
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

els.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  state.page = 0;
  renderRows();
});

els.prevPageBtn.addEventListener("click", () => {
  if (state.page > 0) {
    state.page -= 1;
    renderRows();
  }
});

els.nextPageBtn.addEventListener("click", () => {
  const maxPage = Math.max(0, Math.ceil(filteredThreads().length / PAGE_SIZE) - 1);
  if (state.page < maxPage) {
    state.page += 1;
    renderRows();
  }
});

els.backBtn.addEventListener("click", closeThread);
els.prevThreadBtn.addEventListener("click", () => moveThread(-1));
els.nextThreadBtn.addEventListener("click", () => moveThread(1));

els.folderButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.folder = button.dataset.folder;
    state.page = 0;
    els.detailView.classList.remove("active-view");
    els.inboxView.classList.add("active-view");
    els.folderButtons.forEach((item) => item.classList.toggle("active", item === button));
    renderRows();
  });
});

renderRows();
renderArchiveFooter();

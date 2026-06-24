const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const moodButtons = [...document.querySelectorAll("[data-mood]")];
const focusInput = document.querySelector("#focusInput");
const energyInput = document.querySelector("#energyInput");
const energyValue = document.querySelector("#energyValue");
const sendButton = document.querySelector("#sendButton");
const clearButton = document.querySelector("#clearButton");
const historyList = document.querySelector("#historyList");
const signal = document.querySelector(".signal");

let selectedMood = "Спокойно";

function readHistory() {
  try {
    return JSON.parse(localStorage.getItem("day-ping-history")) || [];
  } catch {
    return [];
  }
}

function writeHistory(items) {
  localStorage.setItem("day-ping-history", JSON.stringify(items.slice(0, 8)));
}

function renderHistory() {
  const items = readHistory();
  historyList.innerHTML = "";

  if (items.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "Пока пусто";
    historyList.append(empty);
    return;
  }

  for (const item of items) {
    const entry = document.createElement("li");
    const title = document.createElement("strong");
    const meta = document.createElement("span");

    title.textContent = item.focus || "Без текста";
    meta.className = "entry-meta";
    meta.textContent = `${item.mood} · энергия ${item.energy}/5`;

    entry.append(title, meta);
    historyList.append(entry);
  }
}

function buildPayload() {
  return {
    mood: selectedMood,
    energy: Number(energyInput.value),
    focus: focusInput.value.trim(),
    createdAt: new Date().toISOString(),
  };
}

function savePayload(payload) {
  const nextHistory = [payload, ...readHistory()];
  writeHistory(nextHistory);
  renderHistory();
}

function setMood(nextMood) {
  selectedMood = nextMood;
  for (const button of moodButtons) {
    button.classList.toggle("is-active", button.dataset.mood === nextMood);
  }
}

moodButtons.forEach((button) => {
  button.addEventListener("click", () => setMood(button.dataset.mood));
});

energyInput.addEventListener("input", () => {
  energyValue.textContent = `${energyInput.value}/5`;
});

sendButton.addEventListener("click", async () => {
  const payload = buildPayload();
  savePayload(payload);

  if (tg?.sendData) {
    tg.sendData(JSON.stringify(payload));
    tg.close();
    return;
  }

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    sendButton.textContent = "Скопировано";
  } else {
    sendButton.textContent = "Открой в Telegram";
  }

  window.setTimeout(() => {
    sendButton.textContent = "Отправить в Telegram";
  }, 1600);
});

clearButton.addEventListener("click", () => {
  writeHistory([]);
  renderHistory();
});

signal.style.background = tg ? "var(--teal)" : "var(--gold)";
renderHistory();

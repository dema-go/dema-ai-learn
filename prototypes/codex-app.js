"use strict";

function showScreen(screenId) {
  const target = document.getElementById(screenId);
  if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
}

function togglePanel(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const visible = panel.classList.toggle("is-visible");
  panel.setAttribute("aria-hidden", String(!visible));
}

function selectOption(button) {
  const group = button.closest("[data-choice-group]");
  if (group) group.querySelectorAll(".choice-card").forEach((item) => item.classList.remove("is-selected"));
  button.classList.add("is-selected");
  button.setAttribute("aria-pressed", "true");
  if (group) group.querySelectorAll(".choice-card:not(.is-selected)").forEach((item) => item.setAttribute("aria-pressed", "false"));
}

function submitAnswer(button) {
  const root = button.closest("[data-quiz]");
  if (!root) return;
  const selected = root.querySelector(".choice-card.is-selected");
  if (!selected) {
    showToast("先选一个答案，考考才好判卷");
    return;
  }
  const correct = selected.dataset.correct === "true";
  selected.classList.add(correct ? "is-correct" : "is-wrong");
  const feedback = root.querySelector(correct ? "[data-feedback-correct]" : "[data-feedback-wrong]");
  if (feedback) feedback.classList.add("is-visible");
}

let toastTimer;
function showToast(message) {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    toast.setAttribute("role", "status");
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 1800);
}

function startGeneration(root) {
  const stages = [...root.querySelectorAll(".stage-list li")];
  const bar = root.querySelector(".progress > i");
  stages.forEach((stage) => stage.classList.remove("active", "done"));
  stages.forEach((stage, index) => {
    setTimeout(() => {
      stages.slice(0, index).forEach((item) => item.classList.add("done"));
      stages.forEach((item) => item.classList.remove("active"));
      stage.classList.add("active");
      if (bar) bar.style.setProperty("--progress", `${(index + 1) * 25}%`);
      if (index === stages.length - 1) setTimeout(() => stage.classList.add("done"), 650);
    }, index * 800);
  });
}

function updateTextCount(textarea) {
  const output = document.getElementById(textarea.getAttribute("aria-describedby"));
  if (!output) return;
  const length = textarea.value.length;
  output.textContent = `${length} / 8000`;
  output.style.color = length > 8000 ? "var(--danger)" : "";
}

document.addEventListener("click", (event) => {
  const close = event.target.closest("[data-close]");
  if (close) togglePanel(close.dataset.close);
});

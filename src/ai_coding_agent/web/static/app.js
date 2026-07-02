const repositoryPath = document.querySelector("#repositoryPath");
const apiStatus = document.querySelector("#apiStatus");
const llmStatus = document.querySelector("#llmStatus");
const repositoryOutput = document.querySelector("#repositoryOutput");
const agentOutput = document.querySelector("#agentOutput");
const historyOutput = document.querySelector("#historyOutput");

repositoryPath.value = window.localStorage.getItem("repositoryPath") || "";

document.querySelector("#loadStatus").addEventListener("click", loadStatus);
document.querySelector("#summarizeBtn").addEventListener("click", summarizeRepository);
document.querySelector("#searchBtn").addEventListener("click", searchRepository);
document.querySelector("#explainBtn").addEventListener("click", explainRepository);
document.querySelector("#runAgentBtn").addEventListener("click", runAgent);
document.querySelector("#historyBtn").addEventListener("click", loadHistory);
document.querySelector("#clearHistoryBtn").addEventListener("click", clearHistory);
repositoryPath.addEventListener("change", () => {
  window.localStorage.setItem("repositoryPath", repositoryPath.value);
});

loadStatus();

async function loadStatus() {
  try {
    const health = await apiGet("/health");
    apiStatus.textContent = health.status;
  } catch (error) {
    apiStatus.textContent = "offline";
  }

  try {
    const llm = await apiGet("/debug/llm");
    llmStatus.textContent = llm.provider === "none" ? "not configured" : `${llm.provider}: ${llm.model}`;
  } catch (error) {
    llmStatus.textContent = "unknown";
  }
}

async function summarizeRepository() {
  setLoading(repositoryOutput, "Reading repository...");
  try {
    const result = await apiPost("/repositories/summary", {
      repository_path: requireRepositoryPath(),
    });
    repositoryOutput.textContent = `Root: ${result.root}\nFiles: ${result.files.length}\n\n${result.files
      .map((file) => `- ${file.path}`)
      .join("\n")}`;
  } catch (error) {
    showError(repositoryOutput, error);
  }
}

async function searchRepository() {
  setLoading(repositoryOutput, "Searching...");
  try {
    const result = await apiPost("/repositories/search", {
      repository_path: requireRepositoryPath(),
      query: document.querySelector("#searchQuery").value,
    });
    repositoryOutput.textContent = result.files.length
      ? result.files.map((file) => `## ${file.path}\n${file.content}`).join("\n\n")
      : "No matching files.";
  } catch (error) {
    showError(repositoryOutput, error);
  }
}

async function explainRepository() {
  setLoading(repositoryOutput, "Asking the LLM...");
  try {
    const result = await apiPost("/repositories/explain", {
      repository_path: requireRepositoryPath(),
      question: document.querySelector("#question").value,
    });
    renderMarkdown(repositoryOutput, result.answer);
  } catch (error) {
    showError(repositoryOutput, error);
  }
}

async function runAgent() {
  setLoading(agentOutput, "Running agent...");
  try {
    const command = document.querySelector("#testCommand").value.trim();
    const patchDiff = document.querySelector("#patchDiff").value.trim();
    const result = await apiPost("/agent/run", {
      repository_path: requireRepositoryPath(),
      instruction: document.querySelector("#instruction").value,
      patch_diff: patchDiff || null,
      test_command: command ? command.split(/\s+/) : null,
      max_fix_attempts: Number(document.querySelector("#maxFixAttempts").value),
    });
    agentOutput.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    showError(agentOutput, error);
  }
}

async function loadHistory() {
  setLoading(historyOutput, "Loading history...");
  try {
    const result = await apiGet("/history");
    renderMarkdown(historyOutput, result.markdown);
  } catch (error) {
    showError(historyOutput, error);
  }
}

async function clearHistory() {
  if (!window.confirm("Clear all saved history?")) {
    return;
  }

  setLoading(historyOutput, "Clearing history...");
  try {
    const result = await apiDelete("/history");
    renderMarkdown(historyOutput, result.markdown);
  } catch (error) {
    showError(historyOutput, error);
  }
}

async function apiGet(path) {
  const response = await fetch(path);
  return parseResponse(response);
}

async function apiPost(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseResponse(response);
}

async function apiDelete(path) {
  const response = await fetch(path, { method: "DELETE" });
  return parseResponse(response);
}

async function parseResponse(response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.detail || JSON.stringify(body));
  }
  return body;
}

function requireRepositoryPath() {
  const value = repositoryPath.value.trim();
  if (!value) {
    throw new Error("Enter a repository path.");
  }
  return value;
}

function setLoading(element, message) {
  element.classList.remove("error");
  element.textContent = message;
}

function showError(element, error) {
  element.classList.add("error");
  element.textContent = error.message;
}

function renderMarkdown(element, markdown) {
  element.classList.remove("error");
  element.innerHTML = markdownToHtml(markdown);
}

function markdownToHtml(markdown) {
  const lines = escapeHtml(markdown).split(/\r?\n/);
  const html = [];
  const codeLines = [];
  let listType = "";
  let inCodeBlock = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        html.push(`<pre><code>${codeLines.join("\n")}</code></pre>`);
        codeLines.length = 0;
        inCodeBlock = false;
      } else {
        closeList(html, listType);
        listType = "";
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    if (!trimmed) {
      closeList(html, listType);
      listType = "";
      continue;
    }

    const unorderedItem = trimmed.match(/^[-*]\s+(.+)$/);
    if (unorderedItem) {
      if (listType !== "ul") {
        closeList(html, listType);
        html.push("<ul>");
        listType = "ul";
      }
      html.push(`<li>${inlineMarkdown(unorderedItem[1])}</li>`);
      continue;
    }

    const orderedItem = trimmed.match(/^\d+\.\s+(.+)$/);
    if (orderedItem) {
      if (listType !== "ol") {
        closeList(html, listType);
        html.push("<ol>");
        listType = "ol";
      }
      html.push(`<li>${inlineMarkdown(orderedItem[1])}</li>`);
      continue;
    }

    closeList(html, listType);
    listType = "";

    if (trimmed.startsWith("### ")) {
      html.push(`<h3>${inlineMarkdown(trimmed.slice(4))}</h3>`);
    } else if (trimmed.startsWith("## ")) {
      html.push(`<h2>${inlineMarkdown(trimmed.slice(3))}</h2>`);
    } else if (trimmed.startsWith("# ")) {
      html.push(`<h2>${inlineMarkdown(trimmed.slice(2))}</h2>`);
    } else {
      html.push(`<p>${inlineMarkdown(trimmed)}</p>`);
    }
  }

  if (inCodeBlock) {
    html.push(`<pre><code>${codeLines.join("\n")}</code></pre>`);
  }
  closeList(html, listType);

  return html.join("");
}

function closeList(html, listType) {
  if (listType) {
    html.push(`</${listType}>`);
  }
}

function inlineMarkdown(text) {
  return text
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

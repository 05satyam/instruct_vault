async function loadPrompts() {
  const list = document.getElementById("promptList");
  list.innerHTML = "Loading...";
  try {
    const ref = document.getElementById("refSelect").value;
    const url = ref ? `/prompts?ref=${encodeURIComponent(ref)}` : "/prompts";
    const res = await fetch(url);
    const data = await res.json();
    list.innerHTML = "";
    if (!data.length) {
      list.innerHTML = "<div style='padding:10px;color:#94a3b8;'>No prompts found.</div>";
      return;
    }
    data.forEach((p) => {
      const btn = document.createElement("button");
      btn.textContent = p;
      btn.onclick = () => loadPrompt(p);
      list.appendChild(btn);
    });
  } catch (e) {
    list.innerHTML = "<div style='padding:10px;color:#f87171;'>Failed to load prompts.</div>";
  }
}

async function loadPrompt(path) {
  const preview = document.getElementById("promptPreview");
  preview.textContent = "Loading...";
  try {
    const ref = document.getElementById("refSelect").value;
    const url = ref
      ? `/prompt?prompt_path=${encodeURIComponent(path)}&ref=${encodeURIComponent(ref)}`
      : `/prompt?prompt_path=${encodeURIComponent(path)}`;
    const res = await fetch(url);
    const data = await res.json();
    preview.textContent = JSON.stringify(data, null, 2);
    window.__currentPromptPath = path;
    window.__currentPromptRef = ref || null;
  } catch (e) {
    preview.textContent = "Failed to load prompt.";
  }
}

async function loadRefs() {
  try {
    const res = await fetch("/refs");
    const data = await res.json();
    const sel = document.getElementById("refSelect");
    data.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      sel.appendChild(opt);
    });
    sel.onchange = () => {
      document.getElementById("promptPreview").textContent = "Select a prompt to view its spec.";
      document.getElementById("renderOutput").textContent = "Rendered messages will appear here.";
      window.__currentPromptPath = null;
      window.__currentPromptRef = sel.value || null;
      loadPrompts();
    };
  } catch (e) {}
}

function attachHandlers() {
  document.getElementById("varsInput").value = JSON.stringify({name: "ivault"});

  document.getElementById("copyBtn").onclick = async () => {
    const text = document.getElementById("promptPreview").textContent;
    try {
      await navigator.clipboard.writeText(text);
      document.getElementById("copyBtn").textContent = "Copied";
      setTimeout(() => (document.getElementById("copyBtn").textContent = "Copy JSON"), 1200);
    } catch (e) {}
  };

  document.getElementById("renderBtn").onclick = async () => {
    const out = document.getElementById("renderOutput");
    out.textContent = "Rendering...";
    try {
      const path = window.__currentPromptPath;
      if (!path) {
        out.textContent = "Select a prompt first.";
        return;
      }
      const varsText = document.getElementById("varsInput").value || "{}";
      let vars;
      try {
        vars = JSON.parse(varsText);
      } catch (e) {
        out.textContent = 'Invalid JSON in vars. Example: {"name":"Ava"}';
        return;
      }
      const ref = window.__currentPromptRef;
      const payload = { prompt_path: path, vars, ref };
      const res = await fetch("/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        out.textContent = data.detail || "Render failed.";
        return;
      }
      out.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      out.textContent = "Render failed. Check JSON vars.";
    }
  };
}

window.addEventListener("load", () => {
  loadPrompts();
  loadRefs();
  attachHandlers();
});

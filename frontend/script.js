document.addEventListener("DOMContentLoaded", () => {
  /* ---------- INDEX PAGE ---------- */

  // Get a Quote -> upload page
  const quoteBtn = document.getElementById("get-quote");
  if (quoteBtn) {
    quoteBtn.addEventListener("click", () => {
      window.location.href = "upload.html";
    });
  }


  // Contact Us -> footer at the bottom
  const contactBtn = document.getElementById("contact-btn");
  const contactSection = document.getElementById("contact");
  if (contactBtn && contactSection) {
    contactBtn.addEventListener("click", () => {
      contactSection.scrollIntoView({ behavior: "smooth" });
    });
  }

  // About -> "How It Works"
  const aboutLink = document.getElementById("about-link");
  const howItWorks = document.getElementById("featured-3");
  if (aboutLink && howItWorks) {
    aboutLink.addEventListener("click", (e) => {
      e.preventDefault();
      howItWorks.scrollIntoView({ behavior: "smooth" });
    });
  }

  // Carousel auto-play (only if Bootstrap and the carousel exist)
  const carouselEl = document.getElementById("carouselExampleIndicators");
  if (carouselEl && typeof bootstrap !== "undefined") {
    new bootstrap.Carousel(carouselEl, {
      interval: 4000,
      ride: "carousel",
      pause: "hover",
    });
  }

  // Footer year
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- UPLOAD PAGE ---------- */

  const uploadButton = document.getElementById("upload-button");
  const uploadBox = document.querySelector(".container");
  const error = document.getElementById("error");
  const imageDisplay = document.getElementById("image-display");

  if (uploadButton && uploadBox && error && imageDisplay) {
    const fileHandler = (file, name, type) => {
      if (type.split("/")[0] !== "image") {
        error.innerText = "Please upload an image file";
        return false;
      }
      error.innerText = "";
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onloadend = () => {
        const imageContainer = document.createElement("figure");
        const img = document.createElement("img");
        img.src = reader.result;
        imageContainer.appendChild(img);
        imageContainer.innerHTML += `<figcaption>${name}</figcaption>`;
        imageDisplay.appendChild(imageContainer);
      };
    };

    // Upload button
    uploadButton.addEventListener("change", () => {
      imageDisplay.innerHTML = "";
      Array.from(uploadButton.files).forEach((file) => {
        fileHandler(file, file.name, file.type);
      });
    });

    // Drag and drop
    ["dragenter", "dragover"].forEach((evt) => {
      uploadBox.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadBox.classList.add("active");
      });
    });

    uploadBox.addEventListener("dragleave", (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadBox.classList.remove("active");
    });

    uploadBox.addEventListener("drop", (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadBox.classList.remove("active");
      imageDisplay.innerHTML = "";
      Array.from(e.dataTransfer.files).forEach((file) => {
        fileHandler(file, file.name, file.type);
      });
    });

    error.innerText = "";
  }
});
  /* ---------- RESULTS PAGE ---------- */
  const resultsPage = document.getElementById("results-page");
  if (resultsPage) {
    const API_BASE = "http://127.0.0.1:8000/api/v1"; // change to your backend URL

    const STATUS = {
      supported: "Supported",
      partially_supported: "Partially Supported",
      unsupported: "Unsupported",
      contradictory: "Contradictory",
      potentially_outdated: "Potentially Outdated",
    };

    // Sample data, used when the URL has no ?doc=ID (e.g. results.html)
    const MOCK = {
      document: { id: "demo", title: "Sample Paper", language: "en", pages: 12 },
      scores: { claim_verification: 72, originality: 85 },
      claims: [
        { id: 1, text: "The drug reduced mortality by 40%.", page: 4, section: "Results",
          status: "partially_supported", confidence: 0.82,
          explanation: "The cited study reports 34%, not 40%.",
          evidence: { text: "Mortality fell by 34% in the treatment group.", translated_text: null,
            source_title: "Cited study", doi: "10.1000/xyz", url: "https://doi.org/10.1000/xyz", page: 7 },
          checks: [{ name: "Numerical", result: "fail" }, { name: "Population", result: "pass" }] },
        { id: 2, text: "Treatment is safe for all age groups.", page: 6, section: "Discussion",
          status: "contradictory", confidence: 0.9,
          explanation: "The source excludes patients under 18.",
          evidence: { text: "Participants were aged 18 to 65.", translated_text: null,
            source_title: "Cited study", doi: null, url: null, page: 3 },
          checks: [{ name: "Overgeneralisation", result: "fail" }] },
        { id: 3, text: "Sleep improves memory consolidation.", page: 2, section: "Introduction",
          status: "supported", confidence: 0.95, explanation: "Matches the source findings.",
          evidence: null, checks: [] },
      ],
    };

    // Escape text, since claims come from uploaded papers
    const esc = (s) =>
      String(s ?? "").replace(/[&<>"']/g, (c) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

    const loadingEl = document.getElementById("rs-loading");
    const errorEl = document.getElementById("rs-error");
    const contentEl = document.getElementById("rs-content");
    const claimsEl = document.getElementById("rs-claims");

    const renderClaim = (c) => {
      const ev = c.evidence;
      const evidenceHtml = ev
        ? `<h4>Evidence</h4>
           <div class="rs-evidence">${esc(ev.text)}</div>
           ${ev.translated_text ? `<div class="rs-evidence"><em>Translated:</em> ${esc(ev.translated_text)}</div>` : ""}
           <p class="rs-muted">${esc(ev.source_title)}${ev.page ? `, p. ${esc(ev.page)}` : ""}
           ${ev.url ? ` · <a href="${esc(ev.url)}" target="_blank" rel="noopener">Source</a>` : ""}
           ${ev.doi ? ` · DOI: ${esc(ev.doi)}` : ""}</p>`
        : `<h4>Evidence</h4><p class="rs-muted">No evidence retrieved.</p>`;
      const checksHtml = (c.checks || []).length
        ? `<h4>Checks</h4><div class="rs-checks">${c.checks
            .map((k) => `<span class="rs-chip ck-${esc(k.result)}">${esc(k.name)}: ${esc(k.result)}</span>`).join("")}</div>`
        : "";
      return `<details class="rs-claim" data-status="${esc(c.status)}">
        <summary>
          <div class="rs-claim-head">
            <span class="rs-chip st-${esc(c.status)}">${esc(STATUS[c.status] || c.status)}</span>
            <span class="rs-muted">${esc(c.section || "")}${c.page ? ` · p. ${esc(c.page)}` : ""}${c.confidence != null ? ` · ${Math.round(c.confidence * 100)}% confidence` : ""}</span>
          </div>
          <span>${esc(c.text)}</span>
        </summary>
        <div class="rs-claim-body">
          <h4>Why</h4><p>${esc(c.explanation)}</p>
          ${evidenceHtml}${checksHtml}
        </div></details>`;
    };

    const render = (r) => {
      document.getElementById("rs-title").textContent = r.document.title;
      document.getElementById("rs-meta").textContent =
        `${r.document.pages} pages · language: ${r.document.language} · ${r.claims.length} claims checked`;

      const setScore = (textId, barId, v) => {
        document.getElementById(textId).textContent = `${v}%`;
        requestAnimationFrame(() => (document.getElementById(barId).style.width = `${v}%`));
      };
      setScore("rs-score-claims", "rs-bar-claims", r.scores.claim_verification);
      setScore("rs-score-orig", "rs-bar-orig", r.scores.originality);

      const counts = {};
      r.claims.forEach((c) => (counts[c.status] = (counts[c.status] || 0) + 1));
      document.getElementById("rs-summary").innerHTML = Object.keys(STATUS)
        .map((k) => `<span class="rs-chip st-${k}">${STATUS[k]}: ${counts[k] || 0}</span>`).join("");

      const filtersEl = document.getElementById("rs-filters");
      filtersEl.innerHTML =
        `<button class="rs-filter active" data-filter="all">All</button>` +
        Object.keys(STATUS).map((k) => `<button class="rs-filter" data-filter="${k}">${STATUS[k]}</button>`).join("");
      filtersEl.addEventListener("click", (e) => {
        const btn = e.target.closest(".rs-filter");
        if (!btn) return;
        filtersEl.querySelectorAll(".rs-filter").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        claimsEl.querySelectorAll(".rs-claim").forEach((el) => {
          el.hidden = btn.dataset.filter !== "all" && el.dataset.status !== btn.dataset.filter;
        });
      });

      claimsEl.innerHTML = r.claims.map(renderClaim).join("");
      loadingEl.hidden = true;
      contentEl.hidden = false;
    };

    const docId = new URLSearchParams(location.search).get("doc");
    if (!docId) {
      render(MOCK);
    } else {
      fetch(`${API_BASE}/documents/${encodeURIComponent(docId)}/report`)
        .then((res) => { if (!res.ok) throw new Error(`Server returned ${res.status}`); return res.json(); })
        .then(render)
        .catch((err) => {
          loadingEl.hidden = true;
          errorEl.hidden = false;
          errorEl.textContent = `Could not load the report: ${err.message}`;
        });
    }
  }
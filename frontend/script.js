const BACKEND_BASE = "https://site-verify-ynqy.onrender.com";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

document.addEventListener("DOMContentLoaded", () => {
  const quoteBtn = document.getElementById("get-quote");
  if (quoteBtn) {
    quoteBtn.addEventListener("click", () => {
      window.location.href = "upload.html";
    });
  }

  const contactBtn = document.getElementById("contact-btn");
  const contactSection = document.getElementById("contact");
  if (contactBtn && contactSection) {
    contactBtn.addEventListener("click", () => {
      contactSection.scrollIntoView({ behavior: "smooth" });
    });
  }

  const aboutLink = document.getElementById("about-link");
  const howItWorks = document.getElementById("featured-3");
  if (aboutLink && howItWorks) {
    aboutLink.addEventListener("click", (e) => {
      e.preventDefault();
      howItWorks.scrollIntoView({ behavior: "smooth" });
    });
  }

  const carouselEl = document.getElementById("carouselExampleIndicators");
  if (carouselEl && typeof bootstrap !== "undefined") {
    new bootstrap.Carousel(carouselEl, {
      interval: 4000,
      ride: "carousel",
      pause: "hover",
    });
  }

  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- UPLOAD PAGE ---------- */
  const uploadButton = document.getElementById("upload-button");
  const uploadBox = document.querySelector(".container");
  const errorEl = document.getElementById("error");
  const previewEl = document.getElementById("image-display");

  if (uploadButton && uploadBox && errorEl && previewEl) {
    const uploadFile = async (file) => {
      if (!file) return;
      const lowerName = file.name.toLowerCase();
      const allowedExt =
        lowerName.endsWith(".pdf") ||
        lowerName.endsWith(".json") ||
        lowerName.endsWith(".csv");
      const allowedMime = [
        "application/pdf",
        "application/json",
        "text/json",
        "text/csv",
        "application/csv",
        "text/plain",
      ].includes(file.type);

      if (!allowedExt && !allowedMime) {
        errorEl.innerText =
          "Please choose a PDF (.pdf), JSON (.json), or CSV (.csv) file so we can check its claims and references.";
        return;
      }

      errorEl.innerText = "";
      previewEl.innerHTML = `<p class="rs-status-msg">Uploading <strong>${esc(file.name)}</strong> and checking claims and references…</p>`;

      try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${BACKEND_BASE}/upload`, {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || `Upload failed (${res.status})`);
        }

        localStorage.setItem("citeverify_doc_id", data.document_id);
        localStorage.setItem("citeverify_payload", JSON.stringify(data));
        window.location.href = `results.html?doc=${encodeURIComponent(data.document_id)}`;
      } catch (err) {
        previewEl.innerHTML = "";
        errorEl.innerText = `Could not process file: ${err.message}`;
      }
    };

    uploadButton.addEventListener("change", () => {
      if (uploadButton.files && uploadButton.files[0]) {
        uploadFile(uploadButton.files[0]);
      }
    });

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
      const files = e.dataTransfer.files;
      if (files && files[0]) {
        uploadFile(files[0]);
      }
    });
  }

  /* ---------- RESULTS PAGE ---------- */
  const resultsPage = document.getElementById("results-page");
  if (resultsPage) {
    const STATUS = {
      supported: "Supported",
      partially_supported: "Partially Supported",
      unsupported: "Unsupported",
      contradictory: "Contradictory",
      potentially_outdated: "Potentially Outdated",
      unverified: "Unverified",
    };

    const DEFAULT_REASONS = {
      supported: "The statement aligns with the matched reference or source evidence found.",
      partially_supported: "Part of the statement matches available evidence, but some details are incomplete or only partly covered.",
      unsupported: "No supporting evidence was found in the matched references for this statement.",
      contradictory: "The statement conflicts with details found in the reference or evidence.",
      potentially_outdated: "The cited source is older and newer findings or context may apply.",
      unverified: "No linked reference or external record could be matched to verify this statement automatically.",
    };

    const cleanText = (s) =>
      String(s ?? "")
        .replace(/([A-Za-z]{2,})-\s+([a-z]{2,})/g, "$1$2")
        .replace(/\s+/g, " ")
        .trim();

    const prettyKey = (key) =>
      key
        .replace(/_/g, " ")
        .replace(/\b\w/g, (m) => m.toUpperCase())
        .replace(/\bDoi\b/g, "DOI");

    const loadingEl = document.getElementById("rs-loading");
    const resultsErrorEl = document.getElementById("rs-error");
    const contentEl = document.getElementById("rs-content");
    const claimsEl = document.getElementById("rs-claims");
    const citationsEl = document.getElementById("rs-citations");
    const integrityEl = document.getElementById("rs-integrity");

    const formatCitationSummary = (cit, fallbackList = []) => {
      if (cit) {
        const title = cleanText(cit.title || cit.source_title || "");
        const rawRef = cleanText(cit.raw_reference || cit.snippet || cit.text || "");
        const year = cit.year ? ` (${esc(cit.year)})` : "";
        const doi = cit.doi ? ` · DOI: ${esc(cit.doi)}` : "";
        const link = cit.url || cit.open_access_url || cit.source_url;
        const linkHtml = link
          ? ` · <a href="${esc(link)}" target="_blank" rel="noopener">Open source</a>`
          : "";

        if (title && rawRef && rawRef !== title) {
          return `<div><strong>${esc(title)}</strong>${year}${doi}${linkHtml}</div><div class="rs-muted">${esc(rawRef)}</div>`;
        }
        return `<div>${esc(title || rawRef)}${year}${doi}${linkHtml}</div>`;
      }

      if (fallbackList.length > 0) {
        const top = fallbackList[0];
        const refText = cleanText(top.raw_reference || top.title || "Reference entry");
        return `<div><span class="rs-muted">Closest document reference:</span> ${esc(refText)}</div><div class="rs-muted">Not directly matched to a verified claim snippet.</div>`;
      }

      return `<div class="rs-muted">No original citation or matched reference was linked to this claim.</div>`;
    };

    const buildReasonText = (c) => {
      const parts = [];
      const baseReason = cleanText(c.explanation || c.reason || "") || DEFAULT_REASONS[c.status] || DEFAULT_REASONS.unverified;
      parts.push(baseReason);

      if (c.discrepancies && typeof c.discrepancies === "object") {
        const notes = [];
        if (c.discrepancies.contradiction_signal) {
          notes.push("A conflict or contradiction signal was detected against the source text.");
        }
        if (c.discrepancies.potentially_outdated) {
          notes.push("The referenced work may be outdated relative to newer research.");
        }
        if (Array.isArray(c.discrepancies.issues) && c.discrepancies.issues.length) {
          notes.push(c.discrepancies.issues.map(cleanText).join("; "));
        }
        if (notes.length) {
          parts.push(notes.join(" "));
        }
      }

      return parts.join(" ");
    };

    const normalizeReport = (raw) => {
      const scoresObj = raw.scores || {};
      const integrityObj = raw.integrity || {};
      const claimsArr = Array.isArray(raw.claims) ? raw.claims : [];
      const citationsArr = Array.isArray(raw.citations) ? raw.citations : [];

      return {
        document: {
          id: raw.document_id || "unknown",
          title: cleanText(raw.filename || raw.document_id || "Document Report"),
          language: raw.language || "en",
          pages: raw.total_pages ?? 0,
        },
        scores: {
          claim_verification:
            scoresObj.claim_verification_score ??
            scoresObj.claim_verification ??
            scoresObj.overall_score ??
            0,
          originality:
            integrityObj.originality_score ??
            scoresObj.originality_score ??
            scoresObj.originality ??
            0,
        },
        integrity: integrityObj,
        claims: claimsArr.map((c, idx) => {
          const matched = Array.isArray(c.matched_citations) ? c.matched_citations : [];
          return {
            id: c.claim_id || c.id || idx + 1,
            text: cleanText(c.claim_text || c.text || ""),
            page: c.page ?? null,
            section: cleanText(c.section || ""),
            status: c.verification_status || c.status || "unverified",
            explanation: c.explanation || c.reason || "",
            discrepancies: c.discrepancies || null,
            evidence: matched[0] || null,
          };
        }),
        citations: citationsArr,
      };
    };

    const renderClaim = (c, index, allCitations) => {
      const labelText = STATUS[c.status] || "Unverified";
      const reasonText = buildReasonText(c);
      const citationHtml = formatCitationSummary(c.evidence, allCitations);
      const locationBits = [
        c.section ? `Section: ${c.section}` : "",
        c.page ? `Page ${c.page}` : "",
      ]
        .filter(Boolean)
        .join(" · ");

      return `
        <article class="rs-claim-card" data-status="${esc(c.status)}">
          <div class="rs-claim-top">
            <span class="rs-chip st-${esc(c.status)}">${esc(labelText)}</span>
            <span class="rs-muted">${esc(locationBits || `Claim #${index + 1}`)}</span>
          </div>

          <p class="rs-claim-statement">${esc(c.text)}</p>

          <div class="rs-detail-grid">
            <div class="rs-detail-block">
              <div class="rs-detail-title">Why it has this label</div>
              <p class="rs-detail-body">${esc(reasonText)}</p>
            </div>
            <div class="rs-detail-block" tabindex="0">
              <div class="rs-detail-title">Original citation</div>
              <div class="rs-detail-body">${citationHtml}</div>
            </div>
          </div>
        </article>
      `;
    };

    const renderIntegrity = (integrityObj, scoresObj) => {
      if (!integrityEl) return;
      const entries = [];
      if (integrityObj && typeof integrityObj === "object") {
        Object.entries(integrityObj).forEach(([key, val]) => {
          if (val === null || val === undefined || typeof val === "object") return;
          const niceKey = prettyKey(key);
          const niceVal = typeof val === "boolean" ? (val ? "Yes" : "No") : cleanText(String(val));
          const isNote = /note/i.test(key);
          entries.push(`<div class="rs-info-pill${isNote ? " rs-note" : ""}"><span>${esc(niceKey)}</span><strong>${esc(niceVal)}</strong></div>`);
        });
      }
      if (scoresObj && typeof scoresObj === "object") {
        Object.entries(scoresObj).forEach(([key, val]) => {
          if (val === null || val === undefined || typeof val === "object") return;
          entries.push(`<div class="rs-info-pill"><span>${esc(prettyKey(key))}</span><strong>${esc(String(val))}</strong></div>`);
        });
      }
      integrityEl.innerHTML = entries.length
        ? entries.join("")
        : `<p class="rs-muted">No extra integrity flags were reported for this document.</p>`;
    };

    const renderCitations = (citations) => {
      if (!citationsEl) return;
      if (!citations.length) {
        citationsEl.innerHTML = `<p class="rs-muted">No references were extracted from this document.</p>`;
        return;
      }

      citationsEl.innerHTML = citations
        .map((cit, i) => {
          const title = cleanText(cit.title || "");
          const rawRef = cleanText(cit.raw_reference || "Reference entry");
          const year = cit.year ? `Year: ${esc(cit.year)}` : "";
          const doi = cit.doi ? `DOI: ${esc(cit.doi)}` : "";
          const meta = [year, doi].filter(Boolean).join(" · ");
          return `
            <div class="rs-citation-item">
              <div class="rs-citation-index">#${i + 1}</div>
              <div class="rs-citation-content">
                ${title ? `<div class="rs-citation-title">${esc(title)}</div>` : ""}
                <div class="rs-citation-ref">${esc(rawRef)}</div>
                ${meta ? `<div class="rs-muted">${meta}</div>` : ""}
              </div>
            </div>
          `;
        })
        .join("");
    };

    const render = (raw) => {
      const r = normalizeReport(raw);
      document.getElementById("rs-title").textContent = r.document.title;
      document.getElementById("rs-meta").textContent =
        `${r.document.pages} pages · Language: ${r.document.language} · ${r.claims.length} claims checked · ${r.citations.length} references found`;

      const counts = {};
      r.claims.forEach((c) => {
        counts[c.status] = (counts[c.status] || 0) + 1;
      });

      const overviewEl = document.getElementById("rs-plain-overview");
      if (overviewEl) {
        const supportedCount = counts.supported || 0;
        const problemCount =
          (counts.unsupported || 0) +
          (counts.contradictory || 0) +
          (counts.potentially_outdated || 0);
        overviewEl.textContent =
          `Out of ${r.claims.length} claims checked, ${supportedCount} are supported, ` +
          `${counts.partially_supported || 0} are partially supported, ` +
          `${counts.unverified || 0} could not be matched automatically, and ${problemCount} show potential issues or contradictions.`;
      }

      const setScore = (textId, barId, v) => {
        const num = Number(v) || 0;
        const pct = num <= 1 ? Math.round(num * 100) : Math.min(100, Math.round(num));
        document.getElementById(textId).textContent = `${pct}%`;
        requestAnimationFrame(() => {
          document.getElementById(barId).style.width = `${pct}%`;
        });
      };

      setScore("rs-score-claims", "rs-bar-claims", r.scores.claim_verification);
      setScore("rs-score-orig", "rs-bar-orig", r.scores.originality);

      renderIntegrity(r.integrity, raw.scores);

      document.getElementById("rs-summary").innerHTML = Object.keys(STATUS)
        .map((k) => `<span class="rs-chip st-${k}">${STATUS[k]}: ${counts[k] || 0}</span>`)
        .join("");

      const filtersEl = document.getElementById("rs-filters");
      filtersEl.innerHTML =
        `<button class="rs-filter active" data-filter="all">All (${r.claims.length})</button>` +
        Object.keys(STATUS)
          .map((k) => `<button class="rs-filter" data-filter="${k}">${STATUS[k]} (${counts[k] || 0})</button>`)
          .join("");

      filtersEl.onclick = (e) => {
        const btn = e.target.closest(".rs-filter");
        if (!btn) return;
        filtersEl.querySelectorAll(".rs-filter").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        claimsEl.querySelectorAll(".rs-claim-card").forEach((el) => {
          el.hidden = btn.dataset.filter !== "all" && el.dataset.status !== btn.dataset.filter;
        });
      };

      claimsEl.innerHTML = r.claims.length
        ? r.claims.map((c, idx) => renderClaim(c, idx, r.citations)).join("")
        : `<p class="rs-muted">No claims were extracted from this document.</p>`;

      renderCitations(r.citations);

      loadingEl.hidden = true;
      resultsErrorEl.hidden = true;
      contentEl.hidden = false;
    };

    const params = new URLSearchParams(location.search);
    const docId = params.get("doc") || localStorage.getItem("citeverify_doc_id");
    const cached = localStorage.getItem("citeverify_payload");

    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (!docId || parsed.document_id === docId) {
          render(parsed);
        }
      } catch {}
    }

    if (docId) {
      fetch(`${BACKEND_BASE}/report/${encodeURIComponent(docId)}`)
        .then((res) => {
          if (!res.ok) throw new Error(`Server returned ${res.status}`);
          return res.json();
        })
        .then((reportData) => {
          localStorage.setItem("citeverify_doc_id", docId);
          render(reportData);
        })
        .catch((err) => {
          if (!cached) {
            loadingEl.hidden = true;
            resultsErrorEl.hidden = false;
            resultsErrorEl.textContent = `Could not load the report: ${err.message}`;
          }
        });
    } else if (!cached) {
      loadingEl.hidden = true;
      resultsErrorEl.hidden = false;
      resultsErrorEl.textContent = "No document found. Please upload a PDF, JSON, or CSV file first.";
    }

    const assistantForm = document.getElementById("rs-assistant-form");
    if (assistantForm) {
      assistantForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const qInput = document.getElementById("rs-assistant-input");
        const ansEl = document.getElementById("rs-assistant-answer");
        const question = qInput.value.trim();
        if (!question) return;

        ansEl.innerHTML = `<p class="rs-muted">Checking your document for an answer…</p>`;
        try {
          const activeDocId =
            new URLSearchParams(location.search).get("doc") ||
            localStorage.getItem("citeverify_doc_id");
          const res = await fetch(`${BACKEND_BASE}/assistant`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, document_id: activeDocId || null }),
          });
          const body = await res.json();
          if (!res.ok) throw new Error(body.detail || `Assistant error (${res.status})`);

          if (typeof body === "string") {
            ansEl.innerHTML = `<p>${esc(cleanText(body))}</p>`;
          } else {
            const answerText = cleanText(body.answer || "No answer returned.");
            const items = Array.isArray(body.grounded_items) ? body.grounded_items : [];
            const itemsHtml = items.length
              ? `<div class="rs-grounded-list"><div class="rs-detail-title">Related items from this document</div>${items
                  .map((it) => {
                    const st = STATUS[it.verification_status] || it.verification_status || "Note";
                    return `<div class="rs-grounded-item"><span class="rs-chip st-${esc(it.verification_status || "unverified")}">${esc(st)}</span><span>${esc(cleanText(it.claim_text || ""))}</span></div>`;
                  })
                  .join("")}</div>`
              : "";
            ansEl.innerHTML = `<p class="rs-assistant-text">${esc(answerText)}</p>${itemsHtml}`;
          }
        } catch (err) {
          ansEl.innerHTML = `<p class="rs-error">Could not get an answer: ${esc(err.message)}</p>`;
        }
      });
    }
  }
});

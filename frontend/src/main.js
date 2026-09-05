const root = document.getElementById("root");

root.innerHTML = `
  <div class="app-shell">

    <header class="topbar">
      <div>
        <div class="brand">Retail Copilot</div>
        <div class="subtitle">Sales & Inventory Intelligence</div>
      </div>

      <div class="status">
        <span class="status-dot"></span>
        Data connected
      </div>
    </header>

    <main class="dashboard">

      <section class="hero">
        <div>
          <span class="eyebrow">MANAGER ASSISTANT</span>
          <h1>Know what needs attention.</h1>
          <p>
            Ask a question about sales or inventory and get a grounded answer
            backed by your retail data.
          </p>
        </div>
      </section>

      <section class="kpi-grid">

        <div class="kpi-card">
          <div class="kpi-label">Stock-out risks</div>
          <div class="kpi-value" id="stockoutKpi">--</div>
          <div class="kpi-note">Items needing attention</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-label">Overstocked</div>
          <div class="kpi-value" id="overstockKpi">--</div>
          <div class="kpi-note">Excess inventory items</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-label">Non-moving</div>
          <div class="kpi-value" id="nonMovingKpi">--</div>
          <div class="kpi-note">No sales in 30 days</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-label">Sales signals</div>
          <div class="kpi-value" id="salesSignalsKpi">--</div>
          <div class="kpi-note">Spikes and drops detected</div>
        </div>

      </section>

      <section class="copilot-card">

        <div class="section-heading">
          <div>
            <span class="eyebrow">ASK THE COPILOT</span>
            <h2>What would you like to know?</h2>
          </div>
        </div>

        <div class="question-box">
          <input
            id="questionInput"
            type="text"
            placeholder="e.g. Which products are running out?"
          />
          <button id="askButton">Ask Copilot</button>
        </div>

        <div class="quick-actions">

          <button data-question="Which products are running out?">
            Stock-out risks
          </button>

          <button data-question="Which products are overstocked?">
            Overstock
          </button>

          <button data-question="Which products are not moving?">
            Non-moving stock
          </button>

          <button data-question="Which products had a sales spike?">
            Sales spikes
          </button>

          <button data-question="Which products had a sales drop?">
            Sales drops
          </button>

          <button data-question="How is Wheat Flour 5kg performing?">
            Product performance
          </button>

        </div>

      </section>

      <section class="answer-card" id="answerCard">

        <div class="answer-header">
          <div>
            <span class="eyebrow">COPILOT RESPONSE</span>
            <h2>Ready when you are</h2>
          </div>

          <span class="grounded-badge">
            Grounded in retail data
          </span>
        </div>

        <div id="answerContent" class="answer-content">
          <p class="empty-state">
            Ask a question above to see the analysis, evidence,
            and recommended action.
          </p>
        </div>

      </section>

      <section class="signals-section">

        <div class="section-heading">
          <div>
            <span class="eyebrow">ATTENTION AREAS</span>
            <h2>Inventory signals</h2>
          </div>
        </div>

        <div class="signal-grid">

          <div class="signal-card danger">
            <div class="signal-icon">!</div>
            <div>
              <h3>Critical stock</h3>
              <p id="criticalStockText">
                Loading inventory signals...
              </p>
            </div>
          </div>

          <div class="signal-card warning">
            <div class="signal-icon">?</div>
            <div>
              <h3>Excess inventory</h3>
              <p id="excessInventoryText">
                Loading inventory signals...
              </p>
            </div>
          </div>

          <div class="signal-card neutral">
            <div class="signal-icon">-</div>
            <div>
              <h3>Non-moving stock</h3>
              <p id="nonMovingText">
                Loading inventory signals...
              </p>
            </div>
          </div>

        </div>

      </section>

      <footer>
        <span>Retail Sales & Inventory Copilot</span>
        <span>Deterministic analytics + Gemini explanation</span>
      </footer>

    </main>

  </div>
`;

const input = document.getElementById("questionInput");
const askButton = document.getElementById("askButton");
const answerContent = document.getElementById("answerContent");

const stockoutKpi = document.getElementById("stockoutKpi");
const overstockKpi = document.getElementById("overstockKpi");
const nonMovingKpi = document.getElementById("nonMovingKpi");
const salesSignalsKpi = document.getElementById("salesSignalsKpi");

const criticalStockText =
  document.getElementById("criticalStockText");

const excessInventoryText =
  document.getElementById("excessInventoryText");

const nonMovingText =
  document.getElementById("nonMovingText");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatAnswer(text) {
  const safeText = escapeHtml(text);

  return safeText
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function showQuestion(question) {
  input.value = question;
  input.focus();
}

async function loadDashboard() {
  try {
    const response = await fetch("/api/dashboard");

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.error || "Unable to load dashboard."
      );
    }

    stockoutKpi.textContent = data.stockout_risks;
    overstockKpi.textContent = data.overstocked;
    nonMovingKpi.textContent = data.non_moving;
    salesSignalsKpi.textContent = data.sales_signals;

    criticalStockText.textContent =
      `${data.stockout_risks} items need stock attention.`;

    excessInventoryText.textContent =
      `${data.overstocked} product-store combinations are overstocked.`;

    nonMovingText.textContent =
      `${data.non_moving} items have positive stock with no recent sales.`;

  } catch (error) {
    console.error("Dashboard loading error:", error);

    stockoutKpi.textContent = "--";
    overstockKpi.textContent = "--";
    nonMovingKpi.textContent = "--";
    salesSignalsKpi.textContent = "--";

    criticalStockText.textContent =
      "Unable to load inventory signals.";

    excessInventoryText.textContent =
      "Unable to load inventory signals.";

    nonMovingText.textContent =
      "Unable to load inventory signals.";
  }
}

async function askCopilot() {
  const question = input.value.trim();

  if (!question) {
    answerContent.innerHTML =
      '<p class="empty-state">Please enter a question first.</p>';
    return;
  }

  askButton.disabled = true;
  askButton.textContent = "Analyzing...";

  answerContent.innerHTML = `
    <div class="loading-state">
      <div class="loading-title">Analyzing your question...</div>
      <div class="loading-text">
        Checking deterministic retail analytics and generating a grounded explanation.
      </div>
    </div>
  `;

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        question: question
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.error || "The request failed."
      );
    }

    const answer = data.answer || "";
    const evidencePackage = data.evidence || {};

    /*
     * Evidence can be:
     *
     * 1. A normal array for most intents.
     *
     * 2. A grouped object for GENERAL_INVENTORY:
     *    {
     *      stockout_risks: [...],
     *      overstock_items: [...],
     *      non_moving_items: [...]
     *    }
     *
     * Convert both formats into one list so the UI
     * can render supporting records consistently.
     */
    const rawEvidence = evidencePackage.evidence;

    let evidenceItems = [];

    if (Array.isArray(rawEvidence)) {
      evidenceItems = rawEvidence;
    } else if (
      rawEvidence &&
      typeof rawEvidence === "object"
    ) {
      Object.entries(rawEvidence).forEach(
        ([category, records]) => {
          if (Array.isArray(records)) {
            records.forEach((record) => {
              evidenceItems.push({
                ...record,
                evidence_category: category
              });
            });
          }
        }
      );
    }

    const calculationRule =
      evidencePackage.calculation_rule ||
      "Not available.";

    const recommendationBasis =
      evidencePackage.recommendation_basis ||
      "Not available.";

    const assumptions =
      Array.isArray(evidencePackage.assumptions)
        ? evidencePackage.assumptions
        : [];

    const evidenceHtml = evidenceItems.length
      ? evidenceItems
          .slice(0, 8)
          .map((item) => {
            const product = escapeHtml(
              item.product_name || "Unknown product"
            );

            const store = escapeHtml(
              item.store_name || "Unknown store"
            );

            const stock =
              item.closing_stock !== undefined
                ? `Stock: ${escapeHtml(item.closing_stock)}`
                : "";

            const reorder =
              item.reorder_level !== undefined
                ? `Reorder: ${escapeHtml(item.reorder_level)}`
                : "";

            const days =
              item.days_of_stock !== undefined
                ? `Days: ${escapeHtml(item.days_of_stock)}`
                : "";

            const risk =
              item.risk_level
                ? `Risk: ${escapeHtml(item.risk_level)}`
                : "";

            let categoryLabel = "";

            if (item.evidence_category) {
              const categoryNames = {
                stockout_risks: "Stock-out risk",
                overstock_items: "Overstock",
                non_moving_items: "Non-moving"
              };

              categoryLabel =
                categoryNames[item.evidence_category] ||
                item.evidence_category;
            }

            return `
              <div class="evidence-item">

                <div class="evidence-item-title">
                  ${product}
                </div>

                <div class="evidence-item-store">
                  ${store}
                </div>

                ${
                  categoryLabel
                    ? `
                      <div class="evidence-item-store">
                        ${escapeHtml(categoryLabel)}
                      </div>
                    `
                    : ""
                }

                <div class="evidence-item-metrics">
                  ${stock ? `<span>${stock}</span>` : ""}
                  ${reorder ? `<span>${reorder}</span>` : ""}
                  ${days ? `<span>${days}</span>` : ""}
                  ${risk ? `<span>${risk}</span>` : ""}
                </div>

              </div>
            `;
          })
          .join("")
      : `
        <div class="evidence-empty">
          No supporting records were returned for this question.
        </div>
      `;

    const assumptionsHtml = assumptions.length
      ? `
        <ul class="assumptions-list">
          ${assumptions
            .map(
              (item) =>
                `<li>${escapeHtml(item)}</li>`
            )
            .join("")}
        </ul>
      `
      : `
        <p class="detail-text">
          No additional assumptions provided.
        </p>
      `;

    answerContent.innerHTML = `
      <div class="copilot-answer">

        <div class="question-label">
          Manager question
        </div>

        <div class="question-text">
          ${escapeHtml(question)}
        </div>

        <div class="answer-divider"></div>

        <div class="response-section">

          <div class="response-section-label">
            Answer
          </div>

          <div class="answer-text">
            ${formatAnswer(answer)}
          </div>

        </div>

        <div class="response-section">

          <div class="response-section-label">
            Key evidence
          </div>

          <div class="evidence-list">
            ${evidenceHtml}
          </div>

        </div>

        <div class="response-section">

          <div class="response-section-label">
            Recommended action basis
          </div>

          <div class="detail-text">
            ${escapeHtml(recommendationBasis)}
          </div>

        </div>

        <div class="response-section">

          <div class="response-section-label">
            Calculation
          </div>

          <div class="detail-text">
            ${escapeHtml(calculationRule)}
          </div>

        </div>

        <div class="response-section">

          <div class="response-section-label">
            Assumptions
          </div>

          ${assumptionsHtml}

        </div>

      </div>
    `;

    document.getElementById("answerCard").scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

  } catch (error) {
    answerContent.innerHTML = `
      <div class="error-state">
        <strong>Unable to process the question.</strong>
        <p>${escapeHtml(error.message)}</p>
      </div>
    `;
  } finally {
    askButton.disabled = false;
    askButton.textContent = "Ask Copilot";
  }
}

document
  .querySelectorAll("[data-question]")
  .forEach((button) => {
    button.addEventListener("click", () => {
      showQuestion(button.dataset.question);
    });
  });

askButton.addEventListener(
  "click",
  askCopilot
);

input.addEventListener(
  "keydown",
  (event) => {
    if (event.key === "Enter") {
      askCopilot();
    }
  }
);

loadDashboard();
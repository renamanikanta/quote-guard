# QuoteGuard — Quote-to-Cash Revenue Assurance

A medium-to-hard end-to-end commercial analytics portfolio app for **Manikanta Rena**, separate from Revenue Lens.

## Business problem
Revenue organizations may lose money through invoice/contract mismatches, discounts beyond approval policy, and overdue receivables. Disconnected spreadsheets leave analysts without a reproducible way to triage exceptions or estimate recovery priorities.

## Solution
1. Validate invoice-level contract, billing, discount, and payment data.
2. Calculate auditable billing-gap and collections signals.
3. Prioritize accounts using a transparent heuristic score and an action queue.
4. Slice exposure by customer segment and risk tier.
5. Run sensitivity tests on recovery assumptions and export action-ready exceptions.

**Important:** All default data is synthetic. Outputs are hypothetical and not proven fraud, confirmed underbilling, cash flow projections, or validated risk probabilities. Policy-approved discounts and complex contractual entitlements require business review. Billing gaps and collection exposures are separate but could still pertain to the same invoice; recovery assumptions must account for real-world dependencies.

## Run locally
```bash
python -m pip install -r requirements.txt
streamlit run app.py
pytest -q
```

## Deploy on Render
1. Push the project files to a new GitHub repository.
2. On Render, choose **New → Blueprint** and connect the GitHub repository.
3. Render detects `render.yaml` and creates the web service.
4. Wait for deployment and check `/_stcore/health` on your actual Render URL.
5. Update your resume/LinkedIn only after checking the live app.

Note: Render free tier availability and service settings can change. The repository does not deploy itself. No service URL can be guaranteed without an actual deployment.

## CSV contract
Required: `invoice_id, customer, segment, invoice_date, due_date, contract_mrr, billed_mrr, discount_pct, approved_discount_pct, payment_date, status`.
Dates: ISO-8601; discount proportions 0–1; status: Paid / Unpaid.

## Tech
Python, Pandas, NumPy, Plotly, Streamlit, Pytest, Render Blueprint. Cleanly separated analytics engine and UI.

## Future production improvements
SQL warehouse ingestion, role-based access, contract-line reconciliation, audit trails, historical recovery calibration, currency/FX handling, credit notes, and deduplication across billing periods.

# Digital Forensic Timeline Analysis — Implementation Tasks

## Project Goal

Build a reliable, interactive digital forensics tool that validates timestamps, identifies potential temporal inconsistencies, and helps investigators reconstruct events chronologically.

**Current status:** Streamlit dashboard runs successfully. Review highlighting and chronological visualization are under development.

---

## Phase 1: Core Functionality

### Task 1: Improve Timestamp Validation
- [ ] Handle missing timestamps.
- [ ] Detect invalid timestamp formats.
- [ ] Detect unknown or unsupported timezones.
- [ ] Correctly process UTC offsets such as `+05:30` and `+00:00`.
- [ ] Convert valid timestamps to UTC.
- [ ] Preserve original timestamp values.
- [ ] Add clear validation messages for each failed record.
- [ ] Test timestamps with and without embedded timezone information.

**Expected result:** Every event has a clear timestamp status, and valid timestamps can be compared consistently.

### Task 2: Improve Temporal Conflict Detection
- [ ] Detect when an access event precedes the earliest recorded creation event for the same entity.
- [ ] Identify related events involved in an ordering conflict.
- [ ] Detect exact-match duplicate candidates.
- [ ] Avoid treating unusual hours alone as suspicious.
- [ ] Provide a reason for every flagged event.
- [ ] Avoid labeling potential inconsistencies as confirmed tampering.
- [ ] Handle missing `entity_key` values safely.

**Expected result:** The system flags potential issues and explains why each record needs review.

### Task 3: Improve Review Highlighting
- [ ] Highlight timestamp validation failures.
- [ ] Highlight primary ordering conflicts.
- [ ] Highlight related events separately.
- [ ] Highlight duplicate candidates.
- [ ] Add a review status column.
- [ ] Create a dedicated review queue.
- [ ] Add filters for review category and source type.
- [ ] Display the total number of records requiring review.

**Expected result:** Investigators can identify records requiring attention without manually examining every row.

### Task 4: Improve Chronological Timeline
- [ ] Sort valid events from earliest to latest.
- [ ] Display event IDs and descriptions clearly.
- [ ] Use colors to distinguish review categories.
- [ ] Make the timeline readable when many events exist.
- [ ] Add date and source-type filters.
- [ ] Keep events with invalid timestamps visible in a separate section.
- [ ] Display timestamps consistently in UTC.
- [ ] Add a chronological event table below the visualization.

**Expected result:** Users can reconstruct the event sequence and quickly identify inconsistencies.

---

## Phase 2: Testing and Reliability

### Task 5: Implement Automated Tests
- [ ] Create `tests/test_timestamp_validation.py`.
- [ ] Create `tests/test_temporal_analysis.py`.
- [ ] Test valid timestamps.
- [ ] Test invalid and missing timestamps.
- [ ] Test unknown timezones.
- [ ] Test creation/access ordering conflicts.
- [ ] Test duplicate-candidate detection.
- [ ] Test records with missing optional fields.
- [ ] Test empty datasets.
- [ ] Run the tests using `python -m pytest -q`.

**Expected result:** Changes to the application do not silently break existing functionality.

### Task 6: Evaluate Against Ground Truth
- [ ] Load `data/ground_truth.csv` in a separate evaluation script.
- [ ] Compare predicted flags with expected labels.
- [ ] Calculate precision, recall, and F1-score where the labels can be mapped reliably.
- [ ] Generate a confusion matrix.
- [ ] Investigate false positives and false negatives.
- [ ] Document limitations of the synthetic dataset.

**Important:** Ground-truth labels must only be used for evaluation, not to generate production predictions.

**Expected result:** The project's detection quality can be measured instead of judged only by visual inspection.

### Task 7: Improve Error Handling
- [ ] Handle missing input files.
- [ ] Handle malformed CSV files.
- [ ] Detect missing required columns.
- [ ] Handle empty uploads.
- [ ] Handle unexpected data types.
- [ ] Show clear error messages instead of Python tracebacks.
- [ ] Prevent invalid records from crashing the entire dashboard.

**Expected result:** The application remains usable when input data is incomplete or malformed.

---

## Phase 3: Useful Dashboard Features

### Task 8: Add Search and Filtering
- [ ] Search by event ID.
- [ ] Search by event description.
- [ ] Filter by source type.
- [ ] Filter by review status.
- [ ] Filter by date range.
- [ ] Filter by entity key.
- [ ] Add a reset-filters option.

**Expected result:** Users can investigate a subset of events quickly.

### Task 9: Add Event Details
- [ ] Display complete details when an event is selected.
- [ ] Show original and normalized timestamps.
- [ ] Show timezone information.
- [ ] Show validation status.
- [ ] Show temporal flags and explanations.
- [ ] Show related events for an ordering conflict.
- [ ] Clearly distinguish recorded facts from system-generated interpretations.

**Expected result:** Each flag is explainable and traceable to its underlying event records.

### Task 10: Add Summary Metrics
- [ ] Total events processed.
- [ ] Valid timestamps.
- [ ] Invalid timestamps.
- [ ] Missing timestamps.
- [ ] Unknown timezones.
- [ ] Potential ordering conflicts.
- [ ] Duplicate candidates.
- [ ] Total records requiring review.

**Expected result:** A quick overview of the dataset appears at the top of the dashboard.

---

## Phase 4: Forensic Reporting

### Task 11: Export Analysis Results
- [ ] Export processed events as CSV.
- [ ] Include UTC timestamps and validation statuses.
- [ ] Include review categories and reasons.
- [ ] Export the flagged-events report separately.
- [ ] Include the original timestamp values.
- [ ] Include the analysis date and tool version where appropriate.
- [ ] Ensure exports do not silently omit invalid records.

**Expected result:** Users can save and examine results outside the dashboard.

### Task 12: Generate an Investigation Report
- [ ] Create a report summary.
- [ ] Include dataset statistics.
- [ ] List potential ordering conflicts.
- [ ] List timestamp validation failures.
- [ ] Include a chronological event table.
- [ ] Explain detection rules and limitations.
- [ ] Clearly label synthetic data and unverified conclusions.
- [ ] Export the report as PDF.

**Expected result:** The tool produces a readable report for academic demonstrations and investigation review.

---

## Phase 5: Advanced Features

### Task 13: Improve Duplicate Analysis
- [ ] Distinguish exact-match duplicates from near-duplicate candidates.
- [ ] Compare source, entity, description, and timestamp.
- [ ] Allow a configurable time tolerance for near-duplicate analysis.
- [ ] Explain why two events were grouped together.
- [ ] Avoid automatically deleting or merging records.

**Expected result:** Repeated records can be reviewed without losing potentially meaningful evidence.

### Task 14: Add Evidence Traceability
- [ ] Assign a stable identifier to each imported record.
- [ ] Preserve the original imported data.
- [ ] Record which rules generated each flag.
- [ ] Record analysis configuration and tool version.
- [ ] Keep raw evidence separate from derived results.
- [ ] Document any transformations applied to timestamps.

**Expected result:** Analysis decisions can be explained and reproduced.

### Task 15: Prepare for FastAPI Integration
- [ ] Separate data processing from Streamlit UI code.
- [ ] Keep timestamp validation in a reusable module.
- [ ] Keep temporal analysis in a reusable module.
- [ ] Define input and output schemas before adding endpoints.
- [ ] Add API endpoints only when the interface is agreed upon.
- [ ] Test API behavior independently of the Streamlit interface.
- [ ] Avoid changing existing behavior without a clear requirement.

**Expected result:** The analysis logic can eventually be reused by a separate frontend or API.

---

## Phase 6: Documentation and Final Validation

### Task 16: Complete Documentation
- [ ] Update `README.md` with setup instructions.
- [ ] Explain the project architecture.
- [ ] Document CSV column requirements.
- [ ] Explain timestamp validation rules.
- [ ] Explain temporal conflict detection.
- [ ] Include screenshots of the dashboard.
- [ ] Document known limitations.
- [ ] Include test execution instructions.

### Task 17: Final System Validation
- [ ] Run the application from a clean terminal.
- [ ] Install dependencies from `requirements.txt`.
- [ ] Test the supplied sample dataset.
- [ ] Test a custom CSV upload.
- [ ] Test invalid and incomplete input.
- [ ] Run all automated tests.
- [ ] Verify that exports contain the expected fields.
- [ ] Confirm that the dashboard does not claim that potential flags prove wrongdoing.

---

## Recommended Implementation Order

1. Timestamp validation.
2. Temporal conflict detection.
3. Review highlighting.
4. Chronological timeline.
5. Automated tests.
6. Ground-truth evaluation.
7. Search and filtering.
8. Event details and summary metrics.
9. CSV and PDF reporting.
10. Evidence traceability.
11. FastAPI integration.
12. Documentation and final validation.

## Definition of Done

The initial version is ready when:

- [ ] The dashboard runs successfully.
- [ ] Timestamp validation works for valid, invalid, missing, and unknown-timezone cases.
- [ ] E016 is flagged as the primary potential ordering conflict in the supplied sample.
- [ ] E015 is shown as a related event when appropriate.
- [ ] Duplicate candidates are identified without being treated as confirmed duplicates.
- [ ] Events with valid timestamps are displayed chronologically.
- [ ] Invalid-timestamp records remain available for review.
- [ ] Automated tests pass.
- [ ] The application explains why events are flagged.
- [ ] The README explains how to install and run the project.

**Development principle:** Prioritize correctness, explainability, and preservation of original evidence before adding advanced features.

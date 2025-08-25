# Zotero to HTML Bibliography

This repository provides an **automated bridge between our reference management system (Zotero) and the TYPO3 backend** of the University of Tübingen.  

👉 **All references are managed centrally in [Zotero](https://www.zotero.org/groups/5693788/cqs/library).**  
[Zotero](https://zotero.org) is a free tool for collecting and organizing academic references. Within Zotero, we use a shared online group (“organization”) where all members of the *Center for Quantum Science (CQS)* can add, edit, and categorize publications.  
This ensures that references are stored in **one place only** and can be kept consistent.

This repository contains a script that:  
1. Fetches all references from the CQS Zotero group via the Zotero API.  
2. Converts them into **ready-to-use HTML code**.  
3. Produces a file (`bibliography.html`) that can be copied directly into TYPO3.  

A GitHub Action ensures that the file is always current:  
Every night at **03:00 (CET)** the script runs automatically and updates the bibliography.  

👉 You can always preview the most **recent bibliography [here](https://htmlpreview.github.io/?https://raw.githubusercontent.com/AG-Lesanovsky/2024-zotero-to-html/refs/heads/master/bibliography.html)**.

---

## Features

- Uses the **Zotero group library** [CQS Publications](https://www.zotero.org/groups/5693788/cqs/library) as the single source of truth.
- Supports **journal articles** and **preprints (arXiv)**.
- Produces clean, formatted **HTML bibliography code**.
- Groups entries into sections based on project tags (e.g. `QUSP FOR5413`, `Quantera Project CoQuaDis`).
- Keeps the bibliography updated **daily at 3am** via GitHub Actions.

---

## How References Are Managed (Zotero Workflow)

All references are **added and edited inside Zotero**, not in this repository.  
If you are part of the CQS Zotero group:

1. Log into the shared Zotero group: [Center for Quantum Science](https://www.zotero.org/groups/5693788/cqs/library).  
   - This is the central database where we keep all publications.  
   - Only group members can add or modify entries.
2. Add a new entry (`journal article` or `preprint`).
3. Enter all information in **plain Unicode text**  
   (🚫 no LaTeX, 🚫 no MathML).
4. Fill in bibliographic details (title, authors, journal, date, etc.).
5. Add project tags (`QUSP FOR5413`, `Quantera Project CoQuaDis`, etc.) to assign the publication to a category.
6. Save the entry.  

The repository will automatically update the HTML bibliography the next morning.  
**No manual editing of HTML is needed.**

---

## How to Copy the Bibliography into TYPO3

1. Open the [latest `bibliography.html`](https://htmlpreview.github.io/?https://raw.githubusercontent.com/AG-Lesanovsky/2024-zotero-to-html/refs/heads/master/bibliography.html).  
2. Copy the HTML section you need.  
3. Go to the TYPO3 backend of the university website.  
4. Paste the HTML where the bibliography should appear.  
5. Save. Done ✅  

---

## Development (Optional)

If you want to modify how the bibliography is generated:

### Installation

```bash
git clone <repository-url>
cd <repository-directory>
pip install requests

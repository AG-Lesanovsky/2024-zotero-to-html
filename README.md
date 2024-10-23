# Zotero to HTML Bibliography

This project fetches bibliography data from the Zotero API and generates an HTML file containing the formatted
bibliography. The purpose of this project is to automatically generate HTML code that can be used to paste in the
backend of TYPO3 to generate the publication lists on https://uni-tuebingen.de/cqs.

You find the recent html file [here](https://htmlpreview.github.io/?https://github.com/TODO).

## Features

- Fetches all entries from the Zotero group https://www.zotero.org/groups/5693788/cqs/library.
- Supported bibliography types in zotero are: Preprint (arXiv) and Journal Article.
- Formats the bibliography items into HTML.
- Categorizes items into different sections in the html based on tags `QUSP FOR5413` and `Quantera Project CoQuaDis`.
- Runs automatically every night at 3:00am and generates a new `bibliography.hml`

## Adding a Reference to Zotero CQS Group

1. You have to be a member of the Zotero
   group [Center for Quantum Science](https://www.zotero.org/groups/5693788/cqs/library).
2. Create a new entry and select the type of reference `journal article` or `preprint`.
3. Fill in the details of the reference (title, authors, publication date, etc.).
4. Add project tags such as `QUSP FOR5413` or `Quantera Project CoQuaDis` to categorize the reference.
5. Save the reference.

## Copying Bibliography to TYPO3

1. Visit [here](https://htmlpreview.github.io/?https://github.com/TODO).
2. Copy the HTML content which you want to copy.
3. Open the TYPO3 backend of the page where you want to add the bibliography.
4. Paste the copied HTML content.
5. Save

## GitHub Action

A GitHub Action is set up to automate the generation of the HTML bibliography. This action runs the script on a
scheduled basis daily at 03:00am and pushes the updated `bibliography.html` file to the repository. This
ensures that the bibliography is always up-to-date without manual intervention.

## Development

This section is only needed if you want to change how `bibliography.html` is generated.

### Installation

1. Clone the repository:
    ```
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Install the required Python packages:
    ```
    pip install requests
    ```

### Usage

1. Run the script to fetch data from the Zotero API and generate the HTML file:
    ```
    python zotero-to-html.py
    ```

2. The generated HTML file `bibliography.html` will be created in the project directory.

### Customization

- Modify the `format_item` function to change how each bibliography item is formatted.
- Adjust the API URL and parameters in the `get_data` function to fetch different data or change the sorting order.

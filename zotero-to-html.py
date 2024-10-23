import warnings
import requests


def get_data():
    """
    Fetches data from the Zotero API by making paginated requests.

    Returns:
        dict: A dictionary where each key is the starting index of a batch of results,
              and the corresponding value is the list of items in that batch.
    """
    start = 0
    pagesize = 100
    all_data = {}

    while True:
        # URL of the Zotero API with specific parameters
        url = (
            f"https://api.zotero.org/groups/5693788/items?order=date&sort=desc&format=json"
            f"&include=data&limit={pagesize}&start={start}"
        )

        try:
            # Fetch the data from the API
            response = requests.get(url)
            response.raise_for_status()  # Raises an error for 4XX/5XX responses

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            exit(1)

        items = response.json()

        # Check if there are no more items
        if not items:
            break

        all_data[start] = items
        print(f"Fetched {len(items)} items, starting at {start}")

        start += pagesize

    return all_data


# Data retrieval from Zotero API
data = get_data()


# %%
def format_item(item):
    """
    Formats a Zotero item as an HTML list item.

    Args:
        item (dict): A single Zotero item in JSON format.

    Returns:
        str: An HTML string for the Zotero item.
    """
    html_item = "<li>"

    # Add creators' names (First Initial + Last Name)
    creators = item["data"].get("creators", [])
    html_item += ", ".join([f"{creator['firstName'][0]}. {creator['lastName']}" for creator in creators])

    # Add title and DOI link
    html_item += f'<br><strong>{item["data"]["title"]}.<br>'

    # DOI link (if available)
    if "DOI" in item["data"]:
        html_item += f'<a href="https://doi.org/{item["data"]["DOI"]}" target="_blank" rel="noreferrer">'

    # Custom handling for preprints
    if item["data"]["itemType"] == "preprint":
        html_item += format_preprint(item)

    # Custom handling for journal articles
    elif item["data"]["itemType"] == "journalArticle":
        html_item += format_journal_article(item)

    # Add publication year from date
    html_item += f'({item["data"]["date"].split("-")[0]})</a></strong></li>\n'

    return html_item


def format_preprint(item):
    """
    Formats preprint-specific data for the Zotero item.

    Args:
        item (dict): A Zotero item of type 'preprint'.

    Returns:
        str: Formatted HTML string for preprint-specific information.
    """
    html = ""
    try:
        html += f'{item["data"]["repository"]}{item["data"]["archiveID"]} '
    except KeyError:
        warnings.warn(f'Missing repository or arXiv info for {item["data"]["title"]}')
    return html


def format_journal_article(item):
    """
    Formats journal article-specific data for the Zotero item.

    Args:
        item (dict): A Zotero item of type 'journalArticle'.

    Returns:
        str: Formatted HTML string for journal article-specific information.
    """
    html = ""
    try:
        html += f'{item["data"]["journalAbbreviation"]} Vol. {item["data"]["volume"]}, '
    except KeyError:
        warnings.warn(f'Missing journal abbreviation for {item["data"]["title"]}')
    try:
        html += f'{item["data"]["pages"]} '
    except KeyError:
        warnings.warn(f'Missing page numbers for {item["data"]["title"]}')
    return html


def process_items_by_tag(data, tag_filter):
    """
    Processes Zotero items by filtering them based on a specific tag and formats them into HTML.

    Args:
        data (dict): The complete Zotero data fetched from the API.
        tag_filter (str): The tag to filter the items by (e.g., 'QUSP FOR5413').

    Returns:
        str: A concatenated HTML string containing the filtered items.
    """
    html = ""
    for page_index in data.keys():
        print(f"Processing {tag_filter}-tagged items starting at page {page_index}...")
        for i, item in enumerate(data[page_index]):
            tags = [tag["tag"] for tag in item["data"].get("tags", [])]
            if tag_filter in tags:
                print(f"  Adding item {i + 1}/{len(data[page_index])}")
                html += format_item(item)
    return html


# Start building the HTML content
html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bibliography</title>
</head>
<body>
    <h1>Center for Quantum Science Publications</h1>
<ul>
'''

# Process all items
for page_index in data.keys():
    print(f"Processing batch starting at page {page_index}...")
    for i, item in enumerate(data[page_index]):
        print(f"  {i + 1}/{len(data[page_index])}")
        html_content += format_item(item)

# Add a section for "QUSP-only"
html_content += "</ul><h2>QUSP-only</h2><ul>"
html_content += process_items_by_tag(data, "QUSP FOR5413")

# Add a section for "CoQuaDis-only"
html_content += "</ul><h2>CoQuaDis-only</h2><ul>"
html_content += process_items_by_tag(data, "Quantera Project CoQuaDis")

# Close the HTML document
html_content += "</ul></body></html>"

# Write the HTML content to a file
with open("bibliography.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("HTML file 'bibliography.html' has been created successfully.")

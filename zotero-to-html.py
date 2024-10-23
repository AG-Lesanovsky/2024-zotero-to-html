import warnings

import requests


def get_data():
    start = 0
    limit = 100
    data = {}
    while True:
        # URL of the Zotero API with specific parameters
        url = f"https://api.zotero.org/groups/5693788/items?order=date&sort=desc&format=json&include=bib,data&style=american-physics-society&sort=date&direction=desc&limit={limit}&start={start}"
        # Fetch the data from the API
        response = requests.get(url)

        # Check if the request was successful
        if not response.status_code == 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            exit(1)

        # Check if there are no more items
        if len(response.json()) == 0:
            break
        # Parse the JSON response
        data[start] = response.json()
        print(f"Got {start + len(data[start])} items")
        start += limit
    return data


data = get_data()


# %% Define a function to format the items
def format_item(item):
    # TODO add heading for years
    # TODO add customization for arXiv items
    html_item = "<li>"
    for creator in item["data"]["creators"]:
        html_item += f"{creator['firstName'][0]}. {creator['lastName']}, "
    # remove last comma
    html_item = html_item[:-2]
    html_item += f'<br>'
    html_item += f'<strong>{item["data"]["title"]}.<br>'
    html_item += f'<a href="https://doi.org/{item["data"]["DOI"]}" target="_blank" rel="noreferrer">'
    if item["data"]["itemType"] == "preprint":
        try:
            html_item += f'{item["data"]["repository"]}{item["data"]["archiveID"]} '
        except KeyError:
            warnings.warn(f'No repository or arXiv for {item["data"]["title"]}')
    if item["data"]["itemType"] == "journalArticle":
        try:
            html_item += f'{item["data"]["journalAbbreviation"]} Vol. {item["data"]["volume"]}, '
        except KeyError:
            warnings.warn(f'No journalAbbreviation, for {item["data"]["title"]}')
        try:
            html_item += f'{item["data"]["pages"]} '
        except KeyError:
            warnings.warn(f'No pages for {item["data"]["title"]}')

    html_item += f'({item["data"]["date"].split('-')[0]})'
    html_item += "</a></strong></li>\n"
    return html_item


# %% Start the HTML content
html_content = '''
<!DOCTYPE html>
<html lang="en-US>
<head>
    <meta charset="UTF-8">
    <title>Bibliography</title>
</head>
<body>
    <h1>Center for Quantum Science Publications</h1>
<ul>
'''
# Create a list for all entries
# Loop through the items and extract the bibliography
for pi in data.keys():
    print(f"Processing {pi}...")
    for i, item in enumerate(data[pi]):
        print(f"  {i + 1}/{len(data[pi])}")
        html_content += format_item(item)

# create list for QUSP-only
html_content += "</ul><h2>QUSP-only</h2><ul>"
for pi in data.keys():
    print(f"Processing {pi}...")
    for i, item in enumerate(data[pi]):
        if "QUSP FOR5413" not in [tag["tag"] for tag in item["data"]["tags"]]:
            continue
        print(f"  {i + 1}/{len(data[pi])}")
        html_content += format_item(item)

# create list for CoQuaDis-only
html_content += "</ul><h2>CoQuaDis-only</h2><ul>"
for pi in data.keys():
    print(f"Processing {pi}...")
    for i, item in enumerate(data[pi]):
        if "Quantera Project CoQuaDis" not in [tag["tag"] for tag in item["data"]["tags"]]:
            continue
        print(f"  {i + 1}/{len(data[pi])}")
        html_content += format_item(item)

# Close the HTML tags
html_content += "</ul></body></html>"

# Write the HTML content to a file
with open("bibliography.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("HTML file 'bibliography.html' has been created successfully.")

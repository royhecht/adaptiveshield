import os
from bs4 import BeautifulSoup
import requests
from threading import Thread

WIKI_URL = "https://en.wikipedia.org"
ANIMAL_URL = f"{WIKI_URL}/wiki/List_of_animal_names"


class AnimalScraper:
    def __init__(self):
        self.dict_of_animals = {}
        self.image_threads = []

    @staticmethod
    def get_soup(url):
        response = requests.get(url)
        return BeautifulSoup(response.content, "html.parser")

    def append_animal(self, columns):
        collateral_adj = columns[6].text.strip()
        row_body_dict = self._extract_animal_info(columns)
        self.dict_of_animals.setdefault(collateral_adj, []).append(row_body_dict)

    @staticmethod
    def _extract_animal_info(columns):
        name = columns[0].text.strip().replace("/", "-")
        return {"name": name,
                "pic_link": columns[0].a['href'],
                "local_image": f"tmp/{name}"}

    @staticmethod
    def _download_img(name_link, name):
        img_page = requests.get(WIKI_URL + name_link)
        img_soup = BeautifulSoup(img_page.content, "html.parser")
        info_box = img_soup.find('table', class_='infobox')
        if info_box:
            img_source = info_box.find('img')['src']
            img_data = requests.get("https:" + img_source).content
            img_path = os.path.join('tmp', f'{name}.jpg')
            with open(img_path, 'wb') as handler:
                handler.write(img_data)
            return img_path
        return None

    def download_images_concurrently(self, columns, name):
        thread = Thread(target=self._download_img, args=(columns, name))
        self.image_threads.append(thread)
        thread.start()

    def scrape_animals(self, url):
        soup = self.get_soup(url)

        # Find all tables with the wikitable sortable class
        tables = soup.find_all('table', class_='wikitable sortable')

        for table in tables:
            for row in table.tbody.find_all('tr'):
                if columns := row.find_all('td'):
                    self.append_animal(columns)

        for _, values in self.dict_of_animals.items():
            for value in values:
                self.download_images_concurrently(value["pic_link"], value["name"])

        # Wait for all image download threads to finish
        for thread in self.image_threads:
            thread.join()

    def generate_html(self):
        self.scrape_animals(ANIMAL_URL)
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Animal Information</title>
        </head>
        <body>

        <h1>Animal Information</h1>
        """
        # Iterate over the dictionary and add content for each category
        for category, animals in self.dict_of_animals.items():
            html_content += f"<h2>{category.capitalize()}</h2>"
            html_content += "<ul>"
            for animal in animals:
                html_content += f"""
                    <li>
                        <h3>{animal['name']}</h3>
                        <img src="{animal['local_image']}" alt="{animal['name']}">
                    </li>
                """
            html_content += "</ul>"

        # Close the HTML document
        html_content += """
        </body>
        </html>
        """

        # Write the HTML content to a file
        with open('output.html', 'w') as file:
            file.write(html_content)

        print("HTML file generated successfully. Check 'output.html'.")


if __name__ == "__main__":
    animal_scraper = AnimalScraper()
    animal_scraper.generate_html()

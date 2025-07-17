import time
from django.db import IntegrityError
import openpyxl
from requests.adapters import HTTPAdapter
import requests
from django.core.management.base import BaseCommand, CommandError
from urllib3 import Retry
from peakquiz.models import Peak, Picture


class Command(BaseCommand):
    help = "Imports peaks from database based on input csv file"

    def add_arguments(self, parser):
        parser.add_argument("input", type=str)

    def get_picture_url_from_wiki_article(self, url: str):
        # Wikipedia API query string to get the main image on a page
        # (partial URL will be added to the end)
        query = "http://de.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles="
        partial_url = url.split("/")[-1]
        time.sleep(10)
        try:

            retries = Retry(total=5, backoff_factor=3, status_forcelist=[429])

            s = requests.Session()
            s.mount("https://", HTTPAdapter(max_retries=retries))
            api_res = s.get(query + partial_url)
            data = api_res.json()
            first_part = data["query"]["pages"]
            # this is a way around not knowing the article id number
            for key, value in first_part.items():
                if value["original"]["source"]:
                    data = value["original"]["source"]
                    return data
        except Exception as exc:
            print(f"Picture not found for: {partial_url}: {exc}")
            return None

    def handle(self, *args, **options):
        # read xlsx
        wb = openpyxl.load_workbook(options["input"])
        ws = wb["Tabellenblatt1"]
        # This will fail if there is no hyperlink to target
        # 1 - Bild
        # 2 - Gipfel
        # 3 - Höhe
        # 4 - Lage
        # 5 - Gebirge
        # 6 - Dominanz
        # 7 - Schartenhöhe
        for row_num in range(2, len(list(ws.rows))):
            try:
                peak_picture = ws.cell(row=row_num, column=1).hyperlink.target
            except AttributeError:
                peak_picture = None
            peak_name = ws.cell(row=row_num, column=2).value
            peak_url = ws.cell(row=row_num, column=2).hyperlink.target
            height = ws.cell(row=row_num, column=3).value
            region = ws.cell(row=row_num, column=4).value
            try:
                dominance_distance, dominance_peak = tuple(ws.cell(row=row_num, column=6).value.split("\n"))
            except AttributeError:
                dominance_peak = None
            try:
                prominence_distance, prominence_peak = tuple(ws.cell(row=row_num, column=7).value.split("\n"))
            except AttributeError:
                prominence_peak = None

            try:
                prominence_distance = float(prominence_distance)
            except ValueError:
                prominence_distance = None

            try:
                dominance_distance = float(ws.cell(row=row_num, column=6).value)
            except (ValueError, TypeError):
                dominance_distance = None

            if isinstance(dominance_distance, str):
                dominance_distance = float(dominance_distance.replace(",", "."))

            if isinstance(prominence_distance, str):
                prominence_distance = float(prominence_distance.replace(",", "."))

            peak = Peak(
                name=peak_name,
                elevation=height if type(height) in [int, float] else height.split(" ")[0],
                region=region,
                dominance_distance=dominance_distance,
                dominance_peak=dominance_peak,
                prominence_distance=prominence_distance,
                prominence_peak=prominence_peak,
            )
            try:
                peak.save()
            except IntegrityError:
                print(f"{peak_name} already exists, skipping")
                peak = Peak.objects.get(name=peak_name)
                if peak_picture:
                    first_pic = Picture(url=peak_picture, peak=peak)
                    try:
                        first_pic.save()
                        print(f"found first picture for {peak_name}: {peak_picture.split('/')[-1]}")
                    except IntegrityError:
                        print(f"Picture {first_pic.url} already exists, skipping")

            second_pic = self.get_picture_url_from_wiki_article(peak_url)
            if second_pic:
                print(f"found second picture for {peak_name}: {second_pic.split('/')[-1]}")
                second_picture = Picture(url=second_pic, peak=peak)
                try:
                    second_picture.save()
                except IntegrityError:
                    print(f"Picture {first_pic.url} already exists, skipping")


import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def fetch_top_hf_papers(past_days: int, to_current: bool = False) -> list:
    """ Fetches top Hugging Face papers from the past 'past_days' days. """

    end_date = datetime.today().date()
    date_of_interest = end_date - timedelta(days=past_days)
    papers = []

    if to_current:
        processed_titles = set()
        while date_of_interest <= end_date:
            formatted_date = date_of_interest.strftime("%Y-%m-%d")
            print(f"Fetching papers for date: {formatted_date}")
            url = f"https://huggingface.co/papers?date={formatted_date}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error: Unable to access URL for the date {formatted_date}. Status code: {response.status_code}")
            else:
                soup = BeautifulSoup(response.text, "html.parser")
                main_section = soup.find("body").find("main")
                for item in main_section.find_all("article", {"class": "flex-col"}):
                    title = item.find("h3").text.strip()
                    print(f"Paper: {title}")
                    if title not in processed_titles:
                        upvote_text = item.find("div", {"class": "leading-none"}).text.strip()
                        upvotes = int(upvote_text) if upvote_text != "-" else 0
                        if upvotes > 20 or ("diffusion" in title.lower() and upvotes >= 15) or ("3D" in title and upvotes >= 10):
                            parse_url = "https://huggingface.co" + item.find("a", {"class": "cursor-pointer"})["href"]
                            title = item.find("h3").text.strip()
                            parts = title.split(':')
                            if len(parts) > 1:
                                paper_name = parts[0] + ":"
                                description = parts[1]
                            else:
                                paper_name = ""
                                description = title 
                            pape_dict = {"name": paper_name, "title": description, "url": parse_url, "upvotes": str(upvotes)}
                            papers.append(pape_dict)
                        processed_titles.add(title)
            date_of_interest += timedelta(days=1)
    else:
        formatted_date = date_of_interest.strftime("%Y-%m-%d")
        url = f"https://huggingface.co/papers?date={formatted_date}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: Unable to access URL for the date {formatted_date}. Status code: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        main_section = soup.find("body").find("main")
        for item in main_section.find_all("article", {"class": "flex-col"}):
            title = item.find("h3").text.strip()
            upvote_text = item.find("div", {"class": "leading-none"}).text.strip()
            upvotes = int(upvote_text) if upvote_text != "-" else 0
            if upvotes > 20 or ("diffusion" in title.lower() and upvotes >= 15):
                parse_url = "https://huggingface.co" + item.find("a", {"class": "cursor-pointer"})["href"]
                parts = title.split(':')
                if len(parts) > 1:
                    paper_name = parts[0] + ":"
                    description = parts[1]
                else:
                    paper_name = ""
                    description = title 
                pape_dict = {"name": paper_name, "title": description, "url": parse_url, "upvotes": str(upvotes)}
                papers.append(pape_dict)

    return papers


def fetch_paper_details(papers: list) -> list:
    """ Fetches additional details for each paper, including abstract and publication date. """

    for paper in papers:
        response = requests.get(paper["url"])
        soup = BeautifulSoup(response.text, "html.parser")

        abstract_header = soup.find("h2", string="Abstract")
        if abstract_header:
            abstract_paragraph = abstract_header.find_next("p")
            if abstract_paragraph:
                paper["abstract"] = abstract_paragraph.text.strip()
            else:
                paper["abstract"] = "Abstract not found."
        else:
            paper["abstract"] = "Abstract header not found."

        published_text_element = soup.find_all(text=re.compile(r"Published on\s"))
        if published_text_element:
            current_year = datetime.now().year 
            published_text = published_text_element[0]
            published_date = re.search(r"Published on ([\w\s]+)", published_text).group(1)
            #month_only = published_date.split(" ")[0]
            paper["date"] = f"{published_date} {current_year}" 
        else:
            paper["date"] = "Published date not found."
    
    return papers

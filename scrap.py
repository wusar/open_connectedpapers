from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import NamedTuple
from bs4 import BeautifulSoup
import re
import logging
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import time
import random


# Configure logging
logger = logging.getLogger(__name__)

# The maximum number of pages to extract data from
page_num = 1


# Placeholder function to build the citation graph (to be implemented)
def build_graph():
    # build the citation graph between the graphs
    pass


# Extract the paper information from the paper div
def parse_paper_div(paper_div):
    try:
        paper_data = {}
        paper_data["related_papers"] = []
        paper_data["cited_papers"] = []
        if paper_div is None:
            logger.error("paper_div is None")

        # Extract paper URL
        paper_title_elemets = paper_div.find("h3", class_="gs_rt")
        if paper_title_elemets is None:
            paper_title_elemets = paper_div.find("h3", class_="gs_a")
        if paper_title_elemets is None:
            logger.info("paper_url is None")
            paper_url = None
            paper_title = None
        else:
            paper_url = paper_title_elemets.find("a")["href"]
            paper_title = paper_div.find("h3", class_="gs_rt").find("a").text.strip()
        paper_data["paper_url"] = paper_url

        # Extract paper title
        paper_data["paper_title"] = paper_title

        # Extract publication date
        publication_date_str = paper_div.find("div", class_="gs_a").text.strip()

        # Assuming the publication date is in the format "K Weman - 2011"
        # Use regular expression to extract the year as a group
        year_match = re.search(r"\d{4}", publication_date_str)
        if year_match:
            publication_year = year_match.group()
        else:
            publication_year = None
        paper_data["publication_year"] = publication_year

        # Extract citation count
        citation_count_element = paper_div.find(
            text=lambda text: text.startswith("被引用次数：")
        )
        if citation_count_element:
            # Extract the number after "被引用次数："
            citation_count_text = citation_count_element.split("：")[1].strip()
            citation_count = int(citation_count_text)
        else:
            citation_count = None
        paper_data["citation_count"] = citation_count
        return paper_data

    except Exception as e:
        logger.error(f"Error parsing paper div: {e}")


# Extract all citations of the paper
options = webdriver.EdgeOptions()
# options.add_argument("--incognito")

# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_argument("--no-sandbox")
# options.add_argument("--lang=zh-CN")
# options.add_argument("user-agent=foo")
# options.add_argument("--user-data-dir="+r"C:/Users/USTC/AppData/Local/Microsoft/Edge/User Data")

driver = webdriver.Edge(options=options)


# Function to get all papers' information from Google Scholar
def search_paper_data(paper_name, reuqired_info="related"):
    driver.get("https://scholar.google.com/")

    # 定位搜索框
    search_box = driver.find_element(By.ID, "gs_hdr_tsi")

    # 输入要搜索的论文名称
    search_box.send_keys(paper_name)

    # Locate and click the submit button
    submit_button = driver.find_element(By.ID, "gs_hdr_tsb")
    sleep(random.randint(1, 3))

    submit_button.click()

    # Choose the first paper in the search results as the target paper
    try:
        allpaper_innerHTML = driver.find_element(
            By.ID, value="gs_res_ccl_mid"
        ).get_attribute("innerHTML")
    except:
        logger.info("No search results found")
        return {}

    soup = BeautifulSoup(allpaper_innerHTML, "lxml")

    try:
        all_paper_elements = soup.find_all(
            "div", class_="gs_r gs_or gs_scl"
        ) + soup.find_all("div", class_="gs_r gs_or gs_scl gs_fmar")
        if len(all_paper_elements) == 0:
            logger.info("No search results found")
            return {}
    except:
        logger.info("No search results found")
        return {}
    paper_data = parse_paper_div(all_paper_elements[0])

    # We need to get the related work of this paper
    if reuqired_info == "related":
        # 点击'相关文章'链接
        related_articles_link = driver.find_element(By.PARTIAL_LINK_TEXT, "相关文章")
        sleep(random.randint(1, 3))
        related_articles_link.click()
    elif reuqired_info == "cited":
        # 点击'被引用次数'链接
        cited_by_link = driver.find_element(By.PARTIAL_LINK_TEXT, "被引用次数")
        sleep(random.randint(1, 3))
        cited_by_link.click()

    logger.info(f"Extracting {reuqired_info} papers")
    # Extract data from up to 2 pages of search results
    for _ in range(page_num):
        allpaper_innerHTML = driver.find_element(
            By.ID, value="gs_res_ccl_mid"
        ).get_attribute("innerHTML")

        soup = BeautifulSoup(allpaper_innerHTML, "lxml")
        for paper_div in soup.find_all("div", class_="gs_r gs_or gs_scl"):
            other_paper_data = parse_paper_div(paper_div)
            if reuqired_info == "related":
                paper_data["related_papers"].append(other_paper_data)
            elif reuqired_info == "cited":
                paper_data["cited_papers"].append(other_paper_data)
        # Find and click the next page button, exit if not found
        try:
            next_page_button = driver.find_element(By.LINK_TEXT, "下一页")
        except:
            next_page_button = None
        if next_page_button:
            sleep(random.randint(1, 3))
            next_page_button.click()
        else:
            break
    return paper_data


# Function to get paper data and save it in JSON format
def get_all_paper_data():
    paper_search_name = "3D Gaussian Splatting for Real-Time Radiance Field Rendering"
    all_paper_data = []
    # Get the root paper data and its site and related information
    root_paper_data_cited = search_paper_data(paper_search_name, reuqired_info="cited")
    root_paper_data_related = search_paper_data(
        paper_search_name, reuqired_info="related"
    )

    # We only need the cited information of the root paper, the related information is used for the next step
    all_paper_data.append(root_paper_data_cited)

    # Get citation information for each related paper
    for paper in root_paper_data_related["related_papers"]:
        related_paper_data = search_paper_data(
            paper["paper_title"], reuqired_info="cited"
        )
        if related_paper_data != {}:
            all_paper_data.append(related_paper_data)

    # Save data in JSON format
    with open("papers_data.json", "w") as f:
        json.dump(all_paper_data, f)
    return all_paper_data


# Function to convert RGBA color to hexadecimal format
def rgba_to_hex(rgba):
    r, g, b, a = rgba
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


# Function to visualize the citation graph
def visualize():
    with open("papers_data.json", "r") as f:
        papers_data = json.load(f)
    from pyecharts import options as opts
    from pyecharts.charts import Graph

    # Extract nodes and edges from data
    nodes = []
    edges = []
    cmap = plt.get_cmap("Blues")  # Use blue color map

    papers_citation_data = papers_data
    for paper in papers_citation_data:
        print(paper)
    # Get the earliest and latest publication years
    min_year = min(int(paper["publication_year"]) for paper in papers_citation_data)
    max_year = max(int(paper["publication_year"]) for paper in papers_citation_data)

    # Convert years to numbers for color mapping
    min_year_num = mdates.date2num(datetime(min_year, 6, 30))
    max_year_num = mdates.date2num(datetime(max_year, 6, 30))

    max_citation_count = max(paper["citation_count"] for paper in papers_citation_data)

    for paper in papers_citation_data:
        year_num = mdates.date2num(datetime(int(paper["publication_year"]), 6, 30))
        rgba_color = cmap(
            max((year_num - min_year_num) / (max_year_num - min_year_num), 0.1)
        )  # Compute color value
        hex_color = rgba_to_hex(rgba_color)

        nodes.append(
            {
                "name": paper["paper_title"],
                "symbolSize": paper["citation_count"] / max_citation_count * 100,
                "itemStyle": {"color": hex_color},
            }
        )
    for paper in papers_citation_data:
        if "cited_papers" in paper:
            for citation in paper["cited_papers"]:
                if citation is not None:
                    if citation["paper_title"] in [
                        paper["paper_title"] for paper in papers_citation_data
                    ]:
                        edges.append(
                            {
                                "source": citation["paper_title"],
                                "target": paper["paper_title"],
                            }
                        )
                        logging.info(
                            f"Adding edge: {citation['paper_title']} -> {paper['paper_title']}"
                        )

    # Create the graph
    graph = (
        Graph()
        .add("", nodes, edges, repulsion=8000, label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(title_opts=opts.TitleOpts(title="Papers Citation Graph"))
    )

    # Render the graph
    graph.render("papers_citation_graph.html")


# Main function
if __name__ == "__main__":
    papers_citation_data = get_all_paper_data()
    driver.close()
    visualize()

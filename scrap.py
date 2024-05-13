from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import NamedTuple
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)


def build_graph():

    # build the citation graph between the graphs
    pass


def parse_paper_div(paper_div, papers_data):
    try:
        paper_info = {}
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
        paper_info["paper_url"] = paper_url
        # Extract paper title

        paper_info["paper_title"] = paper_title

        # Extract publication date
        publication_date_str = paper_div.find("div", class_="gs_a").text.strip()

        # Assuming the publication date is in the format "K Weman - 2011"
        # Use regular expression to extract the year as a group
        year_match = re.search(r"\d{4}", publication_date_str)
        if year_match:
            publication_year = year_match.group()
        else:
            publication_year = None
        paper_info["publication_year"] = publication_year

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
        paper_info["citation_count"] = citation_count
        papers_data.append(paper_info)
    except Exception as e:
        logger.error(f"Error parsing paper div: {e}")



def find_all_citations(paper_url):
    # Extract all citations of the paper
    driver = webdriver.Edge()
    driver.get(paper_url)

    # 定位输入框并输入文本
    search_box = driver.find_element(By.ID, "gs_hdr_tsi")
    search_box.send_keys("Welding")

    # 定位提交按钮并点击
    submit_button = driver.find_element(By.ID, "gs_hdr_tsb")
    submit_button.click()
    papers_data = []

    # 最多解析5页的引用数据
    for _ in range(5):
        allpaper_innerHTML = driver.find_element(
            By.ID, value="gs_res_ccl_mid"
        ).get_attribute("innerHTML")

        soup = BeautifulSoup(allpaper_innerHTML, "lxml")
        for paper_div in soup.find_all("div", class_="gs_r gs_or gs_scl"):
            parse_paper_div(paper_div, papers_data)
        # 找到下一页按钮,并点击，没有找到则退出
        next_page_button = driver.find_element(By.LINK_TEXT, "下一页")
        if next_page_button:
            next_page_button.click()
        else:
            break
    driver.close()
    return papers_data

if __name__ == "__main__":
    papers_citation_data = find_all_citations('https://scholar.google.com/scholar?cites=18198394694373496650&as_sdt=5,29&sciodt=0,29&hl=zh-CN')
    print("finish")

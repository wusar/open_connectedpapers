from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import NamedTuple
from bs4 import BeautifulSoup
import re
import logging
import json

logger = logging.getLogger(__name__)


def build_graph():

    # build the citation graph between the graphs
    pass


# Extract the paper information from the paper div
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

        # Extract the citation work url
        citation_work_elements = paper_div.find("a", href=True, text="相关文章")
        if citation_work_elements is None:
            citation_url = None
        else:
            citation_url = citation_work_elements["href"]
        paper_info["citation_url"] = citation_url

        papers_data.append(paper_info)

    except Exception as e:
        logger.error(f"Error parsing paper div: {e}")


def get_all_papers_info(paper_url):
    # Extract all citations of the paper
    driver = webdriver.Edge()
    driver.get(paper_url)

    # 定位提交按钮并点击
    submit_button = driver.find_element(By.ID, "gs_hdr_tsb")
    submit_button.click()
    papers_data = []

    # 最多解析5页的引用数据
    for _ in range(2):
        allpaper_innerHTML = driver.find_element(
            By.ID, value="gs_res_ccl_mid"
        ).get_attribute("innerHTML")

        soup = BeautifulSoup(allpaper_innerHTML, "lxml")
        for paper_div in soup.find_all("div", class_="gs_r gs_or gs_scl"):
            parse_paper_div(paper_div, papers_data)
        # 找到下一页按钮,并点击，没有找到则退出
        try:
            next_page_button = driver.find_element(By.LINK_TEXT, "下一页")
        except:
            next_page_button = None
        if next_page_button:
            next_page_button.click()
        else:
            break
    driver.close()
    return papers_data


def get_paper_data():
    # 定位输入框并输入文本
    # search_box = driver.find_element(By.ID, "gs_hdr_tsi")
    # search_box.send_keys("Welding")
    papers_citation_data = get_all_papers_info(
        "https://scholar.google.com/scholar?cites=18198394694373496650&as_sdt=5,29&sciodt=0,29&hl=zh-CN"
    )

    # 我们这里获取两层级的引用信息
    for paper in papers_citation_data:
        print(paper)
        print(paper["citation_url"])
        citation_url = "https://scholar.google.com" + paper["citation_url"]
        citation_paper_data = get_all_papers_info(citation_url)
        paper["citation_papers_data"] = citation_paper_data
    print("finish")
    # 以json格式保存数据
    import json

    with open("papers_data.json", "w") as f:
        json.dump(papers_citation_data, f)
    return papers_citation_data


if __name__ == "__main__":
    with open("papers_data.json", "r") as f:
        papers_citation_data = json.load(f)
    from pyecharts import options as opts
    from pyecharts.charts import Graph

    # 从你的数据中提取节点和边
    nodes = []
    edges = []
    for paper in papers_citation_data:
        nodes.append(
            {"name": paper["paper_title"], "symbolSize": paper["citation_count"] / 10}
        )
        if "citation_papers_data" in paper:
            for citation in paper["citation_papers_data"]:
                print("add new edge: ", paper["paper_title"], citation["paper_title"])
                edges.append(
                    {"source": paper["paper_title"], "target": citation["paper_title"]}
                )

    # 创建图表
    graph = (
        Graph()
        .add("", nodes, edges, repulsion=8000, label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(title_opts=opts.TitleOpts(title="Papers Citation Graph"))
    )

    # 渲染图表
    graph.render("papers_citation_graph.html")

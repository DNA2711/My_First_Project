import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
import re
import json
import sys
import time
import traceback

# Hàm kiểm tra các phần tử đăng nhập


def check_login_elements(content):
    soup = BeautifulSoup(content, "html.parser")
    keywords = ["sign up", "sign in", "log in", "signup", "login", "Account",
                "subscribe", "ACCOUNT", "member", "join now", "join us", "register", "NEWSLETTER"]
    regex_pattern = re.compile(
        r"\b(" + "|".join(re.escape(keyword.replace('&', '\&')) for keyword in keywords) + r")\b", re.I)

    matching_elements = []  # Danh sách để lưu trữ các thẻ khớp

    for tag in soup.find_all(['a', 'b', 'p', 'button', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div']):
        if any(keyword in tag.get_text() for keyword in keywords) or regex_pattern.search(str(tag)):
            matching_elements.append(tag)

    return matching_elements


def find_affiliate_links(content):
    soup = BeautifulSoup(content, "html.parser")
    affiliate_keywords = ["affiliate", "Affiliate", "AFFILIATE"]

    matching_links = ''  # Danh sách để lưu trữ các liên kết liên quan đến từ khóa "affiliate"

    for link in soup.find_all('a', href=True):
        href = link['href']
        for keyword in affiliate_keywords:
            if keyword in href:
                matching_links = href

    return matching_links


def find_AboutUs_links(content):
    soup = BeautifulSoup(content, "html.parser")
    AboutUs_keywords = ["About us", "ABOUT US", "About Us", "about us"]

    matching_links = ''  # Danh sách để lưu trữ các liên kết liên quan đến từ khóa "About Us"

    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.text
        for keyword in AboutUs_keywords:
            if keyword in text:
                matching_links = href

    return matching_links


def find_privacy_links(content):
    soup = BeautifulSoup(content, "html.parser")
    privacy_keywords = ["Privacy", "privacy",
                        "Privacy notice", "privacy notice", "Privacy Notice"]

    matching_links = ''

    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.text
        for keyword in privacy_keywords:
            if keyword in text:
                matching_links = href

    return matching_links


def find_contact_links(content):
    soup = BeautifulSoup(content, "html.parser")
    contact_keywords = ["Contact", "contact",
                        "Contact Us", "contact us", "Contact us"]

    matching_links = ''

    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.text
        for keyword in contact_keywords:
            if keyword in text:
                matching_links = href

    return matching_links


def find_term_links(content):
    soup = BeautifulSoup(content, "html.parser")
    term_keywords = ["Terms", "terms", "TERMS"]

    matching_links = ''

    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.text
        for keyword in term_keywords:
            if keyword in text:
                matching_links = href

    return matching_links


def check_brand(brand_name, proxy):
    try:
        proxy_address = proxy

        # Cấu hình proxy
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=http://' + proxy_address)

        # Khởi tạo trình duyệt
        driver = webdriver.Chrome(options=chrome_options)

        # Mã hóa brand_name thành URL an toàn
        encoded_brand_name = quote_plus(brand_name)

        url_link = f"https://www.google.com/search?q={encoded_brand_name}+official+website"
        driver.get(url_link)

        # Tìm trang đầu tiên trong kết quả tìm kiếm và click vào nó
        search_result = driver.find_element(By.CSS_SELECTOR, "h3")
        search_result.click()

        time.sleep(1)

        # Lấy HTML của trang web sau khi click
        page_after_click_html = driver.page_source

        # Kiểm tra các từ khóa trên trang sau khi click
        matching_elements = check_login_elements(page_after_click_html)
        if (len(matching_elements) > 0):
            link_affiliate = find_affiliate_links(page_after_click_html)
            link_AboutUs = find_AboutUs_links(page_after_click_html)
            link_privacy = find_privacy_links(page_after_click_html)
            link_contact = find_contact_links(page_after_click_html)
            link_term = find_term_links(page_after_click_html)

            # Kiểm tra xem liên kết affiliate có phần domain không và thêm nếu cần
            if link_affiliate and not urlparse(link_affiliate).netloc:
                current_url = driver.current_url
                link_affiliate = current_url.rstrip('/') + link_affiliate

            if link_AboutUs and not urlparse(link_AboutUs).netloc:
                current_url = driver.current_url
                link_AboutUs = current_url.rstrip('/') + link_AboutUs

            if link_privacy and not urlparse(link_privacy).netloc:
                current_url = driver.current_url
                link_privacy = current_url.rstrip('/') + link_privacy

            if link_contact and not urlparse(link_contact).netloc:
                current_url = driver.current_url
                link_contact = current_url.rstrip('/') + link_contact

            if link_term and not urlparse(link_term).netloc:
                current_url = driver.current_url
                link_term = current_url.rstrip('/') + link_term

        else:
            link_affiliate = ""
            link_AboutUs = ""
            link_privacy = ""
            link_contact = ""
            link_term = ""

        current_url = driver.current_url
        driver.quit()

        if matching_elements:
            result_item = {
                "brand_name": brand_name,
                "status": "true",
                "data": {
                    "website_url": current_url,
                    "affiliate_links": link_affiliate,
                    "AboutUs_links": link_AboutUs,
                    "privacy_links": link_privacy,
                    "contact_links": link_contact,
                    "term_links": link_term
                }
            }
        else:
            result_item = {
                "brand_name": brand_name,
                "status": "false",
                "data": {
                    "website_url": "",
                    "affiliate_links": "",
                    "AboutUs_links": "",
                    "privacy_links": "",
                    "contact_links": "",
                    "term_links": ""
                }
            }

        return result_item

    except Exception as e:
        error_message = str(e)
        traceback.print_exc()  # In thông tin lỗi ra console
        return {
            "brand_name": brand_name,
            "status": "error",
            "data": {
                "error_message": error_message,
            }
        }


def main():
    try:
        input_array = sys.argv[1:]
        # input_array = ['youn-beauty']
        result_array = []

        proxy_list = [
            "194.26.176.221:8800",
            "194.26.177.235:8800",
            "194.26.177.113:8800",
            "194.26.176.163:8800",
            "192.126.175.207:8800",
            "194.26.177.77:8800",
            "194.26.176.62:8800",
            "192.126.175.216:8800",
            "194.26.177.250:8800",
            "194.26.176.67:8800",
            "192.126.175.194:8800",
            "192.126.175.218:8800"
        ]

        max_workers = len(proxy_list)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            brand_index = 0
            while brand_index < len(input_array):
                proxy_batch = proxy_list[:max_workers]
                brand_batch = input_array[brand_index:brand_index + max_workers]
                results = list(executor.map(
                    check_brand, brand_batch, proxy_batch))
                result_array.extend(results)
                brand_index += max_workers

        result_json = json.dumps(result_array, indent=4)
        print(result_json)

    except Exception as _:
        with open("error.log", "w") as log_file:
            traceback.print_exc(file=log_file)


if __name__ == "__main__":
    main()
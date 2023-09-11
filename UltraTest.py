import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json
import sys

# Hàm kiểm tra các phần tử đăng nhập


def check_login_elements(content):
    soup = BeautifulSoup(content, "html.parser")
    keywords = ["sign up", "sign in", "log in", "signup", "login", "Account",
                "subscribe", "ACCOUNT", "member", "join now", "join us", "register", "NEWSLETTER"]
    regex_pattern = re.compile(
        r"\b(" + "|".join(re.escape(keyword) for keyword in keywords) + r")\b", re.I)

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

# Hàm kiểm tra trang web cho một thương hiệu


def check_brand(brand_name, proxy):
    try:
        proxy_address = proxy

        # Cấu hình proxy
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=http://' + proxy_address)

        # Khởi tạo trình duyệt
        driver = webdriver.Chrome(options=chrome_options)

        url_link = "https://www.google.com/search?q=" + brand_name + " official website"
        driver.get(url_link)

        # Tìm trang đầu tiên trong kết quả tìm kiếm và click vào nó
        search_result = driver.find_element(By.CSS_SELECTOR, "h3")
        search_result.click()

        # Lấy HTML của trang web sau khi click
        page_after_click_html = driver.page_source

        # Kiểm tra các từ khóa trên trang sau khi click
        matching_elements = check_login_elements(page_after_click_html)
        if (len(matching_elements) > 0):
            link_affiliate = find_affiliate_links(page_after_click_html)
            # Kiểm tra xem liên kết affiliate có phần domain không và thêm nếu cần
            if link_affiliate and not urlparse(link_affiliate).netloc:
                current_url = driver.current_url
                link_affiliate = current_url + link_affiliate
        else:
            link_affiliate = ""

        current_url = driver.current_url
        driver.quit()

        if matching_elements:
            result_item = {
                "brand_name": brand_name,
                "status": "true",
                "data": {
                    "website_url": current_url,
                    "affiliate_links": link_affiliate
                }
            }
        else:
            result_item = {
                "brand_name": brand_name,
                "status": "false",
                "data": {
                    "website_url": "",
                    "affiliate_links": ""
                }
            }

        return result_item

    except Exception as e:
        return {
            "brand_name": brand_name,
            "status": "error",
            "data": {
                "error_message": str(e),
            }
        }


def main():
    try:
        # input_array = sys.argv[1:]
        input_array = ['sobel-skin', 'youn-beauty']
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

    except Exception as e:
        with open("error.log", "w") as log_file:
            log_file.write(str(e))


if __name__ == "__main__":
    main()

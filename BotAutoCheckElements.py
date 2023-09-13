from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote_plus
import re
import json
import traceback
import time
import sys


# Định nghĩa các danh sách từ khóa
login_keywords = ["sign up", "sign in", "log in", "signup", "login", "Account", "log in/sign up",
                  "subscribe", "ACCOUNT", "member", "join now", "join us", "register", "NEWSLETTER", "my account"]

login_links_keywords = ["login", "Log in", "sign in", "account", "my account", "LOG IN", "ACCOUNT",
                        "register", "sign up", "sigup", "signin", "log in/sign up", "Register", "LOGIN"]

affiliate_keywords = ["affiliate", "Affiliate", "AFFILIATE"]

AboutUs_keywords = ["About us", "ABOUT US", "About Us", "about us"]

privacy_keywords = ["Privacy", "privacy", "Privacy Policy",
                    "Privacy notice", "privacy notice", "Privacy Notice"]

contact_keywords = ["Contact", "contact",
                    "Contact Us", "contact us", "Contact us"]

term_keywords = ["Terms", "terms", "TERMS", "Terms & Conditions"]

# Hàm kiểm tra các phần tử đăng nhập


def check_login_elements(content):
    soup = BeautifulSoup(content, "html.parser")
    regex_pattern = re.compile(
        r"\b(" + "|".join(re.escape(keyword.replace('&', '\&')) for keyword in login_keywords) + r")\b", re.I)

    matching_elements = []  # Danh sách để lưu trữ các thẻ khớp

    for tag in soup.find_all(['a', 'b', 'p', 'button', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div']):
        if any(keyword in tag.get_text() for keyword in login_keywords) or regex_pattern.search(str(tag)):
            matching_elements.append(tag)

    return matching_elements


# Hàm tìm liên kết dựa trên từ khóa và loại liên kết
def find_links_by_keywords(content, keywords, link_type):
    soup = BeautifulSoup(content, "html.parser")
    matching_links = []

    for keyword in keywords:
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.text
            if keyword in text and link_type in href:
                matching_links.append(href)

    return matching_links


def find_login_links(content, keywords):
    soup = BeautifulSoup(content, "html.parser")
    matching_links = []

    # Tạo một danh sách các thẻ có thể chứa liên kết đăng nhập
    tag_names = ['a', 'button', 'input', 'div', 'span', 'p', 'img']

    for tag_name in tag_names:
        for tag in soup.find_all(tag_name, href=True):
            text = tag.text
            href = tag['href']
            if any(keyword in text for keyword in keywords) or any(keyword in tag.get('class', []) for keyword in keywords):
                matching_links.append(href)

    return matching_links


def find_login_links_near_form(login_form):
    matching_links = []

    if login_form:
        # Tìm các thẻ <a> nằm trong cùng parent với biểu mẫu đăng nhập
        for link in login_form.find_all('a', href=True):
            href = link['href']
            matching_links.append(href)

    return matching_links


def find_login_form(content):
    soup = BeautifulSoup(content, "html.parser")
    login_form = soup.find('form')
    return login_form


def check_brand(brand_name, proxy):
    try:
        proxy_address = proxy

        # Cấu hình proxy
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=http://' + proxy_address)

        # Thêm tùy chọn --headless cho chế độ headless
        chrome_options.add_argument('--headless')

        # Khởi tạo trình duyệt
        driver = webdriver.Chrome(options=chrome_options)

        # Mã hóa brand_name thành URL an toàn
        encoded_brand_name = quote_plus(brand_name)

        url_link = f"https://www.google.com/search?q={encoded_brand_name}+official+website"
        driver.get(url_link)

        # Tìm trang đầu tiên trong kết quả tìm kiếm và click vào nó
        search_result = driver.find_element(By.CSS_SELECTOR, "h3")
        search_result.click()

        time.sleep(2)

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(2)

        # Lấy HTML của trang web sau khi click
        page_after_click_html = driver.page_source

        # Tìm biểu mẫu đăng nhập và liên kết đăng nhập gần nó
        login_form = find_login_form(page_after_click_html)
        login_links_near_form = find_login_links_near_form(login_form)

        matching_elements = check_login_elements(page_after_click_html)

        # Kiểm tra các từ khóa trên trang sau khi click
        matching_login_links = find_login_links(
            page_after_click_html, login_links_keywords)
        matching_affiliate_links = find_links_by_keywords(
            page_after_click_html, affiliate_keywords, 'affiliate')
        matching_AboutUs_links = find_links_by_keywords(
            page_after_click_html, AboutUs_keywords, 'about')
        matching_privacy_links = find_links_by_keywords(
            page_after_click_html, privacy_keywords, 'privacy')
        matching_contact_links = find_links_by_keywords(
            page_after_click_html, contact_keywords, 'contact')
        matching_term_links = find_links_by_keywords(
            page_after_click_html, term_keywords, 'term')

        # Kiểm tra xem liên kết có phần domain không và thêm nếu cần
        def check_and_fix_link(link):
            if link and not urlparse(link).netloc:
                current_url = driver.current_url
                return urljoin(current_url, link)
            return link

        link_login = check_and_fix_link(
            matching_login_links[0] if matching_login_links else '')
        link_affiliate = check_and_fix_link(
            matching_affiliate_links[0] if matching_affiliate_links else '')
        link_AboutUs = check_and_fix_link(
            matching_AboutUs_links[0] if matching_AboutUs_links else '')
        link_privacy = check_and_fix_link(
            matching_privacy_links[0] if matching_privacy_links else '')
        link_contact = check_and_fix_link(
            matching_contact_links[0] if matching_contact_links else '')
        link_term = check_and_fix_link(
            matching_term_links[0] if matching_term_links else '')

        current_url = driver.current_url
        driver.quit()

        if matching_elements:
            result_item = {
                "brand_name": brand_name,
                "status": "true",
                "data": {
                    "website_url": current_url,
                    "login_links": link_login,
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
                    "login_links": "",
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
        traceback.print_exc()
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

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
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

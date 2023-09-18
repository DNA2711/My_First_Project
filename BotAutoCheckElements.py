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
login_keywords = ["sign up", "sign-up", "signup", "sign in", "log-in", "log in", "login", "Account",
                  "subscribe", "ACCOUNT", "member", "join now", "john-now", "join us", "john-us", "register", "NEWSLETTER", "my account", "my-account", "Get a demo", "get-a-demo", "login/sign up"]

login_links_keywords = ["login", "Log in", "sign in", "account", "my account", "LOG IN", "ACCOUNT",
                        "register", "sign up", "sigup", "signin", "log in/sign up", "Register", "LOGIN", "Get a demo"]

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

    for tag in soup.find_all(['a', 'b', 'button', 'span', 'div', 'input']):
        text = tag.get_text()
        # Lấy thuộc tính href của phần tử, nếu không có thì lấy chuỗi rỗng
        href = tag.get('href', '')
        if any(keyword in text for keyword in login_keywords) or regex_pattern.search(text) or any(keyword in href for keyword in login_keywords):
            # Giới hạn độ dài của đoạn văn bản dưới 15 ký tự
            if len(text) <= 15:
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
        # chrome_options.add_argument('--headless')
        # Khởi tạo trình duyệt
        driver = webdriver.Chrome(options=chrome_options)

        # Mã hóa brand_name thành URL an toàn
        encoded_brand_name = quote_plus(brand_name)

        url_link = f"https://google.com/search?q={encoded_brand_name}+official+website"
        driver.get(url_link)

        # Chờ cho trang web tải hoàn tất
        time.sleep(5)  # Đợi 5 giây hoặc nhiều hơn nếu cần

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
        proxy_list = [
            "38.154.99.223:8800",
            "38.154.99.148:8800",
            "38.154.99.255:8800",
            "38.154.99.198:8800",
            "38.154.99.151:8800",
            "38.154.99.186:8800",
            "38.154.99.158:8800",
            "38.154.99.208:8800",
            "38.154.99.138:8800",
            "38.154.99.189:8800",
            "38.154.99.216:8800",
            "38.154.99.183:8800",
            "38.154.99.222:8800",

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
            "192.126.175.218:8800",

            '38.153.192.39:8800',
            '38.153.192.79:8800',
            '45.66.238.155:8800',
            '45.66.238.84:8800',
            '45.66.238.210:8800',
            '154.9.54.137:8800',
            '154.9.54.127:8800',
            '193.168.182.247:8800',
            '38.153.160.52:8800',
            '80.65.222.240:8800',
            '193.168.182.227:8800',
            '38.153.192.102:8800',
            '45.66.238.59:8800',
            '80.65.222.228:8800',
            '154.9.54.85:8800',
            '38.153.160.202:8800',
            '193.168.182.193:8800',
            '38.153.160.187:8800',
            '193.168.182.130:8800',
            '38.153.192.80:8800',
            '80.65.222.167:8800',
            '154.9.54.83:8800',
            '38.153.160.178:8800',
            '80.65.222.195:8800',
            '38.153.160.41:8800'
        ]

        result_array = []
        batch_size = 12  # Số lượng proxy mỗi lần chạy
        total_proxies = len(proxy_list)
        proxy_index = 0  # Vị trí ban đầu của proxy trong danh sách

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            while proxy_index < total_proxies:

                # Tạo batch proxy cho lần chạy hiện tại
                proxy_batch = proxy_list[proxy_index:proxy_index + batch_size]
                brand_batch = input_array[proxy_index:proxy_index + batch_size]

                # Sử dụng ThreadPoolExecutor để chạy các tác vụ đồng thời
                results = list(executor.map(
                    check_brand, brand_batch, proxy_batch))
                result_array.extend(results)

                # Tăng biến đếm proxy_index
                proxy_index += batch_size

        result_json = json.dumps(result_array, indent=4)
        print(result_json)

    except Exception as _:
        with open("error.log", "w") as log_file:
            traceback.print_exc(file=log_file)


if __name__ == "__main__":
    main()

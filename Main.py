from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse
from datetime import datetime
import pytz


def get_firefox_driver(headless=True):
    firefox_options = FirefoxOptions()
    if headless:
        firefox_options.add_argument("-headless")
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    return driver


def bypass_age_gate(driver):
    try:
        if "agecheck" in driver.current_url:
            print("Age check detected. Attempting to bypass...")
            try:
                # Select date
                day_select = Select(WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'ageDay'))
                ))
                day_select.select_by_value('1')

                month_select = Select(WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'ageMonth'))
                ))
                month_select.select_by_value('January')

                year_select = Select(WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'ageYear'))
                ))
                year_select.select_by_value('1990')

                # Try multiple button selectors
                button_selectors = [
                    (By.ID, 'view_product_page_btn'),
                    (By.CLASS_NAME, 'btnv6_blue_hoverfade'),
                    (By.CLASS_NAME, 'age_gate_btn'),
                    (By.XPATH, '//a[contains(text(), "View Page")]')
                ]

                for selector in button_selectors:
                    try:
                        view_page_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable(selector)
                        )
                        view_page_button.click()
                        time.sleep(3)
                        print("Age check bypassed successfully.")
                        return True
                    except TimeoutException:
                        continue

                print("  - Failed to find any 'View Page' button.")
                return False
            except Exception as e:
                print(f"  - Error during age check bypass: {e}")
                return False
        else:
            print("No age check detected.")
            return True
    except Exception as e:
        print(f"  - General error in bypass_age_gate: {e}")
        return False


def extract_requirements(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    requirements_data = {}

    try:
        # First try to get organized tabs
        sysreq_tabs = soup.find('div', class_='sysreq_tabs')
        if sysreq_tabs:
            for tab in sysreq_tabs.find_all('div', class_='sysreq_tab'):
                os = tab.get('data-os')
                if os:
                    os = os.strip().lower()
                    requirements_data[os] = {'minimum': [], 'recommended': []}
                    content = soup.find('div', class_='game_area_sys_req', attrs={'data-os': os})

                    if content:
                        # Try to find requirements organized in columns
                        left_col = content.find('div', class_='game_area_sys_req_leftCol')
                        right_col = content.find('div', class_='game_area_sys_req_rightCol')

                        if left_col:
                            requirements_data[os]['minimum'] = [
                                li.get_text(" ", strip=True) for li in left_col.find_all('li')
                                if not any(x in li.get_text().lower() for x in ['expansion', 'soundtrack', 'artbook'])
                            ]

                        if right_col:
                            requirements_data[os]['recommended'] = [
                                li.get_text(" ", strip=True) for li in right_col.find_all('li')
                                if not any(x in li.get_text().lower() for x in ['expansion', 'soundtrack', 'artbook'])
                            ]

                        # If no columns found, look for full block
                        if not left_col and not right_col:
                            full_div = content.find('div', class_='game_area_sys_req_full')
                            if full_div:
                                # Split minimum and recommended by text
                                parts = re.split(r'(minimum:|recommended:)', full_div.get_text(), flags=re.IGNORECASE)
                                current = None
                                for part in parts:
                                    part = part.strip()
                                    if 'minimum:' in part.lower():
                                        current = 'minimum'
                                    elif 'recommended:' in part.lower():
                                        current = 'recommended'
                                    elif current and part:
                                        requirements_data[os][current].append(part)

        # If no organized tabs found, look in generic lists
        if not requirements_data:
            current_os = 'unknown'
            current_category = 'minimum'
            requirements_data[current_os] = {'minimum': [], 'recommended': []}

            # Look in requirements lists
            for elem in soup.find_all(['ul', 'div'], class_=['bb_ul', 'game_area_sys_req_full']):
                for item in elem.find_all(['li', 'p', 'strong']):
                    text = item.get_text(" ", strip=True)
                    if not text:
                        continue

                    # Detect category change
                    if re.search(r'minimum:', text, re.IGNORECASE):
                        current_category = 'minimum'
                        text = re.sub(r'minimum:', '', text, flags=re.IGNORECASE).strip()
                    elif re.search(r'recommended:', text, re.IGNORECASE):
                        current_category = 'recommended'
                        text = re.sub(r'recommended:', '', text, flags=re.IGNORECASE).strip()

                    # Detect OS change
                    os_match = re.search(r'(windows|mac|linux|steam os|os)', text, re.IGNORECASE)
                    if os_match and ':' in text:
                        current_os = os_match.group(1).lower()
                        if current_os not in requirements_data:
                            requirements_data[current_os] = {'minimum': [], 'recommended': []}
                        text = text.split(':', 1)[1].strip()

                    # Add if valid requirement
                    if text and len(text.split()) > 2 and not any(
                            x in text.lower() for x in ['expansion', 'soundtrack', 'artbook']):
                        requirements_data[current_os][current_category].append(text)

    except Exception as e:
        print(f" - Error extracting requirements: {e}")
        requirements_data = {'unknown': {'minimum': [], 'recommended': []}}

    return requirements_data


def extract_platforms(soup):
    """Extract supported platforms more robustly"""
    platforms = set()

    # 1. Check requirement tabs
    sysreq_tabs = soup.find('div', class_='sysreq_tabs')
    if sysreq_tabs:
        for tab in sysreq_tabs.find_all('div', class_='sysreq_tab'):
            os = tab.get('data-os')
            if os == 'win':
                platforms.add('windows')
            elif os == 'mac':
                platforms.add('macos')
            elif os == 'linux':
                platforms.add('linux')

    # 2. Check platform icons
    platform_icons = soup.find_all('div', class_='platform_img')
    for icon in platform_icons:
        class_list = icon.get('class', [])
        if 'win' in class_list:
            platforms.add('windows')
        if 'mac' in class_list:
            platforms.add('macos')
        if 'linux' in class_list:
            platforms.add('linux')
        if 'steamplay' in class_list:
            platforms.add('linux')  # Steam Play usually indicates Linux support

    # 3. Check page text
    page_text = soup.get_text().lower()
    if 'windows' in page_text:
        platforms.add('windows')
    if 'mac' in page_text or 'macos' in page_text:
        platforms.add('macos')
    if 'linux' in page_text or 'steam os' in page_text:
        platforms.add('linux')

    return sorted(platforms)


def extract_review_details(soup):
    """Extract detailed review information including positive/negative counts"""
    review_data = {
        "summary": None,
        "score": None,
        "total": None,
        "positive": None,
        "negative": None,
        "rating": None
    }

    # Extract from the review summary block
    review_block = soup.find('div', class_='user_reviews')
    if review_block:
        # Overall summary
        summary = review_block.find('span', class_='game_review_summary')
        if summary:
            review_data["summary"] = summary.get_text(strip=True)

        # Score and total reviews
        score = review_block.find('meta', itemprop='ratingValue')
        if score:
            review_data["score"] = score.get('content')

        count = review_block.find('meta', itemprop='reviewCount')
        if count:
            review_data["total"] = count.get('content')

        # Detailed positive/negative breakdown
        rating_text = review_block.get_text()
        positive_match = re.search(r'(\d+%?) of the (\d[\d,]+) user reviews', rating_text)
        if positive_match:
            review_data["positive"] = positive_match.group(1)
            review_data["total"] = positive_match.group(2).replace(',', '')

        # New Steam review format
        review_summary = review_block.find('div', class_='summary_section')
        if review_summary:
            rating_text = review_summary.get_text()
            matches = re.findall(r'(\d[\d,]+\s\w+)', rating_text)
            if len(matches) >= 2:
                review_data["positive"] = matches[0]
                review_data["negative"] = matches[1]

    return review_data


def extract_game_data(driver, url):
    """Complete game data extractor with all requested fields"""
    try:
        # Verify and extract app_id from URL
        parsed_url = urlparse(url)
        if not parsed_url.path.startswith('/app/'):
            print(f"  - Invalid Steam app URL: {url}")
            return None

        app_id = parsed_url.path.split('/')[2]
        if not app_id.isdigit():
            print(f"  - Invalid App ID in URL: {url}")
            return None

        # Access page and bypass age gate
        driver.get(url)
        if not bypass_age_gate(driver):
            print(f"  - Could not bypass age gate for {url}")
            return None

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Complete data structure
        game_data = {
            "basic_info": {
                "app_id": app_id,
                "url": url,
                "title": None,
                "developers": [],
                "publishers": [],
                "release_date": None,
                "price": {},
                "review_score": {}
            },
            "system_requirements": {},
            "metadata": {
                "genres": [],
                "popular_tags": [],
                "languages": {
                    "audio": [],
                    "interface": [],
                    "subtitles": []
                }
            },
            "content": {
                "short_description": None,
                "detailed_description": None,
                "dlc_count": 0
            },
            "media": {
                "header_image": None,
                "screenshots": [],
                "background_color": None
            },
            "technical": {
                "platforms": [],
                "controller_support": None,
                "vr_support": False
            },
            "timestamp": datetime.now(pytz.utc).isoformat()
        }

        # 1. Basic Info
        # Title
        title_elem = soup.find('div', id='appHubAppName') or soup.find('div', class_='apphub_AppName')
        if title_elem:
            game_data["basic_info"]["title"] = title_elem.get_text(strip=True)

        # Developers and Publishers
        dev_rows = soup.find_all('div', class_='dev_row')
        for row in dev_rows:
            label = row.find('b').get_text(strip=True).lower() if row.find('b') else ""
            if 'developer' in label:
                game_data["basic_info"]["developers"] = [a.get_text(strip=True) for a in row.find_all('a')]
            elif 'publisher' in label:
                game_data["basic_info"]["publishers"] = [a.get_text(strip=True) for a in row.find_all('a')]

        # Release Date
        date_elem = soup.find('div', class_='date')
        if date_elem:
            game_data["basic_info"]["release_date"] = date_elem.get_text(strip=True)

        # Price
        price_data = {}
        discount_block = soup.find('div', class_='discount_block')
        if discount_block:
            final_price = discount_block.find('div', class_='discount_final_price')
            if final_price:
                price_data["current"] = final_price.get_text(strip=True)

            original_price = discount_block.find('div', class_='discount_original_price')
            if original_price:
                price_data["original"] = original_price.get_text(strip=True)

            discount_pct = discount_block.find('div', class_='discount_pct')
            if discount_pct:
                try:
                    price_data["discount_pct"] = int(re.search(r'\d+', discount_pct.get_text()).group())
                except:
                    price_data["discount_pct"] = 0
        else:
            price_block = soup.find('div', class_='game_purchase_price price')
            if price_block:
                price_data["current"] = price_block.get_text(strip=True)
                price_data["original"] = None
                price_data["discount_pct"] = 0

        game_data["basic_info"]["price"] = price_data

        # Reviews - Enhanced version
        game_data["basic_info"]["review_score"] = extract_review_details(soup)

        # 2. System Requirements
        game_data["system_requirements"] = extract_requirements(driver.page_source)

        # 3. Metadata
        # Genres
        game_data["metadata"]["genres"] = [
            genre.get_text(strip=True) for genre in soup.select('div.details_block a[href*="/genre/"]')
        ]

        # Popular Tags (limit to 20)
        game_data["metadata"]["popular_tags"] = [
                                                    tag.get_text(strip=True) for tag in
                                                    soup.select('div.glance_tags.popular_tags a')
                                                ][:20]

        # Languages
        lang_table = soup.find('table', class_='game_language_options')
        if lang_table:
            for row in lang_table.find_all('tr')[1:]:  # Skip header
                cells = row.find_all('td')
                if len(cells) >= 4:
                    lang = cells[0].get_text(strip=True)
                    if cells[1].find('span', class_='check'):
                        game_data["metadata"]["languages"]["interface"].append(lang)
                    if cells[2].find('span', class_='check'):
                        game_data["metadata"]["languages"]["audio"].append(lang)
                    if cells[3].find('span', class_='check'):
                        game_data["metadata"]["languages"]["subtitles"].append(lang)

        # 4. Content
        # Short Description
        short_desc = soup.find('div', class_='game_description_snippet')
        if short_desc:
            game_data["content"]["short_description"] = short_desc.get_text(strip=True)

        # Detailed Description
        detailed_desc = soup.find('div', class_='game_area_description')
        if detailed_desc:
            game_data["content"]["detailed_description"] = str(detailed_desc)

        # DLC Count
        dlc_items = soup.select('div.dlc_item')
        if dlc_items:
            game_data["content"]["dlc_count"] = len(dlc_items)

        # 5. Media
        # Header Image
        header_img = soup.find('img', class_='game_header_image_full')
        if header_img:
            game_data["media"]["header_image"] = header_img.get('src')
            # Background color from style if exists
            style = header_img.get('style', '')
            if 'background-color:' in style:
                game_data["media"]["background_color"] = style.split('background-color:')[-1].split(';')[0].strip()

        # Screenshots
        screenshots = soup.select('div.highlight_strip_screenshot img')
        if screenshots:
            game_data["media"]["screenshots"] = [
                img.get('src').replace('116x65', '1920x1080') for img in screenshots
            ]

        # 6. Technical Info
        # Platforms
        game_data["technical"]["platforms"] = extract_platforms(soup)

        # Controller Support
        if soup.find('div', class_='game_area_details_specs', string=re.compile('Full Controller Support')):
            game_data["technical"]["controller_support"] = "Full"
        elif soup.find('div', class_='game_area_details_specs', string=re.compile('Partial Controller Support')):
            game_data["technical"]["controller_support"] = "Partial"

        # VR Support
        game_data["technical"]["vr_support"] = bool(
            soup.find('div', class_='game_area_details_specs', string=re.compile('VR')) or
            soup.find('a', href=re.compile('vr', re.IGNORECASE))
        )

        return game_data

    except Exception as e:
        print(f"  - Error extracting data: {e}")
        return None


if __name__ == "__main__":
    driver = get_firefox_driver(headless=True)

    test_urls = [
        "https://store.steampowered.com/app/730/CounterStrike_2/",
        "https://store.steampowered.com/app/1086940/Baldurs_Gate_3/",
        "https://store.steampowered.com/app/1245620/ELDEN_RING/"
    ]

    all_games_data = []

    for url in test_urls:
        print(f"\nProcessing: {url}")
        game_data = extract_game_data(driver, url)
        if game_data:
            all_games_data.append(game_data)
            output_filename = f"steam_data_{game_data['basic_info']['app_id']}.json"
            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(game_data, f, indent=2, ensure_ascii=False)
                print(f"  - Successfully saved data to {output_filename}")
            except Exception as e:
                print(f"  - Error saving file: {e}")

        time.sleep(5)  # Larger interval to avoid blocks

    driver.quit()

    # Save all data to single file
    with open("all_steam_games_data.json", 'w', encoding='utf-8') as f:
        json.dump(all_games_data, f, indent=2, ensure_ascii=False)

    print("\nScraping completed! Data saved to JSON files.")
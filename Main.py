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
                # -- Select date using Select class --
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

                # -- Try multiple button selectors --
                button_selectors = [
                    (By.ID, 'view_product_page_btn'),
                    (By.CLASS_NAME, 'btnv6_blue_hoverfade'),
                    (By.CLASS_NAME, 'age_gate_btn'),  # Generic class
                    (By.XPATH, '//a[contains(text(), "View Page")]')  # Text-based
                ]

                for selector in button_selectors:
                    try:
                        view_page_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable(selector)
                        )
                        view_page_button.click()
                        time.sleep(3)  # Wait for page load
                        print("Age check bypassed successfully.")
                        return True
                    except TimeoutException:
                        print(f"  - Button not found with selector: {selector}")
                        continue  # Try the next selector

                print("  - Failed to find any 'View Page' button.")
                return False

            except Exception as e:
                print(f"  - Error during age check bypass: {e}")
                return False

        else:
            print("No age check detected.")
            return True  # No age check, so bypass is "successful"

    except Exception as e:
        print(f"  - General error in bypass_age_gate: {e}")
        return False


def extract_requirements(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    requirements_data = {}

    try:
        sysreq_tabs = soup.find('div', class_='sysreq_tabs')
        if sysreq_tabs:
            for tab in sysreq_tabs.find_all('div', class_='sysreq_tab'):
                os = tab.get('data-os')
                if os:
                    os = os.strip().lower()
                    requirements_data[os] = {'minimum': [], 'recommended': []}
                    content = soup.find('div', class_='game_area_sys_req', attrs={'data-os': os})
                    if content:
                        left_col = content.find('div', class_='game_area_sys_req_leftCol')
                        right_col = content.find('div', class_='game_area_sys_req_rightCol')
                        full_div = content.find('div', class_='game_area_sys_req_full')

                        if left_col:
                            requirements_data[os]['minimum'] = [
                                li.text.strip() for li in left_col.find_all('li')
                            ]
                        if right_col:
                            requirements_data[os]['recommended'] = [
                                li.text.strip() for li in right_col.find_all('li')
                            ]
                        elif full_div:
                            requirements_data[os]['minimum'] = [
                                li.text.strip() for li in full_div.find_all('li')
                            ]
        else:
            os_sections = {'unknown': {'minimum': [], 'recommended': []}}
            current_os = 'unknown'
            current_category = 'minimum'
            for list_elem in soup.find_all(['ul', 'div'], class_='bb_ul') or soup.find_all(['ul', 'div']):
                for item in list_elem.find_all(['li', 'p']):
                    text = item.text.strip()
                    if re.search(r'minimum:', text, re.IGNORECASE):
                        current_category = 'minimum'
                        text = re.sub(r'minimum:', '', text, flags=re.IGNORECASE).strip()
                    elif re.search(r'recommended:', text, re.IGNORECASE):
                        current_category = 'recommended'
                        text = re.sub(r'recommended:', '', text, flags=re.IGNORECASE).strip()
                    elif re.search(r'(windows:|mac(os)?(:)?|linux:)', text, re.IGNORECASE):
                        match = re.search(r'(windows:|mac(os)?(:)?|linux:)', text, re.IGNORECASE)
                        if match:
                            current_os = match.group(1).replace(':', '').strip().lower()
                            os_sections.setdefault(current_os, {'minimum': [], 'recommended': []})
                        text = re.sub(r'(windows:|mac(os)?(:)?|linux:)', '', text, flags=re.IGNORECASE).strip()
                    if text:
                        os_sections[current_os][current_category].append(text)
            requirements_data = os_sections or "N/A"

    except Exception as e:
        print(f" - Error: {e}")
        requirements_data = "N/A"

    return requirements_data


def format_requirements_output(requirements):
    output = ""
    if requirements == "N/A":
        return "System Requirements: N/A"

    for os, specs in requirements.items():
        output += f"\n--- {os.capitalize()} ---\n"

        if isinstance(specs, dict):  # Check if specs is a dictionary
            if specs['minimum']:
                output += "Minimum:\n"
                for req in specs['minimum']:
                    output += f"- {req}\n"
            else:
                output += "Minimum: N/A\n"

            if specs['recommended']:
                output += "Recommended:\n"
                for req in specs['recommended']:
                    output += f"- {req}\n"
            else:
                output += "Recommended: N/A\n"
        elif isinstance(specs, list):  # If specs is a list (no min/rec separation)
            output += "Requirements:\n"
            for req in specs:
                output += f"- {req}\n"
        else:
            output += f"{specs}\n"  # Print directly if it's a string or other type

    return output


if __name__ == "__main__":
    driver = get_firefox_driver(headless=True)
    urls = [
        "https://store.steampowered.com/app/227300/Euro_Truck_Simulator_2/",
        "https://store.steampowered.com/app/1127400/Mindustry/",
        "https://store.steampowered.com/app/281990/Stellaris/",
        "https://store.steampowered.com/app/413150/Stardew_Valley/",
        "https://store.steampowered.com/app/105600/Terraria/",
        "https://store.steampowered.com/app/550/Left_4_Dead_2/",
        "https://store.steampowered.com/app/108600/Project_Zomboid/"
    ]

    for url in urls:
        try:
            print(f"\nProcessing: {url}")
            driver.get(url)
            if not bypass_age_gate(driver):
                print(f"  - Could not bypass age gate for {url}. Skipping.")
                continue

            # Extrair o HTML da página
            page_source = driver.page_source
            requirements = extract_requirements(page_source)
            formatted_output = format_requirements_output(requirements)
            print(formatted_output)

            if url == "https://store.steampowered.com/app/108600/Project_Zomboid/":
                with open("Offline - Tests/project_zomboid_page_source.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                print("  - Page source saved to project_zomboid_page_source.html")

        except Exception as e:
            print(f"  - Error processing {url}: {e}")
        finally:
            time.sleep(2)  # Intervalo entre requisições

    driver.quit()
    print("\nScraping completed!")
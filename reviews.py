from bs4 import BeautifulSoup
import re

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
            current_category = 'minimum'  # Definindo valor padrão
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
    if requirements == "N/A":
        return "System Requirements: N/A"

    output = ""
    for os, specs in requirements.items():
        output += f"\n--- {os.capitalize()} ---\n"
        if isinstance(specs, dict):
            for category in ['minimum', 'recommended']:
                if specs[category]:
                    output += f"{category.capitalize()}:\n"
                    output += "\n".join(f"- {req}" for req in specs[category]) + "\n"
                else:
                    output += f"{category.capitalize()}: N/A\n"
        elif isinstance(specs, list):
            output += "Requirements:\n"
            output += "\n".join(f"- {req}" for req in specs) + "\n"
        else:
            output += f"{specs}\n"
    return output

# --- Main execution ---
html_content = """
<div class="game_page_autocollapse sys_req" style="max-height: none;">
  <h2>System Requirements</h2>
  <div class="sysreq_tabs">
  <div class="sysreq_tab active" data-os="win">
  Windows
  </div>
  <div class="sysreq_tab " data-os="mac">
  macOS
  </div>
  <div class="sysreq_tab " data-os="linux">
  SteamOS + Linux
  </div>
  <div style="clear: left;"></div>
  </div>
  <div class="sysreq_contents">
  <div class="game_area_sys_req sysreq_content active" data-os="win">
  <div class="game_area_sys_req_full">
  <ul>
  <strong>Minimum:</strong><br><ul class="bb_ul"><li><strong>OS *:</strong> Windows Vista or greater<br></li><li><strong>Processor:</strong> 2 Ghz<br></li><li><strong>Memory:</strong> 2 GB RAM<br></li><li><strong>Graphics:</strong> 256 mb video memory, shader model 3.0+<br></li><li><strong>DirectX:</strong> Version 10<br></li><li><strong>Storage:</strong> 500 MB available space</li></ul>
  </ul>
  </div>
  <div style="clear: both;"></div>


  <div class="game_area_sys_req_note">
  <strong>*</strong>
  Starting January 1st, 2024, the Steam Client will only support Windows 10 and later versions.
  </div>
  </div>
  <div class="game_area_sys_req sysreq_content " data-os="mac">
  <div class="game_area_sys_req_full">
  <ul>
  <strong>Minimum:</strong><br><ul class="bb_ul"><li><strong>OS:</strong> Mac OSX 10.10+<br></li><li><strong>Processor:</strong> 2 Ghz<br></li><li><strong>Memory:</strong> 2 GB RAM<br></li><li><strong>Graphics:</strong> 256 mb video memory, OpenGL 2<br></li><li><strong>Storage:</strong> 500 MB available space</li></ul>
  </ul>
  </div>
  <div style="clear: both;"></div>


  </div>
  <div class="game_area_sys_req sysreq_content " data-os="linux">
  <div class="game_area_sys_req_full">
  <ul>
  <strong>Minimum:</strong><br><ul class="bb_ul"><li><strong>OS:</strong> Ubuntu 12.04 LTS<br></li><li><strong>Processor:</strong> 2 Ghz<br></li><li><strong>Memory:</strong> 2 GB RAM<br></li><li><strong>Graphics:</strong> 256 mb video memory, OpenGL 2<br></li><li><strong>Storage:</strong> 500 MB available space</li></ul>
  </ul>
  </div>
  <div style="clear: both;"></div>


  </div>
  </div>
  </div>
"""

requirements = extract_requirements(html_content)
formatted_output = format_requirements_output(requirements)
print(formatted_output)
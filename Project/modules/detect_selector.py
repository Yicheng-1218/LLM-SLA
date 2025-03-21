from playwright.sync_api import sync_playwright

def get_unique_selector(element):
    """根據 Playwright ElementHandle 產生唯一的 CSS 選擇器"""
    selectors = []
    
    while element:
        tag = element.evaluate("el => el.tagName.toLowerCase()")
        parent = element.query_selector("xpath=..")

        if parent:
            # 取得所有相同標籤的兄弟元素
            siblings = parent.query_selector_all(f"{tag}")
            siblings = list(siblings)  

            # 轉換為 outerHTML，避免 JSHandle 比較失敗
            element_html = element.evaluate("el => el.outerHTML")
            siblings_html = [s.evaluate("el => el.outerHTML") for s in siblings]

            if element_html in siblings_html:
                index = siblings_html.index(element_html) + 1
                # 只有當兄弟數量 > 1 才加 nth-of-type(n)
                if len(siblings_html) > 1:
                    selectors.insert(0, f"{tag}:nth-of-type({index})")
                else:
                    selectors.insert(0, tag)
            else:
                selectors.insert(0, tag)
        
        element = parent  # 繼續向上尋找父元素

    return " > ".join(selectors)


def detect_input_selector(url):
    """自動偵測輸入框選擇器"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector('textarea')
        input_selector = None
        possible_inputs = page.query_selector_all("textarea, input[type='text'], [contenteditable='true']")
        for input_el in possible_inputs:
            if input_el.is_visible():
                input_selector = get_unique_selector(input_el)
        if not input_selector:
            raise Exception("No visible input element found")
        page.close()
        browser.close()
        return input_selector
        
import os, time, sys, re
sys.stdout.reconfigure(encoding="utf-8")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
opts.add_argument("--no-sandbox")
opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
url = "file:///" + os.path.abspath("MPMRI_PROSTATE_DTA_REVIEW.html").replace("\\", "/")

driver = webdriver.Chrome(options=opts)
try:
    driver.get(url)
    time.sleep(3)
    # Click Summary tab to render the cards
    summary_btns = driver.find_elements("css selector", "button[data-tab='summary']")
    if summary_btns:
        summary_btns[0].click()
        time.sleep(1.0)
    tc = driver.execute_script("return document.getElementById('tier-cards') ? document.getElementById('tier-cards').innerHTML : '';")
    print("TIER_CARDS_LEN:", len(tc))
    miss = driver.execute_script("return document.getElementById('cspca-miss-rate-card') ? document.getElementById('cspca-miss-rate-card').innerHTML : '';")
    print("MISS_CARD_LEN:", len(miss))
    print("MISS_HEADLINE_PRESENT:", "csPCa miss rate" in miss)
    m = re.search(r"pooled probability of harbouring csPCa is <strong>([\d.]+%)</strong>", miss)
    print("POOLED_MISS_RATE:", m.group(1) if m else "NOT FOUND")
    m2 = re.search(r"95% CI ([\d.]+%)[^\d]+([\d.]+%)", miss)
    print("CI:", (m2.group(1), m2.group(2)) if m2 else "NOT FOUND")
    hb = driver.execute_script("return document.getElementById('headline-banners') ? document.getElementById('headline-banners').innerHTML : '';")
    print("HEADLINE_BANNER_LEN:", len(hb))
    print("HEADLINE_DIVLOGLR_PRESENT:", "log(LR" in hb)
    # Tab clicks: walk through 17 tabs
    tabs = driver.find_elements("css selector", ".tab-button")
    print("TAB_COUNT:", len(tabs))
    for t in tabs:
        try:
            label = t.text.strip().split(".")[0]
            t.click()
            time.sleep(0.15)
        except Exception as e:
            print("TAB_CLICK_FAIL:", t.text, e)
    # Methods + References spot-check
    methods_btn = driver.find_elements("css selector", "button[data-tab='methods']")
    if methods_btn:
        methods_btn[0].click()
        time.sleep(0.3)
    methods_html = driver.execute_script("return document.getElementById('tab-methods').innerHTML")
    print("METHODS_HAS_DROST:", "Drost" in methods_html)
    print("METHODS_HAS_OERTHER:", "Oerther" in methods_html)
    print("METHODS_HAS_CC_BIAS:", "Bias-toward-null caveat" in methods_html)
    print("METHODS_HAS_IMPERFECT_REF:", "imperfect reference" in methods_html.lower())
    refs_btn = driver.find_elements("css selector", "button[data-tab='references']")
    if refs_btn:
        refs_btn[0].click()
        time.sleep(0.3)
    refs_html = driver.execute_script("return document.getElementById('tab-references').innerHTML")
    print("REFS_HAS_DROST:", "Drost" in refs_html and "10.1016/j.eururo.2019.06.023" in refs_html)
    print("REFS_HAS_OERTHER:", "Oerther" in refs_html and "10.1038/s41391-021-00417-1" in refs_html)
    print("REFS_HAS_WHITING:", "Whiting" in refs_html and "QUADAS-2" in refs_html)
    print("REFS_HAS_DENDUKURI:", "Dendukuri" in refs_html)
    # Heterogeneity tab CC caveat
    het_btn = driver.find_elements("css selector", "button[data-tab='heterogeneity']")
    if het_btn:
        het_btn[0].click()
        time.sleep(0.3)
    het_html = driver.execute_script("return document.getElementById('tab-heterogeneity').innerHTML")
    print("HET_HAS_CC_CAVEAT:", "Continuity-correction bias-toward-null" in het_html)
    # Search PRISMA-DTA
    search_btn = driver.find_elements("css selector", "button[data-tab='search']")
    if search_btn:
        search_btn[0].click()
        time.sleep(0.3)
    search_html = driver.execute_script("return document.getElementById('tab-search').innerHTML")
    print("SEARCH_HAS_PRISMA_DTA:", "PRISMA-DTA" in search_html)
    # Subgroups dropdown IDs
    sub_btn = driver.find_elements("css selector", "button[data-tab='subgroups']")
    if sub_btn:
        sub_btn[0].click()
        time.sleep(0.3)
    sub_html = driver.execute_script("return document.getElementById('tab-subgroups').innerHTML")
    print("SUB_HAS_PRIOR_BIOPSY:", "sg-prior-biopsy-history" in sub_html)
    print("SUB_NO_HIV:", "sg-hiv-status" not in sub_html)
    print("SUB_NO_SMEAR:", "sg-smear-status" not in sub_html)
    # Plain-language tab spot-check
    plain_btn = driver.find_elements("css selector", "button[data-tab='plain']")
    if plain_btn:
        plain_btn[0].click()
        time.sleep(0.3)
    plain_html = driver.execute_script("return document.getElementById('tab-plain').innerHTML")
    print("PLAIN_HAS_MPMRI_GLOSS:", "Multiparametric MRI (mpMRI)</strong> is a special prostate scan" in plain_html)
    print("PLAIN_HAS_PIRADS_GLOSS:", "1&ndash;2 means cancer is unlikely" in plain_html or "1–2 means cancer is unlikely" in plain_html)
    print("PLAIN_HAS_CSPCA_GLOSS:", "clinically significant prostate cancer (csPCa)" in plain_html)
    print("PLAIN_LEADS_BOTTOM_LINE:", "The bottom line for you" in plain_html)
    print("PLAIN_HAS_BIOPSY_AVOID:", "biopsy" in plain_html and "negative mpMRI" in plain_html)
    print("PLAIN_HAS_AS_EXCLUSION:", "active-surveillance" in plain_html)
    print("PLAIN_HAS_MRI_CONTRA:", "MRI-contraindication" in plain_html or "claustrophobia" in plain_html)
    # Switch tier to combined and re-check
    summary_btns2 = driver.find_elements("css selector", "button[data-tab='summary']")
    if summary_btns2:
        summary_btns2[0].click()
        time.sleep(0.4)
    radio_combined = driver.find_elements("css selector", "input[name='tier'][value='combined']")
    if radio_combined:
        driver.execute_script("arguments[0].click();", radio_combined[0])
        time.sleep(1.0)
        miss2 = driver.execute_script("return document.getElementById('cspca-miss-rate-card').innerHTML")
        m3 = re.search(r"pooled probability of harbouring csPCa is <strong>([\d.]+%)</strong>", miss2)
        print("COMBINED_TIER_POOLED:", m3.group(1) if m3 else "NOT FOUND")
    logs = driver.get_log("browser")
    err = [l for l in logs if l["level"] == "SEVERE"]
    print("SEVERE_ERRORS:", len(err))
    for e in err[:8]:
        print("  -", e.get("message", "")[:250])
finally:
    driver.quit()

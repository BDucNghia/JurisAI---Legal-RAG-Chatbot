from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import random
import re

BASE_URL = "https://luatvietnam.vn/tim-van-ban.html?Keywords=thu%u1ebf+thu+nh%u1eadp+c%u00e1+nh%u00e2n&SearchOptions=1&SearchByDate=IssueDate&DateFrom=&DateTo=&lDocTypeId=11%2c21&OrganId=0&lEffectStatusId=4%2c2&lFieldId=4&LanguageId=1&SignerId=0&pSize=52&page=1"
MAX_PAGES = 1# Tăng nếu muốn tải nhiều trang
START_PAGES = 1
cookies = [
    {"name": "_clck", "value": "1xuac6x%7C2%7Cfxh%7C0%7C2012", "domain": ".luatvietnam.vn"},
    {"name": "_clsk", "value": "a4sbn5%7C1752140170835%7C51%7C0%7Cy.clarity.ms%2Fcollect", "domain": ".luatvietnam.vn"},
    {"name": "_fbp", "value": "fb.1.1751727020434.540834646470119749", "domain": ".luatvietnam.vn"},
    {"name": "_ga", "value": "GA1.2.1842713378.1751542305", "domain": ".luatvietnam.vn"},
    {"name": "_ga_2GQESC9SL5", "value": "GS2.1.s1752138198$o13$g1$t1752140170$j46$l1$h606178095", "domain": ".luatvietnam.vn"},
    {"name": "_ga_DZNHRSYZR1", "value": "GS2.1.s1752070027$o3$g0$t1752070027$j60$l0$h0", "domain": ".luatvietnam.vn"},
    {"name": "_ga_EW2DZ6FMZM", "value": "GS2.2.s1751964490$o2$g1$t1751967084$j60$l0$h0", "domain": ".luatvietnam.vn"},
    {"name": "_ga_ZWHEHZ2EHL", "value": "GS2.1.s1751964490$o2$g1$t1751967084$j60$l0$h2127619635", "domain": ".luatvietnam.vn"},
    {"name": "_gat_UA-10721740-4", "value": "1", "domain": ".luatvietnam.vn"},
    {"name": "_gid", "value": "GA1.2.1114992159.1751964486", "domain": ".luatvietnam.vn"},
    {"name": "_hjSession_5192214", "value": "eyJpZCI6IjdhYWRmNThmLWQzNzYtNDJiMS1hMzBhLTI4NDIwNjcyM2YzOCIsImMiOjE3NTIxMzgxOTc5OTMsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=", "domain": ".luatvietnam.vn"},
    {"name": "_hjSessionUser_5192214", "value": "eyJpZCI6Ijg4YzU5ZDIwLTIwMDUtNTUxNy04NTY1LTIwNDA3NzdlYTM4ZSIsImNyZWF0ZWQiOjE3NTE3MjcwMjA3ODQsImV4aXN0aW5nIjp0cnVlfQ==", "domain": ".luatvietnam.vn"},
    {"name": ".LuatVietNamSSO", "value": "CfDJ8PEAieo9QK1CubjiVO12CoAr6976rnJvO_Fe1uuc1hwxNpi_bO4QjdO-XjbL2PesZdETwlTeH1aOth2fZCLb4dVaei9jkxXmaUn12qjLiYbncCURabsuYkpxm1nXgzw6miX_Njf3U575CiKEFYE1rOs8wmFL_O1GgWB6ZHCrWqMlrcoE4mjq2NrLNwVjeYdDNkIdcLuT6AcI6kfgj_4-IHpO-icmb_-YFBljaxP_iIY20upw0eSN2T9b23-4J1B9DDFiNdziWXGnE6nUZ5erncL6Y7k9OScyRbHSzhRc3Uef1dWt1KqF2tMr_BdLUIkQkGGJ_pEcURfifxeXoadIrqSjMET5sbdGMLCB_PMhl9b4IcXMzs9qa7LGpyEUhmRwZnjFlME-3LfL1rNDi8cINhV71OnzpJJCgBV-7TnND30o90CPdrtpDpzda10UhYg1n2R-Gc8pQw6M5XTar-2gvWOgLMXKSeA6EaYMYQoLfceg2uMGg_yTQ_gw7ia46cGebP4-XKInDBTCc-QHmKcSNZNudEQTTRxqC8UJG50qp_VbCaNTLLdmlV5xhiN78YveSweCDqmPzDs1cJ_EYa4iLvKZo_dkTagRzEQjTd-Y96xqmV9Bd5SbQnGK5qjm7PZNmVnytMwWm4xoWxlKkXKTbBn4CcO-qSewZtPti8ZSp7cSHhqebpZQbdlnF-LTfVo6D7FtuIw5mAJvCvqbA16p4iSfvSI2WoER7ISZxb2kuLBDgmSIpJ9R4h7ymiiiSAacRk4Skks4wgz6DOFKVhL3VtIvVudfEghXbqwaWyxpuaWdD644vPKRGe5Ppbz-nf9J5lFBgIRSeRtWMebXsQVeCQVO7jHLBr20uLuL_RX-jU6QI4UqSFUaeULHjm40FK7S8NxlmRnRwpJVBWsOL0Zq-dD9yYRWqzAKXClQpFTm0Uu-qw4xs1luam7AmGMbNPKkcwRsxdQJbOoT-3H36Brxlt_cvkJ9oRqrb4XFW9LJH48I2122yQV-nwcdbR5bvEcgduxVutiu9j4KtxgtCf58vJT7tZZlYeBfL3RSrBPJR4UlgLxpLaat6sl8YzvXeaKutlcpaqV8j-kclmZGL1tpr4g-sGj-XKWhWcTpGUOkijB-oF8TQp0bx6LUxjQEwg6CKZIwpqIHrCaC7JBunh6f_4csKa8sdQ6CHyDNQF8YIBWz0LOTwKU7SkTbuSIlzUyGTWq7IrvFo3iA20OeLF8_qiDSDHHm07IAar_XPqsvVMF8KJXsP-XR6wlukRRcFWqbP67e22nJJdzsJ5je5XCnDiCoSgFPYIMUNZnhbKJCp1mK4XpYf_AK0n6DdgweCwbkDjEOz7ETDdlLZlMcFpajsHA481aPYcgadlgw8CxRKCChipQd6AqA09M316fOX3rJMQiyNLwGl_-p89bUtDE0_fqCq00ApoDAYvtKuDLtEr9Q3GVIkQjPWGaMLPYibgj7h99oAeJNPPYyIMgKg7drIcxbzxy25zWHz_Ya91W4rPdV59popMBlXJmzkJ2OVeA_COCcvqYxZmAPb5D45E2qdz0s9gsArmgRn4TYC3QUbslAZXh7_ylZNLE9CuzX3DJYv4NyABZ2ZBCFitpkcZ4MnsigNs29WGsL6qXCTuOZIuRnGL--3y1zrDLsDwlFTAU5kE9ELEu5P3hAIdprVZrjjjdmcweU5TJmnMBZ4CN9zck8eu-PBB5MWdE93PV9lOEeSgvrZx9rkTiKOwkeojKYhtVfaVOItwZX_vHsVxAJvE6-nWGBbz2fRdfXB8AqqqLQQzMck3ggZqa0RL2SXRE3hV8", "domain": ".luatvietnam.vn"},
    {"name": "LAWSVN_AUTH", "value": "83F94BD8D7029159F6F7526BA324AEC544A29E480E7C417570E492983B1062A6E559AF63B75DAD309A3B3DDB43CB41ED8FADE4443161661CFF3735AD840FE7212F2BCE509474D0AF6816BC0587D6B9F1B0D9CBB8F4E1C68B679B9510159D2ABF0147CFA30754B3108E048F8BC55CFF83AFBA2F862661A187AF3591DCFF3ECB81AD13AE9FE161D2FF056B2A47CF6663CB28B2EC55FD80F26A0C5B877A0945B883D355E1F0250A237EA621B3C121C4A95D8265959722D583D40FBFFB2A34E6591E1B4CAA313710E4C0C2D0CCDE8447CDDDB5EBF8B6CB294B022CCC7B8BEC16A3BA7E0394556960D82C66E7AB1CD27D4059AAEA9D80361729A7F66CEB029AD3C324183290BAB0000AD0F0D40EB8A952F43D515B244CE10A141AAB0BD3AEEB4A1BF38A218EF36A1C09672FDAE50D042253576F6025F3971647BF831ED054C0DF95F803A6C67D491BE3918465FF7CB3ABED5F19A85D1E188D128B14C870E6C82DB6C894D203E9BFF45BA3ACE0E865B5EA62202DA4BB135691903BA0204716E81725215557D059CA6D0F92A236630B2D277C05996AC5A5900DEFB5352E6F775DF5F95F414DBF7EF89BAAE83E0091D7B29B3AFFD451306D5118AA52D21ED25810D31DC6E8519EAC2E9B335F8CBC6080CF09FD3526196252D230C2C447B85D7CE8D10F3CAE9782DE797002A92029C44036BD0B6220847B41618331AAD4DA326A7A18D9F9FCE33391E9CDD670432C5F7E1DB8EE6D06989C425255D10C6370F7A97E8805346F604A8C6AD84B69F5E8DD3CEB2A860C6BE1CC1F56E7442CAFE2283C967D5009417B48E9AA4EC626A7351790C24F522946AF484329E632265933AC4B2E6E881FDE3ABC7CA21501AAA5B7642C55954E7228F29F7EB0F0B90E35DA62951B84D8ABF97B01074D3BB329E1455ECDAB0AFBA3FCD1EBE5EC914C9D359F09FF0AAEABE5A19626E48073BCED221961B7602CD416789BD8B272403420CF93A6F0C9554A10D3DE4935668A8292E3EDCE49E42A2BB0A5296C6B50AB1643F50F5D183D0EAF25FBE5FB5038681DE281402F7F757C5BD98F3C9698420403FB74DE4FBF5797057DBFB36C95A88BF8D797FDC52D9AA8BD5E2C7DEF6207B8289844200628A257F098BBABEBE8CA80C56BF85E5B2DA9CC69C83B2ABB2AA5FCB1C421FA4B1A4839A5A5EDE2063089CBA571B323692445A8A2224E8498558832B7A297BB9D631F9552054190E0A2DF55C64A441C7C5E6338D35FC46D26B28128B4BB66BCF4AA0259A3F243ED11C547CD6FE6CD8AAC70663BEAB9027A2BFC206FD589DA67E7C69F2B79C99554901D7F1CE24D4553086C52EBCB4FB64B9F6FB11C37A5EC6C4C5E759BAA9A01C2D3307BFEA2C43CF91F384AF291088B655BFCC6A48D37DD5819D23E86149155C86BB4AEA06F2ECB86D0029DE2FF93B4F32E06DD0BCCD81C4928985B3E951A186393E954B77EFFBAD31818D762DC15F24DF2F07BA19AF81A9EE8E760609D4A69F69BF0AB22BBF3EC3BCD054BFC566F0F2DFA5F50F7AFE9F246B1AC38796A1BB14C42E69F6F930AA9F353F7D972A3E85134829A3673D217B991BB23E38B61BBDECE482F390391EC8DB8A0872397FC80E02F24100C916D4576B343F21E6BC16F0BF4C2CF7A61A1B9B39777F48C222A100F69C433F3E92356A51E4723533C22EB5F2063DC2F5BA9E5F965D10B884F118475F95DE4BA7F26FDD1481AC2B81EF059F027C057EA608C593C0E3347294F4CF2CAA19AB38438E65FBC7A84B7950D4C2EF6DA14357045C1B69468621E64CBE51EB9FEC0E4D178BD6A7A79D3EFFF9BF0D11335B5D88F0E5489385BFF5EF2117D544EEC4CEC2A0B20862D0B9F6D481864A5E14DEE697A6693CA09B19C13BBAB9C437D63422E0ED16A82C64758EF38E36D5DC73663F3C132117B8A59CACED01B7D4B2807BF7F4A223207A056A74193EC7320F1654ED6BA78A00B52551E84BC1A213F5821D3D7B700CC3B52D63C20FE8B989FC82B0019F8F301C397290485662358B8953AFC589D7A269E0CA9FFE385283FD214C9950963FE9DFAD1D5B2D13FE4A49F76FECDF01422BDD9755316ECB5DB3B2CE5289EE6F9F32B16606B6BAE1618BAEBB2AC3ABF7899929410DD52D4D24025007B0FD75430632E8447523A19D733FF4C1A23B1B6BDE631E8995E64D395AA513203B59CF0DBBD5D2B2176B63AC17D59534AC52AB68EB6974D5FBA9EBE2FCF6BE51C764A85006FFEF590F54F38CB5E057CF9BFD99DE6A9AD81BF1C5B04EFEEC3F6D0899042E6257B8649392F12D158D7EA62E67FA7F466F6E95F4C3CDCC90655F09B4E974246D77D9D6399617004DD1B54E84BEB639D052FBDA0EC760E5A87607139F9DC6A71122453E97AD9AA43AE53F6E7C1ABB4F1FF221032819E1527D09CC4D5747941025B5DE7E1D8D50F37FB6E0E62055528167BD6AD4A53D5136E27B52919384CD5A59A9665EB376C2BB1265595CFC97644316FD9F4E4AC3AD159AE01317CF731B1", "domain": ".luatvietnam.vn"},
    {"name": "LuatVietnamShare", "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJDdXN0b21lcklkIjoiMTExMjgwNCIsIlBhcnRuZXJJZCI6IjAiLCJTZXNzaW9uSWQiOiI1NzkyNWE0OS1hNWJiLTQzMGQtYWYwMC0xMzc2MTkxMDdiOGQiLCJleHAiOjE3NTIwNTI1NjgsImlzcyI6Imh0dHBzOi8vYWlsdWF0Lmx1YXR2aWV0bmFtLnZuLyJ9.4vqKAK0Dx0_L_4xFTaeZGKJvvwnn0_xz3BKF0MV5PUE", "domain": ".luatvietnam.vn"},
    {"name": "__RequestVerificationToken", "value": "iEIFkoKygQrRIM_9KUpDfKmyNIk6Y36s8V6hRrLDyO16_Mmj3MfGmZnh1FfwscJcpA57EPYVURGwV1RATh0MTEROT0g1", "domain": "luatvietnam.vn"},
    {"name": "__vnp_guest_id", "value": "356386522", "domain": "luatvietnam.vn"},
    {"name": "_gta_uni", "value": "823749984.356386522.094934686275", "domain": "luatvietnam.vn"},
    {"name": ".AspNetCore.Antiforgery.TTwcN29AroI", "value": "CfDJ8PEAieo9QK1CubjiVO12CoDdL_PxB7KfsEnhzTh7X-V09W9YQnJAzT7PJcx2_oce9oGI0sjgB5bpBT7LcEN9KLWQPEgl7bah8jvrcYFxOFFBMqsLCJ7VR4WGqUXbyIfJC95NbyALGkypH993RJTNCc4", "domain": "luatvietnam.vn"},
    {"name": "ASP.NET_SessionId", "value": "5ucpobjknvmhjegu4v0ytkjr", "domain": "luatvietnam.vn"},
    {"name": "fbm_117134849575084", "value": "base_domain=", "domain": "luatvietnam.vn"},
    {"name": "fbm_117134849575084", "value": "1_bfXUAp58H_bKQICTEqN81p-7VgOrao5sgbrxqftWU.eyJ1c2VyX2lkIjoiMjU3MTQ5MTI3OTg1NDMyNCIsImNvZGUiOiJBUUJCZjA3b21ZUVNQUkQ2ZHhMV1YwT1NwTXBSUmdTdnl4NnZucHk0R1J3UDQ4OW1IU2VEYzV3cU1GY0t6U0hxYzN3WnpwQnVvSGo5R2p4aURmRzhrZHJpMzBXVWdad1VIaTF4RzAwVmU0Zi1JYUx0SFVsUG5TZjI4Nk92UGJmYWtmQTh0Z2xWS1E5S1VuaF9tQlZrcTNzcmFoUGROZkhsS3d5UExfN2l1a1g3a1VVQ2tiYVZfbkprSUdJQ1BIWGRIaWFhdnpDZjRGdHJfUkxHaHZHd2FWMlpGb3FWNGlMSnhjWXczMnZFYVNNekoxLU9HV01jSGprZHU4TlJkZjFHdTdNbUptT3pja1o2a05uV1ZwcDRya0p3eEp5bVZNNmJhOHZEWXZiVWQyVDZRUzk3cFdxblVBNUVMcTdwRlFxSTRyX2dodThzaUtzTjhreXVLVlVXSXg0NnRVVWhCMEdBakVtM3kyLVJlWTVVTEEiLCJvYXV0aF90b2tlbiI6IkVBQUJxaUpVWkFpS3dCUFBkd05kOUJlbGdmNVhKamF1YnBFalZOYXg0ZU1hN0cya3dhNFFFbVF1WkJsZFpDUXQ2UWQwMFRQYmhEOXJTSEUwM3NyR2d2eDRlM3Y5TDhEVEpvOFZmWUhZRUpmelpBZUdFUHJaQ0tCWkJocXQ2RklMSTBhdG1xZENaQU1LVHZFTVRrSlc0U0NqQUU1ZkY0cHIxM1pDb1A0bHc1VGdsOTEzb1VwTWl3UkF4VEVkZWxhZFpBMkRkak45UFM1OHVYUXZNR3FWS25vQVpEWkQiLCJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImlzc3VlZF9hdCI6MTc1MjEzODE5OX0", "domain": "luatvietnam.vn"},
    {"name": "LuatVietNamCulture", "value": "vi", "domain": "luatvietnam.vn"},
]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]


def setup_driver():
    """Set up Selenium WebDriver with headless Chrome."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

    # Optional: Proxy configuration (uncomment and configure if needed)
    # chrome_options.add_argument('--proxy-server=http://your_proxy:port')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def load_cookies(driver, cookies):
    """Load cookies into the Selenium driver."""
    try:
        print("Loading cookies...")
        driver.get("https://luatvietnam.vn")  # Load base domain to set cookies
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(random.uniform(2, 4))
        print("Cookies loaded successfully.")
    except Exception as e:
        print(f"Error loading cookies: {e}")
        with open("failed_urls.txt", "a", encoding="utf-8") as f:
            f.write(f"Cookie Loading Error: {e}\n")
        raise

def main():
    driver = setup_driver()
    load_cookies(driver, cookies)

    folder = "Thuế TNCN"
    filename = "Tên văn bản NĐ-TT liên quan đến Thuế TNCN.txt"
    filepdf = "Link tải văn bản NĐ-TT liên quan đến Thuế TNCN.txt"
    name = ""
    link = ""

    for page in range(START_PAGES, MAX_PAGES + 1):
        print(f"\n🔎 Đang xử lý trang {page}")
        #driver.get(BASE_URL + str(page))
        driver.get(BASE_URL)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Trên mỗi trang kết quả
        links = soup.select('a[href*="#taive"]')
        # links = driver.find_elements(By.CSS_SELECTOR, "a[href*='#taive']")
        doc_links = ["https://luatvietnam.vn" + link.get("href") for link in links]

        print(f"📄 Tìm thấy {len(doc_links)} tài liệu trên trang {page}")

        for doc_url in doc_links:
            driver.get(doc_url)
            time.sleep(2)

            # Lấy tiêu đề
            title = driver.find_element(By.TAG_NAME, "h1").text.strip()
            # safe_title = title.replace("/", "-").replace("\\", "-")
            name += title + "\n"
            print(f"📄 {title}")
            link += doc_url + "\n"

    with open(f"{folder}/{filename}", 'a', encoding='utf-8') as f:
        f.write(name)

    with open(f"{folder}/{filepdf}", 'a', encoding='utf-8') as f:
        f.write(link)

    driver.quit()


if __name__ == "__main__":
    main()
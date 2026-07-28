from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import random

cookies = [
    {"name": "_clck", "value": "1xuac6x%7C2%7Cfxh%7C0%7C2012", "domain": ".luatvietnam.vn"},
    {"name": "_clsk", "value": "bqqtih%7C1752397269969%7C1%7C1%7Ck.clarity.ms%2Fcollect", "domain": ".luatvietnam.vn"},
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
    {"name": "LAWSVN_AUTH", "value": "0A19B6585900199FE87F205694C072E04D929C0E3EF7A65440B3EE37631984753C0B992577EC369132D7E8472B27197FCD7A988CD701912C51318DD0F997B59595CF08058C1FE46F1DD4F862DDD8659E9BFEABEE200DC34D305A4388F80EE1E4D01AC9D217041AC5F3A4EC340CD849C21CB45C489FE956B5921E83FCFA5A07E17EAC58E0212A5D0546D34F557EB5272EF00AD18CC77054C75817A77EE7F3BCBAD3BD72C902E232C7C2C08ECAAE775FCF1A146821DCF1925FBC25A3B80E53E5BA8DB229F880FEA976815F75AF5191368A3B03FB044B71D04F25D3CBDF09C7C7730D7933B7FD4A8BBCE4C1554C125B3D8FEF3BBC344FAD61A44F0C83087C128D453CB1F11C837DC0B51BB89433C2152F540F93810EAFC7D0AEED230926704E79443EFA974CC657BF0C212C9794ECB87FE0FBFAADEED4CF9CBAFFFF44867AB010045F5C1E8DF4362B07D740B7632E1260FD1B45F364CF25DEFD00D09C7195764B7A701CFE99B1A58B5C3D0A2B478F049874890B40D92B0D71ECA310ECA6B7536816400E62DBABAE2503DD47FE1FA2AD285FF246C8EB666899236D17C9440DE3F3E2FE00E8454D51E5E54428312CDAC416E308C49B9EEE0C87AFA2AC0B49C10E3F3F1B71E202D0CE19389E15888DEAF87E623B5FBCB5DCB918F406BFC14F0C69288A1F112E8D5B792DADC990B9CC5168A540A5A0CA79A60E7E6D6CF421AB5450CDE02FA09DC4E1C43118F055D1FF45045A4A045F075C8A813A17ED2901DFE7A625453D57E0DF01A47C147EAF62C9A3671B2776A573A5445D36199389A822D6E02E6F337BFDE5747586B4938846CEA92AF05629233ED62E6131B309FC7C113E420F85BCB02757BC530EE2756F9E3AF27AC3F5F57847E14A6AEDF6F3E3B53BB017EB1611AAFE00A3BF329D91AF33D7DE128CD421B1E7C070E9DFA88177404AAAA59682992ACBC6FDB5BC97FBBB952E566DDB8A793ED94CC3E61D72870F04E869092B9872AFF0FFED55886A5CC16CDF1C754B6DEEE507787109DF2CB5BD3EE3A518967ADA8D423FCA816F51B724A3D1A21083DE793E18DC3A9BE3AF58640583EE6A534393BC61579D5555A766B759F2E830AF2F6CE04454D1F91E2EE8C77FFE6C94EAECEB54C50536377F93BADC16CABCD65F155132C1D618766AB8183B2981CA73F3CECF5253E2A03B18A7C481CED933466A8FD05862489F7396DA8878DD25D8A40501A17492766E8B26E6951A7CC712A7CD084D4B80B64D7E1123F92B6E8882082239CED77994ABF3DC25E3B3E9E20065B5A7C2F26D4371EAE0DE9FB5FADDFF5A81DD16C9428F94FE0FDC584C84CC6D10E63DF69A5C4A7CF49651D178CDC0BE9A647B847E6EABBFC7E441521B63C6922BBA9CC90CC8E5F5D52940EF213311D45D6F2F56171187EB6A1A7564A9209003B12B38678511189F84C94118C94DDF0685EBC0C3EC7911B54092DA2AE0E27F7A11192728B0BA5EF8B013B5F0B0405911A15038AD5F2B1BFAFE913BB3649CA0CAB7D66C1F33551C257CF590D99F11719676DF47F820CF83873A7F65CD5C01E56B09C09EDA886F48A721E152BB551C1CC88C94CA88991E9BD35AC6AC2B75DA34C298057A37CA1D23B7258019D8E6C6E46EF6E1874C32B399E13DE67E6756D1FA50290BC6D22B86E6ED9B32AB0B2B5E1D89FF1EDB939EBAF3BF586662711279C7E13641B9C3821FE1CF92CD923D9FCE5E695088C5A13E29910F4837EE02EC61C427CD8F84B31AD3FEFD5C4F9EE9AEA51CDF10386ED26C62DC22F6D64CEA501A323ED2450E013DBB29B954E458C5DC521DA044D132DB9FDF8972E2CFCFCF7DDC30C2DE9629CEE0339FBA6756071CAC2322E9ACE3701A3A82BCB974172A4BE1442AC27C578C7BC5DD6419F95771AF1F17E9F3D062064D3E28111440B7D27E2F73BC28AD4237638800B091DB741585B226C1C3B83CA7CB921FF08A70FDA28B2C989360887DFD49924B268B747AF78CAE1309A22AABAE5CAD04A117155608E11263EF215EC9068333E9A7C1B5CA209AE0EBCD3D8560FBB525281EC3111453DC693B06518E3C46FEE9A4A17B8D579766EEDDDF273AFA15477DF9EC1C43AAC0A755F1482266D41EA5712BFE1ECD30B28AE1451068B094192F15FB56E23ACF8B2C12517CF1D3B1DE85A69F7AF4C25B823BB5AF02A56BA3196CBD22FE8898A9E19884779F619B7F5287DC8E01510848D04D6E08820ABAACF436B67C45F0C941555E45EA48A4C861206F62B5B8E75C4E6C20664F1D57BF432124D7D2BD9559A05037A152BFDC04C28293272B344F1CD1F157247BF5881AE4FF84F60AF733E88A3BF1BCA8BED22B7EB66AFD9FC8AB835EA169656FD0495548365CBFF8FA2DA6C5C1AA6EDE9EDEAC0FD9A06BEE4C2689E7338477496F43272867A4FA725CBBE7559202CDA6591083581BCC54613DD4F80F4D28244A30B426D903C0AC4320D6AF1BEA03F76402B4089B6C3186C1CE3EBF75BD2C86712F32D53440F15D9CB0C199149765AA94881E28D2031B6829F405F72997A87C56FA14326B6A306411B3", "domain": ".luatvietnam.vn"},
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

input_link = "BHXH/Link tải văn bản NĐ-TT liên quan đến BHXH.txt"
output_link = "BHXH/NĐ-TT liên quan đến BHXH.txt"

with open(input_link, 'r', encoding='utf-8') as f:
    urls = [line.strip() for line in f if line.strip()]

priority = ['.docx', '.doc', '.pdf']


def extract_download_link(url, driver):
    try:
        # Truy cập URL và thêm thời gian chờ
        driver.get(url)
        time.sleep(random.uniform(3, 5))  # Thêm thời gian chờ ngẫu nhiên từ 3-5 giây sau khi tải trang
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        test_find_link = soup.find_all('a', href=True)

        # Tìm thẻ div với id='taive'
        div = soup.find('div', id='taive')
        if div:
            a_tag_word = div.find('a', href=True, title='Bản Word (.doc)')
            a_tag_pdf = div.find('a', href=True, title='Bản PDF (.pdf)')
            if a_tag_word:
                link = a_tag_word['href']
                print(link)
                return link
            elif a_tag_pdf:
                link = a_tag_pdf['href']  # Sửa lỗi: Sử dụng a_tag_pdf thay vì a_tag_word
                print(link)
                return link

    except Exception as e:
        print(f"Lỗi khi xử lý {url}: {e}")
        with open("failed_urls.txt", "a", encoding="utf-8") as f:
            f.write(f"Error processing {url}: {e}\n")
    return None


def main():
    driver = setup_driver()
    load_cookies(driver, cookies)

    with open(output_link, 'a', encoding='utf-8') as out:
        for url in urls:
            print(f"Đang xử lý: {url}")
            link = extract_download_link(url, driver)
            if link:
                out.write(link + '\n')
            else:
                out.write('\n')
            time.sleep(random.uniform(1, 3))  # Thêm thời gian chờ ngẫu nhiên từ 1-3 giây giữa các URL

    driver.quit()


if __name__ == "__main__":
    main()
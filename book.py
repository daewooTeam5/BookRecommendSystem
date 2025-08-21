import requests
import re
from bs4 import BeautifulSoup
from lxml import html
import csv
import time
import random
import pandas as pd

CSV_HEADER = [
    'id', 'title', 'author', 'publisher', 'image', 'price',
    'genre', 'published_at', 'page', 'introduction'
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
]

# 상세페이지에서 소개 & 쪽수 가져오기
def get_extra_details(book_url):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS),
                   #"Cookie": "CheckSameSite4=IsValidSameSiteSet; AladdinUser=UID=-994978082&SID=zr5bblB%2f5gRzR%2fQnNI%2f17A%3d%3d; _gcl_au=1.1.876579939.1751874263; _fwb=133sGyoBy5ihSERts21dbaF.1751874262917; _ga=GA1.1.814483838.1751874263; _BS_GUUID=zQgyaX65cHCBV9Ls6LgTi3AYdlvNeuRNk7mv4tAg; _fbp=fb.2.1751874273576.174623020985880236; _ga_YF1PFVVFXL=GS2.1.s1751874273$o1$g1$t1751874280$j53$l0$h0; AladdinUS=6evLM5wQvzTD2JSBWHr8MQ%3d%3d&USA=0; _gcl_gs=2.1.k1$i1755661099$u252127833; _gcl_aw=GCL.1755661105.Cj0KCQjwwZDFBhCpARIsAB95qO0YCPUONEIi1w8pYbRvw3C0OvVwuQ0hWmuZ2rD-ZRocsiVxhPnNJBMaApkiEALw_wcB; ala_qs_use=1; _TRK_AUIDA_13987=2cce00e6306d9f131920cc30d308b085:16; _TRK_ASID_13987=d4b486a4f65d467d4662048011e00681; ASP.NET_SessionId=554ly4icdnfjmpuf4bzw5nuj; Supplier=; QsSNSLoginCookies=returnurl=https%3a%2f%2fwww.aladin.co.kr%2fshop%2fwproduct.aspx%3fItemId%3d369848660&snsAppId=1&SecureOpener=1; AladdinLogin=6evLM5wQvzTD2JSBWHr8MQ%3d%3d; AladdinSite=Aladin; AladdinLoginSNS=UID=-994978082&SNSTYPE=4; Aladin.AuthAdult=mKanQyO2sLYOe4z6Xs0MZg==; wcs_bt=s_1c519d64863a:1755712475|b78bdfda7ab45:1755712475; _ga_VKYKBC0ZHH=GS2.1.s1755712276$o21$g1$t1755712475$j16$l0$h0;",

                   }
        response = requests.get(book_url, headers=headers)
        response.raise_for_status()
        tree = html.fromstring(response.content)

        # 책 소개 (meta description)
        description_list = tree.xpath('//meta[@name="description"]/@content')
        description = description_list[0].strip() if description_list else None
        published_at = tree.xpath('//*[@id="Ere_prod_allwrap"]/div[3]/div[2]/div[1]/div/ul/li[3]/text()')[1]

        # 페이지 수 ("쪽" 들어간 텍스트 찾기)
        page_list = tree.xpath('//*[@id="Ere_prod_allwrap"]//li/text()')
        page = None
        for item in page_list:
            if "쪽" in item:
                page = int(item.replace("쪽", "").strip())
                break

        return description, page,published_at
    except Exception as e:
        print(f"Error crawling {book_url}: {e}")
        return None, None


# 리스트 페이지에서 기본 정보 가져오기
def get_books_from_list(list_url,genere):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    response = requests.get(list_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    book_items = soup.select('div.ss_book_box')
    books = []

    for item in book_items:
        try:
            # 링크
            link = item.select_one('a.bo3')['href'] if item.select_one('a.bo3') else None
            # 제목
            title = item.select_one('a.bo3').get_text(strip=True) if item.select_one('a.bo3') else None
            # 저자, 출판사, 출판일
            info_text = item.select_one('div.ss_book_list').get_text(" ", strip=True)
            author, publisher, published_at = None, None, None
            parts = info_text.split(" | ")

            if len(parts) >= 3:
                author, publisher, published_at = parts[0], parts[1], parts[2].replace(".","-")

            author =parts[0].split("(지은이)")[0].split(" ")[-2]

            # 날짜 데이터만 정규식으로 추출 nnnn년 nn월
            date_pattern = re.compile(r'\d{4}년 \d{1,2}월')
            date_match = date_pattern.search(parts[2])
            published_at = date_match.group()
            published_at = published_at.replace("년", "-").replace("월", "").replace(" ","")
            # 월이 한자리면 앞에 0 추가
            if len(published_at.split("-")[1]) == 1:
                published_at = published_at.replace("-", "-0", 1)

            # 이미지
            imgs = item.select('.flipcover_in > img')

            if len(imgs) > 1:
                image = imgs[1]['src']  # 2개 이상이면 두 번째 이미지
            elif len(imgs) == 1:
                image = imgs[0]['src']  # 1개면 첫 번째 이미지
            else:
                image = None  # 이미지 없으면 None
            # 가격
            price_tag = item.select_one('td > div:nth-child(1) > ul > li:nth-child(4) > span:nth-child(1)')  # 원래 리스트 페이지에 있음
            price = None
            if price_tag:
                price_text = price_tag.get_text(strip=True).replace(",", "").replace("원", "")
                if price_text.isdigit():
                    price = int(price_text)


            books.append({
                'title': title, 'author': author, 'publisher': publisher,
                'image': image, 'price': price,
                'published_at': published_at,
                'genre': genere,
                'page': None, 'introduction': None,
                'link': link
            })
        except Exception as e:
            print(f"리스트 파싱 중 오류: {e}")
            continue

    return books

def main():
    #                                                                                                                                            | 여기 중괄호
    # base_url = "https://www.aladin.co.kr/shop/wbrowse.aspx?BrowseTarget=List&ViewRowsCount=25&ViewType=Detail&PublishMonth=0&SortOrder=2&page={}&Stockstatus=1&PublishDay=84&CID=170&SearchOption="
    base_url = "https://www.aladin.co.kr/shop/wbrowse.aspx?BrowseTarget=List&ViewRowsCount=25&ViewType=Detail&PublishMonth=0&SortOrder=2&page={}&Stockstatus=1&PublishDay=84&CID=1322&SearchOption="
    # base_url = "https://www.aladin.co.kr/shop/wbrowse.aspx?BrowseTarget=List&ViewRowsCount=25&ViewType=Detail&PublishMonth=0&SortOrder=2&page={}&Stockstatus=1&PublishDay=84&CID=170&SearchOption="
    genere = "외국어"
    print("🚀 리스트 페이지에서 기본 도서 정보 수집 시작...")

    all_books_data = []
    book_id = 1
    # 경제 1-20 itz컴퓨터 1-19 만화 1-12 외국어 1-6

    # 👉 1 ~ 20 페이지까지 반복
    for page_num in range(1, 6):
        list_url = base_url.format(page_num)
        print(f"📖 {page_num}페이지 크롤링 중...")

        books = get_books_from_list(list_url,genere)
        print(f"✅ {page_num}페이지: {len(books)}권 발견")

        for book in books:
            if not book['link']:
                continue

            intro, page, published_at = get_extra_details(book['link'])

            if not intro or not page:
                print(f"⚠️ {book['title']} 상세정보 부족 → 스킵")
                continue

            book['introduction'] = intro
            book['page'] = page
            # 날짜 형식 변환 (예: "2023년 1월" → "2023-01-01")
            # 해당 데이터가 날짜 한글 혹은 영어가 하나라도 있을경우
            print("대충나와있는거",book['published_at'])
            print("제대로가져온거",published_at)
            if published_at and re.search(r'[가-힣a-zA-Z,]', published_at):
                print(book['published_at'])
                book['published_at'] = book['published_at']+("-"+ str(random.randint(10, 26)))
            else:
                book['published_at'] = published_at


            all_books_data.append(book)

            #time.sleep(0.5)  # 서버 부하 방지

    # DataFrame으로 변환 후 널값 있는 행 제거
    df = pd.DataFrame(all_books_data, columns=CSV_HEADER)
    print(df.head())  # 미리보기

    output_filename = f'aladin_books_final_{genere.replace("/", "")}.csv'
    df.to_csv(output_filename, index=False, encoding='utf-8-sig')

    print(f"\n🎉 크롤링 완료! 총 {len(df)}권 저장 -> '{output_filename}'")

if __name__ == '__main__':
    main()

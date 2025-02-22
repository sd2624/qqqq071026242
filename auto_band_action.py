from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json
import time
import random
import subprocess
import shutil
import requests

class BandAutoAction:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.script_dir, 'config.json')
        self.bands_file = os.path.join(self.script_dir, 'band_urls.json')
        self.setup_vpn()
        self.setup_driver()
        
    def setup_vpn(self):
        """한국 VPN 연결 확인"""
        try:
            # GitHub Actions에서 설정된 프록시 사용
            proxies = {
                'http': 'socks5h://127.0.0.1:1080',
                'https': 'socks5h://127.0.0.1:1080'
            } if os.getenv('GITHUB_ACTIONS') else None
            
            response = requests.get("http://ip-api.com/json", proxies=proxies)
            ip_info = response.json()
            
            print("\n============== VPN 상태 ==============")
            print(f"현재 IP: {ip_info.get('query')}")
            print(f"국가: {ip_info.get('country')}")
            print(f"지역: {ip_info.get('regionName')}")
            print(f"도시: {ip_info.get('city')}")
            print(f"ISP: {ip_info.get('isp')}")
            print("=====================================\n")
            
            if ip_info.get('country') != 'South Korea':
                raise Exception("한국 IP가 아닙니다!")
                
        except Exception as e:
            print(f"VPN 설정 실패: {str(e)}")
            raise

    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            options = Options()
            
            # GitHub Actions 환경인 경우
            if os.getenv('GITHUB_ACTIONS'):
                options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--proxy-server=socks5://127.0.0.1:1080')  # VPN 프록시 설정
                chrome_profile_path = os.getenv('CHROME_PROFILE_PATH', './chrome-profile')
            else:
                # 로컬 환경
                chrome_profile_path = os.path.join(self.script_dir, 'chrome-profile')
            
            # 프로필 경로 설정
            options.add_argument(f'--user-data-dir={chrome_profile_path}')
            options.add_argument('--profile-directory=Default')
            
            # 기본 옵션 설정
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            
            print("Chrome driver initialized")
            
        except Exception as e:
            print(f"Driver setup failed: {str(e)}")
            raise

    def login(self):
        try:
            print("\n============== 로그인 시작 ==============")
            print("1. 로그인 페이지 이동...")
            self.driver.get('https://auth.band.us/login')
            time.sleep(3)
            
            # 이메일 로그인 버튼 찾고 클릭
            print("2. 이메일 로그인 버튼 찾는 중...")
            email_login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.uButtonRound.-h56.-icoType.-email'))
            )
            email_login_btn.click()
            print("   이메일 로그인 버튼 클릭 완료")
            time.sleep(2)

            # 이메일 입력
            print("3. 이메일 입력...")
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'input_email'))
            )
            # config.json에서 이메일 가져오기
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                email = config.get('email', '')
            
            email_input.send_keys(email)
            print(f"   이메일 입력 완료: {email}")
            time.sleep(1)
            
            # 다음 버튼 클릭
            email_next_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.uBtn.-tcType.-confirm'))
            )
            email_next_btn.click()
            print("   다음 버튼 클릭 완료")
            time.sleep(2)

            # 비밀번호 입력
            print("4. 비밀번호 입력...")
            pw_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'pw'))
            )
            password = config.get('password', '')
            pw_input.send_keys(password)
            print("   비밀번호 입력 완료")
            time.sleep(1)
            
            # 로그인 버튼 클릭
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.uBtn.-tcType.-confirm'))
            )
            login_btn.click()
            print("   로그인 버튼 클릭 완료")

            # 메인 페이지 로딩 대기
            print("5. 메인 페이지 로딩 대기 중...")
            if not self.wait_for_main_page():
                raise Exception("메인 페이지 로딩 실패")
                
            print("로그인 성공!")
            print("==========================================")
            
        except Exception as e:
            print("\n============== 로그인 실패 ==============")
            print(f"오류 내용: {str(e)}")
            print("========================================")
            raise

    def get_band_list(self):
        """밴드 목록 가져오기"""
        try:
            print("============== 밴드 목록 수집 시작 ==============")
            print("1. 피드 페이지 로딩 중...")
            self.driver.get('https://band.us/feed')
            time.sleep(5)
            
            print("2. 페이지 초기 로딩 완료")
            print("3. '내 밴드 더보기' 버튼 찾는 중...")
            
            try:
                # 스크롤 시도 횟수 표시
                for scroll_attempt in range(1, 4):
                    print(f"   스크롤 시도 {scroll_attempt}/3...")
                    try:
                        more_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.myBandMoreView._btnMore'))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                        time.sleep(2)
                        print("   '더보기' 버튼 발견, 클릭 시도...")
                        more_btn.click()
                        print("   '더보기' 버튼 클릭 성공")
                        time.sleep(3)
                        break
                    except:
                        print(f"   {scroll_attempt}번째 스크롤 - 버튼 찾기 실패")
                        self.driver.execute_script("window.scrollBy(0, 300);")
                        time.sleep(1)
            except Exception as e:
                print(f"더보기 버튼 처리 중 오류 (무시됨): {str(e)}")
            
            print("4. 밴드 목록 요소 찾는 중...")
            band_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[data-viewname="DMyGroupBandBannerView.MyGroupBandListView"]'))
            )
            print("   밴드 목록 요소 찾기 성공")
            
            print("5. 개별 밴드 정보 수집 중...")
            band_items = band_list.find_elements(By.CSS_SELECTOR, 'li[data-viewname="DMyGroupBandListItemView"]')
            print(f"   총 {len(band_items)}개의 밴드 항목 발견")
            
            bands = []
            success_count = 0
            failed_count = 0
            
            for index, item in enumerate(band_items, 1):
                try:
                    band_link = item.find_element(By.CSS_SELECTOR, 'a.itemMyBand')
                    band_name = item.find_element(By.CSS_SELECTOR, 'span.body strong.ellipsis').text.strip()
                    band_url = band_link.get_attribute('href')
                    
                    if band_url and band_name:
                        bands.append({
                            'name': band_name,
                            'url': band_url
                        })
                        success_count += 1
                        print(f"   [{index}/{len(band_items)}] 성공: {band_name}")
                except Exception as e:
                    failed_count += 1
                    print(f"   [{index}/{len(band_items)}] 실패: {str(e)}")
                    continue
            
            print("\n6. 밴드 정렬 중...")
            bands.sort(key=lambda x: int(x['url'].split('/')[-1]), reverse=True)
            print("   정렬 완료")
            
            print("\n7. 수집된 정보 저장 중...")
            with open(self.bands_file, 'w', encoding='utf-8') as f:
                json.dump(bands, f, ensure_ascii=False, indent=4)
            
            print("\n============== 밴드 목록 수집 결과 ==============")
            print(f"총 발견된 밴드: {len(band_items)}개")
            print(f"성공적으로 수집: {success_count}개")
            print(f"수집 실패: {failed_count}개")
            print(f"저장된 파일 위치: {self.bands_file}")
            print("===============================================")
            
            return bands
            
        except Exception as e:
            print("\n============== 오류 발생 ==============")
            print(f"밴드 목록 수집 실패: {str(e)}")
            print("======================================")
            raise

    def post_to_band(self, band_info, post_url, url_number):
        """밴드에 포스팅"""
        try:
            print("\n" + "="*50)
            print(f"현재 작업 중인 URL #{url_number}")
            print(f"URL 주소: {post_url}")
            print(f"포스팅 밴드: {band_info['name']}")
            print(f"밴드 주소: {band_info['url']}")
            print("="*50 + "\n")
            
            # 밴드로 이동
            self.driver.get(band_info['url'])
            time.sleep(5)
            
            # 글쓰기 버튼 찾기
            write_btn = None
            write_btn_selectors = [
                'button._btnPostWrite',
                'button.uButton.-sizeL.-confirm.sf_bg',
                'button[type="button"][class*="_btnPostWrite"]'
            ]
            
            for selector in write_btn_selectors:
                try:
                    write_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
                    
            if not write_btn:
                raise Exception("글쓰기 버튼을 찾을 수 없습니다")
                
            print("글쓰기 버튼 클릭...")
            write_btn.click()
            time.sleep(3)
            
            # 에디터 찾기
            editor = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
            )
            
            # URL 입력
            print("URL 입력 중...")
            editor.send_keys(post_url)
            time.sleep(1)
            
            # 미리보기 로딩 대기
            print("미리보기 로딩 대기 중...")
            time.sleep(240)  # 4분 대기
            
            # URL 텍스트 삭제
            editor.clear()
            
            # 게시 버튼 클릭
            submit_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-sizeM._btnSubmitPost.-confirm'))
            )
            submit_btn.click()
            time.sleep(3)
            
            print(f"'{band_info['name']}' 밴드에 포스팅 완료")
            return True
            
        except Exception as e:
            print(f"포스팅 실패: {str(e)}")
            return False

    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass
            
        # VPN 연결 해제
        try:
            # VPN 해제 로직 추가 (실제 구현 필요)
            print("VPN disconnected")
        except:
            pass

def main():
    bot = None
    try:
        bot = BandAutoAction()
        
        print("\n============== 작업 시작 ==============")
        print("1. 로그인 시도...")
        bot.login()  # 로그인 먼저 실행
        
        print("\n2. 밴드 목록 수집 중...")
        bands = bot.get_band_list()
        
        print("\n2. 설정 파일 읽기...")
        with open(bot.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 빈 URL을 제외한 URL 목록 생성
        urls = []
        for i in range(1, 31):
            url = config.get(f'post_url_{i}', '').strip()
            if url:
                urls.append((i, url))  # URL과 함께 인덱스도 저장
                
        if not urls:
            print("포스팅할 URL이 없습니다!")
            return
            
        print(f"포스팅할 URL 수: {len(urls)}개")
        
        # 각 URL 순차적으로 처리 (1시간 간격)
        for url_idx, (url_num, post_url) in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"URL {url_num}/{len(urls)} 포스팅 시작")
            print(f"현재 URL: {post_url}")
            print(f"{'='*60}\n")
            success_count = 0
            
            # 해당 URL로 모든 밴드에 포스팅
            for band_idx, band in enumerate(bands, 1):
                if bot.post_to_band(band, post_url, url_num):
                    success_count += 1
                
                # 다음 밴드로 이동 전 대기 (4분)
                if band_idx < len(bands):
                    print(f"\n현재 진행 상황:")
                    print(f"- URL {url_num}/{len(urls)}")
                    print(f"- 현재 URL: {post_url}")
                    print(f"- 밴드 진행: {band_idx}/{len(bands)}")
                    print(f"- 성공: {success_count}회")
                    print("다음 밴드로 이동 전 4분 대기...")
                    time.sleep(240)
            
            print(f"\nURL {url_num} 포스팅 통계:")
            print(f"- 작업한 URL: {post_url}")
            print(f"- 총 시도: {len(bands)}회")
            print(f"- 성공: {success_count}회")
            print(f"- 실패: {len(bands) - success_count}회")
            
            # 다음 URL로 넘어가기 전에 1시간 대기
            if url_idx < len(urls):
                next_url = urls[url_idx][1]
                wait_time = 3600  # 1시간 = 3600초
                print(f"\n다음 URL 정보:")
                print(f"- 다음 URL 번호: {urls[url_idx][0]}")
                print(f"- 다음 URL 주소: {next_url}")
                print(f"- 대기 시작: 1시간")
                
                # 1분 단위로 남은 시간 표시
                while wait_time > 0:
                    hours = wait_time // 3600
                    minutes = (wait_time % 3600) // 60
                    print(f"남은 시간: {hours}시간 {minutes}분 | 다음 URL: {next_url}")
                    time.sleep(60)
                    wait_time -= 60
        
        print("\n============== 모든 URL 작업 완료 ==============")
        
    except Exception as e:
        print(f"\n============== 오류 발생 ==============")
        print(f"Error: {str(e)}")
        print("=======================================")
    finally:
        if bot:
            bot.cleanup()

if __name__ == "__main__":
    main()

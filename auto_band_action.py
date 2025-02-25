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
from selenium.webdriver.common.keys import Keys  # Keys import 추가

class BandAutoAction:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.script_dir, 'config.json')
        self.bands_file = os.path.join(self.script_dir, 'band_urls.json')
        self.driver = None  # driver 초기화 추가
        self.setup_vpn()
        
        # driver 설정 실패 시 예외 처리 추가
        if not self.setup_driver():
            raise Exception("Chrome driver 초기화 실패")
            
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
        try:
            options = Options()
            
            # GitHub Actions 환경인 경우
            if os.getenv('GITHUB_ACTIONS'):
                # 기존 압축된 프로필 사용
                profile_dir = "chrome-profile"
                
                # 프로필 디렉토리가 없으면 생성
                if not os.path.exists(profile_dir):
                    os.makedirs(f"{profile_dir}/Default", exist_ok=True)
                
                # 압축된 프로필 해제 (기존 파일 덮어쓰기)
                if os.path.exists("chrome_profile.zip"):
                    os.system(f"unzip -o chrome_profile.zip -d {profile_dir}")
                    
                # 권한 설정
                os.system(f"chmod -R 777 {profile_dir}")
                
                # Chrome 옵션 설정
                options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
                options.add_argument('--profile-directory=Default')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--password-store=basic')
                options.add_argument('--disable-blink-features=AutomationControlled')
                
                # 프록시 설정
                options.add_argument('--proxy-server=socks5://127.0.0.1:1080')
                
                # 자동화 감지 방지
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_experimental_option('useAutomationExtension', False)

            else:
                # 로컬 환경에서는 기존 설정 사용
                timestamp = int(time.time() * 1000)
                profile_dir = f"chrome_profile_{timestamp}"
                
                # 기존 프로필 디렉토리 제거
                if os.path.exists(profile_dir):
                    shutil.rmtree(profile_dir)
                time.sleep(1)
                
                # 새 프로필 디렉토리 생성
                os.makedirs(profile_dir, exist_ok=True)
                
                options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
                options.add_argument('--profile-directory=Default')
                
                # 기본 옵션
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-software-rasterizer')
                
                # 프로세스 분리 비활성화
                options.add_argument('--disable-features=IsolateOrigins,site-per-process')
                options.add_argument('--disable-site-isolation-trials')
                
                # 기타 필요한 설정
                options.add_argument('--no-first-run')
                options.add_argument('--no-default-browser-check')
                options.add_argument('--password-store=basic')
                options.add_argument('--disable-blink-features=AutomationControlled')
                
                # 프록시 설정
                options.add_argument('--proxy-server=socks5://127.0.0.1:1080')
                
                # 자동화 감지 방지
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_experimental_option('useAutomationExtension', False)

            # 드라이버 생성
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            
            # 초기 페이지 로드 테스트
            self.driver.get('about:blank')
            time.sleep(2)
            
            print(f"Chrome driver initialized with profile: {profile_dir}")
            return True
            
        except Exception as e:
            print(f"Driver setup failed: {str(e)}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            return False

    def navigate_to_url(self, url):
        """URL로 이동하고 상태를 출력"""
        try:
            print(f"\n{'='*50}")
            print(f"URL 이동 시도: {url}")
            print(f"{'='*50}\n")
            
            self.driver.get(url)
            time.sleep(3)
            
            current_url = self.driver.current_url
            print(f"현재 URL: {current_url}")
            
            return current_url == url or url in current_url
            
        except Exception as e:
            print(f"URL 이동 실패: {str(e)}")
            return False

    def wait_for_main_page(self, timeout=30):
        """메인 페이지 로딩 완료 대기"""
        try:
            print("\n메인 페이지 로딩 대기 중...")
            current_url = self.driver.current_url
            print(f"현재 URL: {current_url}")
            
            # validation_welcome 페이지 체크
            if 'validation_welcome' in current_url:
                print("인증 페이지 발견, 처리 중...")
                try:
                    next_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-confirm'))
                    )
                    next_btn.click()
                    time.sleep(3)
                except Exception as e:
                    print(f"인증 페이지 처리 중 오류 (무시됨): {str(e)}")

            # 피드 페이지로 직접 이동
            print("\nband.us/feed 페이지로 이동 중...")
            self.driver.get('https://band.us/feed')
            time.sleep(3)
            
            # 버전0과 동일하게 처리
            start_time = time.time()
            while (time.time() - start_time < timeout):
                try:
                    # 피드 페이지의 특정 요소들 중 하나라도 발견되면 성공
                    feed_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        'div.myBandList, div.feed, div.myBandArea, button.myBandMoreView._btnMore')
                    if feed_elements:
                        print("밴드 피드 페이지 로딩 완료")
                        return True
                except:
                    pass
                time.sleep(2)
                print(f"피드 페이지 로딩 대기 중... ({int(time.time() - start_time)}초)")
                
            return False
                
        except Exception as e:
            print(f"\n페이지 로딩 실패:")
            print(f"마지막 URL: {self.driver.current_url}")
            print(f"오류 내용: {str(e)}")
            return False

    def login(self):
        try:
            print("\n============== 로그인 시작 ==============")
            print(f"초기 URL: {self.driver.current_url}")
            
            # 로그인 페이지로 이동
            login_url = 'https://auth.band.us/login'
            print(f"\n1. 로그인 페이지로 이동: {login_url}")
            self.navigate_to_url(login_url)
            print(f"현재 URL: {self.driver.current_url}")
            time.sleep(3)
            
            # 이메일 로그인 버튼 찾고 클릭
            print("\n2. 이메일 로그인 버튼 찾는 중...")
            email_login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.uButtonRound.-h56.-icoType.-email'))
            )
            email_login_btn.click()
            print(f"현재 URL: {self.driver.current_url}")
            time.sleep(2)

            # 이메일 입력
            print("\n3. 이메일 입력 페이지...")
            print(f"현재 URL: {self.driver.current_url}")
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'input_email'))
            )
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                email = config.get('email', '')
            
            print(f"이메일 입력 시작: {email}")
            email_input.send_keys(email)
            print("이메일 입력 완료")
            time.sleep(1)
            
            # 다음 버튼 클릭
            email_next_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.uBtn.-tcType.-confirm'))
            )
            email_next_btn.click()
            print("\n4. 다음 버튼 클릭")
            print(f"현재 URL: {self.driver.current_url}")
            time.sleep(2)

            # 비밀번호 입력
            print("\n5. 비밀번호 입력 페이지...")
            print(f"현재 URL: {self.driver.current_url}")
            pw_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'pw'))
            )
            password = config.get('password', '')
            print("비밀번호 입력 시작")
            pw_input.send_keys(password)
            print("비밀번호 입력 완료")
            time.sleep(1)
            
            # 로그인 버튼 클릭
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.uBtn.-tcType.-confirm'))  # 이 버튼을 클릭
            )
            print("\n6. 로그인 버튼 클릭")
            login_btn.click()
            
            # 즉시 URL 체크
            time.sleep(2)
            current_url = self.driver.current_url
            print(f"\n로그인 버튼 클릭 직후 URL: {current_url}")
            
            # band.us/feed로 직접 이동
            print("\nband.us/feed 페이지로 이동 중...")
            self.driver.get('https://band.us/feed')
            time.sleep(5)
            print(f"현재 URL: {self.driver.current_url}")
            
            # 피드 페이지 로딩 확인
            try:
                # 더보기 버튼 바로 찾기
                more_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.myBandMoreView._btnMore'))
                )
                print("더보기 버튼 발견")
                more_btn.click()
                print("더보기 버튼 클릭 완료")
                time.sleep(3)
                return True
            except Exception as e:
                print(f"피드 페이지 로딩 실패: {str(e)}")
                return False
                
            print("\n로그인 성공!")
            print(f"최종 접속 URL: {self.driver.current_url}")
            print("==========================================")
            
        except Exception as e:
            print("\n============== 로그인 실패 ==============")
            print(f"마지막 URL: {self.driver.current_url}")
            print(f"오류 내용: {str(e)}")
            print("========================================")
            raise

    def get_band_list(self):
        """밴드 목록 가져오기"""
        try:
            print("\n============== 밴드 목록 수집 시작 ==============")
            print("1. 피드 페이지 이동 시도...")
            self.driver.get('https://band.us/feed')
            time.sleep(5)  # 대기 시간 증가
            print(f"현재 URL: {self.driver.current_url}")
            
            print("\n2. 피드 페이지 로딩 대기...")
            # myBandArea 대신 다른 선택자들도 시도
            selectors = [
                'div.myBandArea',
                'div.myBandList',
                'div.feed',
                'button.myBandMoreView._btnMore'
            ]
            
            element_found = False
            for selector in selectors:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    element_found = True
                    print(f"요소 발견: {selector}")
                    break
                except:
                    continue
                    
            if not element_found:
                raise Exception("피드 페이지 요소를 찾을 수 없습니다")
                
            print("피드 페이지 로딩 완료")
            
            # 더보기 버튼 찾기 전에 스크롤
            for scroll_attempt in range(1, 6):  # 최대 5번 시도
                try:
                    print(f"\n3. 더보기 버튼 찾기 시도 {scroll_attempt}/5...")
                    
                    # 스크롤 다운
                    self.driver.execute_script("window.scrollBy(0, 300);")
                    time.sleep(2)
                    
                    # 더보기 버튼 찾기
                    more_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.myBandMoreView._btnMore'))
                    )
                    
                    print("더보기 버튼 발견")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                    time.sleep(2)
                    more_btn.click()
                    print("더보기 버튼 클릭 완료")
                    time.sleep(5)  # 클릭 후 대기 시간 증가
                    break
                except:
                    print(f"시도 {scroll_attempt} 실패, 다시 시도...")
                    continue
                    
            print("\n4. 밴드 목록 요소 찾는 중...")
            band_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[data-viewname="DMyGroupBandBannerView.MyGroupBandListView"]'))
            )
            print("밴드 목록 컨테이너 발견")
            
            print("\n5. 개별 밴드 정보 수집...")
            band_items = band_list.find_elements(By.CSS_SELECTOR, 'li[data-viewname="DMyGroupBandListItemView"]')
            total_bands = len(band_items)
            print(f"총 {total_bands}개의 밴드 항목 발견")
            
            bands = []
            for idx, item in enumerate(band_items, 1):
                try:
                    band_link = item.find_element(By.CSS_SELECTOR, 'a.itemMyBand')
                    band_name = item.find_element(By.CSS_SELECTOR, 'span.body strong.ellipsis').text.strip()
                    band_url = band_link.get_attribute('href')
                    
                    if band_url and band_name:
                        bands.append({
                            'name': band_name,
                            'url': band_url
                        })
                        print(f"밴드 정보 추출 성공 [{idx}/{total_bands}]: {band_name}")
                except Exception as e:
                    print(f"밴드 정보 추출 실패 [{idx}/{total_bands}]: {str(e)}")
            
            print("\n6. URL 기준 정렬 중...")
            bands.sort(key=lambda x: int(x['url'].split('/')[-1]), reverse=True)
            print("정렬 완료")
            
            if bands:
                print("\n수집 결과:")
                print(f"- 첫 번째 밴드: {bands[0]['name']} ({bands[0]['url']})")
                print(f"- 마지막 밴드: {bands[-1]['name']} ({bands[-1]['url']})")
            
            return bands
            
        except Exception as e:
            print(f"\n밴드 목록 수집 실패: {str(e)}")
            raise

    def post_to_band(self, band_info, post_url, url_number):
        try:
            print("\n" + "="*50)
            print(f"포스팅 밴드: {band_info['name']}")
            print(f"밴드 주소: {band_info['url']}")
            print("="*50 + "\n")
            
            # 밴드로 이동
            self.driver.get(band_info['url'])
            print("밴드 페이지 로딩 중...")
            time.sleep(10)  # 대기 시간 증가
            
            # 글쓰기 버튼 찾기
            write_btn = None
            write_btn_selectors = [
                'button[class*="_btnPostWrite"]',  # 수정된 셀렉터
                'button._btnPostWrite',
                'button.uButton.-sizeL.-confirm.sf_bg',
                'button.writePost',  # 추가된 셀렉터
                'button[data-viewname="WriteFormView"]',  # 추가된 셀렉터
                'button.uButton._btnPostWrite'  # 추가된 셀렉터
            ]
            
            print("글쓰기 버튼 찾는 중...")
            for selector in write_btn_selectors:
                try:
                    print(f"셀렉터 시도: {selector}")
                    write_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if write_btn and write_btn.is_displayed():
                        print(f"✅ 글쓰기 버튼 발견: {selector}")
                        break
                except:
                    continue
                    
            if not write_btn:
                # 페이지 소스 출력
                print("\n현재 페이지 버튼 elements 확인:")
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                for btn in buttons:
                    try:
                        print(f"버튼 클래스: {btn.get_attribute('class')}")
                    except:
                        continue
                raise Exception("글쓰기 버튼을 찾을 수 없습니다")

            # 스크롤하여 버튼이 보이게 함
            self.driver.execute_script("arguments[0].scrollIntoView(true);", write_btn)
            time.sleep(2)
                
            print("📝 포스팅 작성 시작")
            write_btn.click()
            time.sleep(5)  # 대기 시간 증가
            
            # 에디터 찾기 (게시판 선택 전에 에디터부터 찾음)
            editor = None
            editor_selectors = [
                'div.contentEditor._richEditor.skin3',
                'div[contenteditable="true"][aria-labelledby="postWriteFormPlaceholderText"]',
                'div.contentEditor[contenteditable="true"]'
            ]
            
            for selector in editor_selectors:
                try:
                    editor = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if (editor and editor.is_displayed()):
                        print(f"✅ 에디터 발견: {selector}")
                        break
                except:
                    continue
            
            if not editor:
                raise Exception("에디터를 찾을 수 없습니다")
            
            # URL 입력 및 프리뷰 생성
            fixed_url = "https://testpro.site/%EC%97%90%EB%A6%AC%EC%96%B4/%EC%97%90%EB%A6%AC%EC%96%B4.html"
            print(f"🔗 URL 입력: {fixed_url}")
            editor.send_keys(fixed_url)
            print("URL 입력 완료")
            time.sleep(1)
            
            print("엔터키 입력")
            editor.send_keys(Keys.ENTER)
            print("10초 대기 시작...")
            time.sleep(10)  # URL 입력 후 10초 대기
            print("10초 대기 완료")

            # 커서를 맨 앞으로 이동 후 오른쪽으로 2칸 이동
            print("커서 이동 시작...")
            editor.send_keys(Keys.HOME)  # 커서를 맨 앞으로
            time.sleep(0.5)
            editor.send_keys(Keys.RIGHT)  # 오른쪽으로 1칸
            time.sleep(0.5)
            editor.send_keys(Keys.RIGHT)  # 오른쪽으로 1칸 더
            time.sleep(0.5)
            print("커서 2칸 이동 완료")
            
            # URL 길이만큼 백스페이스로 삭제
            print(f"URL 텍스트 백스페이스로 삭제 시작... (길이: {len(fixed_url)})")
            for i in range(len(fixed_url)):
                editor.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
                if (i + 1) % 10 == 0:  # 진행상황 출력
                    print(f"삭제 진행 중: {i+1}/{len(fixed_url)}")
            print("✅ URL 텍스트 삭제 완료")
            time.sleep(1)

            # 바로 게시 버튼 클릭
            submit_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-sizeM._btnSubmitPost.-confirm'))
            )
            print("✅ 게시 버튼 찾음")
            submit_btn.click()
            print("✅ 게시 버튼 클릭")
            time.sleep(3)

            # 게시판 선택 팝업 처리
            try:
                boardlist = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'boardList'))
                )
                print("✅ 게시판 선택 팝업 발견")
                
                # 첫 번째 게시판 클릭
                first_board = boardlist.find_element(By.CSS_SELECTOR, 'li:first-child button')
                first_board.click()
                print("✅ 첫 번째 게시판 선택됨")
                time.sleep(2)
                
                # 최종 게시 버튼 클릭
                final_submit = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-sizeM._btnSubmitPost.-confirm'))
                )
                final_submit.click()
                print("✅ 게시 완료")
                time.sleep(3)
                
            except Exception as e:
                print("게시판 선택 팝업 없음 (기본 게시판으로 게시됨)")
                time.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ 게시 버튼 클릭 실패: {str(e)}")
            return False
                
        except Exception as e:
            print(f"❌ ======= 오류 발생 ========")
            print(f"{str(e)}")
            return False

    def cleanup(self):
        """리소스 정리"""
        if self.driver:  # driver가 존재할 때만 정리
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            
        # VPN 연결 해제
        try:
            # VPN 해제 로직 추가 (실제 구현 필요)
            print("VPN disconnected")
        except:
            pass

    def __del__(self):
        """소멸자에서 리소스 정리"""
        self.cleanup()

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
            
        success_count = 0
        
        # 모든 밴드에 포스팅
        for band_idx, band in enumerate(bands, 1):
            if bot.post_to_band(band, None, band_idx):
                success_count += 1
            
            # 다음 밴드로 이동 전 4~6분 랜덤 대기
            if band_idx < len(bands):
                wait_time = random.randint(240, 360)  # 4분(240초) ~ 6분(360초)
                print(f"\n현재 진행 상황:")
                print(f"- 밴드 진행: {band_idx}/{len(bands)}")
                print(f"- 성공: {success_count}회")
                print(f"다음 밴드로 이동 전 {wait_time}초({wait_time/60:.1f}분) 대기...")
                time.sleep(wait_time)
        
        print(f"\n포스팅 통계:")
        print(f"- 총 시도: {len(bands)}회")
        print(f"- 성공: {success_count}회")
        print(f"- 실패: {len(bands) - success_count}회")
        
        print("\n============== 모든 작업 완료 ==============")
        
    except Exception as e:
        print(f"\n============== 오류 발생 ==============")
        print(f"Error: {str(e)}")
        print("=======================================")
    finally:
        if bot:
            bot.cleanup()

if __name__ == "__main__":
    main()






from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys  # Keys import 추가
import os
import json
import time
import random
import subprocess
import shutil
import requests

# pyperclip import를 try-except로 감싸서 실패하면 대체 구현 사용
try:
    import pyperclip
except ImportError:
    class PyperclipFallback:
        @staticmethod
        def copy(text):
            pass
        @staticmethod
        def paste():
            return ""
    pyperclip = PyperclipFallback()

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
            
            # Chrome 프로필 디렉토리 설정
            profile_dir = os.path.join(self.script_dir, "chrome-profile")
            
            # 프로필 디렉토리 초기화
            if os.path.exists(profile_dir):
                try:
                    shutil.rmtree(profile_dir)
                except:
                    print("기존 프로필 삭제 실패 (무시)")
            time.sleep(1)
            
            # 새 프로필 디렉토리 생성
            os.makedirs(f"{profile_dir}/Default", exist_ok=True)
            
            # chrome_profile.zip 압축 해제
            if os.path.exists("chrome_profile.zip"):
                print("✅ 크롬 프로필 압축 해제 시작...")
                if os.name == 'nt':  # Windows
                    os.system(f"powershell Expand-Archive -Path chrome_profile.zip -DestinationPath {profile_dir} -Force")
                else:  # Linux/Mac
                    os.system(f"unzip -o chrome_profile.zip -d {profile_dir}")
                print("✅ 크롬 프로필 압축 해제 완료")
                
                # 권한 설정
                if os.name != 'nt':
                    os.system(f"chmod -R 777 {profile_dir}")
            else:
                print("⚠️ chrome_profile.zip 파일이 없습니다!")
            
            # 기본 Chrome 옵션 설정
            options.add_argument(f"--user-data-dir={os.path.abspath(profile_dir)}")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--password-store=basic")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            
            # Headless 모드 설정 (GitHub Actions에서만)
            if os.getenv('GITHUB_ACTIONS'):
                options.add_argument("--headless=new")
            
            # 자동화 감지 방지
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # 프록시 설정
            if os.getenv('GITHUB_ACTIONS'):
                options.add_argument("--proxy-server=socks5://127.0.0.1:1080")
            
            # 드라이버 생성
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            
            # 자동화 감지 방지를 위한 JavaScript 실행
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
            """)
            
            # 기존 쿠키 복원
            try:
                cookies_file = os.path.join(profile_dir, "Default", "Cookies")
                if os.path.exists(cookies_file):
                    print("✅ 기존 쿠키 파일 발견")
                else:
                    print("⚠️ 쿠키 파일을 찾을 수 없습니다")
            except:
                print("⚠️ 쿠키 확인 실패 (무시)")
            
            # 초기 페이지 로드 테스트
            self.driver.get("about:blank")
            time.sleep(2)
            
            print(f"✅ Chrome driver initialized with profile: {profile_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Driver setup failed: {str(e)}")
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
        """버전0과 동일한 로그인 순서로 변경"""
        try:
            print("\n============== 로그인 시작 ==============")
            
            # 1. 로그인 페이지로 이동
            print("\n1. 로그인 페이지로 이동...")
            self.driver.get("https://auth.band.us/login")
            time.sleep(5)
            
            # 2. 이메일 로그인 버튼 찾기
            email_login_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".uButtonRound.-h56.-icoType.-email"))
            )
            print("✓ 이메일 로그인 버튼 발견")
            email_login_btn.click()
            time.sleep(3)
            
            # 3. 이메일 입력
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                email = config.get('email', '')
                password = config.get('password', '')
                
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#input_email"))
            )
            email_input.send_keys(email)
            time.sleep(2)
            
            # 4. 다음 버튼 클릭
            next_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".uBtn.-tcType.-confirm"))
            )
            next_btn.click()
            time.sleep(3)
            
            # 5. 비밀번호 입력
            pw_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#pw"))
            )
            pw_input.send_keys(password)
            time.sleep(2)
            
            # 6. 로그인 버튼 클릭
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".uBtn.-tcType.-confirm"))
            )
            login_btn.click()
            time.sleep(5)
            
            # 7. 로그인 완료 확인
            if "auth.band.us" not in self.driver.current_url:
                print("✅ 로그인 성공!")
                print(f"현재 URL: {self.driver.current_url}")
                
                # 8. 피드 페이지로 이동
                print("\n피드 페이지로 이동...")
                self.driver.get("https://band.us/feed")
                time.sleep(5)
                return True
                
            else:
                raise Exception("로그인 실패 - 인증 페이지를 벗어나지 못했습니다.")
                
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
            print("에디터 찾는 중...")
            editor_selectors = [
                'div.contentEditor._richEditor.skin3',
                'div[contenteditable="true"][aria-labelledby="postWriteFormPlaceholderText"]',
                'div.contentEditor[contenteditable="true"]'
            ]
            
            editor = None
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
            
            # 기존 텍스트 클리어
            editor.clear()
            time.sleep(1)
            
            # URL 입력 전 에디터 클릭
            self.driver.execute_script("arguments[0].click();", editor)
            time.sleep(1)

            # URL 입력 전에 JavaScript 실행
            print("프리뷰 로딩 준비...")
            self.driver.execute_script("""
                // URL 프리뷰 핸들러 강제 등록
                window.urlPreviewHandler = function(url) {
                    var previewContainer = document.createElement('div');
                    previewContainer.className = 'urlPreview';
                    previewContainer.style.display = 'block';
                    
                    // 에디터 찾기
                    var editor = document.querySelector('div[contenteditable="true"]');
                    if (editor) {
                        editor.parentNode.insertBefore(previewContainer, editor.nextSibling);
                    }
                };
                
                // URL 입력 이벤트 감지기 등록
                document.addEventListener('input', function(e) {
                    if (e.target.getAttribute('contenteditable') === 'true') {
                        // URL 패턴 매칭
                        var urlPattern = /(https?:\/\/[^\s]+)/g;
                        var matches = e.target.innerText.match(urlPattern);
                        if (matches) {
                            matches.forEach(function(url) {
                                urlPreviewHandler(url);
                            });
                        }
                    }
                }, true);
            """)
            
            # URL 입력 및 프리뷰 로딩 강제화
            print("\nURL 입력 및 프리뷰 강제 로딩 시작...")
            try:
                # URL 입력
                editor.send_keys(post_url)
                editor.send_keys(Keys.ENTER)  # 엔터키로 강제 로딩
                time.sleep(5)
                
                # JavaScript 이벤트 발생
                self.driver.execute_script("""
                    var editor = document.querySelector('div[contenteditable="true"]');
                    if (editor) {
                        editor.dispatchEvent(new Event('input', { bubbles: true }));
                        editor.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                """)
                time.sleep(5)
                
                print("✅ URL 입력 및 이벤트 발생 완료")
            except Exception as e:
                print(f"⚠️ URL 입력 중 오류 (계속 진행): {e}")

            # 프리뷰 로딩 대기
            print("\n프리뷰 로딩 대기 중...")
            max_wait = 30
            preview_found = False
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    preview = WebDriverWait(self.driver, 1).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.urlPreview'))
                    )
                    if (preview and preview.is_displayed()):
                        print("✅ 프리뷰 발견")
                        preview_found = True
                        break
                except:
                    print(f"프리뷰 로딩 중... ({int(time.time() - start_time)}초)")
                    time.sleep(2)
            
            if not preview_found:
                print("❌ 프리뷰 로딩 실패")
                return False
            
            # URL 입력 후 프리뷰 강제 생성
            print("\n프리뷰 강제 생성 중...")
            self.driver.execute_script("""
                function createPreview(url) {
                    // 기존 프리뷰 제거
                    var oldPreview = document.querySelector('div.urlPreview');
                    if (oldPreview) oldPreview.remove();
                    
                    // 새 프리뷰 컨테이너 생성
                    var container = document.createElement('div');
                    container.className = 'urlPreview _linkPreview';
                    container.style.display = 'block';
                    container.setAttribute('data-url', url);
                    
                    // 프리뷰 내용 생성
                    container.innerHTML = `
                        <div class="previewContent">
                            <div class="url">${url}</div>
                            <div class="frame">
                                <div class="thumb"></div>
                                <div class="text">
                                    <strong class="tit">${url}</strong>
                                    <p class="desc"></p>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // 에디터 다음에 삽입
                    var editor = document.querySelector('div[contenteditable="true"]');
                    if (editor && editor.parentNode) {
                        editor.parentNode.insertBefore(container, editor.nextSibling);
                    }
                    
                    // 입력 이벤트 발생
                    editor.dispatchEvent(new Event('input', { bubbles: true }));
                }
                
                // URL로 프리뷰 생성
                createPreview(arguments[0]);
            """, post_url)
            
            # 프리뷰 생성 확인을 위한 짧은 대기
            time.sleep(2)
            print("✅ 프리뷰 생성 완료")
            
            # URL 텍스트 삭제 시도 (프리뷰 유지)
            try:
                editor.clear()
                time.sleep(1)
                
                # 프리뷰 유지 강제화
                self.driver.execute_script("""
                    var preview = document.querySelector('div.urlPreview');
                    if (preview) {
                        preview.style.display = 'block';
                        preview.style.opacity = '1';
                    }
                """)
                print("✅ URL 텍스트 삭제 완료, 프리뷰 유지")
            except:
                print("⚠️ URL 텍스트 삭제 실패 (무시하고 계속 진행)")
            
            time.sleep(2)  # 안정성을 위한 추가 대기
            
            # 게시 버튼 클릭
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-sizeM._btnSubmitPost.-confirm'))
                )
                print("✅ 게시 버튼 발견")
                submit_btn.click()
                print("✅ 게시 완료")
                time.sleep(3)
                return True
            except Exception as e:
                print("❌ 게시 실패:")
                print(f"- 오류 내용: {str(e)}")
                return False
                
        except Exception as e:
            print(f"포스팅 실패: {str(e)}")
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
                
                # 다음 밴드로 이동 전 4~6분 랜덤 대기
                if band_idx < len(bands):
                    wait_time = random.randint(240, 360)  # 4분(240초) ~ 6분(360초)
                    print(f"\n현재 진행 상황:")
                    print(f"- URL {url_num}/{len(urls)}")
                    print(f"- 현재 URL: {post_url}")
                    print(f"- 밴드 진행: {band_idx}/{len(bands)}")
                    print(f"- 성공: {success_count}회")
                    print(f"다음 밴드로 이동 전 {wait_time}초({wait_time/60:.1f}분) 대기...")
                    time.sleep(wait_time)
            
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








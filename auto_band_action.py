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
        self.driver = None
        
        # driver 설정 실패 시 예외 처리 추가
        if not self.setup_driver():
            raise Exception("Chrome driver 초기화 실패")

    def setup_driver(self):
        try:
            options = Options()
            
            # Chrome 프로필 디렉토리 설정
            profile_dir = os.path.abspath("chrome-profile")
            print(f"프로필 디렉토리: {profile_dir}")
            
            # 프로필 디렉토리와 필수 하위 디렉토리 생성
            default_dir = os.path.join(profile_dir, 'Default')
            for path in [profile_dir, default_dir]:
                os.makedirs(path, exist_ok=True)
            
            # Chrome 옵션 설정
            options.add_argument(f'--user-data-dir={profile_dir}')
            options.add_argument('--profile-directory=Default')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-web-security')  # 쿠키 제한 해제
            options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            
            # 자동화 감지 방지
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 쿠키 관련 프리퍼런스 설정
            prefs = {
                'profile.default_content_settings.cookies': 1,
                'profile.block_third_party_cookies': False,
                'profile.cookie_controls_mode': 0,
                'credentials_enable_service': True,
                'profile.password_manager_enabled': True
            }
            options.add_experimental_option('prefs', prefs)
            
            print("\nChrome 옵션 설정 완료")
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            
            # band.us 도메인에 필요한 쿠키 직접 추가
            print("\n쿠키 설정 중...")
            self.driver.get('https://band.us')
            time.sleep(2)
            
            cookies_to_add = [
                {
                    'name': 'JSESSIONID',
                    'value': 'your_jsessionid_value',
                    'domain': 'band.us'
                },
                {
                    'name': 'BBC',
                    'value': 'your_bbc_value',
                    'domain': '.band.us'
                },
                {
                    'name': 'di',
                    'value': 'your_di_value',
                    'domain': '.band.us'
                },
                {
                    'name': 'SESSION',
                    'value': 'your_session_value',
                    'domain': 'auth.band.us'
                },
                {
                    'name': 'language',
                    'value': 'ko_KR',
                    'domain': '.band.us'
                }
            ]
            
            for cookie in cookies_to_add:
                try:
                    self.driver.add_cookie(cookie)
                    print(f"Added cookie: {cookie['name']} for {cookie['domain']}")
                except Exception as e:
                    print(f"Failed to add cookie {cookie['name']}: {str(e)}")
            
            # 쿠키 설정 후 페이지 새로고침
            self.driver.refresh()
            time.sleep(3)
            
            # 최종 쿠키 상태 확인
            cookies = self.driver.get_cookies()
            print("\n현재 쿠키 상태:")
            print(f"쿠키 수: {len(cookies)}")
            for cookie in cookies:
                print(f"Cookie: {cookie.get('name')} = {cookie.get('domain')}")
            
            # band.us 메인 페이지 접속 테스트
            print("\n로그인 상태 확인 중...")
            self.driver.get('https://band.us/feed')
            time.sleep(5)
            
            if 'auth.band.us/login' in self.driver.current_url:
                raise Exception("쿠키 인증 실패")
                
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
            
            # URL 입력
            print(f"URL 입력 시작: {post_url}")
            editor.send_keys(post_url)
            print("URL 입력 완료")
            time.sleep(5)  # URL 입력 후 대기
            
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
                    if (preview.is_displayed()):
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

    def __del__(self):
        """소멸자에서 리소스 정리"""
        self.cleanup()

def main():
    bot = None
    try:
        bot = BandAutoAction()
        print("\n============== 작업 시작 ==============")
        
        # 특정 밴드로 직접 이동
        target_band_url = 'https://band.us/band/96689964'
        print(f"\n타겟 밴드로 이동 중... {target_band_url}")
        bot.driver.get(target_band_url)
        time.sleep(10)  # 페이지 로딩 대기 시간 증가
        
        # 현재 URL 확인
        current_url = bot.driver.current_url
        print(f"현재 URL: {current_url}")
        
        if 'auth.band.us/login' in current_url:
            raise Exception("로그인이 필요합니다")
            
        # 페이지가 완전히 로드될 때까지 대기
        try:
            print("글쓰기 버튼 찾는 중...")
            write_btn = WebDriverWait(bot.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button._btnPostWrite'))
            )
            
            # 버튼이 클릭 가능한 상태가 될 때까지 대기
            write_btn = WebDriverWait(bot.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button._btnPostWrite'))
            )
            print("글쓰기 버튼 발견")
            
            # JavaScript로 버튼 클릭
            bot.driver.execute_script("arguments[0].click();", write_btn)
            print("글쓰기 버튼 클릭 완료")
            time.sleep(5)  # 에디터 로딩 대기
            
            # 에디터 찾기
            editor = WebDriverWait(bot.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.contentEditor[contenteditable="true"]'))
            )
            print("에디터 발견")
            
            # 에디터가 활성화될 때까지 대기
            editor = WebDriverWait(bot.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.contentEditor[contenteditable="true"]'))
            )
            
            # 에디터 클릭 및 URL 입력
            test_url = "https://example.com"
            print(f"URL 입력 시작: {test_url}")
            bot.driver.execute_script("arguments[0].click();", editor)
            time.sleep(2)
            editor.send_keys(test_url)
            print("URL 입력 완료")
            
            # 프리뷰 로딩 대기
            time.sleep(10)
            print("프리뷰 대기 완료")
            
        except Exception as e:
            print(f"\n글쓰기 처리 중 오류 발생:")
            print(f"마지막 URL: {bot.driver.current_url}")
            print(f"오류 내용: {str(e)}")
            raise Exception(f"글쓰기 버튼 처리 실패: {str(e)}")
            
    except Exception as e:
        print(f"\n============== 오류 발생 ==============")
        print(f"Error: {str(e)}")
        print("=======================================")
    finally:
        if bot:
            bot.cleanup()

if __name__ == "__main__":
    main()









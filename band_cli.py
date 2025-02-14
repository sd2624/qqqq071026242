import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

def get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 크롬 프로필 경로 설정 - 저장소에 있는 프로필 사용
    profile_path = os.path.join(os.getcwd(), 'chrome_profile_qqqq071026242')
    print(f"프로필 경로: {profile_path}")
    options.add_argument(f'--user-data-dir={profile_path}')
    options.add_argument('--profile-directory=Default')
    
    # 한국어 및 위치 설정
    options.add_argument('--lang=ko_KR')
    options.add_argument('--geolocation=37.5665,126.9780')  # 서울 좌표
    
    # VPN 프록시 설정
    options.add_argument('--proxy-server=socks5://127.0.0.1:1080')
    
    # User Agent 설정
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
    
    return options

def log_step(message):
    """워크플로우에서 잘 보이도록 단계별 로깅"""
    print(f"::group::{message}")
    print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔄 {message}")

def log_end():
    """로그 그룹 종료"""
    print("::endgroup::")

def post_to_bands():
    urls = json.loads(os.getenv('URLS_JSON', '{}'))
    if not urls:
        log_step("❌ URL 설정을 찾을 수 없음")
        return
        
    print("::group::Chrome 초기화")
    driver = webdriver.Chrome(options=get_chrome_options())
    print("Chrome 드라이버 생성 완료")
    print("::endgroup::")
    
    try:
        print("::group::밴드 페이지 로딩")
        driver.get('https://band.us/feed')
        time.sleep(5)
        print(f"현재 URL: {driver.current_url}")
        
        # 자동 로그인 상태 확인 및 필요시 로그인
        try:
            # 프로필 이미지로 로그인 상태 확인
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.profileImage'))
            )
            print("✅ 이미 로그인된 상태")
        except:
            print("로그인 필요, 로그인 페이지로 이동...")
            driver.get('https://auth.band.us/login')
            time.sleep(3)
            
            # 이메일 로그인 버튼 클릭
            email_login_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.uButtonRound.-h56.-icoType.-email'))
            )
            print("이메일 로그인 버튼 클릭")
            email_login_btn.click()
            time.sleep(2)
            
            # 여기서 이메일/비밀번호는 크롬 프로필에서 자동 입력됨
            print("자동 입력 대기 중...")
            time.sleep(5)
            
            # 로그인 버튼 클릭
            login_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.uBtn.-tcType.-confirm'))
            )
            print("로그인 버튼 클릭")
            login_btn.click()
            time.sleep(5)
            
            # 로그인 성공 확인
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.profileImage'))
                )
                print("✅ 로그인 성공")
            except:
                print("❌ 로그인 실패")
                raise Exception("로그인에 실패했습니다")
            
        print("::endgroup::")
        
        log_step("📋 밴드 목록 로딩 중")
        for i in range(3):
            print(f"스크롤 다운 {i+1}/3...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # 더보기 버튼 클릭
        try:
            print("🔍 더보기 버튼 찾는 중...")
            more_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.myBandMoreView._btnMore'))
            )
            more_btn.click()
            print("✅ 더보기 버튼 클릭 성공")
            time.sleep(3)
        except:
            print("⚠️ 더보기 버튼 없음 (무시)")
        
        bands = driver.find_elements(By.CSS_SELECTOR, 'a.itemMyBand')
        print(f"✅ 총 {len(bands)}개의 밴드 발견")
        log_end()
        
        # 각 밴드에 포스팅
        for idx, band in enumerate(bands, 1):
            try:
                band_url = band.get_attribute('href')
                band_name = band.find_element(By.CSS_SELECTOR, 'strong.ellipsis').text
                
                log_step(f"📝 밴드 포스팅 {idx}/{len(bands)}: {band_name}")
                print(f"🔗 URL: {band_url}")
                
                # 밴드로 이동
                print("➡️ 밴드 페이지 이동 중...")
                driver.get(band_url)
                time.sleep(3)
                
                # 글쓰기 버튼 클릭
                print("✏️ 글쓰기 버튼 클릭 중...")
                write_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button._btnPostWrite'))
                )
                write_btn.click()
                time.sleep(2)
                
                # URL 입력
                print("📋 URL 입력 중...")
                editor = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
                )
                current_url = urls[str(url_index)]
                print(f"🔗 사용 URL ({url_index}번): {current_url}")
                editor.send_keys(current_url)
                time.sleep(1)
                
                # 게시 버튼 클릭
                print("📤 게시 버튼 클릭 중...")
                submit_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-sizeM._btnSubmitPost.-confirm'))
                )
                submit_btn.click()
                time.sleep(3)
                
                # 게시판 선택 팝업 처리
                try:
                    print("📂 게시판 선택 팝업 확인 중...")
                    select_first = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'label.flexList'))
                    )
                    print("✅ 첫 번째 게시판 선택")
                    select_first.click()
                    time.sleep(1)
                    
                    confirm_btn = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-confirm._btnConfirm'))
                    )
                    print("✅ 게시판 선택 확인")
                    confirm_btn.click()
                    time.sleep(2)
                except:
                    print("ℹ️ 게시판 선택 팝업 없음")
                
                print("✅ 포스팅 완료")
                log_end()
                
            except Exception as e:
                print(f"❌ 오류 발생: {str(e)}")
                log_end()
                continue
                
        log_step(f"🏁 모든 밴드 포스팅 완료")
        print(f"📊 통계:")
        print(f"- 시도한 밴드 수: {len(bands)}")
        print(f"- 현재 URL 인덱스: {url_index}")
        log_end()
        
        # 다음 URL 준비
        url_index += 1
        if url_index > 30:
            url_index = 1
            
    except Exception as e:
        log_step("❌ 치명적 오류 발생")
        print(f"오류 내용: {str(e)}")
        log_end()
    finally:
        log_step("🔚 드라이버 정리 중")
        driver.quit()
        log_end()

if __name__ == "__main__":
    print("::notice::밴드 자동 포스팅 시작")
    post_to_bands()
    print("::notice::작업 완료")

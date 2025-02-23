import tkinter as tk
from tkinter import ttk, messagebox, filedialog  # 파일 선택 대화상자 추가
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains  # 추가된 import
import pyperclip  # 추가된 import
import time
import threading
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import json
import os
import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import git  # PyGithub 라이브러리 추가
from github import Github
import subprocess
import sys
import shutil  # shutil 모듈 추가
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import random  # 추가된 import

class BandAutoGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("밴드 자동 포스팅")
        self.root.geometry("500x700")  # 높이 증가
        self.script_dir = os.path.dirname(os.path.abspath(__file__))  # script_dir 추가
        self.poster = BandAutoPoster(self)
        self.save_dir = os.path.join(self.script_dir, '저장')
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.github_token = self.load_github_token()
        self.setup_gui()

    def setup_gui(self):
        # 설정 프레임
        settings_frame = ttk.LabelFrame(self.root, text="설정", padding=10)
        settings_frame.pack(fill=tk.X, padx=5, pady=5)

        # 이메일 설정
        ttk.Label(settings_frame, text="이메일:").grid(row=0, column=0, sticky=tk.W)
        self.email_var = tk.StringVar(value=self.poster.config.get('email', ''))
        ttk.Entry(settings_frame, textvariable=self.email_var).grid(row=0, column=1, sticky=tk.EW)

        # 비밀번호 설정
        ttk.Label(settings_frame, text="비밀번호:").grid(row=1, column=0, sticky=tk.W)
        self.password_var = tk.StringVar(value=self.poster.config.get('password', ''))
        ttk.Entry(settings_frame, textvariable=self.password_var, show="*").grid(row=1, column=1, sticky=tk.EW)

        # URL 설정
        ttk.Label(settings_frame, text="포스팅 URL:").grid(row=2, column=0, sticky=tk.W)
        self.url_var = tk.StringVar(value=self.poster.config.get('post_url', ''))
        ttk.Entry(settings_frame, textvariable=self.url_var).grid(row=2, column=1, sticky=tk.EW)

        # 제목 설정 (추가)
        ttk.Label(settings_frame, text="포스팅 제목:").grid(row=3, column=0, sticky=tk.W)
        self.title_var = tk.StringVar(value=self.poster.config.get('title', ''))
        ttk.Entry(settings_frame, textvariable=self.title_var).grid(row=3, column=1, sticky=tk.EW)

        # 게시 시간 설정 (추가)
        ttk.Label(settings_frame, text="게시 시간(HH:MM):").grid(row=4, column=0, sticky=tk.W)
        self.post_time_var = tk.StringVar(value=self.poster.config.get('post_time', '09:00'))
        ttk.Entry(settings_frame, textvariable=self.post_time_var).grid(row=4, column=1, sticky=tk.EW)

        # 간격 설정
        ttk.Label(settings_frame, text="실행 간격(시간):").grid(row=5, column=0, sticky=tk.W)
        self.interval_var = tk.StringVar(value=str(self.poster.config.get('interval_hours', 24)))
        ttk.Entry(settings_frame, textvariable=self.interval_var).grid(row=5, column=1, sticky=tk.EW)

        # 저장/불러오기 프레임 수정
        save_frame = ttk.LabelFrame(self.root, text="포스팅 저장/불러오기", padding=10)
        save_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 기본 저장 버튼
        save_btn = ttk.Button(save_frame, text="저장", command=lambda: self.save_posting())
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 다른 이름으로 저장 버튼
        save_as_btn = ttk.Button(save_frame, text="다른 이름으로 저장", command=lambda: self.save_posting(save_as=True))
        save_as_btn.pack(side=tk.LEFT, padx=5)
        
        # 불러오기 버튼
        load_btn = ttk.Button(save_frame, text="불러오기", command=self.load_posting)
        load_btn.pack(side=tk.LEFT, padx=5)

        # 내보내기/실행 프레임 추가
        export_frame = ttk.LabelFrame(self.root, text="GitHub 내보내기/실행", padding=10)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # GitHub 토큰 입력
        ttk.Label(export_frame, text="GitHub 토큰:").pack(side=tk.LEFT, padx=5)
        self.github_token_var = tk.StringVar(value=self.github_token)
        token_entry = ttk.Entry(export_frame, textvariable=self.github_token_var, show="*")
        token_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 내보내기 버튼
        export_btn = ttk.Button(export_frame, text="GitHub에 내보내기", command=self.export_to_github)
        export_btn.pack(side=tk.LEFT, padx=5)

        # 상태 표시
        self.status_var = tk.StringVar(value="대기 중...")
        ttk.Label(self.root, textvariable=self.status_var).pack(pady=5)

        # 버튼 프레임
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        # 시작/중지 버튼
        self.start_btn = ttk.Button(btn_frame, text="시작", command=self.start_posting)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="중지", command=self.stop_posting, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 설정 저장 버튼
        ttk.Button(btn_frame, text="설정 저장", command=self.save_config).pack(side=tk.RIGHT, padx=5)

        # 로그 영역 추가
        log_frame = ttk.LabelFrame(self.root, text="로그", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 로그 텍스트 영역
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 복사 버튼 추가
        copy_btn = ttk.Button(log_frame, text="로그 복사", command=self.copy_log)
        copy_btn.pack(pady=5)

    def copy_log(self):
        log_content = self.log_text.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(log_content)
        messagebox.showinfo("알림", "로그가 클립보드에 복사되었습니다.")

    def save_posting(self, save_as=False):
        try:
            title = self.title_var.get()
            email = self.email_var.get()
            
            if not title:
                messagebox.showerror("오류", "포스팅 제목을 입력해주세요.")
                return
            
            if not email and not save_as:
                messagebox.showerror("오류", "이메일 주소를 입력해주세요.")
                return
            
            # 저장할 데이터 준비
            save_data = {
                'email': self.email_var.get(),
                'password': self.password_var.get(),
                'post_url': self.url_var.get(),
                'title': self.title_var.get(),
                'post_time': self.post_time_var.get(),
                'interval_hours': self.interval_var.get(),
                'saved_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if save_as:
                # 다른 이름으로 저장 - 폴더 선택 대화상자
                save_dir = filedialog.askdirectory(
                    initialdir=self.save_dir,
                    title="저장할 폴더 선택"
                )
                
                if not save_dir:  # 취소한 경우
                    return
                    
                # 파일명 생성
                filename = "".join(x for x in title if x.isalnum() or x in [' ', '-', '_']).strip()
                filename = f"{filename}.json"
                filepath = os.path.join(save_dir, filename)
                
            else:
                # 기본 저장 - 이메일 폴더에 저장
                email_dir = os.path.join(self.save_dir, email)
                if not os.path.exists(email_dir):
                    os.makedirs(email_dir)
                
                filename = "".join(x for x in title if x.isalnum() or x in [' ', '-', '_']).strip()
                filename = f"{filename}.json"
                filepath = os.path.join(email_dir, filename)
            
            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
                
            messagebox.showinfo("알림", f"저장 완료:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {str(e)}")

    def load_posting(self):
        try:
            # Windows 스타일 파일 선택 대화상자
            filepath = filedialog.askopenfilename(
                initialdir=self.save_dir,
                title="저장된 포스팅 불러오기",
                filetypes=(("JSON 파일", "*.json"), ("모든 파일", "*.*")),
                parent=self.root
            )
            
            if filepath:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # 모든 설정값 복원
                    self.email_var.set(data.get('email', ''))
                    self.password_var.set(data.get('password', ''))
                    self.url_var.set(data.get('post_url', ''))
                    self.title_var.set(data.get('title', ''))
                    self.post_time_var.set(data.get('post_time', '09:00'))
                    self.interval_var.set(data.get('interval_hours', '24'))
                    
                    saved_date = data.get('saved_date', '알 수 없음')
                    messagebox.showinfo("알림", f"포스팅 내용을 불러왔습니다.\n저장 날짜: {saved_date}")
                    
                except Exception as e:
                    messagebox.showerror("오류", f"파일 읽기 실패: {str(e)}")
            
        except Exception as e:
            messagebox.showerror("오류", f"불러오기 실패: {str(e)}")

    def save_config(self):
        try:
            config = {
                'email': self.email_var.get(),
                'password': self.email_var.get(),
                'post_url': self.url_var.get(),
                'title': self.title_var.get(),  # 추가
                'post_time': self.post_time_var.get(),  # 추가
                'interval_hours': int(self.interval_var.get()),
                'bands': self.poster.config.get('bands', [])
            }
            self.poster.save_config(config)
            messagebox.showinfo("알림", "설정이 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패: {str(e)}")

    def start_posting(self):
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=self.poster.start_posting, daemon=True).start()

    def stop_posting(self):
        self.poster.stop_posting()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def update_status(self, message):
        self.status_var.set(message)
        # 로그에 타임스탬프와 함께 메시지 추가
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)  # 자동 스크롤

    def run(self):
        self.root.mainloop()

    def load_github_token(self):
        try:
            token_path = os.path.join(self.poster.script_dir, 'github_token.txt')
            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    return f.read().strip()  # strip()으로 공백과 개행문자 제거
        except:
            pass
        return ''

    def save_github_token(self):
        token_path = os.path.join(self.poster.script_dir, 'github_token.txt')
        try:
            with open(token_path, 'w') as f:
                f.write(self.github_token_var.get())
        except Exception as e:
            self.update_status(f"GitHub 토큰 저장 실패: {str(e)}")
            messagebox.showerror("오류", f"GitHub 토큰 저장 실패: {str(e)}")

    def download_artifact(self, artifact_name):
        try:
            # GitHub API를 사용하여 아티팩트 목록을 가져옴
            g = Github(self.github_token_var.get().strip())
            repo = g.get_repo("kkdamoa/1")
            artifacts = repo.get_artifacts()
            
            # 아티팩트가 존재하는지 확인
            artifact = next((a for a in artifacts if a.name == artifact_name), None)
            if not artifact:
                raise Exception(f"Artifact not found for name: {artifact_name}")
            
            # 아티팩트 다운로드
            artifact.download()
            self.update_status(f"Artifact '{artifact_name}' 다운로드 완료")
            
        except Exception as e:
            self.update_status(f"Artifact 다운로드 실패: {str(e)}")
            messagebox.showerror("오류", f"Artifact 다운로드 실패: {str(e)}")

    def export_to_github(self):
        try:
            token = self.github_token_var.get().strip()
            if not token:
                messagebox.showerror("오류", "GitHub 토큰을 입력해주세요.")
                return

            # GitHub API 연결
            try:
                g = Github(token)
                repo = g.get_repo("kkdamoa/1")
                
                # 현재 GUI의 값들을 가져옴
                current_config = {
                    'email': self.email_var.get().strip(),
                    'password': self.password_var.get().strip(),
                    'post_url': self.url_var.get().strip(),
                    'title': self.title_var.get().strip(),
                    'post_time': self.post_time_var.get().strip(),
                    'interval_hours': int(self.interval_var.get().strip()),
                    'bands': []
                }

                # 두 config.json 파일 업데이트
                config_paths = [
                    os.path.join(os.path.dirname(self.script_dir), 'config.json'),  # 루트 config
                    os.path.join(self.script_dir, 'config.json')  # 밴드 폴더 config
                ]

                for config_path in config_paths:
                    try:
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(current_config, f, ensure_ascii=False, indent=4)
                        self.update_status(f"설정 파일 업데이트 완료: {config_path}")
                    except Exception as e:
                        self.update_status(f"⚠️ 설정 파일 업데이트 실패: {config_path}")
                        self.update_status(f"오류: {str(e)}")

                # GitHub Actions secrets 업데이트
                secrets_to_update = {
                    'EMAIL': current_config['email'],
                    'PASSWORD': current_config['password'],
                    'URL': current_config['post_url'],
                    'TITLE': current_config['title'],
                    'TIME': current_config['post_time'],
                    'INTERVAL': str(current_config['interval_hours'])
                }

                self.update_status("GitHub Actions secrets 업데이트 중...")
                
                # 기존 secrets 모두 삭제 후 새로 생성
                for key, value in secrets_to_update.items():
                    try:
                        # 기존 secret 삭제
                        try:
                            repo.delete_secret(key)
                        except:
                            pass
                        # 새 secret 생성
                        repo.create_secret(key, str(value))
                        self.update_status(f"✓ Secret '{key}' 업데이트 완료")
                    except Exception as e:
                        self.update_status(f"⚠️ Secret '{key}' 업데이트 실패: {str(e)}")

                self.update_status("GitHub Actions secrets 업데이트 완료!")

            except Exception as e:
                self.update_status(f"설정 파일 또는 GitHub API 오류: {str(e)}")
                messagebox.showerror("오류", str(e))
                return

            # 이후 Git 작업 진행
            try:
                repo_path = os.path.dirname(os.path.dirname(self.script_dir))  # Change this line to:
                source_dir = os.path.dirname(self.script_dir)  # Use parent of script_dir as source
                temp_dir = os.path.join(repo_path, f'temp_git_{int(time.time())}')
                original_dir = os.getcwd()

                self.update_status(f"작업 시작:\n소스={source_dir}\n임시={temp_dir}")

                # 임시 디렉토리 초기화
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    time.sleep(1)  # 삭제 완료 대기
                os.makedirs(temp_dir)

                try:
                    # 파일 복사 전 디렉토리 생성
                    os.makedirs(os.path.join(temp_dir, '밴드'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, '.github', 'workflows'), exist_ok=True)

                    # 파일 복사 함수 정의
                    def safe_copy(src, dst):
                        try:
                            if os.path.exists(dst):
                                if os.path.isdir(dst):
                                    shutil.rmtree(dst)
                                else:
                                    os.remove(dst)
                                time.sleep(1)  # 삭제 후 대기
                            
                            if os.path.isdir(src):
                                shutil.copytree(src, dst)
                            else:
                                dst_dir = os.path.dirname(dst)
                                if not os.path.exists(dst_dir):
                                    os.makedirs(dst_dir)
                                shutil.copy2(src, dst)
                            return True
                        except Exception as e:
                            self.update_status(f"복사 실패 ({src} -> {dst}): {str(e)}")
                            return False

                    # 파일 목록에서 chrome_profile 관련 항목 제거
                    copy_list = [
                        ('run_band_poster.py', ''),
                        ('requirements.txt', ''),
                        ('config.json', ''),
                        ('band_cookies.json', ''),
                        ('band_urls.json', ''),
                        ('band_auto_poster.py', '밴드'),
                        ('config.json', '밴드'),
                        ('band_cookies.json', '밴드'),
                        ('band_urls.json', '밴드'),
                        ('band_auto_post.yml', '.github/workflows')
                    ]

                    # 일반 파일 복사
                    for filename, subdir in copy_list:
                        src = os.path.join(source_dir, subdir, filename) if subdir else os.path.join(source_dir, filename)
                        dst = os.path.join(temp_dir, subdir, filename) if subdir else os.path.join(temp_dir, filename)
                        if os.path.exists(src):
                            if safe_copy(src, dst):
                                self.update_status(f"복사됨: {os.path.relpath(dst, temp_dir)}")
                        else:
                            self.update_status(f"파일 없음: {os.path.relpath(src, source_dir)}")

                    # Chrome 프로필 별도 복사
                    chrome_profile_src = os.path.join(source_dir, 'chrome_profile')
                    chrome_profile_dst = os.path.join(temp_dir, 'chrome_profile')
                    if os.path.exists(chrome_profile_src):
                        if safe_copy(chrome_profile_src, chrome_profile_dst):
                            self.update_status("Chrome 프로필 복사됨: chrome_profile/")

                    band_profile_src = os.path.join(source_dir, '밴드', 'chrome_profile')
                    band_profile_dst = os.path.join(temp_dir, '밴드', 'chrome_profile')
                    if os.path.exists(band_profile_src):
                        if safe_copy(band_profile_src, band_profile_dst):
                            self.update_status("밴드 Chrome 프로필 복사됨: 밴드/chrome_profile/")

                    # Git 작업 시작
                    os.chdir(temp_dir)
                    self.update_status(f"\nGit 초기화 ({os.getcwd()})")

                    # Git 초기화
                    subprocess.run(['git', 'init'], check=True, capture_output=True, text=True)
                    subprocess.run(['git', 'config', '--local', 'user.name', 'kkdamoa'], check=True)
                    subprocess.run(['git', 'config', '--local', 'user.email', 'qufdl0615@naver.com'], check=True)

                    # 파일 추가
                    self.update_status("파일 스테이징...")
                    subprocess.run(['git', 'add', '-A'], check=True)
                    
                    # 현재 상태 확인
                    status = subprocess.run(['git', 'status'], capture_output=True, text=True, check=True)
                    self.update_status(f"Git 상태:\n{status.stdout}")

                    # 커밋
                    commit_msg = f'Update band posting files {datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

                    # 원격 저장소 설정 및 푸시
                    self.update_status("\nGitHub 저장소에 푸시 중...")
                    remote_url = f'https://{token}@github.com/kkdamoa/1.git'
                    subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
                    subprocess.run(['git', 'push', '-f', 'origin', 'master:main'], check=True)

                    self.update_status("GitHub 업로드 완료!")
                    messagebox.showinfo("성공", "GitHub 저장소에 성공적으로 업로드되었습니다.")

                finally:
                    os.chdir(original_dir)
                    try:
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir, ignore_errors=True)
                    except Exception as e:
                        self.update_status(f"임시 디렉토리 정리 실패: {str(e)}")

            except subprocess.CalledProcessError as e:
                error_msg = f"Git 명령어 실패: {e.stdout}\n{e.stderr}" if hasattr(e, 'stdout') else str(e)
                self.update_status(error_msg)
                messagebox.showerror("오류", error_msg)

            except Exception as e:
                self.update_status(f"작업 실패: {str(e)}")
                messagebox.showerror("오류", f"Git 작업 실패: {str(e)}")

        except Exception as e:
            self.update_status(f"내보내기 실패: {str(e)}")
            messagebox.showerror("오류", f"내보내기 실패: {str(e)}")

class BandAutoPoster:
    def __init__(self, gui):
        self.gui = gui
        self.driver = None
        self.running = False
        self.posting_thread = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self.load_config()
        self.bands_file = os.path.join(self.script_dir, 'band_urls.json')
        self.random_delays = [1.1, 1.3, 1.5, 1.7, 2.1, 2.3, 2.5]  # 랜덤 지연 시간 추가

    def save_config(self, config_data):
        """설정 파일을 저장합니다."""
        try:
            config_path = os.path.join(self.script_dir, 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            self.config = config_data
            print(f"설정 파일 저장 완료: {config_path}")
        except Exception as e:
            print(f"설정 파일 저장 실패: {str(e)}")
            raise

    def load_config(self):
        try:
            config_path = os.path.join(self.script_dir, 'config.json')
            if not os.path.exists(config_path):
                # 기본 설정 파일 생성
                default_config = {
                    "email": "your_email@example.com",
                    "password": "your_password",
                    "post_url": "https://example.com/content-to-share",
                    "title": "포스팅 제목",  # 추가
                    "post_time": "09:00",  # 추가
                    "interval_hours": 24,
                    "bands": [
                        {
                            "name": "첫번째 밴드",
                            "url": "https://band.us/band/your_first_band_id"
                        }
                    ]
                }
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
                print(f"설정 파일이 생성되었습니다: {config_path}")
                print("config.json 파일을 수정한 후 다시 실행해주세요.")
                exit(1)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 필수 설정 확인
            required_fields = ['email', 'password', 'post_url', 'bands']
            for field in required_fields:
                if (field not in config):
                    raise ValueError(f"설정 파일에 '{field}' 항목이 없습니다.")
                    
            return config
            
        except Exception as e:
            print(f"설정 파일 로드 중 오류 발생: {str(e)}")
            exit(1)

    def save_band_urls(self, bands):
        """밴드 URL 목록을 파일로 저장"""
        try:
            with open(self.bands_file, 'w', encoding='utf-8') as f:
                json.dump(bands, f, ensure_ascii=False, indent=4)
            self.gui.update_status(f"밴드 URL 저장 완료: {len(bands)}개")
        except Exception as e:
            self.gui.update_status(f"밴드 URL 저장 실패: {str(e)}")

    def load_band_urls(self):
        """저장된 밴드 URL 목록 로드"""
        try:
            if (os.path.exists(self.bands_file)):
                with open(self.bands_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.gui.update_status(f"밴드 URL 로드 실패: {str(e)}")
        return []

    def setup_driver(self):
        try:
            options = webdriver.ChromeOptions()
            
            # headless 모드 비활성화 (GitHub Actions 환경이 아닐 때)
            if not os.getenv('GITHUB_ACTIONS'):
                self.gui.update_status("일반 환경에서 실행 중...")
            else:
                self.gui.update_status("GitHub Actions 환경 감지됨")
                options.add_argument('--headless=new')
            
            # 기본 옵션 설정
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--window-size=1920,1080')
            
            # 프록시 설정
            if os.getenv('GITHUB_ACTIONS'):
                options.add_argument('--proxy-server=socks5://127.0.0.1:1080')
            
            # 자동화 감지 방지
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 최대 재시도 횟수 설정
            max_retries = 3
            current_try = 0
            
            while current_try < max_retries:
                try:
                    current_try += 1
                    self.gui.update_status(f"Chrome 드라이버 초기화 시도 #{current_try}")
                    
                    # Chrome 서비스 설정
                    service = Service()
                    
                    # 드라이버 생성
                    self.driver = webdriver.Chrome(service=service, options=options)
                    
                    # 페이지 로드 타임아웃 설정
                    self.driver.set_page_load_timeout(30)
                    self.driver.implicitly_wait(10)
                    
                    # 연결 테스트
                    self.gui.update_status("연결 테스트 중...")
                    self.driver.get("about:blank")
                    time.sleep(2)
                    
                    # 자동화 탐지 방지 스크립트 실행
                    self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                        'source': '''
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            });
                            window.chrome = {
                                runtime: {},
                                // 기타 필요한 속성들
                            };
                        '''
                    })
                    
                    self.gui.update_status("✅ Chrome 드라이버 초기화 성공")
                    return True
                    
                except Exception as e:
                    self.gui.update_status(f"시도 #{current_try} 실패: {str(e)}")
                    
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None
                    
                    if current_try < max_retries:
                        self.gui.update_status(f"5초 후 재시도... ({current_try}/{max_retries})")
                        time.sleep(5)
                    else:
                        raise Exception(f"Chrome 드라이버 초기화 실패 (최대 재시도 횟수 초과): {str(e)}")
            
            return False
            
        except Exception as e:
            self.gui.update_status(f"❌ Chrome 드라이버 설정 실패: {str(e)}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            return False

    def cleanup_driver(self):
        """드라이버 정리 및 메모리 정리"""
        try:
            if self.driver:
                # 열려있는 모든 탭 닫기
                for handle in self.driver.window_handles[1:]:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
                # 캐시 및 쿠키 삭제
                self.driver.delete_all_cookies()
                self.driver.execute_script("window.localStorage.clear();")
                self.driver.execute_script("window.sessionStorage.clear();")
                
                # 가비지 컬렉션 강제 실행
                self.driver.execute_script("window.gc();")
                
                # 드라이버 종료
                self.driver.quit()
                self.driver = None
                
            # Chrome 프로세스 정리
            self.cleanup_chrome_processes()
            
        except Exception as e:
            self.gui.update_status(f"드라이버 정리 중 오류: {str(e)}")

    def cleanup_chrome_processes(self):
        """Chrome 관련 프로세스를 정리합니다."""
        try:
            if (os.name == 'nt'):  # Windows
                processes = ['chrome.exe', 'chromedriver.exe']
                for proc in processes:
                    try:
                        subprocess.run(['taskkill', '/f', '/im', proc], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                    except:
                        pass
                time.sleep(3)  # 프로세스 종료 대기
            else:  # Linux/Mac
                processes = ['chrome', 'chromedriver']
                for proc in processes:
                    try:
                        subprocess.run(['pkill', '-f', proc],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    except:
                        pass
                time.sleep(3)
        except Exception as e:
            self.gui.update_status(f"프로세스 정리 중 오류: {str(e)}")

    def safe_file_operation(self, operation, max_retries=3, wait_time=2):
        """안전한 파일 작업을 수행합니다."""
        for attempt in range(max_retries):
            try:
                return operation()
            except (PermissionError, OSError) as e:
                if (attempt == max_retries - 1):
                    raise
                self.gui.update_status(f"파일 작업 재시도 중... ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)

    def wait_for_main_page(self, timeout=30):
        start_time = time.time()
        while (time.time() - start_time < timeout):
            current_url = self.driver.current_url
            if (current_url == "https://band.us/"):
                self.gui.update_status("밴드 메인 페이지 로딩 완료")
                return True
            elif ("auth" in current_url):
                self.gui.update_status("인증 페이지 감지, 메인 페이지 로딩 대기 중...")
                time.sleep(2)
            else:
                self.gui.update_status(f"페이지 로딩 대기 중... ({current_url})")
                time.sleep(2)
        return False

    def human_like_click(self, element):
        """자연스러운 마우스 클릭을 시뮬레이션합니다."""
        try:
            # 요소 위치 가져오기
            location = element.location
            size = element.size
            x = location['x'] + size['width']/2 + random.randint(-5, 5)
            y = location['y'] + size['height']/2 + random.randint(-5, 5)
            
            # 마우스 자연스럽게 이동
            actions = ActionChains(self.driver)
            actions.move_by_offset(x, y)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            actions.reset_actions()
            time.sleep(random.uniform(0.5, 1.0))
        except:
            # 실패시 기본 클릭으로 폴백
            element.click()
            time.sleep(random.choice(self.random_delays))

    def human_like_type(self, element, text):
        """자연스러운 타이핑을 시뮬레이션합니다."""
        try:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
        except:
            # 실패시 기본 입력으로 폴백
            element.send_keys(text)

    def login(self):
        try:
            self.driver.get('https://auth.band.us/login')
            time.sleep(3)
            
            # 이메일 로그인 버튼 클릭
            try:
                email_login_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.uButtonRound.-h56.-icoType.-email'))
                )
                self.gui.update_status("이메일 로그인 버튼 찾음")
                self.human_like_click(email_login_btn)
                time.sleep(random.choice(self.random_delays))
            except Exception as e:
                self.gui.update_status(f"이메일 로그인 버튼을 찾을 수 없습니다: {str(e)}")
                raise

            # 이메일 입력
            try:
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'input_email'))
                )
                self.gui.update_status("이메일 입력 중...")
                self.human_like_type(email_input, self.config['email'])
                time.sleep(random.choice(self.random_delays))
                
                email_confirm_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.uBtn.-tcType.-confirm'))
                )
                self.human_like_click(email_confirm_btn)
            except Exception as e:
                self.gui.update_status(f"이메일 입력 또는 확인 버튼 클릭 실패: {str(e)}")
                raise

            # 비밀번호 입력
            try:
                pw_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'pw'))
                )
                self.gui.update_status("비밀번호 입력 중...")
                self.human_like_type(pw_input, self.config['password'])
                time.sleep(random.choice(self.random_delays))
                
                pw_confirm_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.uBtn.-tcType.-confirm'))
                )
                self.human_like_click(pw_confirm_btn)
            except Exception as e:
                self.gui.update_status(f"비밀번호 입력 또는 확인 버튼 클릭 실패: {str(e)}")
                raise

            # 로그인 성공 후 메인 페이지 로딩 대기
            if not self.wait_for_main_page():
                raise Exception("메인 페이지 로딩 실패")
            
            # 로그인 성공 시 쿠키 저장
            try:
                cookies = self.driver.get_cookies()
                if not cookies:
                    raise Exception("쿠키를 가져올 수 없습니다")
                
                self.gui.update_status(f"가져온 쿠키 수: {len(cookies)}")

                # 쿠키 저장
                cookies_paths = [
                    os.path.join(os.path.dirname(self.script_dir), 'band_cookies.json'),
                    os.path.join(self.script_dir, 'band_cookies.json')
                ]

                for cookie_path in cookies_paths:
                    try:
                        with open(cookie_path, 'w', encoding='utf-8') as f:
                            json.dump(cookies, f, ensure_ascii=False, indent=4)
                        self.gui.update_status(f"쿠키 파일 저장 완료: {cookie_path}")
                    except Exception as e:
                        self.gui.update_status(f"⚠️ 쿠키 파일 저장 실패: {cookie_path} - {str(e)}")

            except Exception as e:
                self.gui.update_status(f"⚠️ 쿠키 저장 중 오류 발생: {str(e)}")
                # 쿠키 저장 실패해도 계속 진행

            self.gui.update_status("로그인 성공")
            
        except Exception as e:
            error_msg = str(e)
            self.gui.update_status(f"로그인 중 오류 발생: {error_msg}")
            raise e

    def get_url_content(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # meta 태그에서 description 추출
            description = soup.find('meta', {'name': 'description'})
            if (description):
                return description.get('content', '')
            
            # 본문 텍스트 추출
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text() for p in paragraphs])
            return content.strip()
            
        except Exception as e:
            self.gui.update_status(f"URL 내용 가져오기 실패: {str(e)}")
            return url

    def get_band_list(self):
        try:
            self.driver.get('https://band.us/feed')
            time.sleep(5)  # 페이지 로딩 대기 시간 증가
            
            # "내 밴드 더보기" 버튼 찾고 클릭 (반드시 실행)
            try:
                # 더보기 버튼이 보일 때까지 스크롤
                for _ in range(3):  # 최대 3번 시도
                    try:
                        more_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.myBandMoreView._btnMore'))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                        time.sleep(2)
                        more_btn.click()
                        self.gui.update_status("내 밴드 더보기 버튼 클릭 성공")
                        time.sleep(3)  # 목록 로딩 대기
                        break
                    except:
                        # 스크롤 다운
                        self.driver.execute_script("window.scrollBy(0, 300);")
                        time.sleep(1)
            except Exception as e:
                self.gui.update_status(f"더보기 버튼 찾기/클릭 실패 (무시됨): {str(e)}")
                
            # ...existing code for band list loading...
            band_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[data-viewname="DMyGroupBandBannerView.MyGroupBandListView"]'))
            )
            
            # ...rest of the existing code...
            
            # 모든 밴드 항목 찾기
            band_items = band_list.find_elements(By.CSS_SELECTOR, 'li[data-viewname="DMyGroupBandListItemView"]')
            band_elements = []
            
            for item in band_items:
                try:
                    band_link = item.find_element(By.CSS_SELECTOR, 'a.itemMyBand')
                    band_name = item.find_element(By.CSS_SELECTOR, 'span.body strong.ellipsis').text.strip()
                    band_url = band_link.get_attribute('href')
                    
                    if (band_url and band_name):
                        # WebElement 객체를 제외하고 필요한 정보만 저장
                        band_elements.append({
                            'name': band_name,
                            'url': band_url
                        })
                        self.gui.update_status(f"밴드 발견: {band_name} ({band_url})")
                except Exception as e:
                    continue
            
            # URL 기준으로 내림차순 정렬
            band_elements.sort(key=lambda x: int(x['url'].split('/')[-1]), reverse=True)
            
            total = len(band_elements)
            if (total > 0):
                self.gui.update_status(f"총 {total}개의 밴드를 찾았습니다.")
                self.gui.update_status(f"첫 번째 밴드: {band_elements[0]['name']} ({band_elements[0]['url']})")
                self.gui.update_status(f"마지막 밴드: {band_elements[-1]['name']} ({band_elements[-1]['url']})")
            else:
                self.gui.update_status("밴드를 찾을 수 없습니다.")
            
            return band_elements
            
        except Exception as e:
            self.gui.update_status(f"밴드 목록 가져오기 실패: {str(e)}")
            return []

    def navigate_to_band(self, band_info):
        """밴드로 이동합니다."""
        try:
            # URL로 직접 이동
            band_url = band_info["url"]
            self.driver.get(band_url)
            time.sleep(3)
            
            if (band_url.split("/")[-1] in self.driver.current_url):
                self.gui.update_status(f"'{band_info['name']}' 밴드 페이지 로딩 완료")
                return True
            
            raise Exception("밴드 페이지 로딩 실패")
            
        except Exception as e:
            self.gui.update_status(f"밴드 이동 실패: {str(e)}")
            return False

    def post_to_band(self, band_info):
        try:
            # 밴드로 이동 후 멤버 수 체크 로직 추가
            if not self.navigate_to_band(band_info):
                return False

            # 멤버 수 확인
            try:
                member_count_elem = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.memberCount._memberLink._memberCountText'))
                )
                member_count = int(''.join(filter(str.isdigit, member_count_elem.text)))
                
                if member_count <= 50:
                    self.gui.update_status(f"멤버수 부족 ({member_count}명), 탈퇴 처리...")
                    self.process_leave_band(band_info['url'])
                    with open(failed_url_path, 'a', encoding='utf-8') as f:
                        f.write(f"[멤버수부족] {band_info['url']}\t{band_info['name']}\t{datetime.datetime.now()}\t멤버 수 {member_count}명으로 탈퇴\n")
                    return False  # 탈퇴 처리 후 바로 리턴
            except Exception as e:
                self.gui.update_status(f"멤버 수 확인 실패: {str(e)}")

            # URL 저장 경로 설정
            success_url_path = os.path.join(self.script_dir, 'success_urls.txt')
            failed_url_path = os.path.join(self.script_dir, 'failed_urls.txt')

            def save_url(path, status, reason=""):
                timestamp = datetime.datetime.now()
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(f"[{status}] {band_info['url']}\t{band_info['name']}\t{timestamp}\t{reason}\n")

            # 로그인 상태 확인 및 재로그인 함수
            def check_and_relogin():
                current_url = self.driver.current_url
                login_urls = [
                    'https://band.us/home',
                    'https://auth.band.us/login_page',
                    'https://auth.band.us/email_login'
                ]
                
                if any(url in current_url for url in login_urls):
                    self.gui.update_status("세션 만료, 재로그인 시도...")
                    self.login()
                    return self.navigate_to_band(band_info)  # 다시 해당 밴드로 이동
                return True

            # 밴드로 이동
            if not self.navigate_to_band(band_info):
                if not check_and_relogin():  # 로그인 페이지로 이동된 경우 재로그인 시도
                    return False
                    
            # 현재 GUI에서 설정된 URL 가져오기
            post_url = self.gui.url_var.get()
            if not post_url:
                raise Exception("포스팅 URL이 설정되지 않았습니다")
            
            self.gui.update_status(f"포스팅 URL: {post_url}")
                
            # 글쓰기 버튼 찾기
            write_btn_selectors = [
                'button._btnPostWrite',
                'button.uButton.-sizeL.-confirm.sf_bg',
                'button[type="button"][class*="_btnPostWrite"]'
            ]
            
            write_btn = None
            for selector in write_btn_selectors:
                try:
                    write_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
                    
            if (not write_btn):
                raise Exception("글쓰기 버튼을 찾을 수 없습니다")
                
            self.human_like_click(write_btn)
            time.sleep(random.uniform(2.0, 3.0))
            
            # 글 작성 영역 찾기
            try:
                editor = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
                )
                self.gui.update_status("에디터 찾는 중...")
                
                # URL 입력 (제목 입력 코드 제거)
                time.sleep(random.uniform(1.0, 2.0))
                self.human_like_type(editor, post_url)
                self.gui.update_status(f"URL 입력 시작: {post_url}")
                
                # 에디터 클릭 및 URL 붙여넣기
                editor.click()
                editor.clear()  # 기존 내용 클리어
                editor.send_keys(post_url)
                time.sleep(1)
                self.gui.update_status("URL 입력 및 엔터 완료")
                
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                self.gui.update_status("미리보기 로딩 대기 중 (2초)...")
                time.sleep(2)
                
                # URL 텍스트 삭제
                editor.click()
                
                # JavaScript로 정확한 URL 텍스트만 삭제
                self.driver.execute_script("""
                    var editor = arguments[0];
                    var url = arguments[1];
                    
                    // 현재 내용에서 URL 텍스트만 찾아서 삭제
                    editor.innerHTML = editor.innerHTML.replace(url, '');
                    // 줄바꿈 문자도 삭제
                    editor.innerHTML = editor.innerHTML.replace(/^\\n|\\n$/g, '');
                    editor.innerHTML = editor.innerHTML.trim();
                    
                    // 변경 이벤트 발생
                    editor.dispatchEvent(new Event('input', { bubbles: true }));
                """, editor, post_url)
                
                # 게시 버튼 클릭
                submit_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-sizeM._btnSubmitPost.-confirm'))
                )
                time.sleep(random.uniform(1.0, 2.0))
                self.human_like_click(submit_btn)

                # 알림창 처리 추가
                try:
                    alert = WebDriverWait(self.driver, 5).until(EC.alert_is_present())
                    alert_text = alert.text
                    alert.accept()  # 알림창 확인

                    if "리더의 승인" in alert_text:
                        self.gui.update_status(f"리더 승인이 필요한 밴드: {band_info['name']}, 탈퇴 처리...")
                        self.process_leave_band(band_info['url'])
                        with open(failed_url_path, 'a', encoding='utf-8') as f:
                            f.write(f"[승인필요_탈퇴] {band_info['url']}\t{band_info['name']}\t{datetime.datetime.now()}\t리더 승인이 필요하여 탈퇴\n")
                        return False  # 탈퇴 처리 후 바로 리턴
                    
                except Exception as e:
                    # 알림창이 없으면 게시판 선택 팝업 처리로 진행
                    try:
                        popup_header = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'header.modalHeader'))
                        )
                        
                        if "게시판 선택" in popup_header.text:
                            # ...existing board selection code...
                            # 팝업 헤더 확인
                            popup_header = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'header.modalHeader'))
                            )
                            
                            if ("게시판 선택" in popup_header.text):
                                self.gui.update_status("게시판 선택 팝업 감지됨")
                                
                                # 첫 번째 flexList 요소 찾기 및 클릭
                                first_flex_list = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'label.flexList'))
                                )
                                self.human_like_click(first_flex_list)
                                self.gui.update_status("첫 번째 게시판 선택됨")
                                
                                # 확인 버튼 클릭
                                confirm_btn = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-confirm._btnConfirm'))
                                )
                                self.human_like_click(confirm_btn)
                                self.gui.update_status("게시판 선택 확인")
                                
                                # 최종 게시 버튼 클릭
                                final_submit_btn = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.uButton.-sizeM._btnSubmitPost.-confirm'))
                                )
                                time.sleep(2)
                                self.human_like_click(final_submit_btn)
                                self.gui.update_status("최종 게시 완료")
                                save_url(success_url_path, "게시완료")
                                self.gui.update_status(f"✅ 게시 성공: {band_info['name']}")
                                return True
                        else:
                            # 게시판 선택이 아닌 다른 팝업이 나타난 경우
                            # 실패한 URL을 파일에 저장
                            save_url(failed_url_path, "기타오류", "알 수 없는 팝업 발생")
                            self.gui.update_status(f"⚠️ 다른 팝업 발생으로 글쓰기 실패: {band_info['name']} (다음 URL로 이동)")
                            return False

                    except Exception as e:
                        self.gui.update_status(f"팝업 처리 중 오류: {str(e)} (다음 URL로 이동)")
                        return False

                time.sleep(3)

                # 다음 밴드로 이동 전 랜덤 대기
                wait_time = random.randint(240, 360)  # 4-6분 랜덤 대기
                self.gui.update_status(f"다음 밴드로 이동 대기 시작 (총 {wait_time}초)...")
                
                # 카운트다운 표시
                start_time = time.time()
                while time.time() - start_time < wait_time:
                    remaining = int(wait_time - (time.time() - start_time))
                    minutes = remaining // 60
                    seconds = remaining % 60
                    self.gui.update_status(f"⏱️ 다음 밴드로 이동까지 {minutes:02d}분 {seconds:02d}초 남음 ({band_info['name']} 완료)")
                    time.sleep(1)

                self.gui.update_status(f"✅ 대기 완료! 다음 밴드로 이동합니다.")
                return True
                
            except Exception as e:
                self.gui.update_status(f"글 작성 실패: {str(e)}")
                raise
                
        except Exception as e:
            self.gui.update_status(f"{band_info['name']} 밴드 글 작성 실패: {str(e)}")
            try:
                self.driver.get('https://band.us/feed')
                time.sleep(3)
            except:
                pass
            return False

    def process_leave_band(self, current_url):
        """밴드 탈퇴 처리"""
        try:
            # 설정 페이지로 이동
            setting_url = f"{current_url}/setting" 
            self.gui.update_status(f"설정 페이지로 이동: {setting_url}")
            self.driver.get(setting_url)
            time.sleep(2)

            wait = WebDriverWait(self.driver, 10)

            # 탈퇴하기 버튼 클릭 
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.uButton.-sizeS.-confirm2.-colorError._btnLeaveBand"))
            ).click()
            self.gui.update_status("1. 탈퇴하기 버튼 클릭")
            time.sleep(1)

            # "이 밴드에서 탈퇴하겠습니다" 체크박스 클릭
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.text"))
            ).click()
            self.gui.update_status("2. 탈퇴 확인 체크박스 클릭")
            time.sleep(1)

            # 최종 탈퇴하기 버튼 클릭
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.uButton.-confirm._btnLeaveBand"))
            ).click()
            self.gui.update_status("3. 최종 탈퇴하기 버튼 클릭")
            time.sleep(2)

            # 탈퇴 완료 알림창 처리
            try:
                alert = wait.until(EC.alert_is_present())
                alert.accept()
                self.gui.update_status("탈퇴 완료 알림 확인")
            except:
                self.gui.update_status("탈퇴 완료 알림창이 표시되지 않음")

            # 상태 업데이트
            with open(os.path.join(self.script_dir, 'failed_urls.txt'), 'a', encoding='utf-8') as f:
                f.write(f"[탈퇴완료] {current_url}\t밴드\t{datetime.datetime.now()}\t멤버수부족 또는 승인필요로 탈퇴\n")
            self.gui.update_status("4. 탈퇴 처리 완료")
            
            return True

        except Exception as e:
            self.gui.update_status(f"탈퇴 처리 중 오류 발생: {str(e)}")
            return False

    def run_posting(self):
        try:
            # Chrome 프로필 초기화
            profile_path = os.path.join(self.script_dir, 'chrome_profile')
            if (os.path.exists(profile_path)):
                try:
                    shutil.rmtree(profile_path)
                    time.sleep(2)
                    os.makedirs(profile_path)
                except:
                    pass

            retry_count = 0
            while (retry_count < 3):
                if (self.setup_driver()):
                    break
                retry_count += 1
                time.sleep(5)
                
            if (not self.driver):
                raise Exception("브라우저를 시작할 수 없습니다")
                
            self.login()
            
            # 밴드 목록 가져오기
            bands = self.get_band_list()
            if (not bands):
                raise Exception("작성할 밴드가 없습니다.")
            
            self.gui.update_status(f"총 {len(bands)}개의 밴드에 순차적으로 글을 작성합니다.")
            success_count = 0
            failed_count = 0
            total_bands = len(bands)
            
            for i, band in enumerate(bands, start=1):
                progress = f"[{i}/{total_bands}] ({success_count}성공/{failed_count}실패)"
                remaining = total_bands - i
                self.gui.update_status(f"{progress} {band['name']} ({band['url']}) 밴드 작성 시작... (남은 밴드: {remaining}개)")
                
                if (self.post_to_band(band)):
                    success_count += 1
                else:
                    failed_count += 1
                time.sleep(300)
            
            final_stats = f"모든 밴드 작성 완료 (성공: {success_count}, 실패: {failed_count}, 총: {total_bands})"
            self.gui.update_status(final_stats)
            
        except Exception as e:
            self.gui.update_status(f"실행 중 오류 발생: {str(e)}")
            if (self.driver):
                self.driver.quit()
            raise

    def start_posting(self):
        self.running = True
        threading.Thread(target=self._start_with_band_list, daemon=True).start()

    def _start_with_band_list(self):
        try:
            # cleanup_chrome_processes 호출 제거
            if (not self.setup_driver()):
                raise Exception("브라우저 설정 실패")

            # 로그인
            self.login()
            
            # 밴드 목록 가져오기
            bands = self.get_band_list()
            if not bands:
                raise Exception("밴드 목록을 가져올 수 없습니다")

            # 밴드 폴더에 저장
            self.save_band_urls(bands)

            # 드라이버 재시작 없이 바로 포스팅 시작
            self.gui.update_status("밴드 URL 저장 완료. 포스팅 시작...")
            success_count = 0
            
            for i, band in enumerate(bands, start=1):
                self.gui.update_status(f"[{i}/{len(bands)}] {band['name']} ({band['url']}) 밴드 작성 시작...")
                if self.post_to_band(band):
                    success_count += 1
                time.sleep(300)  # 다음 밴드로 이동 전 5분 대기
            
            self.gui.update_status(f"모든 밴드 작성 완료 (성공: {success_count}, 실패: {len(bands)-success_count})")

            # 포스팅 루프 시작
            self._posting_loop()

        except Exception as e:
            self.gui.update_status(f"시작 실패: {str(e)}")
            self.stop_posting()

    def _posting_loop(self):
        while (self.running):
            try:
                # Check if stopped
                if (not self.running):
                    break

                # 현재 시간과 설정된 시간 비교
                now = datetime.datetime.now()
                post_time = self.gui.post_time_var.get()
                try:
                    hour, minute = map(int, post_time.split(':'))
                    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    # 설정 시간이 지났다면 다음 날로 설정
                    if (now > target_time):
                        target_time += datetime.timedelta(days=1)
                    
                    wait_seconds = (target_time - now).total_seconds()
                    while (wait_seconds > 0 and self.running):
                        self.gui.update_status(f"다음 게시 시간({post_time})까지 {int(wait_seconds/60)}분 대기")
                        time.sleep(min(60, wait_seconds))  # 최대 1분씩 대기
                        wait_seconds -= 60
                        if (not self.running):
                            break
                except ValueError:
                    self.gui.update_status("잘못된 시간 형식입니다. HH:MM 형식으로 입력해주세요.")
                    break

                if (not self.running):
                    break

                self.gui.update_status("포스팅 시작...")
                self.run_posting()
                
                if (self.running):
                    remaining_hours = int(self.gui.interval_var.get())
                    while (remaining_hours > 0 and self.running):
                        self.gui.update_status(f"다음 포스팅까지 {remaining_hours}시간 대기")
                        time.sleep(3600)  # 1시간씩 대기
                        remaining_hours -= 1
            except Exception as e:
                if (not self.running):
                    break
                self.gui.update_status(f"오류 발생: {str(e)}\n1분 후 재시도합니다.")
                time.sleep(60)

    def stop_posting(self):
        self.gui.update_status("중지 요청됨...")
        self.running = False
        
        # 드라이버 종료
        if (self.driver):
            try:
                self.driver.quit()
                time.sleep(2)
            except:
                pass
        
        # 프로세스 정리
        self.cleanup_chrome_processes()
        
        if (self.posting_thread and self.posting_thread.is_alive()):
            self.posting_thread.join(timeout=5)
        
        self.gui.update_status("중지됨")

    def __del__(self):
        """소멸자에서 리소스 정리"""
        if (hasattr(self, 'driver') and self.driver):
            try:
                self.driver.quit()
            except:
                pass
        try:
            self.cleanup_chrome_processes()
        except:
            pass

if __name__ == "__main__":
    gui = BandAutoGUI()
    gui.run()

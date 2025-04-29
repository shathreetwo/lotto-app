from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.text import LabelBase
import random
from kivy.graphics import Color, Rectangle #배경색
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
import base64
from kivy.core.clipboard import Clipboard #복사
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from Crypto.Cipher import DES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import hashlib
import requests
from bs4 import BeautifulSoup
import json
import os
from kivy.utils import platform #쓰기 가능한 앱전용 폴더
from kivy.metrics import dp, sp
from kivy.uix.spinner import SpinnerOption

# 📌 폰트 등록 (파일이 프로젝트 폴더에 있어야 함)
LabelBase.register(name='Font', fn_regular='NotoSansKR.ttf')

# AES 키는 고정 길이 (16, 24, 32바이트)
AES_KEY = b'mysecretaeskey12'  # 반드시 16, 24, 32바이트 중 하나!
AES_BLOCK_SIZE = 16

DES_KEY = b'8bytekey'   # 꼭 8바이트!
DES_BLOCK_SIZE = 8

AES_DEFAULT_KEY = b'myaesdefaultkey1'   # 16바이트
DES_DEFAULT_KEY = b'deskey88'            # 8바이트



class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15)  # 여백 크게
        )

        # 버튼 3개
        btn1 = Button(text='로또 추첨', font_name='Font', font_size=sp(28),
                      size_hint_y=None, height=dp(80))  # 버튼 높이
        btn2 = Button(text='랜덤 숫자 뽑기', font_name='Font', font_size=sp(28),
                      size_hint_y=None, height=dp(80))
        btn3 = Button(text='암호문', font_name='Font', font_size=sp(28),
                      size_hint_y=None, height=dp(80))

        # 스크린 전환
        btn1.bind(on_press=lambda x: App.get_running_app().switch_to_screen('lotto'))
        btn2.bind(on_press=lambda x: App.get_running_app().switch_to_screen('number'))
        btn3.bind(on_press=lambda x: App.get_running_app().switch_to_screen('encry'))

        # 레이아웃에 추가
        layout.add_widget(btn1)
        layout.add_widget(btn2)
        layout.add_widget(btn3)

        self.add_widget(layout)


class LottoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 📂 저장할 파일 경로
        self.saved_numbers = []
        if platform == "android":
            from android.storage import app_storage_path
            self.storage_path = app_storage_path()
        else:
            self.storage_path = "."
        self.save_file = os.path.join(self.storage_path, "saved_numbers.json")

        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # ✅ 번호 뽑기 결과
        self.label_box = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint=(1, 0.4))
        self.labels = []
        for _ in range(6):
            lbl = Label(
                text='?',
                font_name='Font',
                font_size=sp(32),
                color=(0, 0, 0, 1)
            )
            with lbl.canvas.before:
                Color(1, 1, 1, 0.8)
                lbl.rect = Rectangle(size=lbl.size, pos=lbl.pos)
            lbl.bind(size=self._update_rect, pos=self._update_rect)
            self.labels.append(lbl)
            self.label_box.add_widget(lbl)
        layout.add_widget(self.label_box)

        # ✅ 로또 결과
        self.result_label = Label(
            text="여기에 최신 로또 번호가 표시됩니다",
            font_name='Font',
            font_size=sp(20),
            size_hint=(1, None),
            height=dp(60),
            halign='center',
            valign='middle',
            text_size=(dp(320), None)  # 글자 넘치면 자동 줄바꿈
        )
        layout.add_widget(self.result_label)

        # ✅ 저장된 번호 + 저장된 목록
        self.result_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint=(1, None),
            height=dp(180)
        )

        self.saved_title = Label(
            text="저장된 번호",
            font_name='Font',
            font_size=sp(18),
            size_hint=(0.3, 1),
            halign='left',
            valign='top',
            text_size=(None, None)
        )
        self.result_layout.add_widget(self.saved_title)

        self.saved_numbers_box = BoxLayout(
            orientation='vertical',
            spacing=dp(5),
            size_hint=(0.7, 1),
        )
        self.result_layout.add_widget(self.saved_numbers_box)

        layout.add_widget(self.result_layout)

        # ✅ 버튼들
        button_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(50)
        )

        for label, callback in [
            ("번호 뽑기", self.start_rolling),
            ("최신 번호", self.fetch_lotto_numbers),
            ("번호 저장", self.save_current_numbers),
            ("당첨 확인", self.check_winning)
        ]:
            btn = Button(
                text=label,
                font_size=sp(18),
                font_name='Font',
                size_hint_x=0.25
            )
            btn.bind(on_press=callback)
            button_layout.add_widget(btn)

        layout.add_widget(button_layout)

        # ✅ 뒤로가기 버튼
        back_button = Button(
            text='← 뒤로가기',
            font_size=sp(18),
            font_name='Font',
            size_hint=(1, None),
            height=dp(50)
        )
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_button)

        self.add_widget(layout)

        # ✅ 저장된 번호 불러오기
        self.load_numbers_from_file()

        # ✅ 배경색
        with layout.canvas.before:
            Color(0.5, 0.5, 1, 1)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_rect, pos=self._update_rect)
        

    def _update_rect(self, instance, value):
        if hasattr(instance, 'rect'):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size
        else:
            self.rect.pos = instance.pos
            self.rect.size = instance.size

    def start_rolling(self, instance):
        self.count = 0
        self.final_numbers = sorted(random.sample(range(1, 46), 6))
        self.rolling_event = Clock.schedule_interval(self.roll_number, 0.05)

    def roll_number(self, dt):
        if self.count < 6:
            self.labels[self.count].text = str(random.randint(1, 45))
        else:
            self.rolling_event.cancel()
            for i in range(6):
                self.labels[i].text = str(self.final_numbers[i])
            return
        self.count += 1

    def save_current_numbers(self, instance):
        # ⚡ 먼저 '?' 가 남아있으면 저장 막기
        if any(lbl.text == '?' for lbl in self.labels):
            self.saved_title.text = "번호를 먼저 뽑아주세요!"
            return

        numbers = [int(lbl.text) for lbl in self.labels]
        numbers.sort()

        if len(self.saved_numbers) >= 5:
            self.saved_numbers.pop(0)

        self.saved_numbers.append(numbers)
        self.saved_title.text = f"번호 저장 완료! (현재 {len(self.saved_numbers)}개 저장)"

        self.update_saved_numbers_display()
        self.save_numbers_to_file()
        
    def check_winning(self, instance):
        if not hasattr(self, 'final_numbers') or not hasattr(self, 'lotto_numbers'):
            self.saved_title.text = "당첨 번호와 저장된 번호를 먼저 준비하세요."
            return

        results = []

        for saved in self.saved_numbers:
            match = len(set(saved) & set(self.lotto_numbers))
            bonus_matched = self.bonus_number in saved

            if match == 6:
                results.append("1등 (6개 일치)")
            elif match == 5 and bonus_matched:
                results.append("2등 (5개 + 보너스)")
            elif match == 5:
                results.append("3등 (5개 일치)")
            elif match == 4:
                results.append("4등 (4개 일치)")
            elif match == 3:
                results.append("5등 (3개 일치)")
            else:
                results.append("꽝")

        # 결과 출력
        result_text = "\n".join([f"{i+1}번 저장번호: {r}" for i, r in enumerate(results)])
        self.saved_title.text = result_text


    def fetch_lotto_numbers(self, instance):
        try:
            url = "https://dhlottery.co.kr/gameResult.do?method=byWin"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # ✅ 회차 정보
            round_info = soup.find("div", class_="win_result").find("strong").text

            # ✅ 당첨 번호
            win_div = soup.find("div", class_="num win")
            numbers = [int(span.text) for span in win_div.find_all("span")]

            # ✅ 보너스 번호
            bonus_div = soup.find("div", class_="num bonus")
            bonus_number = int(bonus_div.find("span").text)

            self.lotto_numbers = numbers
            self.bonus_number = bonus_number

            result_text = f"{round_info}\n당첨 번호: {', '.join(map(str, numbers))}\n보너스 번호: {bonus_number}"
            self.result_label.text = result_text

        except requests.exceptions.RequestException:
            self.result_label.text = "인터넷 연결을 확인하세요 🌐"
        except Exception as e:
            self.result_label.text = f"로또 정보 처리 중 오류: {str(e)}"
            
    def update_saved_numbers_display(self):
        # 저장된 번호 화면에 표시하는 함수
        self.saved_numbers_box.clear_widgets()
        for idx, numbers in enumerate(self.saved_numbers, start=1):
            label = Label(
                text=f"{idx}번: {', '.join(map(str, numbers))}",
                font_name='Font',
                size_hint=(1, None),
                height=30
            )
            self.saved_numbers_box.add_widget(label)

    def save_numbers_to_file(self):  # ⭐ 여기 추가!
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_numbers, f)
        except Exception as e:
            print(f"번호 저장 실패: {e}")

    def load_numbers_from_file(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    self.saved_numbers = json.load(f)
                self.update_saved_numbers_display()
            except Exception as e:
                print(f"번호 불러오기 실패: {e}")

        
class NumberPicker(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # 범위 시작
        start_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
        start_layout.add_widget(Label(text="시작:", font_name='Font', font_size=sp(22), size_hint=(0.3, 1)))
        self.start_input = TextInput(text='1', multiline=False, input_filter='int', font_name='Font', font_size=sp(22))
        start_layout.add_widget(self.start_input)
        main_layout.add_widget(start_layout)

        # 범위 끝
        end_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
        end_layout.add_widget(Label(text="끝:", font_name='Font', font_size=sp(22), size_hint=(0.3, 1)))
        self.end_input = TextInput(text='45', multiline=False, input_filter='int', font_name='Font', font_size=sp(22))
        end_layout.add_widget(self.end_input)
        main_layout.add_widget(end_layout)

        # 개수
        count_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
        count_layout.add_widget(Label(text="개수:", font_name='Font', font_size=sp(22), size_hint=(0.3, 1)))
        self.count_input = TextInput(text='6', multiline=False, input_filter='int', font_name='Font', font_size=sp(22))
        count_layout.add_widget(self.count_input)
        main_layout.add_widget(count_layout)

        # 결과 라벨
        self.result_label = Label(text="결과가 여기에 표시됩니다.", font_name='Font', font_size=sp(20))
        main_layout.add_widget(self.result_label)

        # 숫자 뽑기 버튼
        self.pick_button = Button(text="숫자 뽑기", font_name='Font', font_size=sp(24), size_hint=(1, None), height=dp(60))
        self.pick_button.bind(on_press=self.pick_numbers)
        main_layout.add_widget(self.pick_button)

        # 뒤로가기 버튼
        back_button = Button(text='← 뒤로가기', font_name='Font', font_size=sp(20), size_hint=(1, None), height=dp(50))
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        main_layout.add_widget(back_button)

        self.add_widget(main_layout)
        
        

    def pick_numbers(self, instance):
        try:
            start = int(self.start_input.text)
            end = int(self.end_input.text)
            count = int(self.count_input.text)

            if count > (end - start + 1):
                self.result_label.text = "개수가 범위보다 많습니다."
                return

            numbers = random.sample(range(start, end + 1), count)
            self.result_label.text = f"뽑은 숫자: {sorted(numbers)}"
        except ValueError:
            self.result_label.text = "입력을 숫자로 정확히 해주세요."

# 드롭다운에 한글폰트 적용된 옵션
class KoreanSpinnerOption(SpinnerOption):
    font_name = 'Font'  # ✅ 네가 등록한 한글 폰트
    font_size = sp(20)


class CipherApp(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.algorithm_groups = {
            '대칭키 암호화': ['AES', 'DES'],
            '비대칭키 암호화': ['RSA'],
            '해시': ['SHA-256'],
            '고전 암호': ['Caesar', 'Reverse'],
            '인코딩': ['Base64', 'ASCII', 'Unicode']
        }
        self.rsa_key = RSA.generate(2048)

        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # ✅ 스피너 레이아웃
        spinner_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))

        self.group_spinner = Spinner(
            text='암호화 종류 선택',
            values=tuple(self.algorithm_groups.keys()),
            font_name='Font',
            font_size=sp(20),
            option_cls=KoreanSpinnerOption,
            size_hint=(0.5, 1),
            height=dp(50)
        )
        self.group_spinner.bind(text=self.on_group_select)
        spinner_layout.add_widget(self.group_spinner)

        self.algo_spinner = Spinner(
            text='알고리즘 선택',
            values=self.algorithm_groups['대칭키 암호화'],
            font_name='Font',
            font_size=sp(20),
            size_hint=(0.5, 1),
            height=dp(50)
        )
        self.algo_spinner.bind(text=self.on_algo_select)
        spinner_layout.add_widget(self.algo_spinner)

        layout.add_widget(spinner_layout)

        # ✅ 키 입력창
        self.key_input_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=0)
        self.key_input = TextInput(
            hint_text="암호 키 입력 (AES/DES)",
            font_name='Font',
            font_size=sp(20),
            multiline=False,
            size_hint_y=None,
            height=dp(50)
        )
        self.key_input_layout.add_widget(self.key_input)
        self.key_input_layout.opacity = 0
        self.key_input_layout.disabled = True
        layout.add_widget(self.key_input_layout)

        # ✅ RSA 키 입력 레이아웃
        self.rsa_key_line = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=0)

        self.rsa_pubkey_label = Label(text="공개키:", font_name='Font', font_size=sp(18), size_hint=(0.15, 1))
        self.rsa_pubkey_input = TextInput(
            hint_text="-----BEGIN PUBLIC KEY----- ...",
            font_name='Font',
            font_size=sp(16),
            multiline=False,
            size_hint=(0.35, 1)
        )
        self.rsa_privkey_label = Label(text="개인키:", font_name='Font', font_size=sp(18), size_hint=(0.15, 1))
        self.rsa_privkey_input = TextInput(
            hint_text="-----BEGIN PRIVATE KEY----- ...",
            font_name='Font',
            font_size=sp(16),
            multiline=False,
            size_hint=(0.35, 1)
        )

        self.rsa_key_line.add_widget(self.rsa_pubkey_label)
        self.rsa_key_line.add_widget(self.rsa_pubkey_input)
        self.rsa_key_line.add_widget(self.rsa_privkey_label)
        self.rsa_key_line.add_widget(self.rsa_privkey_input)

        self.rsa_key_line.opacity = 0
        self.rsa_key_line.disabled = True
        layout.add_widget(self.rsa_key_line)

        # ✅ 평문 입력창
        self.plain_input = TextInput(
            hint_text="여기에 평문 입력 (키 없으면 기본키)",
            font_name='Font',
            font_size=sp(20),
            multiline=False
        )
        layout.add_widget(self.plain_input)

        # ✅ 암호화 버튼
        self.encrypt_button = Button(
            text="암호화",
            font_name='Font',
            font_size=sp(22),
            size_hint=(1, None),
            height=dp(50)
        )
        self.encrypt_button.bind(on_press=self.encrypt_text)
        layout.add_widget(self.encrypt_button)

        # ✅ 암호문 출력
        output_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))

        self.encrypted_output = Label(
            text="암호문이 여기에 표시됩니다",
            font_name='Font',
            font_size=sp(18)
        )
        output_layout.add_widget(self.encrypted_output)

        self.copy_button = Button(
            text="복사",
            font_name='Font',
            font_size=sp(18),
            size_hint=(None, 1),
            width=dp(80)
        )
        self.copy_button.bind(on_press=self.copy_to_clipboard)
        output_layout.add_widget(self.copy_button)

        layout.add_widget(output_layout)

        # ✅ 복호화 입력
        self.cipher_input = TextInput(
            hint_text="여기에 암호문 입력",
            font_name='Font',
            font_size=sp(20),
            multiline=False
        )
        layout.add_widget(self.cipher_input)

        # ✅ 복호화 버튼
        self.decrypt_button = Button(
            text="복호화",
            font_name='Font',
            font_size=sp(22),
            size_hint=(1, None),
            height=dp(50)
        )
        self.decrypt_button.bind(on_press=self.decrypt_text)
        layout.add_widget(self.decrypt_button)

        # ✅ 복호화 결과 출력
        decrypt_output_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))

        self.decrypted_output = Label(
            text="복호화된 평문이 여기에 표시됩니다",
            font_name='Font',
            font_size=sp(18)
        )
        decrypt_output_layout.add_widget(self.decrypted_output)

        self.copy_decrypted_button = Button(
            text="복사",
            font_name='Font',
            font_size=sp(18),
            size_hint=(None, 1),
            width=dp(80)
        )
        self.copy_decrypted_button.bind(on_press=self.copy_decrypted_text)
        decrypt_output_layout.add_widget(self.copy_decrypted_button)

        layout.add_widget(decrypt_output_layout)

        # ✅ 뒤로가기 버튼
        back_button = Button(
            text='← 뒤로가기',
            font_name='Font',
            font_size=sp(20),
            size_hint=(1, None),
            height=dp(50)
        )
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_button)

        self.add_widget(layout)

    def caesar_encrypt(self, text, shift=3):
        return ''.join(chr((ord(char) + shift) % 1114112) for char in text)  # 전체 유니코드 범위

    def caesar_decrypt(self, text, shift=3):
        return ''.join(chr((ord(char) - shift) % 1114112) for char in text)

    def encrypt_text(self, instance):
        algo = self.algo_spinner.text
        plain = self.plain_input.text
        if algo == 'Caesar':
            result = self.caesar_encrypt(plain)
        elif algo == 'Base64':
            result = base64.b64encode(plain.encode('utf-8')).decode('utf-8')
        elif algo == 'AES':
            result = self.aes_encrypt(plain)
        elif algo == 'Reverse':
            result = plain[::-1]  # 문자열 뒤집기
        elif algo == 'DES':
            result = self.des_encrypt(plain)
        elif algo == 'RSA':
            result = self.rsa_encrypt(plain)

        elif algo == 'SHA-256':
            result = self.hash_text_sha256(plain)

        elif algo == 'ASCII':
            result = ' '.join(str(ord(c)) for c in plain)  # ex: "A" → "65"

        elif algo == 'Unicode':
            result = ' '.join(f'U+{ord(c):04X}' for c in plain)  # ex: "가" → "U+AC00"
    
        else:
            result = "지원되지 않는 알고리즘입니다."
            
        self.encrypted_output.text = f"암호문: {result}"

    def decrypt_text(self, instance):
        algo = self.algo_spinner.text
        cipher = self.cipher_input.text
        try:
            if algo == 'Caesar':
                result = self.caesar_decrypt(cipher)
            elif algo == 'Base64':
                result = base64.b64decode(cipher.encode('utf-8')).decode('utf-8')
            elif algo == 'AES':
                result = self.aes_decrypt(cipher)
            elif algo == 'Reverse':
                result = cipher[::-1]  # 뒤집으면 복호화
            elif algo == 'DES':
                result = self.des_decrypt(cipher)
            elif algo == 'RSA':
                result = self.rsa_decrypt(cipher)
            elif algo == 'SHA-256':
                result = "해시는 복호화가 불가능합니다."
            elif algo == 'ASCII':
                try:
                    result = ''.join(chr(int(code)) for code in cipher.strip().split())
                except:
                    result = "숫자 형식 오류: 공백으로 구분된 숫자여야 합니다."

            elif algo == 'Unicode':
                try:
                    result = ''.join(chr(int(code.replace("U+", ""), 16)) for code in cipher.strip().split())
                except:
                    result = "형식 오류: U+로 시작하는 유니코드 값이어야 합니다."
                
            else:
                result = "지원되지 않는 알고리즘입니다."
            
            self.decrypted_output.text = f"평문: {result}"
        except Exception:
            self.decrypted_output.text = "복호화 오류: 형식을 확인하세요."

    def copy_to_clipboard(self, instance):
        text = self.encrypted_output.text.replace("암호문: ", "")
        Clipboard.copy(text)
        #self.encrypted_output.text = "복사 완료! "

    def copy_decrypted_text(self, instance):
        text = self.decrypted_output.text.replace("평문: ", "")
        Clipboard.copy(text)
        #self.decrypted_output.text = "복사 완료! "

    def aes_encrypt(self, plaintext):
        key_input_text = self.key_input.text.strip()
        key = key_input_text.encode('utf-8') if key_input_text else AES_DEFAULT_KEY

        if len(key) not in [16, 24, 32]:
            return "AES 키는 16, 24 또는 32바이트여야 합니다."

        cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return f"{iv}:{ct}"

    def aes_decrypt(self, ciphertext):
        try:
            key_input_text = self.key_input.text.strip()
            key = key_input_text.encode('utf-8') if key_input_text else AES_DEFAULT_KEY

            if len(key) not in [16, 24, 32]:
                return "AES 키는 16, 24 또는 32바이트여야 합니다."

            iv_b64, ct_b64 = ciphertext.split(":")
            iv = base64.b64decode(iv_b64)
            ct = base64.b64decode(ct_b64)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')
            return pt
        except Exception:
            return "복호화 실패"
            
    def des_encrypt(self, plaintext):
        key_input = self.key_input.text.encode('utf-8')
        key = key_input if key_input else DES_DEFAULT_KEY
        
        if len(key) != 8:
            return "DES 키는 정확히 8바이트여야 합니다."
        cipher = DES.new(key, DES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), 8))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return f"{iv}:{ct}"

    def des_decrypt(self, ciphertext):
        try:
            key_input = self.key_input.text.encode('utf-8')
            key = key_input if key_input else DES_DEFAULT_KEY
            
            if len(key) != 8:
                return "DES 키는 정확히 8바이트여야 합니다."
            iv_b64, ct_b64 = ciphertext.split(":")
            iv = base64.b64decode(iv_b64)
            ct = base64.b64decode(ct_b64)
            cipher = DES.new(key, DES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), 8).decode('utf-8')
            return pt
        except Exception:
            return "복호화 실패"
        
    def rsa_encrypt(self, plaintext):
        try:
            if not hasattr(self, 'rsa_key'):
                self.rsa_key = RSA.generate(2048)  # ❗ rsa_key가 없으면 새로 생성

            if self.rsa_pubkey_input.text.strip():
                pub_key = RSA.import_key(self.rsa_pubkey_input.text.strip().encode('utf-8'))
            else:
                pub_key = self.rsa_key.publickey()  # 기본 키 사용

            cipher = PKCS1_OAEP.new(pub_key)
            encrypted = cipher.encrypt(plaintext.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            return f"암호화 실패: {str(e)}"

    def rsa_decrypt(self, ciphertext):
        try:
            if not hasattr(self, 'rsa_key'):
                self.rsa_key = RSA.generate(2048)

            if self.rsa_privkey_input.text.strip():
                priv_key = RSA.import_key(self.rsa_privkey_input.text.strip().encode('utf-8'))
            else:
                priv_key = self.rsa_key

            cipher = PKCS1_OAEP.new(priv_key)
            decrypted = cipher.decrypt(base64.b64decode(ciphertext))
            return decrypted.decode('utf-8')
        except Exception as e:
            return f"복호화 실패: {str(e)}"

    def hash_text_sha256(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def on_group_select(self, spinner, text):
        self.algo_spinner.values = self.algorithm_groups[text]
        self.algo_spinner.text = self.algorithm_groups[text][0]

    def on_algo_select(self, spinner, text):
        key_needed_algos = ['AES', 'DES']
        rsa_needed_algos = ['RSA']

        if text in key_needed_algos:
            self.key_input_layout.opacity = 1
            self.key_input_layout.disabled = False
            self.key_input_layout.height = dp(50)

            self.rsa_key_line.opacity = 0
            self.rsa_key_line.disabled = True
            self.rsa_key_line.height = 0

        elif text in rsa_needed_algos:
            self.key_input_layout.opacity = 0
            self.key_input_layout.disabled = True
            self.key_input_layout.height = 0

            self.rsa_key_line.opacity = 1
            self.rsa_key_line.disabled = False
            self.rsa_key_line.height = dp(50)

        else:
            # 둘 다 숨기기
            self.key_input_layout.opacity = 0
            self.key_input_layout.disabled = True
            self.key_input_layout.height = 0

            self.rsa_key_line.opacity = 0
            self.rsa_key_line.disabled = True
            self.rsa_key_line.height = 0





class LottoApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(MainScreen(name='main'))
        self.title = "로또 랜덤 숫자 암호"  # ← 앱 이름(제목 바꾸기)
        return self.sm

    def switch_to_screen(self, screen_name):
        if not self.sm.has_screen(screen_name):
            if screen_name == 'lotto':
                self.sm.add_widget(LottoScreen(name='lotto'))
            elif screen_name == 'number':
                self.sm.add_widget(NumberPicker(name='number'))
            elif screen_name == 'encry':
                self.sm.add_widget(CipherApp(name='encry'))
        self.sm.current = screen_name


if __name__ == '__main__':
    LottoApp().run()

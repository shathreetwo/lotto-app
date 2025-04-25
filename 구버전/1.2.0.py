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


# 📌 폰트 등록 (파일이 프로젝트 폴더에 있어야 함)
LabelBase.register(name='Font', fn_regular='NotoSansKR.ttf')

# AES 키는 고정 길이 (16, 24, 32바이트)
AES_KEY = b'mysecretaeskey12'  # 반드시 16, 24, 32바이트 중 하나!
AES_BLOCK_SIZE = 16

DES_KEY = b'8bytekey'   # 꼭 8바이트!
DES_BLOCK_SIZE = 8

AES_DEFAULT_KEY = b'myaesdefaultkey12'   # 16바이트
DES_DEFAULT_KEY = b'deskey88'            # 8바이트

class KoreanSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.option_cls = lambda **kw: Button(font_name='Font', **kw)



class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        btn1 = Button(text='로또 추첨', font_name='Font', font_size=24)
        btn2 = Button(text='랜덤 숫자 뽑기', font_name='Font', font_size=24)
        btn3 = Button(text='암호문', font_name='Font', font_size=24)

        btn1.bind(on_press=lambda x: setattr(self.manager, 'current', 'lotto'))
        btn2.bind(on_press=lambda x: setattr(self.manager, 'current', 'number'))
        btn3.bind(on_press=lambda x: setattr(self.manager, 'current', 'encry'))

        layout.add_widget(btn1)
        layout.add_widget(btn2)
        layout.add_widget(btn3)
        self.add_widget(layout)


class LottoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        button = Button(text='번호 뽑기', font_size=24, size_hint=(1, 0.2), font_name='Font')
        back_button = Button(text='← 뒤로가기', font_size=18, size_hint=(1, 0.2), font_name='Font')
        button.bind(on_press=self.start_rolling)
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))

        

        # ✅ 가로로 번호 출력될 박스
        self.label_box = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.4))
        self.labels = []

        for _ in range(6):
            lbl = Label(text='?', font_size=32, font_name='Font', color=(0, 0, 0, 1))
            with lbl.canvas.before:
                Color(1, 1, 1, 0.8)  # 흰 배경
                lbl.rect = Rectangle(size=lbl.size, pos=lbl.pos)
            lbl.bind(size=self._update_rect, pos=self._update_rect)
            self.labels.append(lbl)
            self.label_box.add_widget(lbl)

        layout.add_widget(self.label_box)
        

        layout.add_widget(button)
        layout.add_widget(back_button)
        self.add_widget(layout)

        # 배경색
        with layout.canvas.before:
            Color(0.5, 0.5, 1, 1)  # 연한 파란색
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


        
class NumberPicker(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 범위 시작
        start_layout = BoxLayout(orientation='horizontal', spacing=10)
        start_layout.add_widget(Label(text="시작:", font_name='Font', size_hint=(0.3, 1)))
        self.start_input = TextInput(text='1', multiline=False, input_filter='int', font_name='Font')
        start_layout.add_widget(self.start_input)
        main_layout.add_widget(start_layout)

        # 범위 끝
        end_layout = BoxLayout(orientation='horizontal', spacing=10)
        end_layout.add_widget(Label(text="끝:", font_name='Font', size_hint=(0.3, 1)))
        self.end_input = TextInput(text='45', multiline=False, input_filter='int', font_name='Font')
        end_layout.add_widget(self.end_input)
        main_layout.add_widget(end_layout)

        # 개수
        count_layout = BoxLayout(orientation='horizontal', spacing=10)
        count_layout.add_widget(Label(text="개수:", font_name='Font', size_hint=(0.3, 1)))
        self.count_input = TextInput(text='6', multiline=False, input_filter='int', font_name='Font')
        count_layout.add_widget(self.count_input)
        main_layout.add_widget(count_layout)

        # 결과 라벨
        self.result_label = Label(text="결과가 여기에 표시됩니다.", font_name='Font')
        main_layout.add_widget(self.result_label)

        # 버튼
        self.pick_button = Button(text="숫자 뽑기", font_name='Font')
        self.pick_button.bind(on_press=self.pick_numbers)
        main_layout.add_widget(self.pick_button)

        self.add_widget(main_layout)
        
        back_button = Button(text='← 뒤로가기', font_size=18, font_name='Font')
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))

        main_layout.add_widget(back_button)
        
        

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




class CipherApp(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.rsa_key = RSA.generate(2048)
        self.rsa_public_key = self.rsa_key.publickey()

        self.algorithm_groups = {
            'Symmetric-key algorithm': ['AES', 'DES'],
            'Public-key Encryption': ['RSA'],
            'Hash': ['SHA-256'],
            'Classical Cipher': ['Caesar', 'Reverse'],
            'encoding': ['Base64', 'ASCII', 'Unicode']
        }


        # 메인 레이아웃 추가
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        

        # 암호화 알고리즘 선택
        layout.add_widget(Label(text="암호화 알고리즘 선택:", font_name='Font'))
                # 그룹 선택 Spinner
        self.group_spinner = Spinner(
            text='암호화 종류 선택',
            values=tuple(self.algorithm_groups.keys()),
            font_name='Font',
            size_hint=(1, None),
            height=44
        )
        layout.add_widget(self.group_spinner)

        # 알고리즘 선택 Spinner
        self.algo_spinner = Spinner(
            text='알고리즘 선택',
            values=self.algorithm_groups['Symmetric-key algorithm'],  # 기본값 설정
            font_name='Font',
            size_hint=(1, None),
            height=44
        )
        layout.add_widget(self.algo_spinner)

        # 그룹 선택 시 알고리즘 Spinner 값 변경
        self.group_spinner.bind(text=self.on_group_select)
        self.key_input = TextInput(
            hint_text="암호 키 입력 (AES: 16/24/32바이트, DES: 8바이트)",
            font_name='Font',
            multiline=False
        )
        layout.add_widget(self.key_input)

        # 평문 입력
        self.plain_input = TextInput(hint_text="여기에 평문 입력", font_name='Font', multiline=False)
        layout.add_widget(self.plain_input)

        # 암호화 버튼
        self.encrypt_button = Button(text="암호화", font_name='Font')
        self.encrypt_button.bind(on_press=self.encrypt_text)
        layout.add_widget(self.encrypt_button)

        # 암호문 + 복사 버튼 (가로 정렬)
        output_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=44)

        self.encrypted_output = Label(text="암호문이 여기에 표시됩니다", font_name='Font')
        output_layout.add_widget(self.encrypted_output)

        self.copy_button = Button(text="복사", font_name='Font', size_hint=(None, 1), width=80)
        self.copy_button.bind(on_press=self.copy_to_clipboard)
        output_layout.add_widget(self.copy_button)

        layout.add_widget(output_layout)

        # 복호화 입력
        self.cipher_input = TextInput(hint_text="여기에 암호문 입력", font_name='Font', multiline=False)
        layout.add_widget(self.cipher_input)

        # 복호화 버튼
        self.decrypt_button = Button(text="복호화", font_name='Font')
        self.decrypt_button.bind(on_press=self.decrypt_text)
        layout.add_widget(self.decrypt_button)

        # 복호화 출력 + 복사 버튼
        decrypt_output_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=44)

        self.decrypted_output = Label(text="복호화된 평문이 여기에 표시됩니다", font_name='Font')
        decrypt_output_layout.add_widget(self.decrypted_output)

        self.copy_decrypted_button = Button(text="복사", font_name='Font', size_hint=(None, 1), width=80)
        self.copy_decrypted_button.bind(on_press=self.copy_decrypted_text)
        decrypt_output_layout.add_widget(self.copy_decrypted_button)

        layout.add_widget(decrypt_output_layout)




        # 최종 레이아웃을 스크린에 추가
        self.add_widget(layout)

    def caesar_encrypt(self, text, shift=3):
        return ''.join(chr((ord(char) + shift) % 256) for char in text)

    def caesar_decrypt(self, text, shift=3):
        return ''.join(chr((ord(char) - shift) % 256) for char in text)

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
        key_input = self.key_input.text.encode('utf-8')
        key = key_input if key_input else AES_DEFAULT_KEY
        
        if len(key) not in [16, 24, 32]:
            return "AES 키는 16, 24 또는 32바이트여야 합니다."
        cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return f"{iv}:{ct}"

    def aes_decrypt(self, ciphertext):
        try:
            key_input = self.key_input.text.encode('utf-8')
            key = key_input if key_input else AES_DEFAULT_KEY
            
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
        cipher = PKCS1_OAEP.new(self.rsa_public_key)
        encrypted = cipher.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    def rsa_decrypt(self, ciphertext):
        try:
            cipher = PKCS1_OAEP.new(self.rsa_key)
            decrypted = cipher.decrypt(base64.b64decode(ciphertext))
            return decrypted.decode('utf-8')
        except Exception:
            return "복호화 실패"

    def hash_text_sha256(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    def on_group_select(self, spinner, text):
        self.algo_spinner.values = self.algorithm_groups[text]
        self.algo_spinner.text = self.algorithm_groups[text][0]


class LottoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(LottoScreen(name='lotto'))
        sm.add_widget(NumberPicker(name='number'))
        sm.add_widget(CipherApp(name='encry'))
        return sm


if __name__ == '__main__':
    LottoApp().run()

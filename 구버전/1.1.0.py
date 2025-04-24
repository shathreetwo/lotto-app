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


# 📌 폰트 등록 (파일이 프로젝트 폴더에 있어야 함)
LabelBase.register(name='Font', fn_regular='NotoSansKR.ttf')


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

        # 메인 레이아웃 추가
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 암호화 알고리즘 선택
        layout.add_widget(Label(text="암호화 알고리즘 선택:", font_name='Font'))
        self.spinner = Spinner(
            text='Caesar',
            values=('Caesar', 'Base64'),
            font_name='Font',
            size_hint=(1, None),
            height=44
        )
        layout.add_widget(self.spinner)

        # 평문 입력
        self.plain_input = TextInput(hint_text="여기에 평문 입력", font_name='Font', multiline=False)
        layout.add_widget(self.plain_input)

        # 암호화 버튼
        self.encrypt_button = Button(text="암호화", font_name='Font')
        self.encrypt_button.bind(on_press=self.encrypt_text)
        layout.add_widget(self.encrypt_button)

        # 암호문 출력
        self.encrypted_output = Label(text="암호문이 여기에 표시됩니다", font_name='Font')
        layout.add_widget(self.encrypted_output)

        # 복호화 입력
        self.cipher_input = TextInput(hint_text="여기에 암호문 입력", font_name='Font', multiline=False)
        layout.add_widget(self.cipher_input)

        # 복호화 버튼
        self.decrypt_button = Button(text="복호화", font_name='Font')
        self.decrypt_button.bind(on_press=self.decrypt_text)
        layout.add_widget(self.decrypt_button)

        # 복호화 출력
        self.decrypted_output = Label(text="복호화된 평문이 여기에 표시됩니다", font_name='Font')
        layout.add_widget(self.decrypted_output)

        # 최종 레이아웃을 스크린에 추가
        self.add_widget(layout)

    def caesar_encrypt(self, text, shift=3):
        return ''.join(chr((ord(char) + shift) % 256) for char in text)

    def caesar_decrypt(self, text, shift=3):
        return ''.join(chr((ord(char) - shift) % 256) for char in text)

    def encrypt_text(self, instance):
        algo = self.spinner.text
        plain = self.plain_input.text
        if algo == 'Caesar':
            result = self.caesar_encrypt(plain)
        elif algo == 'Base64':
            result = base64.b64encode(plain.encode('utf-8')).decode('utf-8')
        self.encrypted_output.text = f"암호문: {result}"

    def decrypt_text(self, instance):
        algo = self.spinner.text
        cipher = self.cipher_input.text
        try:
            if algo == 'Caesar':
                result = self.caesar_decrypt(cipher)
            elif algo == 'Base64':
                result = base64.b64decode(cipher.encode('utf-8')).decode('utf-8')
            self.decrypted_output.text = f"평문: {result}"
        except Exception:
            self.decrypted_output.text = "복호화 오류: 형식을 확인하세요."

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

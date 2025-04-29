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
from Crypto.Cipher import PKCS1_OAEP
import hashlib
import requests
from bs4 import BeautifulSoup
import json
import os
from kivy.utils import platform #쓰기 가능한 앱전용 폴더
from kivy.metrics import dp, sp
from kivy.uix.spinner import SpinnerOption
from kivy.uix.image import Image
from kivy.uix.widget import Widget

# 📌 폰트 등록 (파일이 프로젝트 폴더에 있어야 함)
LabelBase.register(name='Font', fn_regular='NotoSansKR.ttf')




class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15)
        )

        # 상단 이미지 (예: logo.png)
        top_image = Image(
            source='logo.png',  # 프로젝트 내 이미지 파일 경로
            size_hint=(1, 0.4),  # 화면 비율로 조절 (높이 40%)
            allow_stretch=True,
            keep_ratio=True
        )
        layout.add_widget(top_image)

        # 버튼들
        btn1 = Button(text='로또 추첨', font_name='Font', font_size=sp(28),
                      size_hint_y=None, height=dp(80))
        btn2 = Button(text='랜덤 숫자 뽑기', font_name='Font', font_size=sp(28),
                      size_hint_y=None, height=dp(80))

        btn1.bind(on_press=lambda x: App.get_running_app().switch_to_screen('lotto'))
        btn2.bind(on_press=lambda x: App.get_running_app().switch_to_screen('number'))

        layout.add_widget(btn1)
        layout.add_widget(btn2)

        self.add_widget(layout)


class LottoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.saved_numbers = []
        if platform == "android":
            from android.storage import app_storage_path
            self.storage_path = app_storage_path()
        else:
            self.storage_path = "."
        self.save_file = os.path.join(self.storage_path, "saved_numbers.json")

        layout = BoxLayout(
            orientation='vertical',
            padding=[dp(20), dp(0), dp(20), dp(0)],
            spacing=dp(5)
        )

        # ✅ 번호 뽑기 결과 상자 (최상단)
        self.label_box = BoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(70),
            padding=[dp(0), dp(10), dp(0), dp(0)],
        )
        self.labels = []
        for _ in range(6):
            lbl = Label(
                text='?',
                font_size=sp(28),
                font_name='Font',
                color=(0, 0, 0, 1),
                size_hint=(1/6, None),
                height=dp(60)
            )

            def sync_height(instance, value):
                instance.height = instance.width

            lbl.bind(width=sync_height)

            with lbl.canvas.before:
                Color(1, 1, 1, 0.8)
                lbl.rect = Rectangle(size=lbl.size, pos=lbl.pos)
            lbl.bind(size=self._update_rect, pos=self._update_rect)

            self.labels.append(lbl)
            
            layout.add_widget(Widget(size_hint_y=1))
            self.label_box.add_widget(lbl)

        layout.add_widget(self.label_box)  # ⬅️ 맨 처음에 추가
        layout.add_widget(Widget(size_hint_y=1))


        # ✅ 로또 결과 텍스트
        self.result_label = Label(
            text="여기에 최신 로또 번호가 표시됩니다",
            font_name='Font',
            font_size=sp(20),
            size_hint=(1, None),
            height=dp(80),
            halign='center',
            valign='top',
            text_size=(dp(320), None)
        )
        layout.add_widget(self.result_label)
        layout.add_widget(Widget(size_hint_y=1))


        # ✅ 저장된 번호 섹션
        self.result_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint=(1, None),
            height=dp(180)
        )

        title_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.5, 1)
        )
        self.saved_title = Label(
            text="저장된 번호",
            font_name='Font',
            font_size=sp(20),
            halign='center',
            valign='top'
        )
        self.saved_title.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        title_box.add_widget(self.saved_title)

        self.saved_numbers_box = BoxLayout(
            orientation='vertical',
            spacing=dp(5),
            size_hint=(0.5, 1)
        )

        self.result_layout.add_widget(self.saved_numbers_box)
        self.result_layout.add_widget(title_box)
        layout.add_widget(self.result_layout)

        # ✅ 버튼 섹션
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

        for i, child in enumerate(layout.children):
            print(f"{i}: {type(child).__name__} -> {getattr(child, 'text', 'Container')}")
            

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
                font_size=sp(18),  # 👈 일관된 크기 적용
                size_hint=(1, None),
                height=dp(30)
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






class LottoApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(MainScreen(name='main'))
        self.title = "로또픽"  # ← 앱 이름(제목 바꾸기)
        return self.sm

    def switch_to_screen(self, screen_name):
        if not self.sm.has_screen(screen_name):
            if screen_name == 'lotto':
                self.sm.add_widget(LottoScreen(name='lotto'))
            elif screen_name == 'number':
                self.sm.add_widget(NumberPicker(name='number'))
        self.sm.current = screen_name


if __name__ == '__main__':
    LottoApp().run()

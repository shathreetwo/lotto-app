from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.text import LabelBase
import random

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
        btn2.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        btn3.bind(on_press=lambda x: setattr(self.manager, 'current', 'about'))

        layout.add_widget(btn1)
        layout.add_widget(btn2)
        layout.add_widget(btn3)
        self.add_widget(layout)


class LottoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.label = Label(text='로또 번호를 눌러주세요!', font_size=32, font_name='Font')
        button = Button(text='번호 뽑기', font_size=24, size_hint=(1, 0.3), font_name='Font')
        back_button = Button(text='← 뒤로가기', font_size=18, size_hint=(1, 0.2), font_name='Font')

        button.bind(on_press=self.generate_numbers)
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))

        layout.add_widget(self.label)
        layout.add_widget(button)
        layout.add_widget(back_button)
        self.add_widget(layout)

    def generate_numbers(self, instance):
        numbers = sorted(random.sample(range(1, 46), 6))
        self.label.text = "로또 번호: " + ', '.join(map(str, numbers))


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        layout.add_widget(Label(text='설정 화면입니다.', font_name='Font', font_size=24))
        back_button = Button(text='← 뒤로가기', font_size=18, font_name='Font')
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))

        layout.add_widget(back_button)
        self.add_widget(layout)


class AboutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        layout.add_widget(Label(text='정보 화면입니다.', font_name='Font', font_size=24))
        back_button = Button(text='← 뒤로가기', font_size=18, font_name='Font')
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))

        layout.add_widget(back_button)
        self.add_widget(layout)


class LottoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(LottoScreen(name='lotto'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(AboutScreen(name='about'))
        return sm


if __name__ == '__main__':
    LottoApp().run()

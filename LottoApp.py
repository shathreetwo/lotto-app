from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.text import LabelBase
import random
import os
print(os.listdir('.'))  # 현재 폴더 안의 파일들 목록 출력

# ✅ 폰트 등록
LabelBase.register(name='Font', fn_regular='NotoSansKR.ttf')

class LottoApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.label = Label(text='로또 번호를 눌러주세요!', font_size=32, font_name='Font')
        self.button = Button(text='번호 뽑기', font_size=24, size_hint=(1, 0.3), font_name='Font')
        self.button.bind(on_press=self.generate_numbers)

        self.layout.add_widget(self.label)
        self.layout.add_widget(self.button)

        return self.layout

    def generate_numbers(self, instance):
        numbers = sorted(random.sample(range(1, 46), 6))
        self.label.text = "로또 번호: " + ', '.join(map(str, numbers))

if __name__ == '__main__':
    LottoApp().run()

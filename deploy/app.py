import streamlit as st
import requests
from datetime import datetime
import os
import json
from openai import OpenAI
import uuid


# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = st.secrets['API_KEY']

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# OpenWeatherMap API 설정
weather_api_key = "f628ab3133d60e335842dc08769aaba5"
weather_url = "https://api.openweathermap.org/data/2.5/weather"

def get_weather(city):
    params = {
        'q': city,
        'units': 'metric',
        'appid': weather_api_key
    }
    response = requests.get(weather_url, params=params)
    return response.json()

def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        print(f"Error generating image: {e}") 
        return None

def generate_message(city, temperature, description):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    messages = [
        {"role": "system", "content": "당신은 굉장히 친절한 직장인 입니다. 내일 출근도 해야하지만 친구를 위해서 애정어린 편지를 쓰는 상황이에요. 항상 한국어로 작성해주세요."},
        {"role": "user", "content": f"입력받은 도시에 대한 감성적인 하루를 시작하는 글귀를 한국어로 작성해주세요. 도시정보: {city}. 현재 날씨는 {description} 그리고 현재 온도는 다음과 같아요. {temperature}°C. 현재 시간은 {now}으로 관련해서 직장인들이 내일 혹은 지금을 열심히 준비할 수 있도록 혹은 살아갈 수 있는 긍정적인 메시지로 작성해줘요.."}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=200,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_title(city, description):
    messages = [
        {"role": "system", "content": "당신은 재치있는 사람입니다."},
        {"role": "user", "content": f"짧지만 현재 시간 과 날씨와 관련되면서 기분을 좋게 해주는 이메일 제목 작성. "}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=20,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def send_email(email, title, message, image_url):
    url = "https://script.google.com/macros/s/AKfycbys0ViMcfWPg8frV1yaf18w_MhgnRD463Kge22irJtYgvnxcFrSyuN4-RshD5kLgSoo/exec"
    payload = {
        "email": email,
        "title": title,
        "message": message,
        "image_url": image_url
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.text

# Streamlit 앱 구성
st.title("날씨 기반 아트와 이메일 알림")

city = st.text_input("날씨 정보를 가져올 도시를 입력하세요", "seoul")

# 페이지 로드 시 날씨 정보 및 이미지 가져오기
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = get_weather(city)
    if st.session_state.weather_data.get("cod") == 200:
        temperature = st.session_state.weather_data['main']['temp']
        description = st.session_state.weather_data['weather'][0]['description']
        
        with st.spinner('이미지를 생성하는 중입니다...'):
            st.session_state.prompt = f"{city}의 날씨를 기반으로 고품질 아트를 생성하세요. 현재 날씨는 {description}이고 온도는 {temperature}°C입니다. 아트 스타일은 검은색이며 중요한 스타일은 라인 아트입니다."
            st.session_state.image_url = generate_image(st.session_state.prompt)
            st.session_state.message = generate_message(city, temperature, description)
            st.session_state.title = generate_title(city, description)

# 현재 시간 표시
st.write(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.session_state.weather_data.get("cod") == 200:
    unique_id = uuid.uuid4()
    st.write(f"온도: {st.session_state.weather_data['main']['temp']}°C")
    st.write(f"날씨 설명: {st.session_state.weather_data['weather'][0]['description']}")
    st.image(st.session_state.image_url, caption=f"오직 당신을 위한 오늘의 아트워크. 일련번호: {unique_id}")
else:
    st.error("도시를 찾을 수 없거나 날씨 데이터를 가져오는 중 오류가 발생했습니다.")

email = st.text_input("이메일을 입력하세요")

if st.button("이메일 전송"):
    if 'message' in st.session_state and 'image_url' in st.session_state:
        with st.spinner('이메일을 전송하는 중입니다...'):
            response = send_email(email, st.session_state.title, st.session_state.message, st.session_state.image_url)
            st.success("이메일이 성공적으로 전송되었습니다!")
    else:
        st.error("메시지 또는 이미지를 생성하지 못했습니다. 다시 시도해 주세요.")

# 광고 추가
st.markdown("## 광고")
st.write("**광고 1:** 더 많은 아트 작품 보러가기: 인스타그램 [@ai_lineart](https://www.instagram.com/ai_lineart)")
st.write("**광고 2:** 역삼역 직장인들 주목! 고객 만족에 진심인 호텔급 피트니스가 찾아옵니다.")
st.write("[딱 지금만 가능한 사전 접수신청 바로가기](https://litt.ly/isolink_academy)")

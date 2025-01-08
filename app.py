from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Render! Your Flask app is live!"

# Mafia42 API URL
MAFIA42_API_URL = "https://mafia42.com/api/user/user-info"

# 헤더 설정
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Cookie": "G_ENABLED_IDPS=google; airbridge_session=%7B%22id%22%3A%22c5d2bbf4-cea4-4567-b505-ec2465b7389b%22%2C%22timeout%22%3A1800000%2C%22start%22%3A1705565863109%2C%22end%22%3A1705565863110%7D; _ga=GA1.1.1713971407.1712408014; _gcl_au=1.1.1828275006.1736131791; G_AUTHUSER_H=2; _ga_Q74W811ST6=GS1.1.1736131791.2.1.1736131838.0.0.0; _ga_FZ502S68NW=GS1.1.1736131791.2.1.1736131838.0.0.0; _ga_Y6XLS8BV40=GS1.1.1736131791.16.1.1736131838.0.0.0; _session_id=2cf2c36abc831ca4376a43baf6bbed8e",
    "Host": "mafia42.com",
    "Origin": "https://mafia42.com",
    "Referer": "https://mafia42.com/",
    "Sec-Ch-Ua": '"Chromium";v="130", "Whale";v="4", "Not.A/Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Whale/4.29.282.14 Safari/537.36"
}

@app.route('/user-info', methods=['POST'])
def get_user_info():
    """Mafia42 API를 호출하여 유저 정보를 반환"""
    try:
        # 요청 JSON에서 user_id 가져오기
        user_id = request.json.get("id")
        if not user_id:
            return jsonify({"error": "유효한 user_id가 필요합니다"}), 400
        
        # Mafia42 API 요청 데이터
        data = {"id": user_id}

        # 요청 로깅 (디버깅 용도)
        print(f"Request Headers: {HEADERS}")
        print(f"Request Data: {data}")

        # Mafia42 API 호출
        response = requests.post(MAFIA42_API_URL, headers=HEADERS, data=json.dumps(data))

        # 상태 코드 확인
        if response.status_code == 200:
            try:
                response_data = response.json()
                return jsonify(response_data), 200
            except json.JSONDecodeError:
                return jsonify({"error": "응답 데이터를 처리할 수 없습니다."}), 500
        elif response.status_code == 401:
            return jsonify({"error": "쿠키 정보가 만료되었습니다. 개발자에게 문의하세요."}), 401
        else:
            return jsonify({
                "error": "Mafia42 API 요청 실패",
                "status_code": response.status_code,
                "response_text": response.text
            }), 500
    except Exception as e:
        return jsonify({"error": f"서버 내부 오류: {str(e)}"}), 500

# 메인 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

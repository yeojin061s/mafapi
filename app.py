from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Mafia42 API URL
MAFIA42_API_URL = "https://mafia42.com/api/user/user-info"

# 헤더 설정
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Content-Length": "17",
    "Content-Type": "application/json",
    "Cookie": "세션 쿠키 정보",
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
    """엔드포인트: Mafia42 API를 호출하여 유저 정보를 반환"""
    try:
        # 요청 JSON에서 user_id 가져오기
        user_id = request.json.get("id")
        if not user_id:
            return jsonify({"error": "유효한 user_id가 필요합니다"}), 400
        
        # Mafia42 API 요청 데이터
        data = {"id": user_id}

        # Mafia42 API 호출
        response = requests.post(MAFIA42_API_URL, headers=HEADERS, data=json.dumps(data))

        # 응답 데이터 처리
        if response.status_code == 200:
            response_data = response.json()
            return jsonify(response_data), 200
        else:
            return jsonify({"error": "Mafia42 API 요청 실패", "status_code": response.status_code}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 메인 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

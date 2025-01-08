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
    try:
        user_id = request.json.get("id")
        if not user_id:
            return jsonify({"error": "유효한 user_id가 필요합니다"}), 400

        response = requests.post(
            MAFIA42_API_URL,
            headers=HEADERS,
            data=json.dumps({"id": user_id})
        )

        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Body: {response.text}")  # 로그에 응답 내용 출력


        # Mafia42 API의 JSON 응답 처리
        if response.status_code == 200:
            try:
                return jsonify(response.json()), 200
            except json.JSONDecodeError:
                return jsonify({"error": "Mafia42 API가 유효한 JSON을 반환하지 않았습니다."}), 500
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


@app.route('/update-nickname', methods=['POST'])
def update_nickname():
    """
    Mafia42 게시판 API에서 댓글 데이터를 가져와 닉네임과 유저 ID를 갱신
    """
    try:
        # 게시판 API URL과 요청 데이터
        board_url = "https://mafia42.com/comment/show-lastDiscussion"
        payload = {"comment": {"article_id": "1044039", "value": 0}}

        # 게시판 API 호출
        response = requests.post(board_url, headers=HEADERS, json=payload)

        # 응답 상태 코드 확인
        if response.status_code != 200:
            return jsonify({"error": "게시판 API 호출 실패"}), response.status_code

        # 게시판 API 응답 데이터
        data = response.json()

        if data.get("responseCode") != 12:
            return jsonify({"error": "게시판 API 응답 실패"}), 400

        # 닉네임 및 유저 ID 갱신
        comment_data = data.get("commentData", [])
        updated_count = 0

        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            for comment in comment_data:
                user_id = comment.get("user_id")
                nickname = comment.get("nickname")

                if user_id and nickname:
                    # 데이터베이스에 닉네임과 ID 저장 (중복 시 덮어쓰기)
                    cursor.execute("""
                        INSERT OR REPLACE INTO users (id, nickname)
                        VALUES (?, ?)
                    """, (user_id, nickname))
                    updated_count += 1

            conn.commit()

        return jsonify({"message": f"{updated_count}개의 닉네임이 갱신되었습니다."}), 200

    except Exception as e:
        return jsonify({"error": f"서버 내부 오류: {str(e)}"}), 500


# 메인 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

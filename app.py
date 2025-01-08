from flask import Flask, request, jsonify
import requests
import json
import os
import psycopg2  # PostgreSQL 연동을 위한 라이브러리

############################
# init_db()를 먼저 정의
############################
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def init_db():
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR PRIMARY KEY,
                        nickname TEXT,
                        daily_wins INT DEFAULT 0,
                        daily_losses INT DEFAULT 0
                    );
                """)
    finally:
        conn.close()

# 이제 Flask 인스턴스 생성
app = Flask(__name__)

############################
# 여기서 init_db()를 호출
############################
init_db()  # 함수 정의 후 호출하므로 NameError 없음


##################################################
# Mafia42 API URL 및 공통 HEADERS (원본 그대로 유지)
##################################################
MAFIA42_API_URL = "https://mafia42.com/api/user/user-info"

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


##################################
# 라우트들 (원본 로직을 최대한 유지)
##################################

@app.route("/")
def home():
    return "Hello, Render! Your Flask app is live with PostgreSQL!"

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

        if response.status_code == 200:
            user_data = response.json().get("userData", {})
            return jsonify({
                "win_count": user_data.get("win_count", 0),
                "lose_count": user_data.get("lose_count", 0),
                "guild_initial": user_data.get("guild_initial", ""),
                "guild_name": user_data.get("guild_name", ""),
                "rankpoint": user_data.get("rankpoint", 0),
                "fame": user_data.get("fame", 0)
            }), 200
        else:
            return jsonify({"error": "Mafia42 API 요청 실패"}), response.status_code

    except Exception as e:
        return jsonify({"error": f"서버 내부 오류: {str(e)}"}), 500


@app.route('/update-nickname', methods=['POST'])
def update_nickname():
    """
    Mafia42 게시판 API에서 댓글 데이터를 가져와 닉네임과 유저 ID를 갱신
    """
    try:
        board_url = "https://mafia42.com/comment/show-lastDiscussion"
        payload = {"comment": {"article_id": "1044039", "value": 0}}

        print("📤 게시판 API 요청:", payload)
        response = requests.post(board_url, headers=HEADERS, json=payload)

        print("📥 게시판 API 응답 상태 코드:", response.status_code)
        print("📥 게시판 API 응답 데이터:", response.text)

        if response.status_code != 200:
            return jsonify({"error": "게시판 API 호출 실패"}), response.status_code

        data = response.json()
        if data.get("responseCode") != 12:
            return jsonify({"error": "게시판 API 응답 실패"}), 400

        comment_data = data.get("commentData", [])
        updated_count = 0

        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
                    # PostgreSQL의 ON CONFLICT (id) DO UPDATE
                    for comment in comment_data:
                        user_id = comment.get("user_id")
                        nickname = comment.get("nickname")

                        if user_id and nickname:
                            cursor.execute("""
                                INSERT INTO users (id, nickname)
                                VALUES (%s, %s)
                                ON CONFLICT (id)
                                DO UPDATE SET nickname = EXCLUDED.nickname
                            """, (user_id, nickname))
                            updated_count += 1
        finally:
            conn.close()

        print(f"🔄 갱신된 닉네임 수: {updated_count}")
        return jsonify({"message": f"{updated_count}개의 닉네임이 갱신되었습니다."}), 200

    except Exception as e:
        print("🚨 서버 내부 오류:", str(e))
        return jsonify({"error": f"서버 내부 오류: {str(e)}"}), 500


@app.route('/show-users', methods=['GET'])
def show_users():
    """
    users 테이블의 데이터를 JSON 형식으로 반환
    """
    try:
        print("🔍 PostgreSQL 연결 시도 중...")
        conn = get_connection()
        users = []
        try:
            with conn:
                with conn.cursor() as cursor:
                    print("🔍 users 테이블 데이터 조회 중...")
                    cursor.execute("SELECT id, nickname, daily_wins, daily_losses FROM users")
                    rows = cursor.fetchall()
                    print(f"✅ 조회된 데이터: {rows}")

                    for row in rows:
                        users.append({
                            "id": row[0],
                            "nickname": row[1],
                            "daily_wins": row[2],
                            "daily_losses": row[3],
                        })
        finally:
            conn.close()

        print(f"✅ JSON 변환된 데이터: {users}")
        return jsonify({"users": users}), 200

    except Exception as e:
        print(f"🚨 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/get-user-id', methods=['POST'])
def get_user_id():
    """
    닉네임으로 user_id를 조회
    """
    try:
        data = request.json
        nickname = data.get("nickname")

        if not nickname:
            return jsonify({"error": "유효한 닉네임이 필요합니다"}), 400

        conn = get_connection()
        user_id = None
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM users WHERE nickname = %s", (nickname,))
                    result = cursor.fetchone()
                    if result:
                        user_id = result[0]
        finally:
            conn.close()

        if not user_id:
            return jsonify({"error": "해당 닉네임의 유저를 찾을 수 없습니다"}), 404

        return jsonify({"user_id": user_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/update-daily', methods=['POST'])
def update_daily():
    """
    모든 유저의 전적을 갱신
    """
    try:
        print("🔄 /update-daily 요청 도착")

        conn = get_connection()
        updated_count = 0
        try:
            with conn:
                with conn.cursor() as cursor:
                    # 1. 이전 전적 초기화
                    print("🔄 이전 전적 초기화 중...")
                    cursor.execute("UPDATE users SET daily_wins = 0, daily_losses = 0")

                    # 2. 모든 유저의 새로운 전적 가져와 갱신
                    print("📥 새로운 전적 갱신 중...")
                    cursor.execute("SELECT id FROM users")
                    all_users = cursor.fetchall()

                    for (user_id,) in all_users:
                        response = requests.post(
                            MAFIA42_API_URL, headers=HEADERS, data=json.dumps({"id": user_id})
                        )
                        if response.status_code == 200:
                            user_data = response.json().get("userData", {})
                            wins = user_data.get("win_count", 0)
                            losses = user_data.get("lose_count", 0)

                            cursor.execute("""
                                UPDATE users
                                SET daily_wins = %s, daily_losses = %s
                                WHERE id = %s
                            """, (wins, losses, user_id))
                            updated_count += 1
                        else:
                            print(f"❌ 유저 {user_id}의 전적 API 호출 실패: {response.status_code}")

        finally:
            conn.close()

        print(f"✅ {updated_count}명의 유저 전적이 갱신되었습니다.")
        return jsonify({"message": f"{updated_count}명의 유저 전적이 갱신되었습니다."}), 200
    except Exception as e:
        print(f"🚨 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/check-activity', methods=['POST'])
def check_activity():
    """
    닉네임으로 유저의 오늘 플레이 횟수를 계산하여 반환
    """
    try:
        data = request.json
        nickname = data.get("nickname")

        if not nickname:
            return jsonify({"error": "유효한 닉네임이 필요합니다"}), 400

        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, daily_wins, daily_losses
                        FROM users
                        WHERE nickname = %s
                    """, (nickname,))
                    result = cursor.fetchone()

                    if not result:
                        return jsonify({"error": "해당 닉네임의 유저를 찾을 수 없습니다"}), 404

                    user_id, db_wins, db_losses = result

                    # 최신 전적 API
                    response = requests.post(MAFIA42_API_URL, headers=HEADERS, data=json.dumps({"id": user_id}))
                    if response.status_code != 200:
                        return jsonify({"error": f"전적 API 호출 실패: {response.status_code}"}), 500

                    user_data = response.json().get("userData", {})
                    current_wins = user_data.get("win_count", 0)
                    current_losses = user_data.get("lose_count", 0)

                    daily_wins = current_wins - db_wins
                    daily_losses = current_losses - db_losses
                    total_games = daily_wins + daily_losses

                    return jsonify({
                        "nickname": nickname,
                        "daily_wins": daily_wins,
                        "daily_losses": daily_losses,
                        "total_games": total_games
                    }), 200
        finally:
            conn.close()

    except Exception as e:
        return jsonify({"error": f"서버 내부 오류: {str(e)}"}), 500


@app.route('/update-user', methods=['POST'])
def update_user():
    """
    유저 데이터를 데이터베이스에 업데이트(또는 삽입)하는 엔드포인트
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        nickname = data.get("nickname")
        wins = data.get("wins")
        losses = data.get("losses")

        if not user_id or not nickname or wins is None or losses is None:
            return jsonify({"error": "유효한 데이터가 필요합니다 (user_id, nickname, wins, losses 모두 필수)"}), 400

        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
                    # 만약 해당 id가 이미 존재하면 nickname, daily_wins, daily_losses만 업데이트
                    # 없으면 새로 INSERT
                    # → ON CONFLICT로 처리
                    cursor.execute("""
                        INSERT INTO users (id, nickname, daily_wins, daily_losses)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id)
                        DO UPDATE
                            SET nickname = EXCLUDED.nickname,
                                daily_wins = EXCLUDED.daily_wins,
                                daily_losses = EXCLUDED.daily_losses
                    """, (user_id, nickname, wins, losses))
        finally:
            conn.close()

        return jsonify({"message": "유저 데이터가 성공적으로 업데이트되었습니다."}), 200
    except Exception as e:
        return jsonify({"error": f"서버 내부 오류: {str(e)}"}), 500

@app.route("/ping", methods=["GET"])
def ping():
    print("🔔 Ping received from GitHub Actions!")  # 이 메시지가 Render Logs에 찍힘
    return "Pong!", 200



################################
# 메인 실행
################################
if __name__ == "__main__":
    # 서버 시작 전에 테이블이 없으면 만들기
    init_db()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

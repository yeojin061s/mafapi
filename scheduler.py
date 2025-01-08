import os
import sqlite3
import requests
from datetime import datetime
import schedule
import time

# 데이터베이스 경로 설정 (현재 파일의 디렉토리를 기준으로 설정)
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "users.db")

# 전적 API URL
API_URL = "https://mafapi.onrender.com/user-info"

def update_daily_stats():
    """
    매일 유저 전적을 갱신하는 함수
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # 1. 모든 유저의 이전 전적 초기화
            print("🔄 이전 전적 초기화 중...")
            cursor.execute("""
                UPDATE users
                SET daily_wins = 0, daily_losses = 0
            """)
            conn.commit()

            # 2. 모든 유저의 새로운 전적 가져와 갱신
            print("📥 새로운 전적 갱신 중...")
            for user in cursor.execute("SELECT id FROM users").fetchall():
                user_id = user[0]

                # 전적 API 호출
                response = requests.post(API_URL, json={"id": user_id})
                if response.status_code == 200:
                    user_data = response.json().get("userData", {})
                    wins = user_data.get("win_count", 0)
                    losses = user_data.get("lose_count", 0)

                    # 데이터베이스 업데이트
                    cursor.execute("""
                        UPDATE users
                        SET daily_wins = ?, daily_losses = ?
                        WHERE id = ?
                    """, (wins, losses, user_id))
                    conn.commit()
                else:
                    print(f"❌ 유저 {user_id}의 전적 API 호출 실패: {response.status_code}")

        print("✅ 모든 유저의 전적이 갱신되었습니다.")
    except Exception as e:
        print(f"🚨 자동 갱신 중 오류 발생: {e}")

# 스케줄 설정: 매일 밤 11시 59분
schedule.every().day.at("23:59").do(update_daily_stats)

def run_scheduler():
    """
    스케줄러 실행 루프
    """
    print("⏳ 스케줄러 실행 중...")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()

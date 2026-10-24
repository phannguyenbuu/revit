#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
db_postgres.py
Module quản lý lưu trữ lâu dài cấu hình cốt thép dầm ETABS vào cơ sở dữ liệu PostgreSQL.
- Tự động tạo bảng beam_rebar_designs nếu chưa tồn tại.
- Hỗ trợ lưu từng dầm hoặc lưu batch toàn bộ dầm dài liên tục.
- Cơ chế Fallback SQLite tự động (revit_ai_persistent.db) khi PostgreSQL chưa được bật,
  đảm bảo dữ liệu của kỹ sư luôn được lưu trữ vĩnh viễn không bao giờ thất lạc.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# Cấu hình mặc định từ biến môi trường
DEFAULT_PG_HOST = os.environ.get("POSTGRES_HOST", "127.0.0.1")
DEFAULT_PG_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
DEFAULT_PG_DB = os.environ.get("POSTGRES_DB", "revit_ai")
DEFAULT_PG_USER = os.environ.get("POSTGRES_USER", "postgres")
DEFAULT_PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
DATABASE_URL = os.environ.get("DATABASE_URL")

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "revit_ai_persistent.db")

class RebarDatabaseManager:
    def __init__(self):
        self.host = DEFAULT_PG_HOST
        self.port = DEFAULT_PG_PORT
        self.db = DEFAULT_PG_DB
        self.user = DEFAULT_PG_USER
        self.password = DEFAULT_PG_PASSWORD
        self.database_url = DATABASE_URL
        self.engine = "unknown"
        self.last_error = None
        self._last_pg_check = 0
        self._init_sqlite()
        self.check_and_init_pg(force=True)

    def _init_sqlite(self):
        """Khởi tạo bảng SQLite dự phòng."""
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS beam_rebar_designs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT DEFAULT 'CAI_TAO_PHUONG_AN_B',
                    story TEXT NOT NULL,
                    long_beam_id TEXT NOT NULL,
                    section TEXT,
                    span_count INTEGER DEFAULT 1,
                    total_length_mm REAL DEFAULT 0,
                    rebar_top_left TEXT,
                    rebar_bot_mid TEXT,
                    rebar_top_right TEXT,
                    rebar_hanger TEXT,
                    stirrup TEXT,
                    is_safe INTEGER DEFAULT 1,
                    safety_status TEXT,
                    spans_data TEXT,
                    layout_settings TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_name, story, long_beam_id)
                );
                """)
                conn.commit()
        except Exception as e:
            print(f"[DB] Lỗi tạo bảng SQLite: {e}")

    def get_pg_connection(self):
        """Kết nối tới PostgreSQL."""
        import psycopg2
        if self.database_url:
            return psycopg2.connect(self.database_url, connect_timeout=1)
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.db,
            user=self.user,
            password=self.password,
            connect_timeout=1
        )

    def check_and_init_pg(self, force=False):
        """Kiểm tra và khởi tạo bảng trên PostgreSQL."""
        import time
        now = time.time()
        if not force and (now - self._last_pg_check < 60):
            return (self.engine == "postgresql")
        self._last_pg_check = now

        # Thử thăm dò cổng raw socket trước trong 0.15s để tránh nghẽn thread
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                if s.connect_ex((self.host, self.port)) != 0:
                    self.engine = "sqlite"
                    self.last_error = f"Khong the ket noi toi PostgreSQL {self.host}:{self.port}"
                    return False
        except Exception as se:
            self.engine = "sqlite"
            self.last_error = str(se)
            return False

        try:
            import psycopg2
            conn = self.get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS beam_rebar_designs (
                    id SERIAL PRIMARY KEY,
                    project_name VARCHAR(100) DEFAULT 'CAI_TAO_PHUONG_AN_B',
                    story VARCHAR(50) NOT NULL,
                    long_beam_id VARCHAR(50) NOT NULL,
                    section VARCHAR(50),
                    span_count INT DEFAULT 1,
                    total_length_mm FLOAT DEFAULT 0,
                    rebar_top_left TEXT,
                    rebar_bot_mid TEXT,
                    rebar_top_right TEXT,
                    rebar_hanger TEXT,
                    stirrup TEXT,
                    is_safe BOOLEAN DEFAULT TRUE,
                    safety_status TEXT,
                    spans_data JSONB,
                    layout_settings JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_beam_design UNIQUE (project_name, story, long_beam_id)
                );
                """)
                conn.commit()
            conn.close()
            self.engine = "postgresql"
            self.last_error = None
            print(f"[DB] Connected to PostgreSQL ({self.host}:{self.port}/{self.db}) successfully.")
            return True
        except Exception as e:
            self.engine = "sqlite"
            self.last_error = str(e)
            try:
                print(f"[DB] PostgreSQL offline ({e}), auto fallback to SQLite: {SQLITE_PATH}")
            except Exception:
                pass
            return False

    def save_beam_design(self, data):
        """Lưu hoặc cập nhật 1 dầm dài vào DB."""
        proj = data.get("project_name", "CAI_TAO_PHUONG_AN_B")
        story = data.get("story", "T1")
        long_id = data.get("long_beam_id", "")
        if not long_id:
            return {"success": False, "message": "Thieu long_beam_id"}

        sec = data.get("section", "")
        spans_count = int(data.get("span_count", 1))
        tot_len = float(data.get("total_length_mm", 0))
        reb_l = data.get("rebar_top_left", "")
        reb_m = data.get("rebar_bot_mid", "")
        reb_r = data.get("rebar_top_right", "")
        reb_h = data.get("rebar_hanger", "")
        stirrup = data.get("stirrup", "")
        is_safe = bool(data.get("is_safe", True))
        status = data.get("safety_status", "Toàn dầm Đạt")
        spans_json = json.dumps(data.get("spans_data", []), ensure_ascii=False)
        layout_json = json.dumps(data.get("layout_settings", {}), ensure_ascii=False)
        now_str = datetime.now().isoformat()

        # Thử lưu vào PostgreSQL trước nếu engine là postgresql
        if self.engine == "postgresql" or self.check_and_init_pg():
            try:
                conn = self.get_pg_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO beam_rebar_designs (
                        project_name, story, long_beam_id, section, span_count, total_length_mm,
                        rebar_top_left, rebar_bot_mid, rebar_top_right, rebar_hanger, stirrup,
                        is_safe, safety_status, spans_data, layout_settings, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (project_name, story, long_beam_id) DO UPDATE SET
                        section = EXCLUDED.section,
                        span_count = EXCLUDED.span_count,
                        total_length_mm = EXCLUDED.total_length_mm,
                        rebar_top_left = EXCLUDED.rebar_top_left,
                        rebar_bot_mid = EXCLUDED.rebar_bot_mid,
                        rebar_top_right = EXCLUDED.rebar_top_right,
                        rebar_hanger = EXCLUDED.rebar_hanger,
                        stirrup = EXCLUDED.stirrup,
                        is_safe = EXCLUDED.is_safe,
                        safety_status = EXCLUDED.safety_status,
                        spans_data = EXCLUDED.spans_data,
                        layout_settings = EXCLUDED.layout_settings,
                        updated_at = EXCLUDED.updated_at;
                    """, (
                        proj, story, long_id, sec, spans_count, tot_len,
                        reb_l, reb_m, reb_r, reb_h, stirrup,
                        is_safe, status, spans_json, layout_json, now_str
                    ))
                    conn.commit()
                conn.close()
                self._save_sqlite(proj, story, long_id, sec, spans_count, tot_len, reb_l, reb_m, reb_r, reb_h, stirrup, is_safe, status, spans_json, layout_json, now_str)
                return {"success": True, "engine": "postgresql", "message": f"Saved {story}::{long_id} to PostgreSQL successfully"}
            except Exception as e:
                self.engine = "sqlite"
                self.last_error = str(e)
                try:
                    print(f"[DB] Error saving PostgreSQL, switching to SQLite: {e}")
                except Exception:
                    pass

        # Fallback lưu vào SQLite
        try:
            self._save_sqlite(proj, story, long_id, sec, spans_count, tot_len, reb_l, reb_m, reb_r, reb_h, stirrup, is_safe, status, spans_json, layout_json, now_str)
            return {"success": True, "engine": "sqlite", "message": f"Da luu dam {story}::{long_id} vao SQLite thanh cong"}
        except Exception as e:
            return {"success": False, "message": f"Loi luu DB: {str(e)}"}

    def _save_sqlite(self, proj, story, long_id, sec, spans_count, tot_len, reb_l, reb_m, reb_r, reb_h, stirrup, is_safe, status, spans_json, layout_json, now_str):
        with sqlite3.connect(SQLITE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO beam_rebar_designs (
                project_name, story, long_beam_id, section, span_count, total_length_mm,
                rebar_top_left, rebar_bot_mid, rebar_top_right, rebar_hanger, stirrup,
                is_safe, safety_status, spans_data, layout_settings, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_name, story, long_beam_id) DO UPDATE SET
                section = excluded.section,
                span_count = excluded.span_count,
                total_length_mm = excluded.total_length_mm,
                rebar_top_left = excluded.rebar_top_left,
                rebar_bot_mid = excluded.rebar_bot_mid,
                rebar_top_right = excluded.rebar_top_right,
                rebar_hanger = excluded.rebar_hanger,
                stirrup = excluded.stirrup,
                is_safe = excluded.is_safe,
                safety_status = excluded.safety_status,
                spans_data = excluded.spans_data,
                layout_settings = excluded.layout_settings,
                updated_at = excluded.updated_at;
            """, (
                proj, story, long_id, sec, spans_count, tot_len,
                reb_l, reb_m, reb_r, reb_h, stirrup,
                1 if is_safe else 0, status, spans_json, layout_json, now_str
            ))
            conn.commit()

    def save_all_designs(self, designs_list):
        """Lưu toàn bộ danh sách thiết kế dầm."""
        saved_count = 0
        for item in designs_list:
            res = self.save_beam_design(item)
            if res.get("success"):
                saved_count += 1
        return {
            "success": True,
            "engine": self.engine,
            "total": len(designs_list),
            "saved": saved_count,
            "message": f"Đã lưu thành công {saved_count}/{len(designs_list)} dầm vào {self.engine.upper()}"
        }

    def load_all_designs(self, project_name="CAI_TAO_PHUONG_AN_B"):
        """Tải toàn bộ cấu hình dầm đã lưu."""
        # Ưu tiên PostgreSQL nếu kết nối được
        if self.engine == "postgresql" or self.check_and_init_pg():
            try:
                conn = self.get_pg_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                    SELECT story, long_beam_id, section, span_count, total_length_mm,
                           rebar_top_left, rebar_bot_mid, rebar_top_right, rebar_hanger, stirrup,
                           is_safe, safety_status, spans_data, layout_settings, updated_at
                    FROM beam_rebar_designs
                    WHERE project_name = %s
                    ORDER BY story, long_beam_id;
                    """, (project_name,))
                    rows = cur.fetchall()
                conn.close()
                results = []
                for r in rows:
                    results.append({
                        "story": r[0],
                        "long_beam_id": r[1],
                        "section": r[2],
                        "span_count": r[3],
                        "total_length_mm": r[4],
                        "rebar_top_left": r[5],
                        "rebar_bot_mid": r[6],
                        "rebar_top_right": r[7],
                        "rebar_hanger": r[8],
                        "stirrup": r[9],
                        "is_safe": r[10],
                        "safety_status": r[11],
                        "spans_data": r[12] if isinstance(r[12], list) else (json.loads(r[12]) if r[12] else []),
                        "layout_settings": r[13] if isinstance(r[13], dict) else (json.loads(r[13]) if r[13] else {}),
                        "updated_at": str(r[14])
                    })
                return {"success": True, "engine": "postgresql", "count": len(results), "designs": results}
            except Exception as e:
                self.engine = "sqlite"
                self.last_error = str(e)

        # Fallback đọc từ SQLite
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT story, long_beam_id, section, span_count, total_length_mm,
                       rebar_top_left, rebar_bot_mid, rebar_top_right, rebar_hanger, stirrup,
                       is_safe, safety_status, spans_data, layout_settings, updated_at
                FROM beam_rebar_designs
                WHERE project_name = ?
                ORDER BY story, long_beam_id;
                """, (project_name,))
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    spans = json.loads(r[12]) if r[12] else []
                    layout = json.loads(r[13]) if r[13] else {}
                    results.append({
                        "story": r[0],
                        "long_beam_id": r[1],
                        "section": r[2],
                        "span_count": r[3],
                        "total_length_mm": r[4],
                        "rebar_top_left": r[5],
                        "rebar_bot_mid": r[6],
                        "rebar_top_right": r[7],
                        "rebar_hanger": r[8],
                        "stirrup": r[9],
                        "is_safe": bool(r[10]),
                        "safety_status": r[11],
                        "spans_data": spans,
                        "layout_settings": layout,
                        "updated_at": str(r[14])
                    })
                return {"success": True, "engine": "sqlite", "count": len(results), "designs": results}
        except Exception as e:
            return {"success": False, "message": f"Lỗi đọc DB: {str(e)}", "designs": []}

    def get_status(self):
        """Lấy thông tin trạng thái DB."""
        pg_online = self.check_and_init_pg()
        sqlite_count = 0
        try:
            with sqlite3.connect(SQLITE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM beam_rebar_designs")
                sqlite_count = cur.fetchone()[0]
        except Exception:
            pass

        pg_count = 0
        if pg_online:
            try:
                conn = self.get_pg_connection()
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM beam_rebar_designs")
                    pg_count = cur.fetchone()[0]
                conn.close()
            except Exception:
                pass

        return {
            "postgresql_online": pg_online,
            "current_engine": self.engine,
            "host": self.host,
            "port": self.port,
            "database": self.db,
            "user": self.user,
            "sqlite_count": sqlite_count,
            "postgresql_count": pg_count,
            "last_error": self.last_error
        }

    get_db_status = get_status

# Singleton instance
db_manager = RebarDatabaseManager()

import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Optional

class MeetingDatabase:
    """会议数据存储模块，使用SQLite数据库"""
    
    def __init__(self, db_path="meetings.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建会议表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                audio_path TEXT,
                transcript_text TEXT,
                meeting_date DATE,
                duration_seconds INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建行动项表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER,
                description TEXT NOT NULL,
                owner TEXT,
                deadline TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_meeting(self, title: str, audio_path: str = None, 
                   transcript_text: str = None, duration_seconds: int = None) -> int:
        """
        添加新的会议记录
        
        Args:
            title: 会议标题
            audio_path: 音频文件路径
            transcript_text: 转写文本
            duration_seconds: 会议时长（秒）
            
        Returns:
            int: 新会议记录的ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        meeting_date = datetime.datetime.now().date().isoformat()
        
        cursor.execute('''
            INSERT INTO meetings (title, audio_path, transcript_text, meeting_date, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, audio_path, transcript_text, meeting_date, duration_seconds))
        
        meeting_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return meeting_id
    
    def add_action_item(self, meeting_id: int, description: str, 
                       owner: str = None, deadline: str = None, 
                       priority: str = "medium") -> int:
        """
        添加行动项
        
        Args:
            meeting_id: 关联的会议ID
            description: 行动项描述
            owner: 负责人
            deadline: 截止时间
            priority: 优先级（low/medium/high）
            
        Returns:
            int: 新行动项的ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO action_items (meeting_id, description, owner, deadline, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (meeting_id, description, owner, deadline, priority))
        
        action_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return action_id
    
    def get_meetings(self, limit: int = 10) -> List[Dict]:
        """
        获取会议列表
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            List[Dict]: 会议记录列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM meetings 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return meetings
    
    def get_action_items(self, meeting_id: Optional[int] = None, 
                        status: str = None) -> List[Dict]:
        """
        获取行动项列表
        
        Args:
            meeting_id: 可选的会议ID过滤器
            status: 可选的状态过滤器
            
        Returns:
            List[Dict]: 行动项列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM action_items WHERE 1=1"
        params = []
        
        if meeting_id is not None:
            query += " AND meeting_id = ?"
            params.append(meeting_id)
        
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        action_items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return action_items
    
    def update_action_item_status(self, action_id: int, status: str):
        """
        更新行动项状态
        
        Args:
            action_id: 行动项ID
            status: 新状态（pending/in_progress/completed）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE action_items 
            SET status = ? 
            WHERE id = ?
        ''', (status, action_id))
        
        conn.commit()
        conn.close()
    
    def delete_meeting(self, meeting_id: int):
        """
        删除会议记录及关联的行动项
        
        Args:
            meeting_id: 会议ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 先删除关联的行动项
        cursor.execute('DELETE FROM action_items WHERE meeting_id = ?', (meeting_id,))
        # 再删除会议记录
        cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        
        conn.commit()
        conn.close()
    
    def get_meeting_with_actions(self, meeting_id: int) -> Optional[Dict]:
        """
        获取会议详情及其所有行动项
        
        Args:
            meeting_id: 会议ID
            
        Returns:
            Optional[Dict]: 会议详情和行动项列表，如果不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取会议信息
        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        meeting_row = cursor.fetchone()
        
        if not meeting_row:
            conn.close()
            return None
        
        meeting = dict(meeting_row)
        
        # 获取关联的行动项
        action_items = self.get_action_items(meeting_id=meeting_id)
        meeting['action_items'] = action_items
        
        conn.close()
        return meeting


def test_database():
    """测试数据库功能"""
    db = MeetingDatabase("test_meetings.db")
    
    # 添加测试会议
    meeting_id = db.add_meeting(
        title="项目启动会",
        audio_path="meeting_20240403.mp3",
        transcript_text="今天我们讨论项目目标和时间安排。",
        duration_seconds=1800
    )
    print(f"添加会议成功，ID: {meeting_id}")
    
    # 添加测试行动项
    action_id1 = db.add_action_item(
        meeting_id=meeting_id,
        description="编写项目需求文档",
        owner="小张",
        deadline="2024-04-10",
        priority="high"
    )
    print(f"添加行动项1成功，ID: {action_id1}")
    
    action_id2 = db.add_action_item(
        meeting_id=meeting_id,
        description="准备技术方案",
        owner="小李",
        deadline="2024-04-12",
        priority="medium"
    )
    print(f"添加行动项2成功，ID: {action_id2}")
    
    # 查询会议列表
    meetings = db.get_meetings()
    print(f"\n会议列表 (共{len(meetings)}个):")
    for meeting in meetings:
        print(f"  - {meeting['title']} (ID: {meeting['id']})")
    
    # 查询行动项
    action_items = db.get_action_items(meeting_id=meeting_id)
    print(f"\n行动项列表 (共{len(action_items)}个):")
    for item in action_items:
        print(f"  - {item['description']} (负责人: {item['owner']}, 状态: {item['status']})")
    
    # 更新行动项状态
    db.update_action_item_status(action_id1, "in_progress")
    print(f"\n更新行动项 {action_id1} 状态为 in_progress")
    
    # 查询会议详情
    meeting_detail = db.get_meeting_with_actions(meeting_id)
    if meeting_detail:
        print(f"\n会议详情:")
        print(f"标题: {meeting_detail['title']}")
        print(f"行动项数量: {len(meeting_detail['action_items'])}")
    
    # 清理测试数据库
    import os
    if os.path.exists("test_meetings.db"):
        os.remove("test_meetings.db")
        print("\n已清理测试数据库")


if __name__ == "__main__":
    test_database()
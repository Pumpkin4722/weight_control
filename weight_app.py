import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. 数据库管理 ---
def get_db_connection():
    return sqlite3.connect('weight_data.db')

def init_and_upgrade_db():
    """初始化数据库，自动升级字段"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date TEXT NOT NULL,
            weight REAL NOT NULL,
            note TEXT
        )
    ''')
    # 尝试添加三餐字段
    new_columns = ['breakfast', 'lunch', 'dinner']
    for col in new_columns:
        try:
            c.execute(f"ALTER TABLE records ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass 
    conn.commit()
    conn.close()

def add_record(record_date, weight_kg, note, breakfast, lunch, dinner):
    """保存记录"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM records WHERE record_date = ?", (record_date,))
    data = c.fetchone()
    if data:
        c.execute('''UPDATE records SET weight=?, note=?, breakfast=?, lunch=?, dinner=? WHERE id=?''', 
                  (weight_kg, note, breakfast, lunch, dinner, data[0]))
    else:
        c.execute('''INSERT INTO records (record_date, weight, note, breakfast, lunch, dinner) VALUES (?, ?, ?, ?, ?, ?)''', 
                  (record_date, weight_kg, note, breakfast, lunch, dinner))
    conn.commit()
    conn.close()

def get_records():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM records ORDER BY record_date ASC", conn)
    conn.close()
    return df

# --- 2. 辅助函数：BMI 状态 ---
def get_bmi_status(bmi):
    if bmi < 18.5:
        return "🟦 偏瘦", "blue"
    elif 18.5 <= bmi < 24.0:
        return "✅ 正常", "green"
    elif 24.0 <= bmi < 28.0:
        return "⚠️ 超重", "orange"
    else:
        return "🔴 肥胖", "red"

# --- 3. 页面主逻辑 ---
def main():
    st.set_page_config(page_title="体重与饮食管理", page_icon="🍱", layout="wide")
    init_and_upgrade_db()

    st.title("🍱 体重与饮食管理助手")

    # --- 侧边栏 ---
    with st.sidebar:
        st.header("⚙️ 单位设置")
        unit_mode = st.radio("显示单位", ["公斤 (kg)", "市斤 (斤)"], horizontal=True)
        unit_factor = 2 if "斤" in unit_mode else 1
        unit_label = "斤" if "斤" in unit_mode else "kg"
        
        st.divider()
        st.header("📝 录入数据")
        input_date = st.date_input("日期", date.today())
        
        # 默认体重
        default_val = 60.0 * unit_factor
        input_val = st.number_input(f"今日体重 ({unit_label})", 0.0, 600.0, default_val, 0.1)
        weight_to_save_kg = input_val / unit_factor 

        # --- 修改点 1: 默认身高改为 180 ---
        input_height = st.number_input("📏 身高 (cm)", 100, 250, 180) 
        
        st.subheader("🍽️ 三餐记录")
        input_bk = st.text_input("🥪 早餐")
        input_lc = st.text_input("🍱 午餐")
        input_dn = st.text_input("🥗 晚餐")
        input_note = st.text_area("📝 备注", height=60)

        if st.button("💾 保存记录", type="primary", use_container_width=True):
            add_record(input_date, weight_to_save_kg, input_note, input_bk, input_lc, input_dn)
            st.success("✅ 保存成功！")
            st.rerun()

        # 侧边栏 BMI 展示
        st.divider()
        current_bmi = weight_to_save_kg / ((input_height/100) ** 2)
        status_text, status_color = get_bmi_status(current_bmi)
        st.markdown(f"当前 BMI: **{current_bmi:.1f}** ({status_text})")
        
        with st.expander("ℹ️ BMI 标准表"):
            st.markdown("""
            | BMI | 状态 |
            | :--- | :--- |
            | < 18.5 | 🟦 偏瘦 |
            | 18.5~23.9 | ✅ 正常 |
            | 24.0~27.9 | ⚠️ 超重 |
            | ≥ 28.0 | 🔴 肥胖 |
            """)

    # --- 主界面 ---
    df = get_records()

    if not df.empty:
        df['record_date'] = pd.to_datetime(df['record_date'])
        
        current_kg = df.iloc[-1]['weight']
        display_current = current_kg * unit_factor
        
        delta_str = "-"
        if len(df) > 1:
            prev = df.iloc[-2]['weight']
            diff = (current_kg - prev) * unit_factor
            delta_str = f"{diff:+.1f} {unit_label}"
            
        # --- 修改点 2: 顶部改为 4 列，增加身高显示 ---
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(f"最新体重 ({unit_label})", f"{display_current:.1f}", delta_str)
        col2.metric("当前 BMI", f"{current_bmi:.1f}", status_text)
        col3.metric("记录天数", f"{len(df)} 天")
        col4.metric("设定身高", f"{input_height} cm") # 新增的身高显示

        # 趋势图
        st.subheader(f"📈 趋势图 ({unit_label})")
        df['display_weight'] = df['weight'] * unit_factor
        st.line_chart(df, x='record_date', y='display_weight')

        # 详细记录表
        st.subheader("🗂️ 详细记录")
        
        df_show = df.copy()
        df_show['weight'] = df_show['weight'] * unit_factor 
        
        # 动态计算表格中的 BMI
        height_m = input_height / 100
        df_show['BMI'] = df_show['weight'] / unit_factor / (height_m ** 2)
        df_show['BMI'] = df_show['BMI'].round(1)
        df_show['健康状态'] = df_show['BMI'].apply(lambda x: get_bmi_status(x)[0])
        
        df_show['record_date'] = df_show['record_date'].dt.strftime('%Y-%m-%d')
        
        rename_dict = {
            'record_date': '日期',
            'weight': f'体重({unit_label})',
            'breakfast': '早餐',
            'lunch': '午餐',
            'dinner': '晚餐',
            'note': '备注',
            'BMI': 'BMI',
            '健康状态': '健康状态'
        }
        df_show = df_show.rename(columns=rename_dict)
        
        cols = ['日期', f'体重({unit_label})', 'BMI', '健康状态', '早餐', '午餐', '晚餐', '备注']
        valid_cols = [c for c in cols if c in df_show.columns]
        
        st.dataframe(
            df_show[valid_cols], 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "健康状态": st.column_config.TextColumn("健康状态", width="small"),
                "BMI": st.column_config.NumberColumn("BMI", format="%.1f"),
            }
        )

    else:
        st.info("👈 请在左侧添加第一条记录")

if __name__ == '__main__':
    main()
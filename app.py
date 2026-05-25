import streamlit as st
from solver_core import solve_cube

st.set_page_config(page_title="Smart Cube Solver", page_icon="🎲")

st.title("🎲 智慧魔術方塊解題器 (Spike)")
st.markdown("""
這是一個技術原型，用於驗證 Kociemba 演算法。
請輸入方塊的 54 字元狀態字串。
""")

# 說明資訊
with st.expander("如何輸入字串？"):
    st.write("""
    字串順序：**U (頂), R (右), F (前), D (底), L (左), B (後)**
    每個面 9 個格子，從左上到右下掃描。
    
    範例（已完成）：
    `UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB`
    """)

# 輸入框
cube_input = st.text_area("請輸入方塊字串 (54 字元):", 
                          value="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB",
                          height=100)

if st.button("計算解法"):
    if len(cube_input.strip()) == 54:
        with st.spinner('正在計算最佳路徑...'):
            result = solve_cube(cube_input.strip())
            
            if "錯誤" in result or "失敗" in result:
                st.error(result)
            else:
                st.success("找到解法！")
                st.code(result, language="text")
                st.info(f"總步數：{len(result.split())} 步")
    else:
        st.warning(f"請輸入正確的 54 字元 (目前：{len(cube_input.strip())} 字元)")

# 視覺化輔助 (簡易版)
st.sidebar.header("方塊狀態參考")
st.sidebar.info("""
U: Up (白色)
R: Right (紅色)
F: Front (綠色)
D: Down (黃色)
L: Left (橘色)
B: Back (藍色)
""")

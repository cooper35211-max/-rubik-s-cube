import twophase.solver as sv

def format_moves(solution_string):
    """
    將 twophase 的輸出格式轉換為標準魔術方塊代號
    twophase 輸出範例: "R2 U1 D3 (14f)"
    轉換目標: "R2 U D'"
    """
    # 移除最後的 "(xx f)" 以及首尾空白
    if "(" in solution_string:
        solution_string = solution_string[:solution_string.rfind("(")].strip()
        
    moves = solution_string.split()
    formatted_moves = []
    
    for move in moves:
        if len(move) == 2:
            face = move[0]
            turn = move[1]
            if turn == "1":
                formatted_moves.append(face)
            elif turn == "2":
                formatted_moves.append(face + "2")
            elif turn == "3":
                formatted_moves.append(face + "'")
            else:
                formatted_moves.append(move)
        else:
            formatted_moves.append(move)
            
    return " ".join(formatted_moves)

def solve_cube(cube_string):
    """
    使用 RubikTwoPhase 解魔術方塊
    """
    try:
        # 1. 驗證長度
        if len(cube_string) != 54:
            return f"錯誤：長度應為 54，目前為 {len(cube_string)}"
        
        # 2. 驗證顏色分布
        for color in set(cube_string):
            if cube_string.count(color) != 9:
                return f"錯誤：顏色 {color} 的數量不正確 ({cube_string.count(color)}/9)"
        
        # 3. 呼叫真正的 Kociemba 解題器
        # sv.solve 參數：(字串, max_length, timeout)
        solution = sv.solve(cube_string, 20, 2)
        
        # twophase 回傳的字串若是錯誤，會包含 'Error'
        if solution.startswith("Error"):
            return f"演算法判定此方塊無解或錯置：{solution}"
            
        # 格式化輸出
        return format_moves(solution)

    except Exception as e:
        return f"解析失敗：{str(e)}"

if __name__ == "__main__":
    test = "BDRFULFBFLBBDRFRBLDUUFFRURFRUDLDDDRBUULDLLBUFUFLRBLDBR"
    print(f"測試使用者字串：\n{solve_cube(test)}")

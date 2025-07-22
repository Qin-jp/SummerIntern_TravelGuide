import random
from typing import List, Tuple
from TravelAgent import TravelAgent
from UserAgent import UserAgent

random.seed(42)

def run_conversation(path: str = None, turns: int = 4) -> List[Tuple[str, str]]:
    """
    仅返回多轮对话结果：[(question1, answer1), (question2, answer2), ...]
    """
    travel_agent = TravelAgent()
    user_agent = UserAgent()

    # 1. 加载并拆分约束（路径按需替换）
    #path = "/home/JingpengQin/travel_guide/final_data/处理结果/黄冈市旅游攻略/攻略_27763706s2_5日游/攻略_27763706s2_5日游_constraints.json"
    user_agent.constraints_manager.load_constraints(path)
    user_agent.constraints_manager.split_constraints(turns)

    qa: List[Tuple[str, str]] = []

    # 第一轮
    q1 = user_agent.generate_x1_question()
    travel_agent.get_user_question_from_user_agent(q1)
    a1 = travel_agent.get_response()
    qa.append((q1, a1['content']))

    # 后续轮次
    for i in range(1, turns):
        user_agent.get_answer_from_travel_agent(qa[-1][1])
        q = user_agent.generate_xn_question(i)
        travel_agent.get_user_question_from_user_agent(q)
        a = travel_agent.get_response()
        qa.append((q, a['content']))

    return qa


# ----------------- 调用示例 -----------------
if __name__ == "__main__":
    conversations = run_conversation(path = "/home/JingpengQin/travel_guide/final_data/处理结果/黄冈市旅游攻略/攻略_27763706s2_5日游/攻略_27763706s2_5日游_constraints.json",turns = 4)
    for idx, (q, a) in enumerate(conversations, 1):
        print(f"Round {idx}:")
        print("Q:", q)
        print("A:", a)
        print("-" * 40)
# import random
# random.seed(42)  # 设置随机种子以确保结果可复现

# from TravelAgent import TravelAgent
# from UserAgent import UserAgent
# import json




# def main():
#     xn = []
#     yn = []
#     conversation_turns = 4 #对话轮数

#     travel_agent = TravelAgent()
#     user_agent = UserAgent()

#     user_agent.constraints_manager.load_constraints("/home/JingpengQin/travel_guide/final_data/处理结果/黄冈市旅游攻略/攻略_27763706s2_5日游/攻略_27763706s2_5日游_constraints.json")
#     user_agent.constraints_manager.split_constraints(conversation_turns)

#     x1_question = user_agent.generate_x1_question()
#     travel_agent.get_user_question_from_user_agent(x1_question)
#     y1_response = travel_agent.get_response()
#     yn_response = y1_response

#     xn.append(x1_question)
#     yn.append(y1_response['content'])

#     print(f"Round 1:")
#     print(f"x1 Question: {x1_question}")
#     print(f"y1 Response: {yn[0]}")


#     for i in range(1, conversation_turns):
#         user_agent.get_answer_from_travel_agent(yn_response['content'])
#         xn_question = user_agent.generate_xn_question(i)
#         print(f"x{i + 1} Question: {xn_question}")
#         travel_agent.get_user_question_from_user_agent(xn_question)

#         yn_response = travel_agent.get_response()
#         print(f"Round {i+1}:")
#         print(f"x{i + 1} Question: {xn_question}")
#         print(f"y{i + 1} Response: {yn_response['content']}")
#         xn.append(xn_question)
#         yn.append(yn_response["content"])
#     user_agent.get_answer_from_travel_agent(yn_response['content'])
    
#     with open("/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/conversation_history.md", "w") as f:
#         for i in range(conversation_turns):
#             f.write(f"Round {i+1}:\n")
#             f.write(f"x{i + 1} Question: {xn[i]}\n")
#             if i == 0:
#                 f.write(f"x{i + 1} constraints: {user_agent.constraints_manager.x1_constraints}\n")
#             else:
#                 f.write(f"x{i + 1} constraints: {user_agent.constraints_manager.xn_constraints[i-1]}\n")
#             f.write(f"y{i + 1} Response: {yn[i]}\n\n")

#     with open("/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/conversation_history_UserAgent.md", "w", encoding="utf-8") as f:
#         i = 0
#         f.write("# User Agent Conversation History\n\n")
#         for msg in user_agent.conversation_history:
#             role = msg["role"].capitalize()
#             content = msg["content"]
#             if i % 2 == 0:
#                 f.write(f"Round {i//2+1}:\n")
#             i = i + 1
#             f.write(f"### {role}\n\n{content}\n\n---\n\n")
#     with open("/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/conversation_history_TravelAgent.md", "w", encoding="utf-8") as f:
#         i = 0
#         f.write("# Travel Agent Conversation History\n\n")
#         for msg in travel_agent.conversation_history:
#             role = msg["role"].capitalize()
#             content = msg["content"]
#             if i % 2 == 0:
#                 f.write(f"Round {i//2+1}:\n")
#             i = i + 1
#             f.write(f"### {role}\n\n{content}\n\n---\n\n")

#     # ✅ 保存 TravelAgent 的 MCP 工具调用记录
#     with open("mcp_calls.md", "w", encoding="utf-8") as md:
#         md.write("# TravelAgent MCP Tool Calls Log\n\n")
#         for rec in travel_agent.mcp_calls:
#             md.write(f"## Call {rec['call_no']} - `{rec['tool']}`\n\n")

#         # ✅ 安全处理 arguments
#             try:
#                 args = json.loads(rec["arguments"])
#                 args_str = json.dumps(args, ensure_ascii=False, indent=2)
#             except Exception:
#                 args_str = rec["arguments"]

#         # ✅ 安全处理 return
#             try:
#                 ret = json.loads(rec["return"])
#                 ret_str = json.dumps(ret, ensure_ascii=False, indent=2)
#             except Exception:
#                 ret_str = rec["return"]

#             md.write("### Arguments\n```json\n")
#             md.write(args_str)
#             md.write("\n```\n\n")

#             md.write("### Return\n```json\n")
#             md.write(ret_str)
#             md.write("\n```\n\n---\n\n")
#             md.write("\n```\n\n---\n\n")

# if __name__ == "__main__":
#     main()



import random
import json
from TravelAgent import TravelAgent
from UserAgent import UserAgent

random.seed(42)

# -------------------------------------------------
# 1. 初始化 agent
# -------------------------------------------------
def init_agents() -> tuple[TravelAgent, UserAgent]:
    return TravelAgent(), UserAgent()

# -------------------------------------------------
# 2. 加载并拆分约束
# -------------------------------------------------
def load_constraints(user_agent: UserAgent, turns: int) -> None:
    path = "/home/JingpengQin/travel_guide/final_data/处理结果/黄冈市旅游攻略/攻略_27763706s2_5日游/攻略_27763706s2_5日游_constraints.json"
    user_agent.constraints_manager.load_constraints(path)
    user_agent.constraints_manager.split_constraints(turns)

# -------------------------------------------------
# 3. 运行对话，收集问题与答案
# -------------------------------------------------
def run_dialogue(travel_agent: TravelAgent,
                 user_agent: UserAgent,
                 turns: int) -> tuple[list[str], list[str]]:
    xn, yn = [], []

    # 第一轮
    x1 = user_agent.generate_x1_question()
    travel_agent.get_user_question_from_user_agent(x1)
    y1 = travel_agent.get_response()
    xn.append(x1)
    yn.append(y1['content'])
    print(f"Round 1:\nx1 Question: {x1}\ny1 Response: {yn[0]}")

    # 后续轮次
    for i in range(1, turns):
        user_agent.get_answer_from_travel_agent(yn[-1])
        xn_q = user_agent.generate_xn_question(i)
        travel_agent.get_user_question_from_user_agent(xn_q)
        yn_resp = travel_agent.get_response()
        print(f"Round {i+1}:\nx{i+1} Question: {xn_q}\ny{i+1} Response: {yn_resp['content']}")
        xn.append(xn_q)
        yn.append(yn_resp['content'])

    user_agent.get_answer_from_travel_agent(yn[-1])  # 最后一次同步
    return xn, yn

# -------------------------------------------------
# 4. 统一保存所有文件
# -------------------------------------------------
def save_outputs(travel_agent: TravelAgent,
                 user_agent: UserAgent,
                 xn: list[str],
                 yn: list[str],
                 turns: int) -> None:

    # 1) 对话总览
    with open("/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/conversation_history.md", "w") as f:
        for i in range(turns):
            f.write(f"Round {i+1}:\n")
            f.write(f"x{i+1} Question: {xn[i]}\n")
            f.write(
                f"x{i+1} constraints: "
                f"{user_agent.constraints_manager.x1_constraints if i == 0 else user_agent.constraints_manager.xn_constraints[i-1]}\n"
            )
            f.write(f"y{i+1} Response: {yn[i]}\n\n")

    # 2) UserAgent 对话
    with open("/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/conversation_history_UserAgent.md", "w", encoding="utf-8") as f:
        f.write("# User Agent Conversation History\n\n")
        for idx, msg in enumerate(user_agent.conversation_history):
            f.write(f"Round {idx//2+1}:\n" if idx % 2 == 0 else "")
            f.write(f"### {msg['role'].capitalize()}\n\n{msg['content']}\n\n---\n\n")

    # 3) TravelAgent 对话
    with open("/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/conversation_history_TravelAgent.md", "w", encoding="utf-8") as f:
        f.write("# Travel Agent Conversation History\n\n")
        for idx, msg in enumerate(travel_agent.conversation_history):
            f.write(f"Round {idx//2+1}:\n" if idx % 2 == 0 else "")
            f.write(f"### {msg['role'].capitalize()}\n\n{msg['content']}\n\n---\n\n")

    # 4) MCP 调用
    with open("/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/mcp_calls.md", "w", encoding="utf-8") as md:
        md.write("# TravelAgent MCP Tool Calls Log\n\n")
        for rec in travel_agent.mcp_calls:
            md.write(f"## Call {rec['call_no']} - `{rec['tool']}`\n\n")

            # arguments
            try:
                args_str = json.dumps(json.loads(rec["arguments"]), ensure_ascii=False, indent=2)
            except Exception:
                args_str = rec["arguments"]
            md.write("### Arguments\n```json\n" + args_str + "\n```\n\n")

            # return
            try:
                ret_str = json.dumps(json.loads(rec["return"]), ensure_ascii=False, indent=2)
            except Exception:
                ret_str = rec["return"]
            md.write("### Return\n```json\n" + ret_str + "\n```\n\n---\n\n")

# -------------------------------------------------
# 5. 主函数：按序调用
# -------------------------------------------------
def main():
    turns = 4
    travel_agent, user_agent = init_agents()
    load_constraints(user_agent, turns)
    xn, yn = run_dialogue(travel_agent, user_agent, turns)
    save_outputs(travel_agent, user_agent, xn, yn, turns)

if __name__ == "__main__":
    main()
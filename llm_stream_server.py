from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import uvicorn
import json

# --- FastAPI 설정 ---
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 클래스 정의
class QueryRequest(BaseModel):
    query: str
    selected_option: Optional[str] = None

# ChatOllama 인스턴스 생성
llm = ChatOllama(
        model="cookieshake/kanana-1.5-8b-instruct-2505:Q4_K_M",
        base_url="http://localhost:11434",
        temperature=0
    )

# 시스템 메시지 정의
system_message = SystemMessage(content="You are a helpful AI assistant who remembers the last few turns of our conversation.")

# 추천 프롬프트 생성을 위한 시스템 메시지
recommendation_system_message = SystemMessage(content="""당신은 사용자의 대화 내용을 분석하여 다음에 물어볼 만한 유용한 질문들을 추천하는 AI 어시스턴트입니다.

다음 규칙을 따라 추천 프롬프트를 생성해주세요:
1. 사용자의 질문과 AI의 답변을 고려하여 자연스럽고 관련성 높은 후속 질문을 생성
2. 구체적이고 실용적인 질문 위주로 구성
3. 3개의 추천 프롬프트를 생성하며, 각각 다른 관점이나 깊이의 질문이 되도록 함
4. 한국어로 자연스럽게 작성
5. JSON 배열 형태로 반환 (예: ["질문1", "질문2", "질문3"])

예시:
- 기술적 질문에 대한 답변 후: ["더 자세한 사용법을 알려주세요", "다른 대안은 무엇인가요?", "실제 적용 사례를 보여주세요"]
- 일반적인 질문에 대한 답변 후: ["관련된 다른 주제는 무엇인가요?", "실제로 어떻게 적용할 수 있나요?", "더 구체적인 예시를 들어주세요"]
""")

# 대화 내용(Chat History)을 저장할 리스트
chat_history = []

# LLM에 전달할 최근 메시지 개수 설정 (예: 최근 4개 메시지 쌍)
# 이 값을 조절하여 얼마나 많은 과거 대화를 LLM이 기억하게 할지 결정(시스템 메시지는 항상 포함됨)
MAX_HISTORY_MESSAGES = 4

# 추천 프롬프트 생성 함수
def generate_recommendations(user_query: str, ai_response: str) -> list[str]:
    """
    사용자의 질문과 AI의 답변을 기반으로 추천 프롬프트를 생성합니다.
    """
    try:
        # 추천 프롬프트 생성을 위한 메시지 구성
        recommendation_messages = [
            recommendation_system_message,
            HumanMessage(content=f"""다음 대화 내용을 분석하여 3개의 추천 프롬프트를 생성해주세요:

사용자 질문: {user_query}
AI 답변: {ai_response}

JSON 배열 형태로만 응답해주세요. 예: ["질문1", "질문2", "질문3"]""")
        ]
        
        # LLM을 사용하여 추천 프롬프트 생성
        response = llm.invoke(recommendation_messages)
        content = response.content.strip()
        
        # JSON 파싱 시도
        try:
            import ast
            # 안전한 리터럴 평가 사용
            recommendations = ast.literal_eval(content)
            if isinstance(recommendations, list) and len(recommendations) >= 3:
                return recommendations[:3]  # 최대 3개만 반환
        except (ValueError, SyntaxError):
            pass
        
        # JSON 파싱 실패 시 기본 추천 프롬프트 반환
        return [
            "더 구체적으로 답변해 주세요.",
            "다른 관점에서 설명해 주세요.",
            "실제 적용 방법을 알려주세요."
        ]
        
    except Exception as e:
        print(f"추천 프롬프트 생성 중 오류: {e}")
        # 오류 발생 시 기본 추천 프롬프트 반환
        return [
            "더 구체적으로 답변해 주세요.",
            "다른 관점에서 설명해 주세요.",
            "실제 적용 방법을 알려주세요."
        ]

# 스트리밍 응답 함수
def stream_rag_response(query: str, selected_option: Optional[str] = None):
    """
    ChatOllama를 통한 실시간 스트리밍 응답을 받아서 클라이언트에 전달하는 함수
    """
    global chat_history  # 대화 히스토리 전역 변수 선언
    
    try:
        # 사용자 질문 메시지 구성
        if selected_option:
            user_query = f"{query}\n\n추가 요청: {selected_option}"
        else:
            user_query = query
            
        # 새로운 사용자 메시지 생성
        user_message = HumanMessage(content=user_query)
        
        # 메시지 리스트 구성: 시스템 메시지 + 최근 대화 히스토리 + 현재 사용자 메시지
        messages = [system_message]
        
        # 최근 대화 히스토리 추가 (MAX_HISTORY_MESSAGES 개수만큼)
        recent_history = chat_history[-MAX_HISTORY_MESSAGES:] if len(chat_history) > MAX_HISTORY_MESSAGES else chat_history
        messages.extend(recent_history)
        
        # 현재 사용자 메시지 추가
        messages.append(user_message)
        
        # AI 응답을 저장할 변수
        full_response = ""
        
        # ChatOllama 스트리밍 응답 처리
        for chunk in llm.stream(messages):
            # chunk.content가 있는지 확인하고 사용
            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            full_response += content
            
            # 각 토큰을 JSON 형태로 yield
            token_data = {
                "type": "token",
                "content": content
            }
            yield json.dumps(token_data, ensure_ascii=False) + "\n"
        
        # 대화 히스토리에 사용자 메시지와 AI 응답 저장
        chat_history.append(user_message)
        chat_history.append(AIMessage(content=full_response.strip()))
        
        # 히스토리가 너무 길어지면 오래된 메시지 제거 (시스템 메시지는 제외)
        # MAX_HISTORY_MESSAGES * 2 (사용자 + AI 메시지 쌍의 개수를 제한)
        max_total_messages = MAX_HISTORY_MESSAGES * 2
        if len(chat_history) > max_total_messages:
            # 가장 오래된 메시지 쌍 제거
            chat_history = chat_history[2:]
        
        # 응답 완료 후 동적으로 추천 프롬프트 생성
        recommendations = generate_recommendations(user_query, full_response.strip())
        
        recommendation_data = {
            "type": "recommendations",
            "data": recommendations
        }
        yield json.dumps(recommendation_data, ensure_ascii=False) + "\n"
        
    except Exception as e:
        # 에러 발생 시 에러 메시지 전송
        error_data = {
            "type": "error",
            "content": f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        }
        yield json.dumps(error_data, ensure_ascii=False) + "\n"

@app.post("/rag-query")
async def rag_query(request: QueryRequest):
    return StreamingResponse(
        stream_rag_response(request.query, request.selected_option),
        media_type="text/plain"
    )

# @app.get("/chat-history")
# async def get_chat_history():
#     """현재 대화 히스토리 조회"""
#     history_data = []
#     for msg in chat_history:
#         if isinstance(msg, HumanMessage):
#             history_data.append({"type": "human", "content": msg.content})
#         elif isinstance(msg, AIMessage):
#             history_data.append({"type": "ai", "content": msg.content})
    
#     return {"history": history_data, "total_messages": len(chat_history)}

@app.post("/clear-history")
async def clear_chat_history():
    """대화 히스토리 초기화"""
    global chat_history
    chat_history = []
    return {"message": "대화 히스토리가 초기화되었습니다."}
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 
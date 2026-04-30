import time
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
import random  # 仅用于Demo中模拟不确定性

# ==========================================
# 1. 定义核心数据模型与枚举
# ==========================================

class Priority(Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    CRITICAL = "紧急"

@dataclass
class CustomerTicket:
    """原始客户工单"""
    ticket_id: str
    customer_id: str
    customer_tier: str  # VIP, Enterprise, Standard
    raw_query: str
    timestamp: float

@dataclass
class KnowledgeNode:
    """知识图谱中的节点"""
    id: str
    content: str
    source: str  # doc, wiki, ticket, release_note
    module: str  # 产品模块
    last_updated: float
    confidence: float = 0.9  # 置信度

@dataclass
class StructuredIntent:
    """结构化意图"""
    intent: str  # 如 "bug_report", "feature_request", "how_to"
    urgency: Priority
    entities: Dict[str, Any]  # 提取的关键实体，如 {"error_code": "E102", "feature": "dashboard"}
    keywords: List[str]
    raw_query: str

@dataclass
class SynthesizedAnswer:
    """合成的答案"""
    answer_text: str
    citations: List[Dict[str, Any]]  # 引用来源，包含链接和置信度
    confidence: float
    reasoning: str  # 推理过程摘要
    estimated_token_usage: int
    requires_human_review: bool = False

@dataclass
class FinalResponse:
    """最终合规响应"""
    ticket_id: str
    final_answer: str
    compliance_notes: List[str]  # 合规检查项
    processing_time_sec: float
    agents_involved: List[str]
    token_usage_estimate: int

# ==========================================
# 2. 模拟外部数据源 (真实项目中替换为API/DB调用)
# ==========================================

class MockDataStore:
    """模拟动态知识库、历史工单等"""
    def __init__(self):
        self.knowledge_graph = self._build_knowledge_graph()
        self.historical_tickets = self._build_historical_tickets()
        self.product_updates = self._build_updates()

    def _build_knowledge_graph(self) -> Dict[str, KnowledgeNode]:
        # 实际应从DB或向量库加载
        return {
            "kb_001": KnowledgeNode(
                id="kb_001",
                content="错误码E102表示API调用频率超限。解决方案：1. 检查调用速率 2. 实施指数退避重试 3. 联系管理员提升配额。",
                source="官方文档",
                module="API网关",
                last_updated=time.time() - 86400 * 2
            ),
            "kb_002": KnowledgeNode(
                id="kb_002",
                content="2024-05-20版本v2.5.1发布：新增仪表盘自定义功能，修复了E102在特定场景下的误报问题。",
                source="发布日志",
                module="全局",
                last_updated=time.time() - 86400
            ),
            "kb_003": KnowledgeNode(
                id="kb_003",
                content="如何为VIP客户重置API配额？路径：管理控制台 -> 客户管理 -> 选择客户 -> API设置 -> 重置配额。",
                source="内部Wiki",
                module="管理后台",
                last_updated=time.time() - 86400 * 5
            )
        }

    def _build_historical_tickets(self) -> List[Dict]:
        return [
            {"id": "t_old_001", "query": "我的API返回E102错误怎么办？", "resolution": "参考kb_001，建议客户检查代码并实施重试机制。"},
            {"id": "t_old_002", "query": "为什么我的仪表盘无法保存布局？", "resolution": "确认客户使用v2.5.1以上版本，旧版本存在此问题。"}
        ]

    def _build_updates(self) -> List[Dict]:
        return [
            {"date": "2024-05-20", "version": "v2.5.1", "content": "修复E102误报；新增仪表盘自定义。"}
        ]

    def get_relevant_knowledge(self, query: str, module_hint: str = None) -> List[KnowledgeNode]:
        """核心检索逻辑：模拟语义检索+模块过滤"""
        # 真实场景：使用Embedding相似度搜索 + 元数据过滤
        results = []
        query_lower = query.lower()

        for node in self.knowledge_graph.values():
            score = 0
            # 简单关键词匹配模拟相关性
            if "e102" in query_lower and "e102" in node.content.lower():
                score += 10
            if "仪表盘" in query_lower and "仪表盘" in node.content.lower():
                score += 8
            if node.module == module_hint:
                score += 5
            if score > 0:
                results.append((node, score))

        # 按相关性降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [node for node, _ in results[:3]]  # 返回Top3

    def get_historical_similar_tickets(self, query: str, intent: str) -> List[Dict]:
        """检索历史相似工单"""
        # 真实场景：基于意图和查询向量的混合检索
        if intent == "bug_report":
            return [t for t in self.historical_tickets if "错误" in t["query"] or "e102" in t["query"].lower()]
        return []

# ==========================================
# 3. 核心Agent实现
# ==========================================

class AgentKnowledgeAggregator:
    """Agent 1: 知识聚合与更新 (后台常驻)"""
    def __init__(self, data_store: MockDataStore):
        self.data_store = data_store
        self.knowledge_graph = data_store.knowledge_graph

    def monitor_and_update(self):
        """模拟监控新文档、工单、更新日志，并更新知识图谱"""
        print("  [Agent-KA] 监控知识源变更...")
        time.sleep(0.1)  # 模拟耗时

        # 模拟：发现一个新知识（例如从最新工单中提炼）
        new_node = KnowledgeNode(
            id="kb_004",
            content="重要提示：v2.5.1以下版本仪表盘保存功能存在兼容性问题，请升级。",
            source="工单提炼",
            module="前端UI",
            last_updated=time.time()
        )
        self.knowledge_graph["kb_004"] = new_node
        print(f"  [Agent-KA] 已新增知识节点: {new_node.id} (来源: {new_node.source})")
        return True

class AgentIntentClassifier:
    """Agent 2: 意图理解与实体提取"""
    def analyze(self, ticket: CustomerTicket) -> StructuredIntent:
        print(f"  [Agent-IC] 分析工单 {ticket.ticket_id}...")
        time.sleep(0.2)

        query = ticket.raw_query.lower()
        intent = "general_inquiry"
        urgency = Priority.MEDIUM
        entities = {}
        keywords = []

        # 规则+关键词的混合推理 (真实项目用LLM)
        if "错误" in query or "e102" in query or "报错" in query:
            intent = "bug_report"
            urgency = Priority.HIGH if "紧急" in query else Priority.MEDIUM
            entities["error_code"] = "E102" if "e102" in query else None
        elif "如何" in query or "怎么" in query or "?" in query:
            intent = "how_to"
        elif "新功能" in query or "建议" in query:
            intent = "feature_request"
            urgency = Priority.LOW

        # 提取简单实体
        if "仪表盘" in query:
            entities["feature"] = "dashboard"
        if "配额" in query or "限制" in query:
            entities["resource"] = "api_quota"

        keywords = [w for w in ["e102", "仪表盘", "配额", "重置", "保存"] if w in query]

        print(f"  [Agent-IC] 识别意图: {intent}, 实体: {entities}")
        return StructuredIntent(
            intent=intent,
            urgency=urgency,
            entities=entities,
            keywords=keywords,
            raw_query=ticket.raw_query
        )

class AgentAnswerSynthesizer:
    """Agent 3: 多源信息检索与答案合成 (核心推理Agent)"""
    def __init__(self, data_store: MockDataStore):
        self.data_store = data_store

    def synthesize(self, ticket: CustomerTicket, intent: StructuredIntent) -> SynthesizedAnswer:
        print(f"  [Agent-AS] 为工单 {ticket.ticket_id} 合成答案...")
        start_time = time.time()

        # 1. 多源并行检索 (模拟)
        kb_results = self.data_store.get_relevant_knowledge(ticket.raw_query, intent.entities.get("feature"))
        historical_results = self.data_store.get_historical_similar_tickets(ticket.raw_query, intent.intent)

        # 2. 信息整合与冲突检测 (核心推理)
        reasoning_steps = []
        answer_parts = []
        citations = []
        confidence = 0.0

        # 根据意图和实体组合答案
        if intent.intent == "bug_report" and "e102" in intent.entities.values():
            # 查找关于E102的解决方案
            e102_doc = next((n for n in kb_results if "E102" in n.content), None)
            if e102_doc:
                answer_parts.append(e102_doc.content)
                citations.append({"node_id": e102_doc.id, "text": e102_doc.content[:50] + "...", "source": e102_doc.source})
                reasoning_steps.append("找到E102官方解决方案")
                confidence += 0.4

            # 检查是否有相关版本更新
            update_note = next((n for n in kb_results if "v2.5.1" in n.content), None)
            if update_note:
                if "修复" in update_note.content:
                    answer_parts.append("\n此外，请注意：此问题已在最新版本v2.5.1中修复。")
                    reasoning_steps.append("发现版本修复记录")
                    confidence += 0.3
            else:
                # 冲突：有知识说修复了，但本次检索没找到？这里模拟处理
                reasoning_steps.append("未发现明确的版本修复记录，建议按当前方案处理")

        elif "仪表盘" in intent.entities.values() and intent.intent == "how_to":
            how_to_doc = next((n for n in kb_results if "重置" in n.content or "保存" in n.content), None)
            if how_to_doc:
                answer_parts.append(how_to_doc.content)
                citations.append({"node_id": how_to_doc.id, "text": how_to_doc.content[:50] + "...", "source": how_to_doc.source})
                reasoning_steps.append("找到操作指南")
                confidence += 0.5

        # 3. 结合历史工单经验 (个性化)
        if historical_results:
            last_resolution = historical_results[-1]["resolution"]
            answer_parts.append(f"\n参考以往类似案例：{last_resolution}")
            reasoning_steps.append("参考近期成功解决案例")
            confidence += 0.2

        # 4. 最终答案构建与置信度计算
        final_answer = "\n".join(answer_parts) if answer_parts else "抱歉，未找到直接相关的解决方案。建议联系人工客服并提供详细错误信息。"
        confidence = min(confidence, 0.95)  # 封顶

        if confidence < 0.6:
            reasoning_steps.append("答案置信度较低，建议人工复核")
        else:
            reasoning_steps.append("多源信息一致，答案可靠")

        processing_time = time.time() - start_time
        # 粗略估算Token (1中文字≈1.5 token，1英文≈1 token)
        estimated_tokens = int(len(final_answer) * 1.5) + 500  # 加上推理过程的token

        print(f"  [Agent-AS] 合成完成，置信度: {confidence:.2f}, 耗时: {processing_time:.2f}s")
        return SynthesizedAnswer(
            answer_text=final_answer,
            citations=[{"text": c["text"], "source": c["source"]} for c in citations],
            confidence=confidence,
            reasoning=" -> ".join(reasoning_steps),
            estimated_token_usage=estimated_tokens
        )

class AgentComplianceChecker:
    """Agent 4: 合规与风格校准"""
    def check(self, answer: SynthesizedAnswer, ticket: CustomerTicket) -> (str, List[str]):
        print(f"  [Agent-CC] 执行合规检查...")
        time.sleep(0.1)
        issues = []
        final_text = answer.answer_text

        # 规则1: 隐私检查 (不能泄露其他客户信息)
        if "客户ID" in final_text and ticket.customer_id not in final_text:
            issues.append("答案中可能提及了其他客户ID，已自动过滤")
            final_text = final_text.replace("客户ID ABC123", "[其他客户]")

        # 规则2: 对VIP客户语气调整
        if ticket.customer_tier == "VIP" and "建议" in final_text:
            final_text = final_text.replace("建议", "我们将为您优先安排")
            issues.append("已根据VIP等级优化服务语气")

        # 规则3: 必须包含免责声明（如果涉及操作）
        if "步骤" in final_text or "操作" in final_text:
            disclaimer = "\n\n【免责声明】操作前请确保已备份数据，如有疑问请联系技术支持。"
            if disclaimer not in final_text:
                final_text += disclaimer
                issues.append("已补充标准操作免责声明")

        # 规则4: 低置信度答案必须转人工
        requires_human = answer.confidence < 0.7
        if requires_human:
            final_text = f"【系统提示】该问题较复杂，已为您转接高级客服。\n\n当前参考信息：\n{final_text}"
            issues.append("置信度低，已自动添加转接提示")

        print(f"  [Agent-CC] 检查完成，发现 {len(issues)} 项调整")
        return final_text, issues

# ==========================================
# 4. 工作流协调器 (Orchestrator)
# ==========================================

class CustomerSupportOrchestrator:
    """主协调器：串联所有Agent，管理状态与数据流"""
    def __init__(self):
        self.data_store = MockDataStore()
        self.ka_agent = AgentKnowledgeAggregator(self.data_store)
        self.ic_agent = AgentIntentClassifier()
        self.as_agent = AgentAnswerSynthesizer(self.data_store)
        self.cc_agent = AgentComplianceChecker()
        self.metrics = {
            "tickets_processed": 0,
            "total_token_usage": 0,
            "avg_processing_time": 0,
            "agent_involvement_counter": {  # 统计每个Agent被调用的次数
                "KA": 0, "IC": 0, "AS": 0, "CC": 0
            }
        }

    def process_ticket(self, ticket: CustomerTicket) -> FinalResponse:
        print(f"\n{'='*40}")
        print(f"开始处理工单 {ticket.ticket_id} (客户等级: {ticket.customer_tier})")
        print(f"原始问题: {ticket.raw_query}")
        print(f"{'='*40}")

        start_total = time.time()
        agents_used = []

        # 1. (可选) 触发知识聚合 - 实际可能是独立后台任务
        self.ka_agent.monitor_and_update()
        agents_used.append("KA")
        self.metrics["agent_involvement_counter"]["KA"] += 1

        # 2. 意图理解
        intent = self.ic_agent.analyze(ticket)
        agents_used.append("IC")
        self.metrics["agent_involvement_counter"]["IC"] += 1

        # 3. 答案合成 (核心)
        synthesized = self.as_agent.synthesize(ticket, intent)
        agents_used.append("AS")
        self.metrics["agent_involvement_counter"]["AS"] += 1

        # 4. 合规检查
        final_answer, compliance_notes = self.cc_agent.check(synthesized, ticket)
        agents_used.append("CC")
        self.metrics["agent_involvement_counter"]["CC"] += 1

        total_time = time.time() - start_total

        # 更新全局指标
        self.metrics["tickets_processed"] += 1
        self.metrics["total_token_usage"] += synthesized.estimated_token_usage
        self.metrics["avg_processing_time"] = (
            (self.metrics["avg_processing_time"] * (self.metrics["tickets_processed"] - 1) + total_time)
            / self.metrics["tickets_processed"]
        )

        # 构建最终响应
        response = FinalResponse(
            ticket_id=ticket.ticket_id,
            final_answer=final_answer,
            compliance_notes=compliance_notes,
            processing_time_sec=total_time,
            agents_involved=agents_used,
            token_usage_estimate=synthesized.estimated_token_usage
        )

        print(f"\n【最终响应】\n{final_answer}")
        print(f"\n处理耗时: {total_time:.2f}s | 预估Token: {synthesized.estimated_token_usage}")
        print(f"涉及Agent: {', '.join(agents_used)}")
        print(f"合规调整: {compliance_notes if compliance_notes else '无'}")

        return response

    def get_performance_report(self) -> Dict[str, Any]:
        """输出系统性能指标，用于评估"""
        return {
            "total_tickets": self.metrics["tickets_processed"],
            "total_tokens_used": self.metrics["total_token_usage"],
            "avg_time_per_ticket_sec": round(self.metrics["avg_processing_time"], 2),
            "agent_utilization": self.metrics["agent_involvement_counter"],
            "avg_tokens_per_ticket": int(self.metrics["total_token_usage"] / max(self.metrics["tickets_processed"], 1))
        }

# ==========================================
# 5. 演示运行
# ==========================================

if __name__ == "__main__":
    # 初始化协调器
    orchestrator = CustomerSupportOrchestrator()

    # 模拟两个典型客户工单
    test_tickets = [
        CustomerTicket(
            ticket_id="T20240521-001",
            customer_id="VIP_889",
            customer_tier="VIP",
            raw_query="紧急！我的API一直报E102错误，已经影响了生产环境！怎么解决？",
            timestamp=time.time()
        ),
        CustomerTicket(
            ticket_id="T20240521-002",
            customer_tier="Standard",
            raw_query="请问新版仪表盘怎么保存自定义布局？旧版可以，升级后不行了。",
            timestamp=time.time()
        )
    ]

    # 处理工单
    for ticket in test_tickets:
        response = orchestrator.process_ticket(ticket)
        time.sleep(1)  # 模拟间隔

    # 输出性能报告 (用于评估材料)
    report = orchestrator.get_performance_report()
    print("\n" + "="*50)
    print("【系统性能报告】")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("="*50)

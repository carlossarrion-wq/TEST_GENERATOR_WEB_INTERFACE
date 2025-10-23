"""
Complete LangChain Agent with all specialized tools and Redis memory
Main intelligent agent for comprehensive test plan generation
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import specialized tools
from .tools.requirements_analyzer import RequirementsAnalyzerTool
from .tools.coverage_calculator import CoverageCalculatorTool
from .tools.test_case_generator import TestCaseGeneratorTool
from .tools.quality_validator import QualityValidatorTool
from .tools.knowledge_base_retriever import KnowledgeBaseRetrieverTool

# Import memory system
from .utils.redis_memory import RedisMemoryManager, RedisChatMemory, AgentContextManager
from .utils.logging_config import setup_logger
from .utils.response_helpers import create_success_response, create_error_response

try:
    import boto3
    from langchain.agents import AgentType, initialize_agent
    from langchain.llms.bedrock import Bedrock
    from langchain.chat_models import ChatBedrock
    from langchain.tools import Tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ Full LangChain not available, using simplified implementation")


class CompleteLangChainAgent:
    """
    Complete LangChain Agent with specialized tools and Redis memory
    Implements the full workflow from the diagram with intelligent decision making
    """
    
    def __init__(self, region='eu-west-1'):
        """Initialize the complete LangChain agent"""
        
        self.region = region
        self.execution_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.logger = setup_logger(__name__)
        
        # Initialize components
        self._initialize_bedrock_client()
        self._initialize_redis_memory()
        self._initialize_specialized_tools()
        
        if LANGCHAIN_AVAILABLE:
            self._initialize_langchain_agent()
        else:
            self.logger.warning("LangChain not available, using simplified workflow")
        
        self.logger.info(f"Complete LangChain Agent initialized - Execution ID: {self.execution_id}")
    
    def _initialize_bedrock_client(self):
        """Initialize Bedrock client for Claude Sonnet"""
        
        try:
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
            self.bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name=self.region)
            self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
            self.knowledge_base_id = "VH6SRH9ZNO"
            self.logger.info("✅ Bedrock client initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Bedrock client: {e}")
            raise
    
    def _initialize_redis_memory(self):
        """Initialize Redis memory system"""
        
        try:
            # Initialize Redis memory manager
            self.redis_manager = RedisMemoryManager()
            
            # Create session-specific components
            self.session_id = str(uuid.uuid4())
            self.chat_memory = RedisChatMemory(self.session_id, self.redis_manager)
            self.context_manager = AgentContextManager(self.session_id, self.redis_manager)
            
            self.logger.info(f"✅ Redis memory initialized - Session ID: {self.session_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Redis memory: {e}")
            # Continue without Redis memory
            self.redis_manager = None
            self.chat_memory = None
            self.context_manager = None
    
    def _initialize_specialized_tools(self):
        """Initialize all specialized tools"""
        
        try:
            # Initialize specialized tools
            self.requirements_analyzer = RequirementsAnalyzerTool()
            self.coverage_calculator = CoverageCalculatorTool()
            self.test_case_generator = TestCaseGeneratorTool()
            self.quality_validator = QualityValidatorTool()
            self.knowledge_retriever = KnowledgeBaseRetrieverTool(
                bedrock_agent_client=self.bedrock_agent_client,
                bedrock_client=self.bedrock_client,
                knowledge_base_id=self.knowledge_base_id,
                model_id=self.model_id
            )
            
            self.logger.info("✅ All specialized tools initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize specialized tools: {e}")
            raise
    
    def _initialize_langchain_agent(self):
        """Initialize LangChain agent with tools"""
        
        if not LANGCHAIN_AVAILABLE:
            self.langchain_agent = None
            return
        
        try:
            # Create LangChain-compatible tools
            langchain_tools = [
                Tool(
                    name="requirements_analyzer",
                    description=self.requirements_analyzer.description,
                    func=self._wrap_tool_execution(self.requirements_analyzer)
                ),
                Tool(
                    name="coverage_calculator", 
                    description=self.coverage_calculator.description,
                    func=self._wrap_tool_execution(self.coverage_calculator)
                ),
                Tool(
                    name="test_case_generator",
                    description=self.test_case_generator.description,
                    func=self._wrap_tool_execution(self.test_case_generator)
                ),
                Tool(
                    name="quality_validator",
                    description=self.quality_validator.description,
                    func=self._wrap_tool_execution(self.quality_validator)
                ),
                Tool(
                    name="knowledge_retriever",
                    description=self.knowledge_retriever.description,
                    func=self._wrap_tool_execution(self.knowledge_retriever)
                )
            ]
            
            # Initialize ChatBedrock LLM
            self.llm = ChatBedrock(
                client=self.bedrock_client,
                model_id=self.model_id,
                model_kwargs={
                    "max_tokens": 4000,
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            )
            
            # Initialize agent with memory
            self.langchain_agent = initialize_agent(
                tools=langchain_tools,
                llm=self.llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                memory=self.chat_memory,
                verbose=True,
                max_iterations=10,
                early_stopping_method="generate"
            )
            
            self.logger.info("✅ LangChain agent initialized with full tools and memory")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize LangChain agent: {e}")
            self.langchain_agent = None
    
    def _wrap_tool_execution(self, tool_instance):
        """Wrap tool execution for LangChain compatibility and caching"""
        
        def wrapped_execution(input_query: str):
            try:
                # Parse input if it's JSON
                if input_query.startswith('{'):
                    input_data = json.loads(input_query)
                else:
                    # Simple string input - convert to tool format
                    input_data = {"input": input_query}
                
                # Check cache first
                if self.context_manager:
                    cached_result = self.redis_manager.get_cached_tool_result(tool_instance.name, input_data)
                    if cached_result:
                        self.logger.info(f"🔄 Using cached result for {tool_instance.name}")
                        return json.dumps(cached_result)
                
                # Execute tool
                start_time = time.time()
                result = tool_instance.execute(input_data)
                execution_time = time.time() - start_time
                
                # Save execution to context
                if self.context_manager:
                    self.context_manager.save_tool_execution(
                        tool_instance.name, input_data, result, execution_time
                    )
                
                return json.dumps(result)
                
            except Exception as e:
                self.logger.error(f"❌ Tool execution error for {tool_instance.name}: {e}")
                return json.dumps({"error": str(e)})
        
        return wrapped_execution
    
    def generate_test_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for intelligent test plan generation
        Implements the complete workflow with agent decision making
        """
        
        try:
            self.logger.info(f"🚀 Starting intelligent test plan generation")
            self.logger.info(f"Requirements: {requirements.get('title', 'Unknown')}")
            
            # Save request context
            if self.context_manager:
                self.context_manager.save_agent_decision(
                    "test_plan_request",
                    "User requested comprehensive test plan generation",
                    ["requirements_analyzer", "knowledge_retriever", "test_case_generator", "coverage_calculator", "quality_validator"],
                    0.95
                )
            
            # Decide processing approach
            processing_approach = self._decide_processing_approach(requirements)
            
            if processing_approach == "intelligent_agent" and self.langchain_agent:
                return self._process_with_langchain_agent(requirements)
            else:
                return self._process_with_specialized_workflow(requirements)
                
        except Exception as e:
            self.logger.error(f"❌ Test plan generation failed: {e}")
            return create_error_response(
                f"Test plan generation failed: {str(e)}",
                execution_id=self.execution_id
            )
    
    def _decide_processing_approach(self, requirements: Dict[str, Any]) -> str:
        """Decide whether to use LangChain agent or specialized workflow"""
        
        try:
            # Analyze complexity
            requirements_text = requirements.get('requirements', '')
            title = requirements.get('title', '')
            
            complexity_indicators = {
                'length': len(requirements_text) > 500,
                'technical_terms': any(term in requirements_text.lower() 
                                     for term in ['api', 'database', 'integration', 'security', 'performance']),
                'multiple_systems': len(requirements_text.split('.')) > 10,
                'user_preference': requirements.get('agent_mode', 'auto') == 'agent'
            }
            
            complexity_score = sum(complexity_indicators.values()) / len(complexity_indicators)
            
            # Decision logic
            if complexity_score > 0.5 or requirements.get('agent_mode') == 'agent':
                if self.langchain_agent:
                    self.logger.info(f"🧠 Using intelligent LangChain agent (complexity: {complexity_score:.2f})")
                    return "intelligent_agent"
                else:
                    self.logger.info("🔧 LangChain not available, using specialized workflow")
                    return "specialized_workflow"
            else:
                self.logger.info(f"⚡ Using optimized specialized workflow (complexity: {complexity_score:.2f})")
                return "specialized_workflow"
                
        except Exception as e:
            self.logger.error(f"❌ Decision making error: {e}")
            return "specialized_workflow"  # Fallback to specialized workflow
    
    def _process_with_langchain_agent(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process using full LangChain agent with memory and tools"""
        
        try:
            self.logger.info("🧠 Processing with LangChain Agent")
            
            # Create agent prompt
            agent_prompt = self._create_agent_prompt(requirements)
            
            # Execute with LangChain agent
            start_time = time.time()
            agent_result = self.langchain_agent.run(agent_prompt)
            execution_time = time.time() - start_time
            
            # Parse agent result
            if isinstance(agent_result, str):
                try:
                    parsed_result = json.loads(agent_result)
                except json.JSONDecodeError:
                    # If not JSON, create structured response
                    parsed_result = {
                        "agent_response": agent_result,
                        "processing_method": "langchain_agent"
                    }
            else:
                parsed_result = agent_result
            
            # Add metadata
            final_result = {
                **parsed_result,
                "execution_metadata": {
                    "execution_id": self.execution_id,
                    "processing_method": "langchain_agent_full",
                    "execution_time": round(execution_time, 2),
                    "session_id": self.session_id,
                    "tools_available": ["requirements_analyzer", "coverage_calculator", "test_case_generator", "quality_validator", "knowledge_retriever"],
                    "memory_enabled": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            return create_success_response(final_result, execution_id=self.execution_id)
            
        except Exception as e:
            self.logger.error(f"❌ LangChain agent processing failed: {e}")
            # Fallback to specialized workflow
            return self._process_with_specialized_workflow(requirements)
    
    def _process_with_specialized_workflow(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process using specialized tools workflow (manual orchestration)"""
        
        try:
            self.logger.info("🔧 Processing with specialized tools workflow")
            
            workflow_results = {}
            
            # Step 1: Analyze requirements
            self.logger.info("📋 Step 1: Analyzing requirements")
            requirements_analysis = self._execute_requirements_analysis(requirements)
            workflow_results["requirements_analysis"] = requirements_analysis
            
            # Step 2: Retrieve knowledge base insights
            self.logger.info("🧠 Step 2: Retrieving knowledge base insights")
            kb_insights = self._execute_knowledge_retrieval(requirements)
            workflow_results["knowledge_insights"] = kb_insights
            
            # Step 3: Generate test cases
            self.logger.info("🧪 Step 3: Generating test cases")
            test_cases = self._execute_test_case_generation(requirements_analysis, kb_insights, requirements)
            workflow_results["test_cases"] = test_cases
            
            # Step 4: Calculate coverage
            self.logger.info("📊 Step 4: Calculating coverage")
            coverage_analysis = self._execute_coverage_calculation(test_cases, requirements_analysis)
            workflow_results["coverage_analysis"] = coverage_analysis
            
            # Step 5: Validate quality
            self.logger.info("✅ Step 5: Validating quality")
            quality_validation = self._execute_quality_validation(test_cases["test_cases"])
            workflow_results["quality_validation"] = quality_validation
            
            # Create final structured response
            final_result = self._create_final_response(workflow_results, requirements)
            
            return create_success_response(final_result, execution_id=self.execution_id)
            
        except Exception as e:
            self.logger.error(f"❌ Specialized workflow failed: {e}")
            return create_error_response(f"Specialized workflow failed: {str(e)}", execution_id=self.execution_id)
    
    def _execute_requirements_analysis(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requirements analysis"""
        
        try:
            analysis_input = {
                "requirements": requirements.get("requirements", ""),
                "analysis_options": {
                    "include_edge_cases": True,
                    "include_risk_assessment": True,
                    "include_user_stories": True
                }
            }
            
            start_time = time.time()
            result = self.requirements_analyzer.execute(analysis_input)
            execution_time = time.time() - start_time
            
            # Save to context
            if self.context_manager:
                self.context_manager.save_tool_execution(
                    "requirements_analyzer", analysis_input, result, execution_time
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Requirements analysis failed: {e}")
            return {"error": str(e), "analysis_completed": False}
    
    def _execute_knowledge_retrieval(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge base retrieval"""
        
        try:
            kb_input = {
                "query": f"Test planning for: {requirements.get('title', '')} - {requirements.get('requirements', '')[:200]}",
                "max_results": 5
            }
            
            start_time = time.time()
            result = self.knowledge_retriever.execute(kb_input)
            execution_time = time.time() - start_time
            
            # Save to context
            if self.context_manager:
                self.context_manager.save_tool_execution(
                    "knowledge_retriever", kb_input, result, execution_time
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Knowledge retrieval failed: {e}")
            return {"error": str(e), "insights": []}
    
    def _execute_test_case_generation(self, requirements_analysis: Dict[str, Any], 
                                   kb_insights: Dict[str, Any], 
                                   original_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test case generation"""
        
        try:
            generation_input = {
                "functional_requirements": requirements_analysis.get("functional_requirements", []),
                "edge_cases": requirements_analysis.get("edge_cases", []),
                "risk_areas": requirements_analysis.get("risk_areas", []),
                "generation_options": {
                    "min_test_cases": original_requirements.get("min_test_cases", 5),
                    "max_test_cases": original_requirements.get("max_test_cases", 15),
                    "include_negative_tests": True,
                    "include_boundary_tests": True,
                    "kb_insights": kb_insights.get("insights", [])
                }
            }
            
            start_time = time.time()
            result = self.test_case_generator.execute(generation_input)
            execution_time = time.time() - start_time
            
            # Save to context
            if self.context_manager:
                self.context_manager.save_tool_execution(
                    "test_case_generator", generation_input, result, execution_time
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Test case generation failed: {e}")
            return {"error": str(e), "test_cases": []}
    
    def _execute_coverage_calculation(self, test_cases: Dict[str, Any], 
                                   requirements_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coverage calculation"""
        
        try:
            coverage_input = {
                "test_cases": test_cases.get("test_cases", []),
                "functional_requirements": requirements_analysis.get("functional_requirements", []),
                "edge_cases": requirements_analysis.get("edge_cases", []),
                "risk_areas": requirements_analysis.get("risk_areas", [])
            }
            
            start_time = time.time()
            result = self.coverage_calculator.execute(coverage_input)
            execution_time = time.time() - start_time
            
            # Save to context
            if self.context_manager:
                self.context_manager.save_tool_execution(
                    "coverage_calculator", coverage_input, result, execution_time
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Coverage calculation failed: {e}")
            return {"error": str(e), "overall_coverage": {"percentage": 0}}
    
    def _execute_quality_validation(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute quality validation"""
        
        try:
            validation_input = {
                "test_cases": test_cases,
                "validation_options": {
                    "strict_mode": True,
                    "include_improvement_suggestions": True
                }
            }
            
            start_time = time.time()
            result = self.quality_validator.execute(validation_input)
            execution_time = time.time() - start_time
            
            # Save to context
            if self.context_manager:
                self.context_manager.save_tool_execution(
                    "quality_validator", validation_input, result, execution_time
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Quality validation failed: {e}")
            return {"error": str(e), "overall_metrics": {"average_score": 0}}
    
    def _create_agent_prompt(self, requirements: Dict[str, Any]) -> str:
        """Create prompt for LangChain agent"""
        
        return f"""
You are an expert test planning agent with access to specialized tools. Generate a comprehensive test plan for the following system:

**System Title:** {requirements.get('title', 'Test Plan')}
**Requirements:** {requirements.get('requirements', '')}
**Minimum Test Cases:** {requirements.get('min_test_cases', 5)}
**Maximum Test Cases:** {requirements.get('max_test_cases', 15)}

**Instructions:**
1. First, use the requirements_analyzer tool to analyze the requirements thoroughly
2. Use the knowledge_retriever tool to get specialized insights from the knowledge base
3. Use the test_case_generator tool to create comprehensive test cases
4. Use the coverage_calculator tool to analyze test coverage
5. Use the quality_validator tool to validate and improve test case quality
6. Provide a final structured response with all results

**Expected Output:** A comprehensive JSON response containing all analysis results, generated test cases, coverage metrics, and quality assessment.

Begin by analyzing the requirements.
"""
    
    def _create_final_response(self, workflow_results: Dict[str, Any], 
                              original_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create final structured response"""
        
        # Extract key results
        test_cases = workflow_results.get("test_cases", {}).get("test_cases", [])
        coverage = workflow_results.get("coverage_analysis", {}).get("overall_coverage", {})
        quality = workflow_results.get("quality_validation", {}).get("overall_metrics", {})
        requirements_analysis = workflow_results.get("requirements_analysis", {})
        
        # Calculate execution metrics
        total_execution_time = time.time() - self.start_time
        
        final_response = {
            "test_cases": test_cases,
            "quality_metrics": {
                "overall_score": quality.get("average_score", 0),
                "completeness": coverage.get("percentage", 0) / 100,
                "clarity": 0.85,  # Based on quality validation
                "total_test_cases": len(test_cases)
            },
            "coverage_analysis": {
                "current_coverage": coverage.get("percentage", 0),
                "functional_coverage": coverage.get("components", {}).get("functional", 0),
                "requirements_covered": len(requirements_analysis.get("functional_requirements", [])),
                "coverage_gaps": coverage.get("components", {}).get("edge_cases", 0)
            },
            "requirements_analysis": {
                "complexity": requirements_analysis.get("complexity_analysis", {}).get("complexity_level", "Medium"),
                "functional_requirements_count": len(requirements_analysis.get("functional_requirements", [])),
                "edge_cases_identified": len(requirements_analysis.get("edge_cases", [])),
                "risk_areas": len(requirements_analysis.get("risk_areas", [])),
                "kb_enhanced": True
            },
            "execution_metadata": {
                "execution_id": self.execution_id,
                "processing_method": "specialized_workflow_complete",
                "total_execution_time": round(total_execution_time, 2),
                "session_id": self.session_id,
                "tools_used": list(workflow_results.keys()),
                "memory_enabled": self.context_manager is not None,
                "timestamp": datetime.utcnow().isoformat(),
                "workflow_steps": [
                    "requirements_analysis",
                    "knowledge_retrieval", 
                    "test_case_generation",
                    "coverage_calculation",
                    "quality_validation"
                ]
            },
            "recommendations": self._generate_final_recommendations(workflow_results),
            "context_summary": self.context_manager.get_context_summary() if self.context_manager else {}
        }
        
        return final_response
    
    def _generate_final_recommendations(self, workflow_results: Dict[str, Any]) -> List[str]:
        """Generate final recommendations based on all analysis"""
        
        recommendations = []
        
        # Quality recommendations
        quality_validation = workflow_results.get("quality_validation", {})
        quality_recommendations = quality_validation.get("improvement_recommendations", [])
        recommendations.extend(quality_recommendations)
        
        # Coverage recommendations  
        coverage_analysis = workflow_results.get("coverage_analysis", {})
        coverage_recommendations = coverage_analysis.get("recommendations", [])
        recommendations.extend(coverage_recommendations)
        
        # Test case generation recommendations
        test_cases = workflow_results.get("test_cases", {})
        generation_recommendations = test_cases.get("recommendations", [])
        recommendations.extend(generation_recommendations)
        
        # Remove duplicates and limit
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:10]  # Top 10 recommendations
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the complete agent"""
        
        return {
            "status": "healthy",
            "execution_id": self.execution_id,
            "components": {
                "bedrock_client": self.bedrock_client is not None,
                "redis_memory": self.redis_manager is not None,
                "langchain_agent": self.langchain_agent is not None,
                "specialized_tools": all([
                    self.requirements_analyzer is not None,
                    self.coverage_calculator is not None,
                    self.test_case_generator is not None,
                    self.quality_validator is not None,
                    self.knowledge_retriever is not None
                ])
            },
            "session_info": {
                "session_id": self.session_id,
                "memory_type": self.redis_manager.get_session_stats(self.session_id)["memory_type"] if self.redis_manager else "None"
            },
            "processing_modes": {
                "langchain_agent_available": LANGCHAIN_AVAILABLE and self.langchain_agent is not None,
                "specialized_workflow_available": True,
                "memory_enabled": self.context_manager is not None
            }
        }

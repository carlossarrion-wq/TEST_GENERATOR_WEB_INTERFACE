"""
Redis Memory System for LangChain Agent
Provides persistent memory and caching capabilities using Redis
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis not available, using in-memory fallback")

try:
    from langchain.memory import BaseChatMemory
    from langchain.memory.chat_message_histories import BaseChatMessageHistory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    LANGCHAIN_MEMORY_AVAILABLE = True
except ImportError:
    LANGCHAIN_MEMORY_AVAILABLE = False
    print("⚠️ LangChain memory classes not available")


class RedisMemoryManager:
    """
    Redis-based memory manager for LangChain Agent
    Handles session persistence, tool result caching, and context management
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0, redis_password=None):
        """Initialize Redis memory manager"""
        
        self.redis_client = None
        self.fallback_memory = {}  # In-memory fallback
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                print("✅ Redis connected successfully")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}, using fallback memory")
                self.redis_client = None
        
        self.session_ttl = 3600  # 1 hour default TTL
        self.cache_ttl = 1800    # 30 minutes for tool results
    
    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session data"""
        return f"agent_session:{session_id}"
    
    def _get_cache_key(self, cache_type: str, key: str) -> str:
        """Get Redis key for cached data"""
        return f"agent_cache:{cache_type}:{key}"
    
    def _get_tool_result_key(self, tool_name: str, input_hash: str) -> str:
        """Get Redis key for tool result caching"""
        return f"tool_result:{tool_name}:{input_hash}"
    
    def save_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Save session data to Redis or fallback memory"""
        
        try:
            session_key = self._get_session_key(session_id)
            
            # Add metadata
            data['last_updated'] = datetime.utcnow().isoformat()
            data['session_id'] = session_id
            
            if self.redis_client:
                # Save to Redis
                serialized_data = json.dumps(data, default=str)
                self.redis_client.setex(session_key, self.session_ttl, serialized_data)
                return True
            else:
                # Save to fallback memory
                self.fallback_memory[session_key] = data
                return True
                
        except Exception as e:
            print(f"❌ Error saving session data: {e}")
            return False
    
    def load_session_data(self, session_id: str) -> Dict[str, Any]:
        """Load session data from Redis or fallback memory"""
        
        try:
            session_key = self._get_session_key(session_id)
            
            if self.redis_client:
                # Load from Redis
                data = self.redis_client.get(session_key)
                if data:
                    return json.loads(data)
            else:
                # Load from fallback memory
                return self.fallback_memory.get(session_key, {})
                
        except Exception as e:
            print(f"❌ Error loading session data: {e}")
        
        return {}
    
    def cache_tool_result(self, tool_name: str, input_data: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Cache tool execution result"""
        
        try:
            # Create hash of input data for cache key
            input_hash = str(hash(json.dumps(input_data, sort_keys=True)))
            cache_key = self._get_tool_result_key(tool_name, input_hash)
            
            cache_data = {
                'tool_name': tool_name,
                'input_data': input_data,
                'result': result,
                'cached_at': datetime.utcnow().isoformat(),
                'cache_ttl': self.cache_ttl
            }
            
            if self.redis_client:
                serialized_data = json.dumps(cache_data, default=str)
                self.redis_client.setex(cache_key, self.cache_ttl, serialized_data)
            else:
                self.fallback_memory[cache_key] = cache_data
            
            return True
            
        except Exception as e:
            print(f"❌ Error caching tool result: {e}")
            return False
    
    def get_cached_tool_result(self, tool_name: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached tool result if available"""
        
        try:
            input_hash = str(hash(json.dumps(input_data, sort_keys=True)))
            cache_key = self._get_tool_result_key(tool_name, input_hash)
            
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)['result']
            else:
                cached_data = self.fallback_memory.get(cache_key)
                if cached_data:
                    # Check if cache is still valid
                    cached_at = datetime.fromisoformat(cached_data['cached_at'])
                    if datetime.utcnow() - cached_at < timedelta(seconds=self.cache_ttl):
                        return cached_data['result']
            
        except Exception as e:
            print(f"❌ Error retrieving cached tool result: {e}")
        
        return None
    
    def store_conversation_history(self, session_id: str, messages: List[Dict[str, Any]]) -> bool:
        """Store conversation history"""
        
        try:
            history_key = f"conversation_history:{session_id}"
            
            history_data = {
                'messages': messages,
                'updated_at': datetime.utcnow().isoformat(),
                'message_count': len(messages)
            }
            
            if self.redis_client:
                serialized_data = json.dumps(history_data, default=str)
                self.redis_client.setex(history_key, self.session_ttl, serialized_data)
            else:
                self.fallback_memory[history_key] = history_data
            
            return True
            
        except Exception as e:
            print(f"❌ Error storing conversation history: {e}")
            return False
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        
        try:
            history_key = f"conversation_history:{session_id}"
            
            if self.redis_client:
                data = self.redis_client.get(history_key)
                if data:
                    return json.loads(data).get('messages', [])
            else:
                data = self.fallback_memory.get(history_key)
                if data:
                    return data.get('messages', [])
                    
        except Exception as e:
            print(f"❌ Error retrieving conversation history: {e}")
        
        return []
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all session data"""
        
        try:
            patterns = [
                self._get_session_key(session_id),
                f"conversation_history:{session_id}",
                f"agent_cache:*:{session_id}*"
            ]
            
            if self.redis_client:
                for pattern in patterns:
                    if '*' in pattern:
                        keys = self.redis_client.keys(pattern)
                        if keys:
                            self.redis_client.delete(*keys)
                    else:
                        self.redis_client.delete(pattern)
            else:
                keys_to_delete = []
                for key in self.fallback_memory.keys():
                    if any(pattern.replace('*', '') in key for pattern in patterns):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self.fallback_memory[key]
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing session: {e}")
            return False
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        
        try:
            session_data = self.load_session_data(session_id)
            history = self.get_conversation_history(session_id)
            
            return {
                'session_exists': bool(session_data),
                'last_updated': session_data.get('last_updated'),
                'message_count': len(history),
                'session_duration': self._calculate_session_duration(session_data),
                'memory_type': 'Redis' if self.redis_client else 'In-Memory'
            }
            
        except Exception as e:
            print(f"❌ Error getting session stats: {e}")
            return {'error': str(e)}
    
    def _calculate_session_duration(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Calculate session duration"""
        
        try:
            if 'created_at' in session_data and 'last_updated' in session_data:
                created = datetime.fromisoformat(session_data['created_at'])
                updated = datetime.fromisoformat(session_data['last_updated'])
                duration = updated - created
                return str(duration)
        except:
            pass
        
        return None


class RedisChatMemory:
    """
    LangChain compatible Redis-based chat memory
    """
    
    def __init__(self, session_id: str, redis_manager: RedisMemoryManager, memory_key: str = "chat_history"):
        """Initialize Redis chat memory"""
        
        self.session_id = session_id
        self.redis_manager = redis_manager
        self.memory_key = memory_key
        self.return_messages = True
        
        # Initialize session if not exists
        session_data = self.redis_manager.load_session_data(session_id)
        if not session_data:
            initial_data = {
                'created_at': datetime.utcnow().isoformat(),
                'session_id': session_id,
                'memory_key': memory_key
            }
            self.redis_manager.save_session_data(session_id, initial_data)
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save context to Redis memory"""
        
        try:
            # Create message objects
            messages = []
            
            if 'input' in inputs:
                messages.append({
                    'type': 'human',
                    'content': str(inputs['input']),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            if 'output' in outputs:
                messages.append({
                    'type': 'ai',
                    'content': str(outputs['output']),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Get existing history and append new messages
            existing_history = self.redis_manager.get_conversation_history(self.session_id)
            existing_history.extend(messages)
            
            # Keep only last 20 messages to prevent memory overflow
            if len(existing_history) > 20:
                existing_history = existing_history[-20:]
            
            # Save updated history
            self.redis_manager.store_conversation_history(self.session_id, existing_history)
            
        except Exception as e:
            print(f"❌ Error saving context: {e}")
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables from Redis"""
        
        try:
            history = self.redis_manager.get_conversation_history(self.session_id)
            
            if self.return_messages:
                # Convert to message format
                messages = []
                for msg in history:
                    if msg['type'] == 'human':
                        messages.append(f"Human: {msg['content']}")
                    elif msg['type'] == 'ai':
                        messages.append(f"AI: {msg['content']}")
                
                return {self.memory_key: "\n".join(messages)}
            else:
                return {self.memory_key: history}
                
        except Exception as e:
            print(f"❌ Error loading memory variables: {e}")
            return {self.memory_key: ""}
    
    def clear(self) -> None:
        """Clear memory"""
        self.redis_manager.clear_session(self.session_id)


class AgentContextManager:
    """
    Manages agent context including tool results, decision history, and planning
    """
    
    def __init__(self, session_id: str, redis_manager: RedisMemoryManager):
        """Initialize context manager"""
        
        self.session_id = session_id
        self.redis_manager = redis_manager
        self.execution_id = str(uuid.uuid4())
        
    def save_tool_execution(self, tool_name: str, input_data: Dict[str, Any], 
                           result: Dict[str, Any], execution_time: float) -> None:
        """Save tool execution details"""
        
        execution_data = {
            'tool_name': tool_name,
            'input_data': input_data,
            'result': result,
            'execution_time': execution_time,
            'timestamp': datetime.utcnow().isoformat(),
            'execution_id': self.execution_id
        }
        
        # Save to cache for reuse
        self.redis_manager.cache_tool_result(tool_name, input_data, result)
        
        # Save execution history
        history_key = f"tool_executions:{self.session_id}"
        
        try:
            if self.redis_manager.redis_client:
                # Add to list of executions
                self.redis_manager.redis_client.lpush(
                    history_key, 
                    json.dumps(execution_data, default=str)
                )
                # Keep only last 50 executions  
                self.redis_manager.redis_client.ltrim(history_key, 0, 49)
                self.redis_manager.redis_client.expire(history_key, self.redis_manager.session_ttl)
        except Exception as e:
            print(f"❌ Error saving tool execution: {e}")
    
    def get_tool_execution_history(self) -> List[Dict[str, Any]]:
        """Get tool execution history"""
        
        try:
            history_key = f"tool_executions:{self.session_id}"
            
            if self.redis_manager.redis_client:
                executions = self.redis_manager.redis_client.lrange(history_key, 0, -1)
                return [json.loads(exec_data) for exec_data in executions]
                
        except Exception as e:
            print(f"❌ Error getting tool execution history: {e}")
        
        return []
    
    def save_agent_decision(self, decision_type: str, reasoning: str, 
                          tools_selected: List[str], confidence: float) -> None:
        """Save agent decision for analysis"""
        
        decision_data = {
            'decision_type': decision_type,
            'reasoning': reasoning,
            'tools_selected': tools_selected,
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'execution_id': self.execution_id
        }
        
        decision_key = f"agent_decisions:{self.session_id}"
        
        try:
            if self.redis_manager.redis_client:
                self.redis_manager.redis_client.lpush(
                    decision_key, 
                    json.dumps(decision_data, default=str)
                )
                self.redis_manager.redis_client.ltrim(decision_key, 0, 19)  # Keep last 20
                self.redis_manager.redis_client.expire(decision_key, self.redis_manager.session_ttl)
        except Exception as e:
            print(f"❌ Error saving agent decision: {e}")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context"""
        
        return {
            'session_id': self.session_id,
            'execution_id': self.execution_id,
            'session_stats': self.redis_manager.get_session_stats(self.session_id),
            'recent_tools': self._get_recent_tool_usage(),
            'memory_status': 'Redis' if self.redis_manager.redis_client else 'In-Memory'
        }
    
    def _get_recent_tool_usage(self) -> List[str]:
        """Get recently used tools"""
        
        try:
            history = self.get_tool_execution_history()
            recent_tools = []
            
            for execution in history[:5]:  # Last 5 executions
                tool_name = execution.get('tool_name', 'Unknown')
                if tool_name not in recent_tools:
                    recent_tools.append(tool_name)
            
            return recent_tools
            
        except Exception as e:
            print(f"❌ Error getting recent tool usage: {e}")
            return []

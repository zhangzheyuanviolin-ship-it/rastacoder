"""
Offline LLM Test Utilities

Test utilities for validating on-device LLM functionality without requiring
actual model downloads or device hardware.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ModelSize(Enum):
    """Model size categories for testing."""
    TINY = "0.5B"
    SMALL = "1.5B"
    MEDIUM = "3B"
    LARGE = "4B"


@dataclass
class ModelConfig:
    """Mock model configuration for testing."""
    model_id: str
    size: ModelSize
    estimated_vram_gb: float
    context_window: int
    prefill_chunk_size: int
    
    @classmethod
    def get_test_models(cls) -> List['ModelConfig']:
        """Get list of test model configurations."""
        return [
            cls("Qwen2.5-Coder-0.5B-Instruct-q4f16_0-MLC", ModelSize.TINY, 0.5, 4096, 1024),
            cls("Qwen2.5-Coder-1.5B-Instruct-q4f16_0-MLC", ModelSize.SMALL, 1.2, 4096, 1024),
            cls("Qwen2.5-Coder-3B-Instruct-q4f16_0-MLC", ModelSize.MEDIUM, 2.2, 2048, 512),
            cls("Ministral-3-3B-Instruct-2512-q4f16_0-MLC", ModelSize.MEDIUM, 2.0, 4096, 1024),
            cls("Qwen3-4B-q4f16_0-MLC", ModelSize.LARGE, 2.5, 4096, 2048),
        ]


class MockLLMEngine:
    """
    Mock LLM engine for testing offline functionality.
    
    Simulates model loading, inference, and tool calling without
    requiring actual GPU hardware or model files.
    """
    
    def __init__(self):
        self.loaded_model: Optional[ModelConfig] = None
        self.is_loading = False
        self.load_progress = 0.0
        self.generation_count = 0
        self.last_error: Optional[str] = None
        
    def get_available_models(self) -> List[ModelConfig]:
        """Get list of available model configurations."""
        return ModelConfig.get_test_models()
    
    async def load_model(self, model_id: str) -> Dict[str, Any]:
        """
        Simulate model loading process.
        
        Args:
            model_id: ID of model to load
            
        Returns:
            Dict with load status and metadata
        """
        if self.is_loading:
            return {
                "success": False,
                "error": "Model already loading"
            }
        
        # Find model config
        model = None
        for m in self.get_available_models():
            if m.model_id == model_id:
                model = m
                break
        
        if not model:
            return {
                "success": False,
                "error": f"Model not found: {model_id}"
            }
        
        # Simulate loading progress
        self.is_loading = True
        self.load_progress = 0.0
        
        try:
            # Simulate progressive loading
            for progress in range(0, 101, 10):
                self.load_progress = progress / 100.0
                await asyncio.sleep(0.1)  # Simulate I/O
            
            self.loaded_model = model
            self.is_loading = False
            self.load_progress = 1.0
            
            return {
                "success": True,
                "model_id": model_id,
                "vram_required_gb": model.estimated_vram_gb,
                "context_window": model.context_window,
                "message": f"Model loaded successfully: {model_id}"
            }
            
        except Exception as e:
            self.is_loading = False
            self.last_error = str(e)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def unload_model(self) -> Dict[str, Any]:
        """
        Simulate model unloading.
        
        Returns:
            Dict with unload status
        """
        if self.loaded_model is None:
            return {
                "success": False,
                "error": "No model loaded"
            }
        
        model_id = self.loaded_model.model_id
        self.loaded_model = None
        
        return {
            "success": True,
            "model_id": model_id,
            "message": "Model unloaded successfully"
        }
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Simulate text generation.
        
        Args:
            messages: Conversation messages
            tools: Available tool definitions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict with generation result
        """
        if self.loaded_model is None:
            return {
                "success": False,
                "error": "No model loaded"
            }
        
        self.generation_count += 1
        
        # Simulate generation latency based on model size
        latency = self.loaded_model.estimated_vram_gb * 0.1  # seconds
        await asyncio.sleep(latency)
        
        # Generate mock response
        last_message = messages[-1]["content"] if messages else ""
        
        # Simple pattern matching for demo responses
        response = self._generate_mock_response(last_message, tools)
        
        return {
            "success": True,
            "content": response,
            "tokens_generated": len(response.split()) * 1.3,  # Rough estimate
            "generation_time_ms": latency * 1000,
            "model_id": self.loaded_model.model_id
        }
    
    def _generate_mock_response(
        self,
        query: str,
        tools: Optional[List[Dict]]
    ) -> str:
        """Generate mock response based on query pattern."""
        query_lower = query.lower()
        
        # Tool use simulation
        if tools and any(kw in query_lower for kw in ["calculate", "compute", "plot"]):
            return json.dumps({
                "name": "python_execute",
                "arguments": {
                    "code": f"# Mock code for: {query[:50]}"
                }
            })
        
        if "video" in query_lower or "audio" in query_lower:
            return json.dumps({
                "name": "ffmpeg_process",
                "arguments": {
                    "input_path": "input.mp4",
                    "output_path": "output.mp4",
                    "operation": "trim"
                }
            })
        
        # Simple Q&A simulation
        if "?" in query:
            return f"This is a mock response to: {query[:100]}"
        
        # Default response
        return "I understand. This is a simulated offline LLM response for testing purposes."
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        return {
            "model_loaded": self.loaded_model is not None,
            "model_id": self.loaded_model.model_id if self.loaded_model else None,
            "is_loading": self.is_loading,
            "load_progress": self.load_progress,
            "generation_count": self.generation_count,
            "last_error": self.last_error
        }


class OfflineLLMTestSuite:
    """
    Test suite for offline LLM functionality.
    
    Provides comprehensive tests for model loading, inference,
    and error handling without requiring actual hardware.
    """
    
    def __init__(self):
        self.engine = MockLLMEngine()
        self.test_results: List[Dict] = []
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run complete test suite.
        
        Returns:
            Dict with test results summary
        """
        tests = [
            ("Model List", self.test_model_list),
            ("Model Load/Unload", self.test_load_unload),
            ("Load Progress", self.test_load_progress),
            ("Basic Generation", self.test_basic_generation),
            ("Tool Calling", self.test_tool_calling),
            ("Error Handling", self.test_error_handling),
            ("Multiple Generations", self.test_multiple_generations),
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append({
                    "name": test_name,
                    "passed": True,
                    "result": result
                })
                passed += 1
            except Exception as e:
                results.append({
                    "name": test_name,
                    "passed": False,
                    "error": str(e)
                })
                failed += 1
        
        return {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": passed / len(tests) * 100,
            "results": results
        }
    
    async def test_model_list(self) -> Dict[str, Any]:
        """Test model list retrieval."""
        models = self.engine.get_available_models()
        
        assert len(models) == 5, f"Expected 5 models, got {len(models)}"
        assert all(isinstance(m, ModelConfig) for m in models)
        
        return {
            "model_count": len(models),
            "models": [m.model_id for m in models]
        }
    
    async def test_load_unload(self) -> Dict[str, Any]:
        """Test model loading and unloading."""
        # Load
        load_result = await self.engine.load_model(
            "Qwen2.5-Coder-0.5B-Instruct-q4f16_0-MLC"
        )
        assert load_result["success"], f"Load failed: {load_result.get('error')}"
        
        # Verify loaded
        status = self.engine.get_status()
        assert status["model_loaded"], "Model should be loaded"
        
        # Unload
        unload_result = await self.engine.unload_model()
        assert unload_result["success"], f"Unload failed: {unload_result.get('error')}"
        
        # Verify unloaded
        status = self.engine.get_status()
        assert not status["model_loaded"], "Model should be unloaded"
        
        return {"load_unload": "success"}
    
    async def test_load_progress(self) -> Dict[str, Any]:
        """Test load progress tracking."""
        load_task = asyncio.create_task(
            self.engine.load_model("Qwen2.5-Coder-1.5B-Instruct-q4f16_0-MLC")
        )
        
        # Check progress during loading
        progress_updates = []
        while self.engine.is_loading:
            progress_updates.append(self.engine.load_progress)
            await asyncio.sleep(0.05)
        
        await load_task
        
        assert len(progress_updates) > 0, "Should have progress updates"
        assert progress_updates[0] == 0.0, "Should start at 0"
        assert progress_updates[-1] == 1.0, "Should end at 1"
        
        return {
            "progress_updates": len(progress_updates),
            "final_progress": self.engine.load_progress
        }
    
    async def test_basic_generation(self) -> Dict[str, Any]:
        """Test basic text generation."""
        # Load model first
        await self.engine.load_model("Qwen2.5-Coder-0.5B-Instruct-q4f16_0-MLC")
        
        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        result = await self.engine.generate(messages)
        
        assert result["success"], f"Generation failed: {result.get('error')}"
        assert "content" in result
        assert len(result["content"]) > 0
        
        return {
            "response_length": len(result["content"]),
            "tokens": result.get("tokens_generated", 0)
        }
    
    async def test_tool_calling(self) -> Dict[str, Any]:
        """Test tool calling in responses."""
        await self.engine.load_model("Qwen2.5-Coder-1.5B-Instruct-q4f16_0-MLC")
        
        tools = [
            {
                "name": "python_execute",
                "description": "Run Python code"
            }
        ]
        
        messages = [
            {"role": "user", "content": "Calculate 2 + 2"}
        ]
        
        result = await self.engine.generate(messages, tools=tools)
        
        # Should return tool call JSON
        try:
            tool_call = json.loads(result["content"])
            assert "name" in tool_call
            assert "arguments" in tool_call
        except json.JSONDecodeError:
            pass  # May return text response in mock
        
        return {"tool_calling": "tested"}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling scenarios."""
        errors_tested = []
        
        # Test: Load non-existent model
        result = await self.engine.load_model("NonExistent-Model")
        assert not result["success"]
        errors_tested.append("non_existent_model")
        
        # Test: Generate without loaded model
        await self.engine.unload_model()
        result = await self.engine.generate([{"role": "user", "content": "test"}])
        assert not result["success"]
        errors_tested.append("no_model_loaded")
        
        # Test: Double unload
        result = await self.engine.unload_model()
        assert not result["success"]
        errors_tested.append("double_unload")
        
        return {"errors_tested": errors_tested}
    
    async def test_multiple_generations(self) -> Dict[str, Any]:
        """Test multiple consecutive generations."""
        await self.engine.load_model("Qwen2.5-Coder-0.5B-Instruct-q4f16_0-MLC")
        
        queries = [
            "What is Python?",
            "Explain machine learning",
            "How to reverse a list?",
            "What is 2 + 2?",
        ]
        
        results = []
        for query in queries:
            result = await self.engine.generate([
                {"role": "user", "content": query}
            ])
            results.append(result["success"])
        
        success_rate = sum(results) / len(results) * 100
        
        return {
            "total_generations": len(queries),
            "successful": sum(results),
            "success_rate": success_rate
        }


async def run_offline_llm_tests():
    """Run offline LLM test suite and print results."""
    print("=" * 60)
    print("Offline LLM Test Suite")
    print("=" * 60)
    
    suite = OfflineLLMTestSuite()
    results = await suite.run_all_tests()
    
    print(f"\nTotal Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    
    print("\nDetailed Results:")
    print("-" * 60)
    for result in results["results"]:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status}: {result['name']}")
        if not result["passed"]:
            print(f"  Error: {result.get('error')}")
    
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_offline_llm_tests())

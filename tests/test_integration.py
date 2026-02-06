import asyncio
import httpx
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

class IntegrationTests:
    def __init__(self, ai_service_url: str = "http://localhost:8000"):
        self.ai_service_url = ai_service_url
        self.client = httpx.AsyncClient()
        self.results = []
    
    async def test_ai_health(self):
        """Test AI service health check."""
        try:
            response = await self.client.get(f"{self.ai_service_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            self.results.append(("AI Health Check", "PASS"))
            return True
        except Exception as e:
            self.results.append(("AI Health Check", f"FAIL: {e}"))
            return False
    
    async def test_code_analysis(self):
        """Test code analysis endpoint."""
        try:
            code = "function test() { eval(userInput); }"
            payload = {
                "language": "javascript",
                "code": code,
                "filename": "test.js"
            }
            response = await self.client.post(
                f"{self.ai_service_url}/analyze",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "analysis" in data
            self.results.append(("Code Analysis", "PASS"))
            return True
        except Exception as e:
            self.results.append(("Code Analysis", f"FAIL: {e}"))
            return False
    
    async def test_graph_export(self):
        """Test knowledge graph export."""
        try:
            response = await self.client.get(f"{self.ai_service_url}/graph")
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data and "edges" in data
            self.results.append(("Graph Export", "PASS"))
            return True
        except Exception as e:
            self.results.append(("Graph Export", f"FAIL: {e}"))
            return False
    
    async def test_stats(self):
        """Test stats endpoint."""
        try:
            response = await self.client.get(f"{self.ai_service_url}/stats")
            assert response.status_code == 200
            data = response.json()
            assert "embedding_cache" in data
            assert "graph_nodes" in data
            self.results.append(("Stats Endpoint", "PASS"))
            return True
        except Exception as e:
            self.results.append(("Stats Endpoint", f"FAIL: {e}"))
            return False
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*60)
        print("INTEGRATION TEST SUITE")
        print("="*60)
        
        try:
            await self.test_ai_health()
            await self.test_code_analysis()
            await self.test_graph_export()
            await self.test_stats()
        except Exception as e:
            print(f"Test suite error: {e}")
        finally:
            await self.client.aclose()
        
        self._print_results()
    
    def _print_results(self):
        """Print test results."""
        passed = sum(1 for _, result in self.results if result == "PASS")
        total = len(self.results)
        
        for test_name, result in self.results:
            status_icon = "✓" if result == "PASS" else "✗"
            print(f"{status_icon} {test_name}: {result}")
        
        print(f"\nTotal: {passed}/{total} passed")
        print("="*60 + "\n")

if __name__ == "__main__":
    tests = IntegrationTests()
    asyncio.run(tests.run_all_tests())

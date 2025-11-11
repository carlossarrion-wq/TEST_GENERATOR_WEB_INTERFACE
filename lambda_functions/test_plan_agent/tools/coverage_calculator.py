"""
Coverage Calculator Tool
Calculates test coverage based on requirements and test cases
"""

import json
from typing import Dict, Any, List

class CoverageCalculatorTool:
    """Tool for calculating test coverage"""
    
    def __init__(self):
        self.name = "coverage_calculator"
        self.description = """Calculates test coverage metrics:
- Functional requirements coverage
- Edge cases coverage
- Risk areas coverage
- Overall coverage percentage
Use this to ensure adequate test coverage."""
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coverage calculation"""
        try:
            test_cases = input_data.get('test_cases', [])
            functional_reqs = input_data.get('functional_requirements', [])
            edge_cases = input_data.get('edge_cases', [])
            risk_areas = input_data.get('risk_areas', [])
            
            if not test_cases:
                return {
                    "error": "No test cases provided",
                    "overall_coverage": {"percentage": 0}
                }
            
            # Calculate coverage
            total_items = len(functional_reqs) + len(edge_cases) + len(risk_areas)
            if total_items == 0:
                return {
                    "overall_coverage": {"percentage": 100},
                    "components": {
                        "functional": 100,
                        "edge_cases": 100,
                        "risk_areas": 100
                    }
                }
            
            # Estimate coverage based on test case count and priorities
            high_priority_count = sum(1 for tc in test_cases if tc.get('priority') == 'High')
            medium_priority_count = sum(1 for tc in test_cases if tc.get('priority') == 'Medium')
            low_priority_count = sum(1 for tc in test_cases if tc.get('priority') == 'Low')
            
            # Calculate weighted coverage
            functional_coverage = min(100, (len(test_cases) / max(len(functional_reqs), 1)) * 100)
            edge_coverage = min(100, (high_priority_count / max(len(edge_cases), 1)) * 100) if edge_cases else 100
            risk_coverage = min(100, ((high_priority_count + medium_priority_count) / max(len(risk_areas), 1)) * 100) if risk_areas else 100
            
            overall_percentage = (functional_coverage + edge_coverage + risk_coverage) / 3
            
            # Generate recommendations
            recommendations = []
            if functional_coverage < 80:
                recommendations.append("Aumentar casos para cubrir más requerimientos funcionales")
            if edge_coverage < 70:
                recommendations.append("Añadir más casos para edge cases identificados")
            if risk_coverage < 75:
                recommendations.append("Incrementar cobertura de áreas de riesgo")
            if high_priority_count < len(test_cases) * 0.3:
                recommendations.append("Considerar más casos de alta prioridad")
            
            return {
                "overall_coverage": {
                    "percentage": round(overall_percentage, 2),
                    "status": "Excellent" if overall_percentage >= 90 else "Good" if overall_percentage >= 75 else "Needs Improvement"
                },
                "components": {
                    "functional": round(functional_coverage, 2),
                    "edge_cases": round(edge_coverage, 2),
                    "risk_areas": round(risk_coverage, 2)
                },
                "test_case_distribution": {
                    "high_priority": high_priority_count,
                    "medium_priority": medium_priority_count,
                    "low_priority": low_priority_count,
                    "total": len(test_cases)
                },
                "recommendations": recommendations
            }
            
        except Exception as e:
            print(f"Coverage calculation error: {str(e)}")
            return {
                "error": str(e),
                "overall_coverage": {"percentage": 0}
            }

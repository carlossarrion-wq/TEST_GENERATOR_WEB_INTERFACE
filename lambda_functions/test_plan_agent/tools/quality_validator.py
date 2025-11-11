"""
Quality Validator Tool
Validates test case quality and provides improvement suggestions
"""

import json
from typing import Dict, Any, List

class QualityValidatorTool:
    """Tool for validating test case quality"""
    
    def __init__(self):
        self.name = "quality_validator"
        self.description = """Validates test case quality by checking:
- Completeness of test cases
- Clarity of steps and expected results
- Proper prioritization
- Test data adequacy
Provides improvement suggestions."""
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quality validation"""
        try:
            test_cases = input_data.get('test_cases', [])
            validation_options = input_data.get('validation_options', {})
            strict_mode = validation_options.get('strict_mode', True)
            
            if not test_cases:
                return {
                    "error": "No test cases provided",
                    "overall_metrics": {"average_score": 0}
                }
            
            # Validate each test case
            case_scores = []
            improvement_suggestions = []
            
            for i, test_case in enumerate(test_cases, 1):
                score = self._validate_test_case(test_case, strict_mode)
                case_scores.append(score)
                
                # Generate suggestions for low-scoring cases
                if score['total_score'] < 80:
                    suggestions = self._generate_suggestions(test_case, score, i)
                    improvement_suggestions.extend(suggestions)
            
            # Calculate overall metrics
            avg_score = sum(s['total_score'] for s in case_scores) / len(case_scores)
            
            # Quality assessment
            quality_level = "Excellent" if avg_score >= 90 else "Good" if avg_score >= 75 else "Needs Improvement"
            
            return {
                "overall_metrics": {
                    "average_score": round(avg_score, 2),
                    "quality_level": quality_level,
                    "total_cases_validated": len(test_cases),
                    "high_quality_cases": sum(1 for s in case_scores if s['total_score'] >= 85),
                    "needs_improvement_cases": sum(1 for s in case_scores if s['total_score'] < 75)
                },
                "detailed_scores": case_scores,
                "improvement_recommendations": improvement_suggestions[:10],  # Top 10
                "validation_completed": True
            }
            
        except Exception as e:
            print(f"Quality validation error: {str(e)}")
            return {
                "error": str(e),
                "overall_metrics": {"average_score": 0},
                "validation_completed": False
            }
    
    def _validate_test_case(self, test_case: Dict[str, Any], strict_mode: bool) -> Dict[str, Any]:
        """Validate individual test case"""
        scores = {
            'name': 0,
            'description': 0,
            'steps': 0,
            'preconditions': 0,
            'expected_result': 0,
            'test_data': 0,
            'priority': 0
        }
        
        # Name validation (0-15 points)
        name = test_case.get('name', '')
        if name:
            if len(name) > 20:
                scores['name'] = 15
            elif len(name) > 10:
                scores['name'] = 10
            else:
                scores['name'] = 5
        
        # Description validation (0-15 points)
        description = test_case.get('description', '')
        if description:
            if len(description) > 50:
                scores['description'] = 15
            elif len(description) > 20:
                scores['description'] = 10
            else:
                scores['description'] = 5
        
        # Steps validation (0-25 points)
        steps = test_case.get('steps', [])
        if steps:
            if len(steps) >= 3:
                scores['steps'] = 25
            elif len(steps) >= 2:
                scores['steps'] = 15
            else:
                scores['steps'] = 10
        
        # Preconditions validation (0-10 points)
        preconditions = test_case.get('preconditions', '')
        if preconditions and len(preconditions) > 10:
            scores['preconditions'] = 10
        elif preconditions:
            scores['preconditions'] = 5
        
        # Expected result validation (0-20 points)
        expected_result = test_case.get('expected_result', '')
        if expected_result:
            if len(expected_result) > 30:
                scores['expected_result'] = 20
            elif len(expected_result) > 15:
                scores['expected_result'] = 15
            else:
                scores['expected_result'] = 10
        
        # Test data validation (0-10 points)
        test_data = test_case.get('test_data', '')
        if test_data and len(test_data) > 10:
            scores['test_data'] = 10
        elif test_data:
            scores['test_data'] = 5
        
        # Priority validation (0-5 points)
        priority = test_case.get('priority', '')
        if priority in ['High', 'Medium', 'Low']:
            scores['priority'] = 5
        
        total_score = sum(scores.values())
        
        return {
            'total_score': total_score,
            'component_scores': scores,
            'max_possible': 100
        }
    
    def _generate_suggestions(self, test_case: Dict[str, Any], score: Dict[str, Any], case_num: int) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        component_scores = score['component_scores']
        
        if component_scores['name'] < 10:
            suggestions.append(f"Caso {case_num}: Mejorar nombre del caso - debe ser más descriptivo")
        
        if component_scores['description'] < 10:
            suggestions.append(f"Caso {case_num}: Ampliar descripción - explicar objetivo y alcance")
        
        if component_scores['steps'] < 20:
            suggestions.append(f"Caso {case_num}: Añadir más pasos detallados - mínimo 3 pasos recomendados")
        
        if component_scores['preconditions'] < 8:
            suggestions.append(f"Caso {case_num}: Especificar precondiciones necesarias")
        
        if component_scores['expected_result'] < 15:
            suggestions.append(f"Caso {case_num}: Detallar resultado esperado - debe ser específico y medible")
        
        if component_scores['test_data'] < 8:
            suggestions.append(f"Caso {case_num}: Incluir datos de prueba específicos")
        
        return suggestions

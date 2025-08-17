"""
Code execution environment with AI-powered evaluation
"""
import asyncio
import logging
import subprocess
import tempfile
import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Try to import resource module (Unix only)
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

from app.models.coding_challenge import (
    ExecutionResult, TestResult, TestCase, ProgrammingLanguage, CodeSubmission
)

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Code execution environment with security and resource limits"""
    
    def __init__(self, watsonx_client=None):
        self.watsonx_client = watsonx_client
        self.supported_languages = {
            ProgrammingLanguage.PYTHON: self._execute_python,
            ProgrammingLanguage.JAVASCRIPT: self._execute_javascript,
            ProgrammingLanguage.JAVA: self._execute_java
        }
        
        # Security and resource limits
        self.time_limit = 10  # seconds
        self.memory_limit = 128 * 1024 * 1024  # 128MB in bytes
        self.max_output_size = 10000  # characters
    
    async def execute_code(
        self, 
        code: str, 
        language: ProgrammingLanguage, 
        test_cases: List[TestCase],
        submission_id: str
    ) -> ExecutionResult:
        """Execute code against test cases and return results"""
        try:
            if language not in self.supported_languages:
                return ExecutionResult(
                    submission_id=submission_id,
                    success=False,
                    test_results=[],
                    passed_tests=0,
                    total_tests=len(test_cases),
                    overall_status="unsupported_language",
                    error_message=f"Language {language} is not supported"
                )
            
            # Execute code against test cases
            executor_func = self.supported_languages[language]
            test_results = []
            total_execution_time = 0
            max_memory_used = 0
            
            for i, test_case in enumerate(test_cases):
                try:
                    start_time = time.time()
                    result = await executor_func(code, test_case, i)
                    execution_time = int((time.time() - start_time) * 1000)  # milliseconds
                    
                    test_results.append(result)
                    total_execution_time += execution_time
                    max_memory_used = max(max_memory_used, result.memory_used)
                    
                    # Stop execution if time limit exceeded
                    if total_execution_time > self.time_limit * 1000:
                        break
                        
                except Exception as e:
                    logger.error(f"Test case {i} execution failed: {str(e)}")
                    test_results.append(TestResult(
                        test_case_index=i,
                        passed=False,
                        input=test_case.input,
                        expected_output=test_case.expected_output,
                        actual_output=None,
                        execution_time=0,
                        memory_used=0,
                        error_message=str(e)
                    ))
            
            # Calculate results
            passed_tests = sum(1 for result in test_results if result.passed)
            overall_status = self._determine_overall_status(passed_tests, len(test_cases), test_results)
            
            # Generate AI feedback if available
            ai_feedback = None
            if self.watsonx_client and passed_tests > 0:
                ai_feedback = await self._generate_ai_feedback(code, language, test_results)
            
            return ExecutionResult(
                submission_id=submission_id,
                success=True,
                test_results=test_results,
                passed_tests=passed_tests,
                total_tests=len(test_cases),
                overall_status=overall_status,
                execution_time=total_execution_time,
                memory_used=max_memory_used,
                ai_feedback=ai_feedback
            )
            
        except Exception as e:
            logger.error(f"Code execution failed: {str(e)}")
            return ExecutionResult(
                submission_id=submission_id,
                success=False,
                test_results=[],
                passed_tests=0,
                total_tests=len(test_cases),
                overall_status="execution_error",
                error_message=str(e)
            )
    
    async def _execute_python(self, code: str, test_case: TestCase, test_index: int) -> TestResult:
        """Execute Python code for a single test case"""
        try:
            # Create test wrapper
            test_code = self._create_python_test_wrapper(code, test_case)
            
            # Execute in temporary file with resource limits
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_code)
                temp_file = f.name
            
            try:
                # Execute with timeout and resource limits
                start_time = time.time()
                # Create subprocess with or without resource limits
                if HAS_RESOURCE:
                    process = await asyncio.create_subprocess_exec(
                        'python', temp_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        preexec_fn=self._set_resource_limits
                    )
                else:
                    process = await asyncio.create_subprocess_exec(
                        'python', temp_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), 
                        timeout=self.time_limit
                    )
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    if process.returncode != 0:
                        return TestResult(
                            test_case_index=test_index,
                            passed=False,
                            input=test_case.input,
                            expected_output=test_case.expected_output,
                            actual_output=None,
                            execution_time=execution_time,
                            memory_used=0,
                            error_message=stderr.decode('utf-8')[:1000]
                        )
                    
                    # Parse output
                    output_str = stdout.decode('utf-8').strip()
                    try:
                        actual_output = json.loads(output_str)
                    except json.JSONDecodeError:
                        actual_output = output_str
                    
                    # Compare results
                    passed = self._compare_outputs(actual_output, test_case.expected_output)
                    
                    return TestResult(
                        test_case_index=test_index,
                        passed=passed,
                        input=test_case.input,
                        expected_output=test_case.expected_output,
                        actual_output=actual_output,
                        execution_time=execution_time,
                        memory_used=0  # Memory tracking would require additional setup
                    )
                    
                except asyncio.TimeoutError:
                    process.kill()
                    return TestResult(
                        test_case_index=test_index,
                        passed=False,
                        input=test_case.input,
                        expected_output=test_case.expected_output,
                        actual_output=None,
                        execution_time=self.time_limit * 1000,
                        memory_used=0,
                        error_message="Time limit exceeded"
                    )
                    
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            return TestResult(
                test_case_index=test_index,
                passed=False,
                input=test_case.input,
                expected_output=test_case.expected_output,
                actual_output=None,
                execution_time=0,
                memory_used=0,
                error_message=str(e)
            )
    
    async def _execute_javascript(self, code: str, test_case: TestCase, test_index: int) -> TestResult:
        """Execute JavaScript code for a single test case"""
        try:
            # Create test wrapper
            test_code = self._create_javascript_test_wrapper(code, test_case)
            
            # Execute in temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(test_code)
                temp_file = f.name
            
            try:
                start_time = time.time()
                process = await asyncio.create_subprocess_exec(
                    'node', temp_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), 
                        timeout=self.time_limit
                    )
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    if process.returncode != 0:
                        return TestResult(
                            test_case_index=test_index,
                            passed=False,
                            input=test_case.input,
                            expected_output=test_case.expected_output,
                            actual_output=None,
                            execution_time=execution_time,
                            memory_used=0,
                            error_message=stderr.decode('utf-8')[:1000]
                        )
                    
                    # Parse output
                    output_str = stdout.decode('utf-8').strip()
                    try:
                        actual_output = json.loads(output_str)
                    except json.JSONDecodeError:
                        actual_output = output_str
                    
                    # Compare results
                    passed = self._compare_outputs(actual_output, test_case.expected_output)
                    
                    return TestResult(
                        test_case_index=test_index,
                        passed=passed,
                        input=test_case.input,
                        expected_output=test_case.expected_output,
                        actual_output=actual_output,
                        execution_time=execution_time,
                        memory_used=0
                    )
                    
                except asyncio.TimeoutError:
                    process.kill()
                    return TestResult(
                        test_case_index=test_index,
                        passed=False,
                        input=test_case.input,
                        expected_output=test_case.expected_output,
                        actual_output=None,
                        execution_time=self.time_limit * 1000,
                        memory_used=0,
                        error_message="Time limit exceeded"
                    )
                    
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            return TestResult(
                test_case_index=test_index,
                passed=False,
                input=test_case.input,
                expected_output=test_case.expected_output,
                actual_output=None,
                execution_time=0,
                memory_used=0,
                error_message=str(e)
            )
    
    async def _execute_java(self, code: str, test_case: TestCase, test_index: int) -> TestResult:
        """Execute Java code for a single test case"""
        # Java execution is more complex due to compilation step
        # For now, return a placeholder implementation
        return TestResult(
            test_case_index=test_index,
            passed=False,
            input=test_case.input,
            expected_output=test_case.expected_output,
            actual_output=None,
            execution_time=0,
            memory_used=0,
            error_message="Java execution not yet implemented"
        )
    
    def _create_python_test_wrapper(self, code: str, test_case: TestCase) -> str:
        """Create Python test wrapper code"""
        # Extract function name from code (simple heuristic)
        lines = code.split('\n')
        function_name = None
        for line in lines:
            if line.strip().startswith('def '):
                function_name = line.strip().split('(')[0].replace('def ', '')
                break
        
        if not function_name:
            function_name = "solution"  # fallback
        
        # Create test wrapper
        wrapper = f"""
import json
import sys

{code}

# Test execution
try:
    # Prepare input arguments
    test_input = {json.dumps(test_case.input)}
    
    # Call function with unpacked arguments
    if isinstance(test_input, dict):
        result = {function_name}(**test_input)
    else:
        result = {function_name}(test_input)
    
    # Output result as JSON
    print(json.dumps(result))
    
except Exception as e:
    print(f"Error: {{str(e)}}", file=sys.stderr)
    sys.exit(1)
"""
        return wrapper
    
    def _create_javascript_test_wrapper(self, code: str, test_case: TestCase) -> str:
        """Create JavaScript test wrapper code"""
        # Extract function name from code (simple heuristic)
        lines = code.split('\n')
        function_name = None
        for line in lines:
            if 'function' in line or 'var ' in line or 'const ' in line or 'let ' in line:
                if '=' in line:
                    function_name = line.split('=')[0].strip().split()[-1]
                    break
        
        if not function_name:
            function_name = "solution"  # fallback
        
        # Create test wrapper
        wrapper = f"""
{code}

// Test execution
try {{
    const testInput = {json.dumps(test_case.input)};
    
    // Call function with arguments
    let result;
    if (typeof testInput === 'object' && testInput !== null && !Array.isArray(testInput)) {{
        // Unpack object arguments
        const args = Object.values(testInput);
        result = {function_name}(...args);
    }} else {{
        result = {function_name}(testInput);
    }}
    
    // Output result as JSON
    console.log(JSON.stringify(result));
    
}} catch (error) {{
    console.error('Error:', error.message);
    process.exit(1);
}}
"""
        return wrapper
    
    def _set_resource_limits(self):
        """Set resource limits for subprocess (Unix only)"""
        if not HAS_RESOURCE:
            logger.warning("Resource limits not available on this platform")
            return
            
        try:
            # Set memory limit
            resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
            # Set CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.time_limit, self.time_limit))
        except Exception as e:
            logger.warning(f"Failed to set resource limits: {str(e)}")
    
    def _compare_outputs(self, actual: Any, expected: Any) -> bool:
        """Compare actual and expected outputs"""
        try:
            # Handle different types of comparisons
            if isinstance(expected, list) and isinstance(actual, list):
                return len(actual) == len(expected) and all(a == e for a, e in zip(actual, expected))
            elif isinstance(expected, dict) and isinstance(actual, dict):
                return actual == expected
            else:
                return actual == expected
        except Exception:
            return False
    
    def _determine_overall_status(self, passed_tests: int, total_tests: int, test_results: List[TestResult]) -> str:
        """Determine overall execution status"""
        if passed_tests == total_tests:
            return "accepted"
        elif passed_tests == 0:
            # Check if it's a compilation error
            if any(result.error_message and "Error:" in result.error_message for result in test_results):
                return "compilation_error"
            else:
                return "wrong_answer"
        else:
            return "partial_correct"
    
    async def _generate_ai_feedback(self, code: str, language: ProgrammingLanguage, test_results: List[TestResult]) -> Optional[str]:
        """Generate AI-powered feedback on the code solution"""
        try:
            if not self.watsonx_client:
                return None
            
            passed_tests = sum(1 for result in test_results if result.passed)
            total_tests = len(test_results)
            
            # Create feedback prompt
            prompt = f"""
            Analyze this {language} code solution and provide constructive feedback:
            
            Code:
            ```{language}
            {code}
            ```
            
            Test Results: {passed_tests}/{total_tests} tests passed
            
            Failed Test Cases:
            {self._format_failed_tests(test_results)}
            
            Please provide feedback on:
            1. Code correctness and logic
            2. Algorithm efficiency (time/space complexity)
            3. Code style and readability
            4. Potential improvements or optimizations
            5. Common mistakes or edge cases missed
            
            Keep feedback constructive and educational. Focus on helping the developer improve.
            """
            
            if hasattr(self.watsonx_client, 'generate_text'):
                feedback = await self.watsonx_client.generate_text(
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.3
                )
                return feedback
            
        except Exception as e:
            logger.error(f"AI feedback generation failed: {str(e)}")
        
        return None
    
    def _format_failed_tests(self, test_results: List[TestResult]) -> str:
        """Format failed test cases for AI feedback"""
        failed_tests = [result for result in test_results if not result.passed]
        if not failed_tests:
            return "All tests passed!"
        
        formatted = []
        for result in failed_tests[:3]:  # Limit to first 3 failed tests
            formatted.append(f"""
            Test {result.test_case_index + 1}:
            Input: {result.input}
            Expected: {result.expected_output}
            Actual: {result.actual_output}
            Error: {result.error_message or 'Wrong output'}
            """)
        
        return "\n".join(formatted)
# JobSwitch.ai Testing Framework

This comprehensive testing framework ensures the reliability, performance, and quality of the JobSwitch.ai AI Career Copilot platform.

## Overview

The testing framework includes:

- **Unit Tests**: Test individual components, agents, and business logic
- **Integration Tests**: Test agent communication and external API integrations
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Test AI processing times and system load
- **Frontend Tests**: Test React components and user interactions

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_runner.py           # Main test runner script
├── unit/                    # Unit tests
│   ├── agents/             # Agent-specific unit tests
│   ├── api/                # API endpoint tests
│   ├── core/               # Core functionality tests
│   └── models/             # Data model tests
├── integration/            # Integration tests
│   ├── test_agent_communication.py
│   ├── test_external_apis.py
│   └── test_database_integration.py
├── e2e/                    # End-to-end tests
│   ├── test_user_workflows.py
│   └── test_complete_scenarios.py
└── performance/            # Performance tests
    ├── test_ai_processing_performance.py
    └── test_load_testing.py
```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

For frontend tests:

```bash
cd jobswitch-ui/jobswitch-ui
npm install
```

### Test Commands

#### Using the Test Runner

```bash
# Run all tests
python tests/test_runner.py --all

# Run specific test suites
python tests/test_runner.py --unit
python tests/test_runner.py --integration
python tests/test_runner.py --e2e
python tests/test_runner.py --performance
python tests/test_runner.py --frontend

# Run with verbose output
python tests/test_runner.py --all --verbose

# Include performance tests in full run
python tests/test_runner.py --all --include-performance

# Generate comprehensive test report
python tests/test_runner.py --report

# Check test dependencies
python tests/test_runner.py --check-deps
```

#### Using pytest directly

```bash
# Run all backend tests
pytest

# Run specific test categories
pytest tests/unit/ -m unit
pytest tests/integration/ -m integration
pytest tests/e2e/ -m e2e
pytest tests/performance/ -m performance

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/agents/test_job_discovery_agent.py

# Run tests matching pattern
pytest -k "test_job_discovery"
```

#### Frontend Tests

```bash
cd jobswitch-ui/jobswitch-ui

# Run all frontend tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage --watchAll=false

# Run specific test file
npm test -- Dashboard.test.js
```

## Test Categories

### Unit Tests

Test individual components in isolation:

- **Agent Tests**: Test each AI agent's functionality
- **API Tests**: Test API endpoints and request handling
- **Core Tests**: Test authentication, database, caching
- **Model Tests**: Test data models and validation

Example:
```python
@pytest.mark.asyncio
async def test_job_discovery_agent(job_discovery_agent, sample_user_profile):
    result = await job_discovery_agent.discover_jobs(sample_user_profile, {})
    assert result["success"] is True
    assert "jobs" in result["data"]
```

### Integration Tests

Test component interactions:

- **Agent Communication**: Test inter-agent messaging
- **External APIs**: Test job board and AI service integrations
- **Database Integration**: Test data persistence and retrieval
- **WebSocket Communication**: Test real-time updates

Example:
```python
@pytest.mark.asyncio
async def test_cross_agent_workflow(orchestrator, mock_agents):
    workflow_data = {"user_id": "user-123", "workflow_type": "job_application_preparation"}
    result = await orchestrator.execute_workflow(workflow_data)
    assert result["success"] is True
```

### End-to-End Tests

Test complete user workflows:

- **Job Search Workflow**: Registration → Profile → Job Discovery → Application
- **Career Development**: Goal Setting → Skills Analysis → Learning Paths
- **Interview Preparation**: Mock Interviews → Feedback → Improvement
- **Networking**: Contact Discovery → Email Generation → Campaign Management

Example:
```python
@pytest.mark.asyncio
async def test_complete_job_search_workflow(client, authenticated_headers):
    # Test complete workflow from registration to job application
    # ... (see test_user_workflows.py for full implementation)
```

### Performance Tests

Test system performance and scalability:

- **AI Response Times**: Ensure AI processing meets performance thresholds
- **Concurrent Load**: Test system under multiple simultaneous users
- **Memory Usage**: Monitor memory consumption during operations
- **Database Performance**: Test query optimization and response times

Example:
```python
@pytest.mark.asyncio
async def test_ai_response_time_performance(performance_agents, performance_thresholds):
    start_time = time.time()
    result = await agent.process_request(request_data, {})
    response_time_ms = (time.time() - start_time) * 1000
    assert response_time_ms < performance_thresholds["ai_response_time_ms"]
```

## Test Configuration

### Performance Thresholds

Default performance thresholds (configurable in `conftest.py`):

- AI Response Time: 5000ms
- API Response Time: 1000ms
- Database Query Time: 500ms
- Concurrent Users: 100
- Memory Usage: 512MB
- CPU Usage: 80%

### Test Data

The framework provides comprehensive mock data:

- **Sample User Profiles**: Realistic user data for testing
- **Mock Job Postings**: Various job types and requirements
- **Resume Templates**: Different resume formats and content
- **Interview Sessions**: Mock interview data and responses

### Fixtures

Key pytest fixtures available:

- `mock_watsonx_client`: Mock WatsonX AI client
- `mock_langchain_manager`: Mock LangChain manager
- `mock_database`: Mock database session
- `sample_user_profile`: Sample user data
- `sample_job_posting`: Sample job posting
- `performance_thresholds`: Performance testing limits

## Frontend Testing

### Component Tests

Test React components with React Testing Library:

```javascript
test('renders dashboard with user data', async () => {
  renderWithProviders(<Dashboard />);
  expect(screen.getByText(/welcome/i)).toBeInTheDocument();
});
```

### Integration Tests

Test component interactions and API calls:

```javascript
test('displays job recommendations', async () => {
  mockFetch(customResponses);
  renderWithProviders(<Dashboard />);
  await waitFor(() => {
    expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
  });
});
```

### Accessibility Tests

Ensure components meet accessibility standards:

```javascript
test('is accessible', async () => {
  const { container } = renderWithProviders(<Dashboard />);
  const results = await checkAccessibility(container);
  expect(results.violations).toHaveLength(0);
});
```

## Continuous Integration

### GitHub Actions

Example workflow for automated testing:

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/test_runner.py --all --report
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks

Set up pre-commit hooks to run tests before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python tests/test_runner.py --unit
        language: system
        pass_filenames: false
```

## Best Practices

### Writing Tests

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
3. **Mock External Dependencies**: Use mocks for external APIs and services
4. **Test Edge Cases**: Include tests for error conditions and boundary cases
5. **Keep Tests Independent**: Each test should be able to run in isolation

### Performance Testing

1. **Set Realistic Thresholds**: Base performance thresholds on actual requirements
2. **Test Under Load**: Simulate realistic user loads and concurrent operations
3. **Monitor Resources**: Track CPU, memory, and database performance
4. **Profile Bottlenecks**: Identify and test performance-critical code paths

### Maintenance

1. **Regular Updates**: Keep test data and mocks up to date with code changes
2. **Review Test Coverage**: Maintain high test coverage (target: 80%+)
3. **Clean Up**: Remove obsolete tests and update deprecated patterns
4. **Documentation**: Keep test documentation current and comprehensive

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Python path includes the app directory
2. **Async Test Failures**: Use `pytest-asyncio` and proper async/await patterns
3. **Mock Issues**: Verify mocks are properly configured and reset between tests
4. **Performance Test Variability**: Run performance tests multiple times for consistency

### Debug Mode

Run tests with additional debugging:

```bash
# Verbose output with full tracebacks
pytest -vvv --tb=long

# Drop into debugger on failures
pytest --pdb

# Run specific test with debugging
pytest tests/unit/agents/test_job_discovery_agent.py::TestJobDiscoveryAgent::test_discover_jobs -vvv --pdb
```

## Reporting

### Coverage Reports

Generate HTML coverage reports:

```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Performance Reports

Performance test results include:

- Response time statistics (min, max, average)
- Resource usage metrics (CPU, memory)
- Throughput measurements (requests per second)
- Load testing results (concurrent user handling)

### Test Results

JUnit XML format for CI integration:

```bash
pytest --junitxml=test-results.xml
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all test categories are covered
3. Update test documentation
4. Verify performance impact
5. Run full test suite before submitting

For questions or issues with the testing framework, please refer to the project documentation or create an issue in the repository.
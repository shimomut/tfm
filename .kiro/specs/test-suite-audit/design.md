# Design Document

## Overview

This document defines a reusable process for auditing and updating test suites. The process can be applied to any project to systematically examine test programs, identify issues, and apply fixes.

The audit process scans test files, analyzes their content and execution status, identifies issues, and generates actionable reports. The update process applies automated fixes to address common issues and creates missing tests.

The audit process consists of multiple analysis steps that work together to provide a complete picture of test suite health. Each step focuses on a specific aspect (functionality existence, redundancy, outdated patterns, execution status, coverage gaps) and contributes findings to a unified report.

## Process Workflow

### Audit Process Steps

```
┌─────────────────────────────────────────────────────────────┐
│                   1. Discovery Phase                         │
│  - Scan test directory                                       │
│  - Identify all test files                                   │
│  - Scan source directory                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   2. Analysis Phase                          │
│  - Functionality analysis (tests vs source)                  │
│  - Redundancy analysis (duplicate coverage)                  │
│  - Outdated pattern analysis (deprecated usage)              │
│  - Execution analysis (run tests, capture failures)          │
│  - Naming analysis (convention compliance)                   │
│  - Coverage analysis (missing tests)                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. Aggregation Phase                       │
│  - Combine findings from all analyses                        │
│  - Categorize by issue type                                  │
│  - Prioritize by severity and impact                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   4. Reporting Phase                         │
│  - Generate comprehensive markdown report                    │
│  - Include summary statistics                                │
│  - Provide actionable recommendations                        │
└─────────────────────────────────────────────────────────────┘
```

### Update Process Steps

```
┌─────────────────────────────────────────────────────────────┐
│                   1. Review Findings                         │
│  - Examine audit report                                      │
│  - Select issues to address                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   2. Apply Fixes                             │
│  - Update outdated imports and APIs                          │
│  - Consolidate redundant tests                               │
│  - Fix non-functional tests                                  │
│  - Correct naming inconsistencies                            │
│  - Remove unnecessary tests                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. Create Missing Tests                    │
│  - Generate test files for untested modules                  │
│  - Follow naming conventions                                 │
│  - Include basic test structure                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   4. Verification                            │
│  - Run updated tests                                         │
│  - Verify fixes are successful                               │
│  - Re-audit if needed                                        │
└─────────────────────────────────────────────────────────────┘
```

## Process Implementation Guide

### Analysis Steps

Each analysis step examines a specific aspect of the test suite. The following sections describe what each step should accomplish and how to implement it.

### 1. Functionality Analysis

**Purpose**: Determines if tested functionality still exists in the codebase.

**Implementation Approach**:
- Parse test imports to identify tested modules
- Extract class and function names from test cases
- Search source directory for corresponding implementations
- Flag tests where no matching source code is found

### 2. Redundancy Analysis

**Purpose**: Identifies tests that duplicate coverage of the same functionality.

**Implementation Approach**:
- Extract tested components, methods, and scenarios from each test
- Create similarity signatures based on imports, test names, and assertions
- Group tests with high similarity scores (>80%)
- Recommend keeping the most comprehensive test in each group

### 3. Outdated Pattern Analysis

**Purpose**: Detects usage of deprecated APIs, imports, and patterns.

**Implementation Approach**:
- Map old module names to new ones (e.g., `tfm_old_module` → `tfm_new_module`)
- Track deprecated function signatures
- Identify outdated testing patterns (e.g., old assertion styles)

### 4. Execution Analysis

**Purpose**: Attempts to execute tests and captures failures.

**Implementation Approach**:
- Use Python venv (.venv at project top directory) to run tests
  - The venv contains necessary libraries such as PyObjC
  - Without venv, tests may fail due to missing dependencies
  - Execute tests using `.venv/bin/python` or `.venv/bin/pytest`
- Run each test in isolated subprocess using pytest
- Capture stdout, stderr, and exit code
- Parse error messages to categorize failures
- Extract specific error details (missing modules, syntax errors, etc.)

### 5. Naming Analysis

**Purpose**: Verifies tests follow naming conventions.

**Implementation Approach**:
- Test files must match `test_*.py` pattern
- Test functions must match `test_*` pattern
- Test classes must match `Test*` pattern

### 6. Coverage Analysis

**Purpose**: Identifies source code without corresponding tests.

**Implementation Approach**:
- Map each source file to expected test file name
- Parse source files to extract public functions and classes
- Parse test files to identify what's tested
- Report untested components with priority based on complexity

### 7. Report Generation

**Purpose**: Creates comprehensive markdown report from findings.

**Report Structure**:
```markdown
# Test Suite Audit Report

## Executive Summary
- Total tests analyzed: X
- Issues found: Y
- Categories: breakdown by type

## Unnecessary Tests
- List with justification

## Redundant Tests
- Groups with consolidation recommendations

## Outdated Tests
- List with specific deprecated usage

## Non-functional Tests
- List with error details

## Naming Inconsistencies
- List with corrections

## Coverage Gaps
- List with priority and recommendations

## Recommendations
- Prioritized action items
```

### 8. Update Operations

**Purpose**: Applies automated fixes to tests based on audit findings.

**Update Types**:
- **Update outdated imports**: Replace deprecated imports with current equivalents
- **Consolidate redundant tests**: Merge redundant tests into single comprehensive test
- **Fix naming issues**: Rename test files and functions to follow conventions
- **Create missing tests**: Generate new test files for untested modules
- **Fix non-functional tests**: Address import errors, syntax errors, and runtime failures
- **Remove unnecessary tests**: Delete tests for non-existent functionality

## Data Models

### Finding
```python
@dataclass
class Finding:
    category: str  # 'unnecessary', 'redundant', 'outdated', 'non-functional', 'naming', 'coverage'
    severity: str  # 'high', 'medium', 'low'
    test_file: Path
    description: str
    details: Dict[str, Any]
    recommendation: str
```

### AuditReport
```python
@dataclass
class AuditReport:
    timestamp: datetime
    total_tests: int
    findings: List[Finding]
    summary_stats: Dict[str, int]
    
    def get_by_category(self, category: str) -> List[Finding]:
        """Filter findings by category."""
        
    def get_by_severity(self, severity: str) -> List[Finding]:
        """Filter findings by severity."""
```

### TestSignature
```python
@dataclass
class TestSignature:
    imports: Set[str]
    tested_components: Set[str]
    test_methods: Set[str]
    assertion_patterns: Set[str]
    
    def similarity(self, other: 'TestSignature') -> float:
        """Calculate similarity score with another signature."""
```

### ExecutionResult
```python
@dataclass
class ExecutionResult:
    test_file: Path
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    failure_type: Optional[str]  # 'import', 'syntax', 'runtime', None
    error_details: Optional[str]
```

### CoverageGap
```python
@dataclass
class CoverageGap:
    source_file: Path
    missing_test_file: bool
    untested_functions: List[str]
    untested_classes: List[str]
    priority: str  # 'high', 'medium', 'low'
    complexity_score: int
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


Property 1: Functionality existence detection accuracy
*For any* test file and source tree, if the analyzer flags a test as unnecessary, then searching the source tree for the tested components should return no matches
**Validates: Requirements 1.1, 1.4**

Property 2: Redundancy detection consistency
*For any* set of test files with identical test signatures, the redundancy analyzer should group them together as redundant
**Validates: Requirements 2.1, 2.2**

Property 3: Redundancy recommendations completeness
*For any* redundancy group identified, the system should provide a recommendation for which test to keep
**Validates: Requirements 2.3, 2.4**

Property 4: Deprecated pattern detection completeness
*For any* test file containing patterns from the deprecation rules, the outdated analyzer should flag those specific patterns
**Validates: Requirements 3.1, 3.2, 3.3**

Property 5: Execution failure capture completeness
*For any* test file that fails to execute, the execution analyzer should capture the failure type and error details
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

Property 6: Report generation completeness
*For any* audit run, the generated report should include summary statistics, detailed findings, and recommendations for all categories
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

Property 7: Import replacement correctness
*For any* deprecated import in the deprecation rules, applying the update should replace it with the correct modern equivalent
**Validates: Requirements 6.1**

Property 8: Test consolidation coverage preservation
*For any* set of redundant tests being consolidated, the resulting test should include all unique test cases from the original set
**Validates: Requirements 6.3**

Property 9: Test categorization completeness
*For any* test file analyzed, the system should assign it a category (unit, integration, etc.) and identify the primary component being tested
**Validates: Requirements 7.1, 7.2, 7.3**

Property 10: Naming convention validation accuracy
*For any* test filename or function name, the naming analyzer should correctly identify whether it follows the test_* pattern
**Validates: Requirements 8.1, 8.2, 8.3**

Property 11: Coverage gap detection accuracy
*For any* source file without a corresponding test file, the coverage analyzer should identify it as a coverage gap
**Validates: Requirements 9.1**

Property 12: Generated test naming consistency
*For any* test file created by the system, the filename and function names should follow the test_* naming convention
**Validates: Requirements 9.5**

## Error Handling

### File System Errors
- Handle missing test directory gracefully with clear error message
- Handle permission errors when reading test files
- Handle corrupted or binary files in test directory
- Provide fallback behavior when source directory is inaccessible

### Execution Errors
- Isolate test execution in subprocess to prevent crashes
- Set timeout for test execution to prevent hanging
- Capture and categorize all types of execution failures
- Continue audit even if individual tests fail to execute

### Analysis Errors
- Handle malformed Python files that cannot be parsed
- Provide partial results if some analyzers fail
- Log analyzer errors without stopping the audit
- Include error information in the final report

### Report Generation Errors
- Ensure report is generated even with incomplete findings
- Handle file write errors when saving report
- Provide console output if report file cannot be written
- Include error summary in report if issues occurred

## Testing Strategy

### Unit Testing
The test suite will include unit tests for:
- Each analyzer component in isolation
- Finding and report data model operations
- File parsing and pattern matching logic
- Deprecation rule matching
- Test signature similarity calculations
- Report formatting functions

### Property-Based Testing
Property-based tests will verify:
- Functionality detection never flags tests for existing components
- Redundancy detection is symmetric (if A is redundant with B, then B is redundant with A)
- Import replacement preserves test functionality
- Coverage gap detection finds all untested modules
- Naming validation correctly identifies all pattern violations
- Report generation always produces valid markdown
- Test consolidation preserves all unique test cases

### Integration Testing
Integration tests will verify:
- Complete audit workflow from discovery to report generation
- Analyzer coordination and finding aggregation
- Report generation with real test files
- Update operations on actual test files
- End-to-end execution with sample test suite

### Test Data
- Create sample test files representing each issue category
- Include edge cases (empty tests, malformed tests, etc.)
- Use real TFM test files for integration testing
- Generate synthetic test suites for property-based testing

## Implementation Notes

### Performance Considerations
- Use multiprocessing to parallelize test execution analysis
- Cache source file parsing results to avoid redundant work
- Implement incremental analysis for large test suites
- Provide progress indicators for long-running operations

### Extensibility
- Design analyzer interface to allow adding new analysis types
- Make deprecation rules configurable via external file
- Support custom naming conventions through configuration
- Allow pluggable report formats (markdown, HTML, JSON)

### User Experience
- Provide verbose and quiet modes for different use cases
- Show progress during analysis with estimated time remaining
- Generate actionable recommendations, not just problem lists
- Include examples in recommendations for clarity
- Support dry-run mode to preview changes before applying

### Maintenance
- Keep deprecation rules up to date with TFM evolution
- Document analyzer algorithms for future maintainers
- Provide clear error messages for debugging
- Include version information in reports
- Log detailed information for troubleshooting

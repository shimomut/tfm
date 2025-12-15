# Design Document

## Overview

The Documentation Audit and Update project uses Kiro's AI capabilities to systematically review and improve TFM's documentation. Rather than building a complex automated system, we leverage Kiro to intelligently analyze documentation, compare it with implementation, and make improvements directly.

The approach is iterative and AI-driven:
1. **Audit Phase**: Use Kiro to analyze documentation and identify issues
2. **Update Phase**: Use Kiro to apply fixes and improvements
3. **Verification Phase**: Review changes and ensure quality

## Approach

### AI-Driven Analysis

Kiro will be used to:
- Read and understand documentation files
- Read and understand source code
- Compare documentation claims with implementation
- Identify inconsistencies, missing content, and redundancy
- Generate improvement recommendations
- Apply fixes directly to documentation files

### Iterative Process

The audit and update will proceed in focused iterations:
1. **Category-by-Category**: Focus on one type of issue at a time (accuracy, completeness, organization)
2. **File-by-File**: Process documents systematically
3. **Review and Refine**: Review changes before moving to next iteration

### Human Oversight

The process includes human review at key points:
- Review audit findings before making changes
- Review proposed changes before applying
- Verify critical updates manually
- Make final decisions on ambiguous cases

## Analysis Categories

### 1. Accuracy Analysis

**Focus**: Verify documentation matches implementation

**Key Checks**:
- Configuration examples reference valid options
- Key bindings match actual bindings in code
- CLI options match argparse definitions
- API signatures match function definitions
- Feature behaviors match implementation

**Method**: 
- Read documentation files to extract claims
- Read source code to verify claims
- Identify mismatches and outdated information
- Update documentation to match current implementation

### 2. Completeness Analysis

**Focus**: Identify missing documentation

**Key Checks**:
- Features in code have user documentation
- Components have developer documentation
- Configuration options are documented
- Key bindings are documented
- CLI options are documented

**Method**:
- Scan source code for features, APIs, config
- Check if corresponding documentation exists
- Identify gaps in documentation coverage
- Create missing documentation or update existing docs

### 3. Organization Analysis

**Focus**: Improve documentation structure and organization

**Key Checks**:
- Redundant documents covering same topics
- Temporary files that should be cleaned up
- Files in correct directories (doc/, doc/dev/, temp/)
- File names follow conventions
- Merge opportunities for fragmented docs
- Valid cross-references and links
- Obsolete content describing removed features

**Method**:
- Analyze document content for overlap
- Check file locations against policy
- Verify all links and references
- Identify temporary files for cleanup
- Find merge opportunities
- Remove or update obsolete content

## Audit Workflow

### Phase 1: Initial Assessment

1. **Survey Documentation**
   - List all documentation files in doc/, doc/dev/, temp/
   - Categorize by type (user, developer, temporary)
   - Identify obvious issues (misplaced files, naming problems)

2. **Survey Source Code**
   - Identify key modules and features
   - Note configuration options
   - Note key bindings and CLI options
   - Identify major components

3. **Create Initial Report**
   - Document current state
   - Highlight major issues
   - Prioritize areas for improvement

### Phase 2: Accuracy Audit

1. **Configuration Examples**
   - Find all config examples in documentation
   - Verify each option exists in src/_config.py
   - Update or remove invalid examples

2. **Key Bindings**
   - Extract documented key bindings
   - Compare with src/tfm_key_bindings.py
   - Update mismatches

3. **CLI Options**
   - Extract documented CLI options
   - Compare with argparse in src/tfm_main.py
   - Update mismatches

4. **Feature Behaviors**
   - Review feature documentation
   - Verify behaviors match implementation
   - Update outdated descriptions

### Phase 3: Completeness Audit

1. **Missing User Documentation**
   - Identify features without user docs
   - Create stub documentation or update existing
   - Ensure all user-facing features are documented

2. **Missing Developer Documentation**
   - Identify components without developer docs
   - Create or update technical documentation
   - Document architecture and design decisions

3. **Missing Configuration Documentation**
   - Find undocumented config options
   - Add to configuration documentation
   - Include examples and defaults

### Phase 4: Organization Audit

1. **Temporary File Cleanup**
   - Identify all temporary files in temp/
   - Determine which can be deleted
   - Consolidate useful information into permanent docs
   - Delete obsolete temporary files

2. **File Placement**
   - Check all docs are in correct directories
   - Move misplaced files
   - Update references after moves

3. **Redundancy and Merging**
   - Identify redundant documents
   - Merge related documents
   - Consolidate fragmented information
   - Update cross-references

4. **Link Validation**
   - Check all markdown links
   - Fix broken links
   - Update outdated references
   - Ensure "See also" sections are accurate

### Phase 5: Final Review

1. **Verify Changes**
   - Review all modifications
   - Ensure consistency across documents
   - Check for introduced errors

2. **Update Main Documents**
   - Update README.md if needed
   - Update TFM_USER_GUIDE.md if needed
   - Ensure top-level docs are current

3. **Generate Summary**
   - Document all changes made
   - List remaining issues
   - Provide recommendations for future maintenance

## Verification Criteria

*These criteria define what "correct" documentation looks like. They guide the audit and update process.*

### Accuracy Criteria

1. **Configuration Example Validity**: All configuration examples reference valid options that exist in src/_config.py
2. **Key Binding Accuracy**: All documented key bindings match the actual bindings in src/tfm_key_bindings.py
3. **CLI Option Accuracy**: All documented CLI options match the argparse definitions in src/tfm_main.py
4. **Architecture Component Existence**: All components described in architecture docs exist in the codebase
5. **API Signature Accuracy**: All documented function signatures match actual function definitions
6. **Integration Point Validity**: All documented integration points (imports, dependencies) exist in code
7. **Configuration Mechanism Accuracy**: All documented configuration mechanisms work as described

### Completeness Criteria

8. **Feature Documentation Coverage**: All user-facing features have corresponding user documentation
9. **Component Documentation Coverage**: All major components have corresponding developer documentation
10. **Configuration Documentation Coverage**: All configuration options are documented
11. **Key Binding Documentation Coverage**: All key bindings are documented
12. **CLI Documentation Coverage**: All command-line options are documented

### Organization Criteria

13. **No Redundancy**: No two documents cover the same topic with significant overlap
14. **Temporary File Cleanup**: No temporary files remain in temp/ after features are complete
15. **Correct File Placement**: User docs in doc/, developer docs in doc/dev/, temporary docs in temp/
16. **Naming Convention Compliance**: All files follow project naming conventions
17. **Merge Opportunities Addressed**: Related documents are consolidated appropriately
18. **Valid Cross-References**: All links and references point to existing documents
19. **No Obsolete Content**: Documentation doesn't describe removed features or non-existent code

## Key Files to Review

### Source Code Files

**Configuration**:
- `src/_config.py` - All configuration options and defaults

**Key Bindings**:
- `src/tfm_key_bindings.py` - All key binding definitions

**CLI Options**:
- `src/tfm_main.py` - Command-line argument parsing
- `tfm.py` - Main entry point

**Features and Components**:
- `src/tfm_*.py` - All main modules
- `src/tfm_archive.py` - Archive browsing
- `src/tfm_s3.py` - S3 integration
- `src/tfm_text_viewer.py` - Text viewer
- `src/tfm_search_dialog.py` - Search functionality

### Documentation Files

**User Documentation** (doc/):
- `README.md` - Main project documentation
- `doc/TFM_USER_GUIDE.md` - Comprehensive user guide
- `doc/*_FEATURE.md` - Individual feature documentation
- `doc/*_INTEGRATION.md` - Integration guides

**Developer Documentation** (doc/dev/):
- `doc/dev/*_SYSTEM.md` - System architecture docs
- `doc/dev/*_IMPLEMENTATION.md` - Implementation details
- `doc/dev/PROJECT_STRUCTURE.md` - Project organization

**Temporary Files** (temp/):
- `temp/*_SUMMARY.md` - Task/feature summaries
- `temp/*_FIX.md` - Bug fix documentation
- `temp/TASK_*.md` - Task completion notes

## Decision Guidelines

### When to Merge Documents

**Merge when**:
- Multiple small docs cover the same feature
- Documents have >70% content overlap
- Information is fragmented across files
- Documents describe the same system from different angles

**Don't merge when**:
- Documents serve different audiences (user vs developer)
- Documents are large and comprehensive
- Documents cover distinct aspects of a feature
- Separation improves navigation

### When to Delete Temporary Files

**Delete when**:
- Feature is complete and documented permanently
- Bug fix is resolved and changes are integrated
- Task is complete and no unique information remains
- Content is purely procedural (how we did it, not what we built)

**Consolidate when**:
- Temporary file contains unique technical insights
- Implementation details are valuable for developers
- Decisions and rationale should be preserved
- Content fills gaps in permanent documentation

### When to Update vs Rewrite

**Update when**:
- Core structure is sound
- Only specific details are outdated
- Changes are localized
- Document is well-organized

**Rewrite when**:
- Structure is confusing or illogical
- Major sections are obsolete
- Document doesn't match current reality
- Easier to start fresh than fix

## Audit Report Format

The audit will produce a markdown report documenting findings and changes:

```markdown
# Documentation Audit Report

Date: 2024-01-15

## Executive Summary

- Documents Reviewed: 75
- Issues Found: 45
- Issues Fixed: 40
- Remaining Issues: 5

## Changes Made

### Accuracy Improvements
- Updated 5 configuration examples
- Fixed 8 key binding references
- Corrected 3 CLI option descriptions

### Completeness Improvements
- Created 2 missing feature documents
- Added 10 undocumented configuration options
- Documented 5 missing key bindings

### Organization Improvements
- Removed 15 temporary files
- Merged 3 redundant documents
- Fixed 12 broken links
- Moved 4 misplaced files

## Remaining Issues

### High Priority
1. Feature X needs user documentation
2. Component Y needs developer documentation

### Medium Priority
1. Consider merging documents A and B
2. Update installation instructions

### Low Priority
1. Minor formatting inconsistencies
2. Optional cross-references to add

## Recommendations

1. Establish documentation review process
2. Update docs when features change
3. Clean up temp/ directory regularly
4. Maintain cross-reference accuracy
```

## Testing Strategy

Since this is an AI-driven process rather than automated code, testing focuses on verification:

### Manual Verification

**Sample Checks**:
- Verify a sample of configuration examples
- Check a sample of key binding updates
- Review a sample of link fixes
- Validate a sample of content updates

**Completeness Checks**:
- Verify major features are documented
- Check major components have dev docs
- Ensure critical config options are documented

**Organization Checks**:
- Verify file placement is correct
- Check naming conventions are followed
- Ensure temp/ directory is clean

### Review Process

**Before Changes**:
- Review audit findings
- Confirm issues are real
- Approve proposed changes

**After Changes**:
- Review all modifications
- Check for introduced errors
- Verify improvements are correct

**Final Validation**:
- Build and test TFM
- Review updated documentation
- Ensure nothing is broken

## Related Documents

- [Requirements Document](requirements.md)
- [Project File Placement Policy](.kiro/steering/project-file-placement.md)
- [TFM User Guide](../../doc/TFM_USER_GUIDE.md)
- [Project Structure](../../doc/dev/PROJECT_STRUCTURE.md)

# TFM → TTK Migration Requirements

## Introduction

This document specifies the requirements for migrating TFM (TUI File Manager) from direct curses usage to the TTK (TUI Toolkit) rendering library. The migration will enable TFM to run both as a terminal application (using TTK's CursesBackend) and as a native macOS desktop application (using TTK's CoreGraphicsBackend).

## Goals

1. **Maintain Functionality**: All existing TFM features must continue working
2. **Enable Desktop Mode**: TFM should run as a native macOS application
3. **Preserve Performance**: No significant performance degradation
4. **Gradual Migration**: Migrate component-by-component to maintain stability
5. **Clean Architecture**: Remove all direct curses dependencies

## Glossary

- **TTK Adapter**: A compatibility layer that provides curses-like interface using TTK
- **Renderer Instance**: TTK backend instance (CursesBackend or CoreGraphicsBackend)
- **Migration Phase**: A discrete step in the migration process
- **Component**: A TFM module or class (e.g., FileManager, PaneManager, dialogs)
- **Backend Selection**: Choosing between curses and CoreGraphics backends at runtime

## Requirements

### Requirement 1: Direct TTK API Usage

**User Story:** As a developer, I want TFM to use TTK's API directly, so that the code is clean and maintainable without unnecessary abstraction layers.

#### Acceptance Criteria

1. WHEN TFM is migrated THEN it SHALL use TTK's Renderer API directly without adapter layers
2. WHEN drawing text THEN the system SHALL use renderer.draw_text() instead of stdscr.addstr()
3. WHEN handling input THEN the system SHALL use TTK's InputEvent directly instead of curses key codes
4. WHEN managing colors THEN the system SHALL use TTK's RGB color pairs directly
5. WHEN the migration is complete THEN no curses-like wrapper code SHALL exist in TFM

### Requirement 2: Color System Migration

**User Story:** As a developer, I want to migrate TFM's color system to TTK, so that all color schemes work with both backends.

#### Acceptance Criteria

1. WHEN colors are initialized THEN the system SHALL use TTK's init_color_pair() instead of curses.init_pair()
2. WHEN color pairs are used THEN the system SHALL use TTK's color_pair parameter instead of curses.color_pair()
3. WHEN text attributes are applied THEN the system SHALL use TTK's TextAttribute instead of curses.A_* constants
4. WHEN color schemes are loaded THEN the system SHALL work identically with both backends
5. WHEN RGB colors are used THEN the system SHALL preserve exact colors in CoreGraphics backend

### Requirement 3: Input System Migration

**User Story:** As a developer, I want to migrate TFM's input handling to TTK, so that keyboard and mouse input work with both backends.

#### Acceptance Criteria

1. WHEN keyboard input is received THEN the system SHALL use TTK's InputEvent directly
2. WHEN special keys are pressed THEN the system SHALL use TTK's KeyCode enum instead of curses.KEY_* constants
3. WHEN modifier keys are detected THEN the system SHALL use TTK's ModifierKey flags
4. WHEN input timeout is needed THEN the system SHALL use renderer.get_input(timeout_ms) parameter
5. WHEN key bindings are checked THEN the system SHALL map InputEvent to TFM's key binding system

### Requirement 4: Rendering Migration

**User Story:** As a developer, I want to migrate TFM's rendering code to TTK, so that all UI components work with both backends.

#### Acceptance Criteria

1. WHEN text is drawn THEN the system SHALL use renderer.draw_text() instead of stdscr.addstr()
2. WHEN lines are drawn THEN the system SHALL use renderer.draw_hline() and draw_vline() instead of curses equivalents
3. WHEN rectangles are drawn THEN the system SHALL use renderer.draw_rect() instead of manual drawing
4. WHEN screen is cleared THEN the system SHALL use renderer.clear() instead of stdscr.clear()
5. WHEN screen is refreshed THEN the system SHALL use renderer.refresh() instead of stdscr.refresh()

### Requirement 5: Component Migration Order

**User Story:** As a developer, I want a clear migration order, so that I can migrate components systematically without breaking TFM.

#### Acceptance Criteria

1. WHEN migration begins THEN the system SHALL start with backend selection and entry point
2. WHEN entry point is updated THEN the system SHALL migrate tfm_colors.py to use RGB colors
3. WHEN colors are migrated THEN the system SHALL migrate tfm_main.py to use TTK Renderer
4. WHEN main is migrated THEN the system SHALL migrate individual UI components (dialogs, panes, etc.)
5. WHEN all components are migrated THEN the system SHALL remove all direct curses imports

### Requirement 6: Backend Selection

**User Story:** As a user, I want to choose between terminal and desktop modes, so that I can run TFM in my preferred environment.

#### Acceptance Criteria

1. WHEN TFM starts THEN the system SHALL default to CursesBackend for terminal mode
2. WHEN --backend coregraphics is specified THEN the system SHALL use CoreGraphicsBackend for desktop mode
3. WHEN --desktop flag is used THEN the system SHALL use CoreGraphicsBackend as shorthand
4. WHEN backend is selected THEN the system SHALL initialize the appropriate TTK backend
5. WHEN TFM runs THEN all features SHALL work identically regardless of backend

### Requirement 7: Backward Compatibility

**User Story:** As a user, I want TFM to continue working during migration, so that I can use it without interruption.

#### Acceptance Criteria

1. WHEN any migration phase completes THEN TFM SHALL remain fully functional
2. WHEN tests are run THEN all existing tests SHALL continue passing
3. WHEN TFM is launched THEN it SHALL start and run without errors
4. WHEN features are used THEN they SHALL behave identically to pre-migration behavior
5. WHEN migration is complete THEN no functionality SHALL be lost

### Requirement 8: Performance Preservation

**User Story:** As a user, I want TFM to remain fast after migration, so that my workflow is not impacted.

#### Acceptance Criteria

1. WHEN TFM renders UI THEN performance SHALL be equivalent to or better than curses-only version
2. WHEN large directories are displayed THEN rendering SHALL remain responsive
3. WHEN search operations run THEN UI updates SHALL not lag
4. WHEN CoreGraphics backend is used THEN rendering SHALL achieve 60 FPS
5. WHEN performance is measured THEN no operation SHALL be more than 10% slower than pre-migration

### Requirement 9: Testing Strategy

**User Story:** As a developer, I want comprehensive tests for the migration, so that I can verify correctness at each step.

#### Acceptance Criteria

1. WHEN adapter is created THEN unit tests SHALL verify curses compatibility
2. WHEN components are migrated THEN integration tests SHALL verify functionality
3. WHEN both backends are used THEN tests SHALL verify equivalent behavior
4. WHEN migration completes THEN all 720+ existing tests SHALL pass
5. WHEN new tests are added THEN they SHALL cover TTK-specific functionality

### Requirement 10: Documentation Updates

**User Story:** As a user and developer, I want updated documentation, so that I understand how to use desktop mode and how the architecture changed.

#### Acceptance Criteria

1. WHEN migration completes THEN README SHALL document desktop mode usage
2. WHEN architecture changes THEN developer docs SHALL explain TTK integration
3. WHEN backend selection is available THEN user guide SHALL explain options
4. WHEN troubleshooting is needed THEN docs SHALL cover both terminal and desktop modes
5. WHEN examples are provided THEN they SHALL show both backend usage patterns

### Requirement 11: Error Handling

**User Story:** As a user, I want clear error messages, so that I understand issues with backend selection or initialization.

#### Acceptance Criteria

1. WHEN CoreGraphics backend is unavailable THEN the system SHALL provide clear error message
2. WHEN backend initialization fails THEN the system SHALL fall back to CursesBackend gracefully
3. WHEN PyObjC is missing THEN the system SHALL explain how to install it
4. WHEN desktop mode is used on non-macOS THEN the system SHALL provide helpful error
5. WHEN errors occur THEN the system SHALL not crash but degrade gracefully

### Requirement 12: Configuration Integration

**User Story:** As a user, I want to configure my preferred backend, so that TFM remembers my choice.

#### Acceptance Criteria

1. WHEN configuration is loaded THEN the system SHALL support PREFERRED_BACKEND setting
2. WHEN backend preference is set THEN TFM SHALL use it by default
3. WHEN command-line flag is used THEN it SHALL override configuration
4. WHEN backend is invalid THEN the system SHALL fall back to CursesBackend
5. WHEN configuration is saved THEN backend preference SHALL persist

## Migration Phases

### Phase 1: Foundation (Tasks 1-8)
- Create backend selection mechanism
- Update tfm.py entry point to use TTK
- Migrate color system to RGB
- Update tfm_main.py to accept renderer

### Phase 2: Core Components (Tasks 9-16)
- Migrate tfm_main.py rendering to TTK API
- Migrate tfm_pane_manager.py to TTK API
- Migrate input handling to InputEvent
- Update key binding system

### Phase 3: UI Components (Tasks 17-30)
- Migrate dialogs (list, info, search, jump, drives, batch rename)
- Migrate text viewer
- Migrate quick choice bar
- Migrate single line text edit

### Phase 4: Cleanup (Tasks 31-38)
- Remove all curses imports and constants
- Update tests
- Update documentation
- Final verification

## Success Criteria

Migration is complete when:
1. ✅ All 720+ existing tests pass
2. ✅ TFM runs in terminal mode (CursesBackend) identically to pre-migration
3. ✅ TFM runs in desktop mode (CoreGraphicsBackend) on macOS
4. ✅ No direct curses imports remain in TFM code
5. ✅ Documentation is updated
6. ✅ Performance is preserved
7. ✅ All features work in both modes

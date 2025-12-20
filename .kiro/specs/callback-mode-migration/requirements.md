# Requirements Document

## Introduction

This specification defines the requirements for migrating the TTK library to callback-only mode by removing legacy polling mode support. The migration simplifies the architecture, eliminates dead code paths, and aligns with the IME support requirements that mandate callback mode.

## Glossary

- **TTK**: Terminal Toolkit - the underlying UI library used by TFM
- **TFM**: Terminal File Manager - the application built on TTK
- **Polling_Mode**: Legacy event delivery mechanism where the application calls `get_event()` to retrieve events synchronously
- **Callback_Mode**: Modern event delivery mechanism where events are delivered asynchronously via callback methods
- **EventCallback**: Interface defining callback methods for event delivery (on_key_event, on_char_event, etc.)
- **Renderer**: Abstract base class defining the TTK rendering and event interface
- **CoreGraphics_Backend**: macOS-specific implementation of the Renderer interface
- **IME**: Input Method Editor - system for entering complex characters (Japanese, Chinese, Korean)

## Requirements

### Requirement 1: Remove Polling Mode API

**User Story:** As a TTK maintainer, I want to remove the polling mode API, so that the codebase is simpler and easier to maintain.

#### Acceptance Criteria

1. THE Renderer SHALL NOT provide a `get_event()` method
2. THE Renderer SHALL NOT provide a `get_input()` method
3. THE CoreGraphics_Backend SHALL NOT implement a `get_event()` method
4. THE CoreGraphics_Backend SHALL NOT maintain an event queue for polling mode
5. WHEN the codebase is searched for `get_event()` or `get_input()` method calls, THEN no production code SHALL contain such calls

### Requirement 2: Require Event Callback

**User Story:** As a TTK developer, I want event callbacks to be mandatory, so that the event delivery mechanism is clear and consistent.

#### Acceptance Criteria

1. THE Renderer SHALL require an EventCallback to be set via `set_event_callback()` before running the event loop
2. WHEN `run_event_loop()` or `run_event_loop_iteration()` is called without a callback set, THEN the system SHALL raise an error
3. THE CoreGraphics_Backend SHALL always deliver events via the EventCallback
4. THE CoreGraphics_Backend SHALL NOT check if the callback is None before delivering events
5. WHEN `run_event_loop_iteration()` is called, THEN the system SHALL process pending events and deliver them via callbacks

### Requirement 3: Event Loop API

**User Story:** As a TTK developer, I want a clear API for running the event loop, so that I understand how events are processed and delivered.

#### Acceptance Criteria

1. THE Renderer SHALL provide a `run_event_loop()` method that blocks until the application quits
2. THE Renderer SHALL provide a `run_event_loop_iteration()` method that processes one iteration of events
3. WHEN `run_event_loop_iteration()` is called, THEN the system SHALL process pending OS events and deliver them via callbacks
4. THE event loop methods SHALL NOT return events directly
5. WHEN events occur during event loop execution, THEN they SHALL be delivered via the EventCallback methods

### Requirement 4: Simplify Event Delivery

**User Story:** As a TTK maintainer, I want event delivery to be straightforward, so that the code is easier to understand and debug.

#### Acceptance Criteria

1. WHEN a key event occurs in CoreGraphics_Backend, THEN the system SHALL deliver it directly via `event_callback.on_key_event()`
2. THE CoreGraphics_Backend SHALL NOT use conditional logic to choose between polling and callback modes
3. WHEN a character event occurs, THEN the system SHALL deliver it directly via `event_callback.on_char_event()`
4. THE event delivery path SHALL NOT include event queue management code

### Requirement 5: Update TFM Application

**User Story:** As a TFM developer, I want TFM to use the simplified callback-only API, so that the application code is cleaner.

#### Acceptance Criteria

1. THE TFM_Main SHALL NOT call `get_event()` or `get_input()` methods
2. THE TFM_Main SHALL set an event callback during initialization
3. THE TFM_Main SHALL NOT have `enable_callback_mode()` or `disable_callback_mode()` methods
4. THE TFM_Main SHALL NOT have a `callback_mode_enabled` instance variable

### Requirement 6: Update Test Files

**User Story:** As a test developer, I want test files to use callback mode, so that tests reflect the actual production usage.

#### Acceptance Criteria

1. WHEN a test needs to capture events, THEN the test SHALL use an EventCallback implementation
2. THE test utilities SHALL provide helper classes for event capture in callback mode
3. WHEN all tests are executed, THEN no test SHALL call `get_event()` or `get_input()` methods
4. THE test suite SHALL pass with 100% of tests using callback mode

### Requirement 7: Update Demo Scripts

**User Story:** As a developer learning TTK, I want demo scripts to show callback mode usage, so that I understand the correct API patterns.

#### Acceptance Criteria

1. WHEN a demo script runs, THEN it SHALL use callback mode for event delivery
2. THE demo scripts SHALL NOT call `get_event()` or `get_input()` methods
3. WHEN all demo scripts are executed, THEN they SHALL demonstrate callback mode patterns
4. THE demo scripts SHALL provide clear examples of EventCallback implementation

### Requirement 8: Update Documentation

**User Story:** As a TTK user, I want documentation to reflect callback-only mode, so that I'm not confused by outdated polling mode examples.

#### Acceptance Criteria

1. THE TTK documentation SHALL NOT contain examples using `get_event()` or `get_input()`
2. THE TTK documentation SHALL provide clear examples of callback mode usage
3. THE developer documentation SHALL explain the callback-only architecture
4. WHEN documentation mentions event handling, THEN it SHALL describe callback mode exclusively

### Requirement 9: Maintain IME Functionality

**User Story:** As a user entering Japanese/Chinese/Korean text, I want IME to continue working correctly, so that I can input complex characters.

#### Acceptance Criteria

1. WHEN IME composition is active, THEN the system SHALL handle it correctly via callback mode
2. THE CoreGraphics_Backend SHALL call `interpretKeyEvents_()` for unconsumed key events
3. WHEN IME generates composed text, THEN the system SHALL deliver it via `on_char_event()`
4. THE IME candidate window SHALL position correctly during composition

### Requirement 10: Preserve Existing Functionality

**User Story:** As a TFM user, I want all existing features to work after migration, so that my workflow is not disrupted.

#### Acceptance Criteria

1. WHEN the migration is complete, THEN all TFM key bindings SHALL work correctly
2. WHEN the migration is complete, THEN all TFM dialogs SHALL function properly
3. WHEN the migration is complete, THEN all TFM file operations SHALL execute correctly
4. THE existing test suite SHALL pass with no regressions

### Requirement 11: Code Simplification

**User Story:** As a TTK maintainer, I want the codebase to be simpler after migration, so that maintenance is easier.

#### Acceptance Criteria

1. WHEN the migration is complete, THEN at least 400 lines of code SHALL be removed
2. THE CoreGraphics_Backend `keyDown_()` method SHALL NOT contain conditional logic for callback mode
3. THE Renderer interface SHALL be simpler with fewer methods
4. THE codebase SHALL NOT contain dead code paths for polling mode

### Requirement 12: Backward Compatibility Handling

**User Story:** As a TTK maintainer, I want to handle any external dependencies gracefully, so that the migration doesn't break external code.

#### Acceptance Criteria

1. WHEN external TTK users are identified, THEN a migration guide SHALL be provided
2. IF no external users exist, THEN polling mode SHALL be removed immediately without deprecation
3. THE migration SHALL document breaking changes clearly
4. THE version number SHALL be incremented to reflect breaking changes
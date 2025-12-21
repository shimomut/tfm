# Requirements Document

## Introduction

The TFM file manager currently uses multiple if-elif blocks in tfm_main.py to handle different dialog UIs, making the code difficult to maintain and extend. This feature introduces a dynamic UI layer stack system where layers are managed in a stack structure, with proper event routing and intelligent rendering optimization.

## Glossary

- **UI_Layer_Stack**: A dynamic stack data structure that manages all UI layers in the application
- **Layer**: A UI component that can receive events and render content (e.g., FileManager main screen, dialogs, viewers)
- **Top_Layer**: The layer at the top of the stack that receives all input events
- **Bottom_Layer**: The FileManager main screen, which is always present at the bottom of the stack
- **Full_Screen_Layer**: A layer that occupies the entire terminal screen (e.g., TextViewer, DiffViewer)
- **Event_Routing**: The process of directing keyboard and character events to the appropriate layer
- **Render_Suppression**: The optimization technique where full-screen layers prevent unnecessary rendering of lower layers
- **GeneralPurposeDialog**: A UI component that is part of the main screen, not a separate layer

## Requirements

### Requirement 1: UI Layer Stack Management

**User Story:** As a developer, I want a dynamic stack structure to manage UI layers, so that I can easily add, remove, and navigate between different UI components without complex conditional logic.

#### Acceptance Criteria

1. THE UI_Layer_Stack SHALL maintain layers in a stack data structure with LIFO (Last In, First Out) ordering
2. WHEN the application starts, THE UI_Layer_Stack SHALL initialize with the FileManager main screen as the Bottom_Layer
3. WHEN a new layer is added, THE UI_Layer_Stack SHALL push it onto the top of the stack
4. WHEN a layer is closed, THE UI_Layer_Stack SHALL pop it from the stack and activate the layer below
5. THE UI_Layer_Stack SHALL provide methods to query the current Top_Layer
6. THE UI_Layer_Stack SHALL prevent removal of the Bottom_Layer (FileManager main screen)

### Requirement 2: Event Routing to Top Layer

**User Story:** As a user, I want my keyboard input to go to the currently active UI component, so that I can interact with dialogs and viewers without confusion.

#### Acceptance Criteria

1. WHEN a key event occurs, THE UI_Layer_Stack SHALL route it to the Top_Layer
2. WHEN a character event occurs, THE UI_Layer_Stack SHALL route it to the Top_Layer
3. WHEN the Top_Layer handles an event, THE UI_Layer_Stack SHALL not propagate the event to lower layers
4. IF the Top_Layer does not handle an event, THEN THE UI_Layer_Stack SHALL propagate the event to the next layer below
5. THE UI_Layer_Stack SHALL continue event propagation until a layer handles the event or the Bottom_Layer is reached

### Requirement 3: Layer-Based Rendering with Dirty Tracking

**User Story:** As a developer, I want the rendering system to respect layer ordering and only redraw layers with changed content, so that the UI displays correctly and performs efficiently.

#### Acceptance Criteria

1. WHEN rendering the screen, THE UI_Layer_Stack SHALL render layers from bottom to top
2. WHEN a layer is rendered, THE UI_Layer_Stack SHALL ensure it draws over any previously rendered layers
3. THE UI_Layer_Stack SHALL provide each layer with the necessary rendering context
4. WHEN a layer's content changes, THE Layer SHALL mark itself as dirty (needs redraw)
5. WHEN rendering, THE UI_Layer_Stack SHALL only render layers that are marked as dirty
6. WHEN a layer is rendered, THE UI_Layer_Stack SHALL mark all layers above it as dirty
7. WHEN a layer is successfully rendered, THE UI_Layer_Stack SHALL clear its dirty flag
8. THE UI_Layer_Stack SHALL coordinate with the terminal backend to ensure proper screen updates

### Requirement 4: Full-Screen Layer Optimization

**User Story:** As a developer, I want full-screen layers to suppress rendering of lower layers, so that the application performs efficiently without wasting CPU cycles on invisible content.

#### Acceptance Criteria

1. WHEN a Full_Screen_Layer is on the stack, THE UI_Layer_Stack SHALL mark it as obscuring all layers below
2. WHEN rendering with a Full_Screen_Layer present, THE UI_Layer_Stack SHALL skip rendering of all layers below the topmost Full_Screen_Layer
3. WHEN a Full_Screen_Layer is removed, THE UI_Layer_Stack SHALL resume rendering of previously suppressed layers
4. THE UI_Layer_Stack SHALL provide a method for layers to declare themselves as full-screen
5. THE UI_Layer_Stack SHALL optimize rendering by only processing visible layers

### Requirement 5: Layer Interface Definition

**User Story:** As a developer, I want a clear interface for UI layers, so that I can implement new layers consistently and integrate them seamlessly into the stack system.

#### Acceptance Criteria

1. THE Layer interface SHALL define a method for handling key events
2. THE Layer interface SHALL define a method for handling character events
3. THE Layer interface SHALL define a method for rendering the layer
4. THE Layer interface SHALL define a method to query if the layer is full-screen
5. THE Layer interface SHALL define a method to query if the layer needs redrawing
6. THE Layer interface SHALL define a method to mark the layer as dirty (needs redraw)
7. THE Layer interface SHALL define a method to clear the dirty flag after rendering
8. THE Layer interface SHALL define a method to query if the layer should close
9. THE Layer interface SHALL define lifecycle methods for activation and deactivation

### Requirement 6: Integration with Existing Components

**User Story:** As a developer, I want existing UI components to integrate with the layer stack system, so that I can migrate the codebase incrementally without breaking existing functionality.

#### Acceptance Criteria

1. WHEN integrating TextViewer, THE UI_Layer_Stack SHALL treat it as a Full_Screen_Layer
2. WHEN integrating DiffViewer, THE UI_Layer_Stack SHALL treat it as a Full_Screen_Layer
3. WHEN integrating dialogs (JumpDialog, SearchDialog, etc.), THE UI_Layer_Stack SHALL treat them as regular layers
4. THE FileManager main screen SHALL remain as the Bottom_Layer and continue functioning normally
5. THE GeneralPurposeDialog SHALL remain part of the FileManager main screen, not a separate layer
6. THE UI_Layer_Stack SHALL maintain backward compatibility with existing event handling patterns

### Requirement 7: Removal of Conditional Logic

**User Story:** As a developer, I want to eliminate complex if-elif blocks in tfm_main.py, so that the code is more maintainable and easier to understand.

#### Acceptance Criteria

1. WHEN the layer stack system is implemented, THE tfm_main.py SHALL remove if-elif blocks for dialog type checking
2. THE tfm_main.py SHALL delegate event routing decisions to the UI_Layer_Stack
3. THE tfm_main.py SHALL delegate rendering decisions to the UI_Layer_Stack
4. THE refactored code SHALL have fewer lines of code than the original implementation
5. THE refactored code SHALL have lower cyclomatic complexity than the original implementation

### Requirement 8: Layer State Management

**User Story:** As a developer, I want layers to manage their own state independently, so that each UI component is self-contained and easier to test.

#### Acceptance Criteria

1. WHEN a layer is activated, THE Layer SHALL receive a notification to initialize its state
2. WHEN a layer is deactivated, THE Layer SHALL receive a notification to clean up its state
3. THE Layer SHALL maintain its own internal state without relying on global variables
4. WHEN a layer is pushed onto the stack, THE UI_Layer_Stack SHALL preserve the state of layers below
5. WHEN a layer is popped from the stack, THE UI_Layer_Stack SHALL restore the state of the layer below

### Requirement 9: Error Handling and Edge Cases

**User Story:** As a developer, I want the layer stack system to handle errors gracefully, so that the application remains stable even when unexpected conditions occur.

#### Acceptance Criteria

1. IF a layer raises an exception during event handling, THEN THE UI_Layer_Stack SHALL log the error and prevent the exception from crashing the application
2. IF a layer raises an exception during rendering, THEN THE UI_Layer_Stack SHALL log the error and attempt to render other layers
3. WHEN the stack becomes empty (except for Bottom_Layer), THE UI_Layer_Stack SHALL ensure the FileManager main screen remains active
4. IF an attempt is made to remove the Bottom_Layer, THEN THE UI_Layer_Stack SHALL reject the operation and log a warning
5. THE UI_Layer_Stack SHALL validate layer operations and provide clear error messages for invalid operations

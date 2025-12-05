"""
Qt Color Scheme Manager for TFM

This module provides color scheme support for the Qt GUI backend,
mapping TFM color definitions to Qt colors and stylesheets.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# Add src directory to path if needed
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from tfm_colors import COLOR_SCHEMES


def rgb_to_qcolor(rgb: Tuple[int, int, int]) -> QColor:
    """
    Convert RGB tuple to QColor.
    
    Args:
        rgb: RGB tuple (r, g, b) with values 0-255
        
    Returns:
        QColor object
    """
    return QColor(rgb[0], rgb[1], rgb[2])


def get_qt_colors(scheme: str = 'dark') -> Dict[str, QColor]:
    """
    Get Qt colors for the specified color scheme.
    
    Args:
        scheme: Color scheme name ('dark' or 'light')
        
    Returns:
        Dictionary mapping color names to QColor objects
    """
    if scheme not in COLOR_SCHEMES:
        scheme = 'dark'
    
    scheme_colors = COLOR_SCHEMES[scheme]
    qt_colors = {}
    
    for color_name, color_def in scheme_colors.items():
        rgb = color_def['rgb']
        qt_colors[color_name] = rgb_to_qcolor(rgb)
    
    return qt_colors


def get_file_color(file_type: str, scheme: str = 'dark') -> QColor:
    """
    Get color for a specific file type.
    
    Args:
        file_type: File type ('directory', 'executable', 'regular', 'symlink')
        scheme: Color scheme name
        
    Returns:
        QColor for the file type
    """
    colors = get_qt_colors(scheme)
    
    if file_type == 'directory':
        return colors.get('DIRECTORY_FG', QColor(100, 149, 237))
    elif file_type == 'executable':
        return colors.get('EXECUTABLE_FG', QColor(50, 205, 50))
    elif file_type == 'symlink':
        return QColor(0, 255, 255)  # Cyan for symlinks
    else:
        return colors.get('REGULAR_FILE_FG', QColor(220, 220, 220))


def get_stylesheet(scheme: str = 'dark') -> str:
    """
    Generate Qt stylesheet for the specified color scheme.
    
    Args:
        scheme: Color scheme name
        
    Returns:
        Qt stylesheet string
    """
    colors = get_qt_colors(scheme)
    
    # Get key colors
    default_fg = colors.get('DEFAULT_FG', QColor(220, 220, 220))
    default_bg = colors.get('DEFAULT_BG', QColor(0, 0, 0))
    header_bg = colors.get('HEADER_BG', QColor(51, 63, 76))
    footer_bg = colors.get('FOOTER_BG', QColor(51, 63, 76))
    selected_bg = colors.get('SELECTED_BG', QColor(40, 80, 160))
    selected_inactive_bg = colors.get('SELECTED_INACTIVE_BG', QColor(80, 80, 80))
    
    # Build stylesheet
    stylesheet = f"""
    QMainWindow {{
        background-color: {default_bg.name()};
        color: {default_fg.name()};
    }}
    
    QTableWidget {{
        background-color: {default_bg.name()};
        color: {default_fg.name()};
        gridline-color: {header_bg.name()};
        selection-background-color: {selected_bg.name()};
        selection-color: {default_fg.name()};
    }}
    
    QTableWidget::item:selected {{
        background-color: {selected_bg.name()};
    }}
    
    QHeaderView::section {{
        background-color: {header_bg.name()};
        color: {default_fg.name()};
        padding: 4px;
        border: 1px solid {header_bg.darker(120).name()};
    }}
    
    QLabel {{
        color: {default_fg.name()};
    }}
    
    QTextEdit {{
        background-color: {default_bg.name()};
        color: {default_fg.name()};
    }}
    
    QStatusBar {{
        background-color: {footer_bg.name()};
        color: {default_fg.name()};
    }}
    
    QMenuBar {{
        background-color: {header_bg.name()};
        color: {default_fg.name()};
    }}
    
    QMenuBar::item:selected {{
        background-color: {selected_bg.name()};
    }}
    
    QMenu {{
        background-color: {default_bg.name()};
        color: {default_fg.name()};
    }}
    
    QMenu::item:selected {{
        background-color: {selected_bg.name()};
    }}
    
    QToolBar {{
        background-color: {header_bg.name()};
        border: none;
    }}
    
    QDialog {{
        background-color: {default_bg.name()};
        color: {default_fg.name()};
    }}
    
    QPushButton {{
        background-color: {header_bg.name()};
        color: {default_fg.name()};
        border: 1px solid {header_bg.darker(120).name()};
        padding: 5px 15px;
        border-radius: 3px;
    }}
    
    QPushButton:hover {{
        background-color: {header_bg.lighter(120).name()};
    }}
    
    QPushButton:pressed {{
        background-color: {selected_bg.name()};
    }}
    
    QLineEdit {{
        background-color: {default_bg.lighter(110).name()};
        color: {default_fg.name()};
        border: 1px solid {header_bg.name()};
        padding: 3px;
    }}
    
    QProgressBar {{
        border: 1px solid {header_bg.name()};
        border-radius: 3px;
        text-align: center;
        background-color: {default_bg.lighter(110).name()};
    }}
    
    QProgressBar::chunk {{
        background-color: {selected_bg.name()};
    }}
    """
    
    return stylesheet


def apply_color_scheme(app: QApplication, scheme: str = 'dark'):
    """
    Apply color scheme to the Qt application.
    
    Args:
        app: QApplication instance
        scheme: Color scheme name
    """
    stylesheet = get_stylesheet(scheme)
    app.setStyleSheet(stylesheet)

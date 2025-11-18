# Lazy Loading Refactor: Settings File Implementation

## Overview

This document describes the refactoring of the file-based settings implementation to introduce lazy loading and rename classes for better code organization.

## Changes Made

### 1. Class Renames

#### `FileSetting` → `SettingImpl`
- **Reason**: Clear, descriptive name for the implementation class
- **Scope**: Public API, exported from `fivcplayground.implements`
- **Impact**: Users should update imports from `FileSetting` to `SettingImpl`

#### `FileSettingsProvider` → `SettingProviderImpl`
- **Reason**: Impl suffix indicates this is a concrete implementation
- **Scope**: Public API, exported from `fivcplayground.implements`
- **Impact**: Users should update imports from `FileSettingsProvider` to `SettingProviderImpl`

### 2. Lazy Loading Implementation

#### Before
```python
def __init__(self, component_site: IComponentSite, config_file: str = "settings.yaml"):
    self.component_site = component_site
    self.config_file = os.path.abspath(os.path.join(os.getcwd(), config_file))
    self.settings_data = {}
    self._load_config()  # Loaded immediately
```

#### After
```python
def __init__(self, component_site: IComponentSite, config_file: str = "settings.yaml"):
    self.component_site = component_site
    self.config_file = os.path.abspath(os.path.join(os.getcwd(), config_file))
    self.settings_data = None  # None indicates not yet loaded
    self._loaded = False
```

#### New Method: `_ensure_loaded()`
```python
def _ensure_loaded(self) -> None:
    """Ensure configuration is loaded (lazy loading)."""
    if self._loaded:
        return
    
    ext = self.config_file.split(".")[-1].lower()
    if ext in ["yml", "yaml"]:
        self.settings_data = self._load_yaml_file(self.config_file)
    elif ext == "json":
        self.settings_data = self._load_json_file(self.config_file)
    else:
        self.settings_data = {}
    
    self._loaded = True
```

#### Updated Methods
- `get_setting()`: Calls `_ensure_loaded()` before accessing settings
- `list_settings()`: Calls `_ensure_loaded()` before iterating settings

### 3. Benefits of Lazy Loading

1. **Performance**: Configuration file is only loaded when needed
2. **Flexibility**: Allows initialization without file I/O
3. **Caching**: File is loaded only once, subsequent calls use cached data
4. **Transparent**: Users don't need to know about lazy loading

### 4. Updated Exports

**File**: `src/fivcplayground/implements/__init__.py`

```python
__all__ = [
    "SettingProviderImpl",
    "SettingImpl",
]

from .settings_file import SettingProviderImpl, SettingImpl
```

### 5. Test Updates

**File**: `tests/test_settings_file.py`

- Updated class names: `TestFileSetting` → `TestSettingImpl`
- Updated class names: `TestFileSettingsProvider` → `TestSettingProviderImpl`
- Updated all imports to use new class names
- Updated tests to trigger lazy loading before checking `settings_data`

## Test Results

✅ **All 43 tests passing**
- 26 existing Config tests
- 17 file-based settings tests

## Migration Guide

### For Users

If you were importing the old classes:

```python
# Old
from fivcplayground.implements import FileSetting, FileSettingsProvider

# New
from fivcplayground.implements import SettingImpl, SettingProviderImpl
```

However, it's recommended to use the interfaces instead:

```python
from fivcplayground.interfaces import ISetting, ISettingProvider
```

### For Component Registration

```python
from fivcplayground.implements import SettingProviderImpl
from fivcglue.implements.utils import ComponentSite

site = ComponentSite()
provider = SettingProviderImpl(site, "settings.yaml")
site.register_component(ISettingProvider, provider)
```

## Backward Compatibility

⚠️ **Breaking Change**: Class names have changed
- `FileSetting` → `SettingImpl`
- `FileSettingsProvider` → `SettingProviderImpl`

✅ **Preserved**: All functionality remains the same
- Same interface contracts
- Same behavior
- Same error handling

## Implementation Details

### Lazy Loading State

The provider maintains two state variables:
- `settings_data`: The loaded configuration (None until loaded)
- `_loaded`: Boolean flag indicating if configuration has been loaded

### Thread Safety

⚠️ **Note**: Current implementation is not thread-safe. If concurrent access is needed, consider adding locks to `_ensure_loaded()`.

## Future Enhancements

1. Thread-safe lazy loading with locks
2. Configuration reload capability
3. File watching for automatic reloads
4. Caching strategies for large configurations


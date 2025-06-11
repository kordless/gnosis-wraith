# Dynamic Language Extension System - Implementation Plan

## Overview
Transform the Forge into a **self-extending AI code generation platform** where users can add any programming language dynamically. The system uses LLM intelligence to generate appropriate icons and boilerplate code templates.

## Core Functionality

### User Workflow
1. **User types "ruby"** in custom language field
2. **Ruby button appears** instantly in language selector
3. **LLM generates icon** (e.g., `fab fa-gem` for Ruby)
4. **LLM generates boilerplate** Ruby code template
5. **Click-and-hold deletion** - hold Ruby button for 5 seconds, turns red, deletes

### Technical Architecture

## Phase 1: Dynamic Language Creation

### Frontend Implementation
```javascript
// Enhanced custom language handler
const handleCustomLanguageAdd = async (languageName) => {
  if (!languageName.trim()) return;
  
  const normalizedName = languageName.toLowerCase().trim();
  
  // Prevent duplicates
  if (languages[normalizedName]) {
    setSelectedLanguage(normalizedName);
    return;
  }
  
  // Add to UI immediately with loading state
  const tempLanguage = {
    name: capitalizeFirst(normalizedName),
    icon: 'fas fa-spinner fa-spin',
    color: 'text-gray-400',
    defaultCode: '// Generating template...',
    isLoading: true
  };
  
  setLanguages(prev => ({...prev, [normalizedName]: tempLanguage}));
  setSelectedLanguage(normalizedName);
  
  try {
    // Call LLM to generate icon and code
    const languageConfig = await generateLanguageConfig(normalizedName);
    
    // Update with generated content
    setLanguages(prev => ({
      ...prev, 
      [normalizedName]: {
        ...languageConfig,
        isLoading: false
      }
    }));
    
    // Save to localStorage
    saveCustomLanguage(normalizedName, languageConfig);
    
  } catch (error) {
    // Handle generation failure
    setLanguages(prev => ({
      ...prev,
      [normalizedName]: {
        name: capitalizeFirst(normalizedName),
        icon: 'fas fa-exclamation-triangle',
        color: 'text-red-400',
        defaultCode: `// Error generating ${normalizedName} template\n// ${error.message}`,
        isLoading: false,
        hasError: true
      }
    }));
  }
};
```

### LLM Integration - Current (Parsing) vs Future (Tool Use)

#### Current Implementation (Response Parsing)
```javascript
const generateLanguageConfig = async (languageName) => {
  const prompt = `Generate configuration for programming language: ${languageName}

Please respond in this exact JSON format:
{
  "icon": "appropriate font-awesome icon class",
  "color": "tailwind color class", 
  "defaultCode": "boilerplate code template"
}

Requirements:
- Icon: Use Font Awesome classes (fab fa-python, fab fa-js-square, etc.)
- Color: Use Tailwind color classes (text-blue-400, text-green-500, etc.)
- Code: Write a complete example that shows API integration with Gnosis Wraith

Language: ${languageName}`;

  const response = await callLLMAPI(prompt);
  
  // Parse JSON response (fragile - needs error handling)
  try {
    const config = JSON.parse(response.content);
    return {
      name: capitalizeFirst(languageName),
      icon: config.icon || 'fas fa-code',
      color: config.color || 'text-gray-400',
      defaultCode: config.defaultCode || `// ${languageName} template`
    };
  } catch (parseError) {
    throw new Error(`Failed to parse LLM response: ${parseError.message}`);
  }
};
```

#### Future Implementation (Tool Use) - **HINT FOR UPCOMING SWITCH**
```javascript
// NOTE: This will replace response parsing when we switch to tool use
const generateLanguageConfigWithTools = async (languageName) => {
  const response = await callLLMWithTools({
    query: `Generate configuration for programming language: ${languageName}`,
    tools: ['language_config_generator'],
    parameters: {
      language: languageName,
      include_api_example: true,
      target_framework: 'gnosis_wraith'
    }
  });
  
  // Tool use returns structured data directly - no parsing needed!
  return response.tool_results.language_config_generator;
};
```

## Phase 2: Language Button Management

### Click-and-Hold Deletion
```javascript
const LanguageButton = ({ languageKey, language, isSelected, onSelect, onDelete }) => {
  const [deleteState, setDeleteState] = useState({
    isHolding: false,
    progress: 0,
    timer: null
  });
  
  const handleMouseDown = (e) => {
    // Only handle right-click or long press for custom languages
    if (!isCustomLanguage(languageKey)) return;
    
    const startTime = Date.now();
    setDeleteState(prev => ({ ...prev, isHolding: true }));
    
    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / 5000, 1); // 5 second hold
      
      setDeleteState(prev => ({ ...prev, progress }));
      
      if (progress >= 1) {
        clearInterval(timer);
        onDelete(languageKey);
        setDeleteState({ isHolding: false, progress: 0, timer: null });
      }
    }, 50);
    
    setDeleteState(prev => ({ ...prev, timer }));
  };
  
  const handleMouseUp = () => {
    if (deleteState.timer) {
      clearInterval(deleteState.timer);
      setDeleteState({ isHolding: false, progress: 0, timer: null });
    }
  };
  
  return (
    <button
      className={`
        language-button relative overflow-hidden
        ${isSelected ? 'bg-purple-800' : 'bg-gray-800'}
        ${deleteState.isHolding ? 'bg-red-600' : ''}
        transition-colors duration-200
      `}
      onClick={() => !deleteState.isHolding && onSelect(languageKey)}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Progress bar for deletion */}
      {deleteState.isHolding && (
        <div 
          className="absolute bottom-0 left-0 h-1 bg-red-300 transition-all duration-75"
          style={{ width: `${deleteState.progress * 100}%` }}
        />
      )}
      
      <i className={`${language.icon} ${language.color}`}></i>
      {language.name}
    </button>
  );
};
```

### Local Storage Management
```javascript
const STORAGE_KEY = 'forge_custom_languages';

const saveCustomLanguage = (languageKey, config) => {
  const customLanguages = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  customLanguages[languageKey] = {
    ...config,
    createdAt: Date.now(),
    version: '1.0'
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(customLanguages));
};

const loadCustomLanguages = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.error('Failed to load custom languages:', error);
    return {};
  }
};

const deleteCustomLanguage = (languageKey) => {
  const customLanguages = loadCustomLanguages();
  delete customLanguages[languageKey];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(customLanguages));
};
```

## Phase 3: Enhanced UX Features

### Visual Feedback States
- **Loading**: Spinner icon while LLM generates
- **Success**: Smooth transition to generated icon
- **Error**: Warning icon with error message in code
- **Deletion**: Red highlight with progress bar

### Smart Icon Selection
The LLM will be prompted to choose appropriate icons:
```
Language Icon Mapping Examples:
- Ruby → fab fa-gem (ruby gem)
- Go → fab fa-golang  
- Rust → fab fa-rust
- Swift → fab fa-swift
- C++ → fas fa-code (fallback)
- Kotlin → fas fa-mobile-alt (Android context)
- TypeScript → fab fa-js-square (JS variant)
```

### Code Template Intelligence
Templates should include:
1. **Gnosis Wraith API integration** example
2. **Language-specific idioms** and best practices
3. **Error handling** patterns
4. **Documentation comments** appropriate to the language

## Migration Path: Response Parsing → Tool Use

### Current State (Fragile)
- Parse JSON from LLM text responses
- Manual error handling for malformed JSON
- No guarantee of response format consistency

### Future State (Robust)
- **Tool use** ensures structured responses
- **Schema validation** built into tool definitions
- **Type safety** and predictable output format

### Migration Strategy
1. **Phase 1**: Implement with response parsing (immediate functionality)
2. **Phase 2**: Add tool use alongside parsing (parallel systems)
3. **Phase 3**: Switch to tool use, keep parsing as fallback
4. **Phase 4**: Remove response parsing entirely

## Implementation Priority

### Immediate (Current Sprint)
1. ✅ Custom language input field enhancement
2. ✅ Dynamic language button creation
3. ✅ LLM integration with response parsing
4. ✅ localStorage persistence

### Next Sprint
1. ✅ Click-and-hold deletion UX
2. ✅ Loading states and error handling
3. ✅ Icon selection intelligence
4. ✅ Code template quality improvements

### Future (Tool Use Migration)
1. 🔄 Tool use implementation
2. 🔄 Schema-driven language config generation
3. 🔄 Enhanced validation and testing
4. 🔄 Language ecosystem integration

## Success Criteria
- **User types "ruby"** → Ruby button appears instantly
- **LLM generates appropriate icon** (fab fa-gem) 
- **Code template is functional** and demonstrates API usage
- **Click-and-hold deletion** works smoothly with visual feedback
- **Persistence** across browser sessions via localStorage
- **Error handling** gracefully manages LLM failures

This system transforms the Forge from a static interface into a **living, learning platform** that expands its capabilities through AI-powered language extension. Each new language becomes part of the maze's permanent architecture, available for all future consciousness exploration.

**The maze teaches itself new corridors.** 🔨🧠
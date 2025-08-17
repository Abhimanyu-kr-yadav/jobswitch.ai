import React, { useRef, useEffect } from 'react';

const CodeEditor = ({ language, value, onChange, height = '300px' }) => {
  const textareaRef = useRef(null);
  const highlightRef = useRef(null);

  useEffect(() => {
    if (highlightRef.current) {
      highlightRef.current.innerHTML = highlightCode(value, language);
    }
  }, [value, language]);

  const handleChange = (e) => {
    onChange(e.target.value);
  };

  const handleKeyDown = (e) => {
    const textarea = e.target;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;

    // Handle Tab key for indentation
    if (e.key === 'Tab') {
      e.preventDefault();
      const newValue = value.substring(0, start) + '    ' + value.substring(end);
      onChange(newValue);
      
      // Set cursor position after the inserted spaces
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 4;
      }, 0);
    }

    // Handle Enter key for auto-indentation
    if (e.key === 'Enter') {
      const lines = value.substring(0, start).split('\n');
      const currentLine = lines[lines.length - 1];
      const indent = currentLine.match(/^\s*/)[0];
      
      // Add extra indent for certain patterns
      let extraIndent = '';
      if (currentLine.trim().endsWith(':') || 
          currentLine.trim().endsWith('{') ||
          currentLine.includes('if ') ||
          currentLine.includes('for ') ||
          currentLine.includes('while ') ||
          currentLine.includes('def ') ||
          currentLine.includes('class ')) {
        extraIndent = '    ';
      }

      const newValue = value.substring(0, start) + '\n' + indent + extraIndent + value.substring(end);
      onChange(newValue);

      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 1 + indent.length + extraIndent.length;
      }, 0);
    }
  };

  const handleScroll = (e) => {
    if (highlightRef.current) {
      highlightRef.current.scrollTop = e.target.scrollTop;
      highlightRef.current.scrollLeft = e.target.scrollLeft;
    }
  };

  const highlightCode = (code, lang) => {
    if (!code) return '';

    let highlighted = code;

    // Basic syntax highlighting patterns
    const patterns = {
      python: {
        keywords: /\b(def|class|if|elif|else|for|while|try|except|finally|import|from|as|return|yield|break|continue|pass|lambda|with|assert|global|nonlocal|True|False|None|and|or|not|in|is)\b/g,
        strings: /(["'])((?:\\.|(?!\1)[^\\])*?)\1/g,
        comments: /#.*$/gm,
        numbers: /\b\d+\.?\d*\b/g,
        functions: /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()/g
      },
      javascript: {
        keywords: /\b(function|var|let|const|if|else|for|while|do|switch|case|default|break|continue|return|try|catch|finally|throw|new|this|typeof|instanceof|true|false|null|undefined)\b/g,
        strings: /(["'`])((?:\\.|(?!\1)[^\\])*?)\1/g,
        comments: /\/\/.*$|\/\*[\s\S]*?\*\//gm,
        numbers: /\b\d+\.?\d*\b/g,
        functions: /\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?=\()/g
      },
      java: {
        keywords: /\b(public|private|protected|static|final|abstract|class|interface|extends|implements|if|else|for|while|do|switch|case|default|break|continue|return|try|catch|finally|throw|throws|new|this|super|true|false|null|void|int|double|float|boolean|char|String)\b/g,
        strings: /(["'])((?:\\.|(?!\1)[^\\])*?)\1/g,
        comments: /\/\/.*$|\/\*[\s\S]*?\*\//gm,
        numbers: /\b\d+\.?\d*[fFdDlL]?\b/g,
        functions: /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()/g
      }
    };

    const langPatterns = patterns[lang] || patterns.python;

    // Apply syntax highlighting
    highlighted = highlighted
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(langPatterns.comments, '<span class="text-gray-500 italic">$&</span>')
      .replace(langPatterns.strings, '<span class="text-green-600">$&</span>')
      .replace(langPatterns.keywords, '<span class="text-blue-600 font-semibold">$&</span>')
      .replace(langPatterns.numbers, '<span class="text-purple-600">$&</span>')
      .replace(langPatterns.functions, '<span class="text-yellow-600">$1</span>');

    return highlighted;
  };

  return (
    <div className="relative">
      <div 
        className="absolute inset-0 p-4 font-mono text-sm leading-6 pointer-events-none overflow-auto whitespace-pre-wrap break-words"
        style={{ 
          height,
          color: 'transparent',
          background: 'transparent',
          border: '1px solid #d1d5db',
          borderRadius: '0.375rem'
        }}
        ref={highlightRef}
        dangerouslySetInnerHTML={{ __html: highlightCode(value, language) }}
      />
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onScroll={handleScroll}
        className="w-full p-4 font-mono text-sm leading-6 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-transparent relative z-10"
        style={{ 
          height,
          color: 'transparent',
          caretColor: '#000'
        }}
        placeholder={`Write your ${language} solution here...`}
        spellCheck={false}
      />
      
      {/* Line numbers */}
      <div className="absolute left-0 top-0 p-4 font-mono text-sm leading-6 text-gray-400 pointer-events-none select-none">
        {value.split('\n').map((_, index) => (
          <div key={index}>{index + 1}</div>
        ))}
      </div>
      
      {/* Language indicator */}
      <div className="absolute top-2 right-2 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
        {language.charAt(0).toUpperCase() + language.slice(1)}
      </div>
    </div>
  );
};

export default CodeEditor;
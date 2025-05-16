// Global type definitions

import React from 'react';

declare global {
  interface Window {
    // Add any global window properties here if needed
  }
}

// Declare module for any untyped packages
declare module '@uiw/react-md-editor' {
  const MDEditor: React.FC<any>;
  export default MDEditor;
}

// This ensures this file is treated as a module
export {}; 
# Responsive Design Guide

This guide explains the responsive design patterns implemented in Duelo de Plumas to help future developers understand how to implement mobile/desktop responsive features.

## Overview

The responsive design system is built around a **mobile-first approach** using Tailwind CSS with a focus on two primary breakpoints:
- **Mobile**: Default (up to 768px)
- **Desktop**: md and larger (768px+)

## Responsive Utilities

### Location: `frontend/src/utils/responsive.ts`

This file contains utilities and constants that make responsive development consistent across the application.

#### Key Constants
```typescript
export const BREAKPOINTS = {
  mobile: '640px',  // sm in Tailwind
  tablet: '768px',  // md in Tailwind 
  desktop: '1024px', // lg in Tailwind
} as const;
```

#### Common Class Patterns
The `RESPONSIVE_CLASSES` object provides pre-defined class combinations for common patterns:

```typescript
// Grid patterns
gridMobileSingle: 'grid-cols-1',
gridDesktopDouble: 'md:grid-cols-2',
gridDesktopTriple: 'md:grid-cols-3',

// Flex patterns
flexMobileColumn: 'flex-col',
flexDesktopRow: 'md:flex-row',

// Navigation patterns
navMobileHidden: 'hidden',
navDesktopShow: 'md:flex',
navMobileShow: 'block',
navDesktopHidden: 'md:hidden',
```

#### React Hook for Responsive State
```typescript
const useResponsive = () => {
  const [isMobile, setIsMobile] = React.useState(isMobileViewport);
  // ... handles resize events
  return { isMobile, isDesktop: !isMobile };
};
```

## Implementation Examples

### 1. Header Component (`frontend/src/components/Layout/Header.tsx`)

The Header component demonstrates the complete responsive pattern:

#### Desktop Navigation
```tsx
<nav className="hidden md:flex items-center space-x-1">
  {/* Navigation items */}
</nav>
```

#### Mobile Hamburger Menu
```tsx
<button
  onClick={toggleMobileMenu}
  className="md:hidden p-2 rounded-md hover:bg-indigo-500 transition-colors"
>
  {/* Hamburger icon */}
</button>

{/* Mobile Navigation Menu */}
{isMobileMenuOpen && (
  <div className="md:hidden bg-indigo-700 border-t border-indigo-500">
    {/* Mobile menu items */}
  </div>
)}
```

### 2. Profile Page (`frontend/src/pages/Profile/ProfilePage.tsx`)

Shows responsive grid patterns:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  {/* Items automatically stack on mobile, side-by-side on desktop */}
</div>
```

## Responsive Design Patterns

### 1. Navigation Pattern
- **Mobile**: Hamburger menu with slide-down navigation
- **Desktop**: Horizontal navigation bar
- **Implementation**: `hidden md:flex` for desktop nav, `md:hidden` for mobile hamburger

### 2. Grid Layout Pattern
- **Mobile**: Single column (`grid-cols-1`)
- **Desktop**: Multiple columns (`md:grid-cols-2`, `md:grid-cols-3`)
- **Implementation**: Use responsive grid classes

### 3. Flex Layout Pattern
- **Mobile**: Column layout (`flex-col`)
- **Desktop**: Row layout (`md:flex-row`)
- **Implementation**: Responsive flex direction classes

### 4. Spacing Pattern
- **Mobile**: Smaller padding/margins (`px-4 py-4`)
- **Desktop**: Larger padding/margins (`md:px-6 md:py-6`)
- **Implementation**: Use responsive spacing classes

### 5. Typography Pattern
- **Mobile**: Smaller text (`text-base`)
- **Desktop**: Larger text (`md:text-lg`)
- **Implementation**: Responsive text size classes

## How to Add Responsive Features

### Step 1: Plan Your Layout
1. Design for mobile first
2. Identify what needs to change on desktop
3. Choose the appropriate pattern from above

### Step 2: Use Tailwind Classes
```tsx
// Example: A card that stacks on mobile, rows on desktop
<div className="flex flex-col md:flex-row space-y-4 md:space-y-0 md:space-x-4">
  <div className="w-full md:w-1/2">Content 1</div>
  <div className="w-full md:w-1/2">Content 2</div>
</div>
```

### Step 3: Use React Hook (if needed)
```tsx
import { useResponsive } from '../utils/responsive';

const MyComponent = () => {
  const { isMobile, isDesktop } = useResponsive();
  
  return (
    <div>
      {isMobile ? <MobileComponent /> : <DesktopComponent />}
    </div>
  );
};
```

### Step 4: Leverage Utility Constants
```tsx
import { RESPONSIVE_CLASSES } from '../utils/responsive';

const className = `${RESPONSIVE_CLASSES.gridMobileSingle} ${RESPONSIVE_CLASSES.gridDesktopDouble}`;
```

## Testing Responsive Design

1. **Browser DevTools**: Use responsive mode to test different screen sizes
2. **Docker Environment**: The app runs on `http://localhost:3001/`
3. **Key Breakpoints to Test**:
   - 320px (small mobile)
   - 768px (tablet/transition point)
   - 1024px (desktop)

## Common Tailwind Classes Reference

| Purpose | Mobile | Desktop | Combined Class |
|---------|--------|---------|----------------|
| Hide/Show | `hidden` | `md:block` | `hidden md:block` |
| Grid Cols | `grid-cols-1` | `md:grid-cols-2` | `grid-cols-1 md:grid-cols-2` |
| Flex Direction | `flex-col` | `md:flex-row` | `flex-col md:flex-row` |
| Text Size | `text-base` | `md:text-lg` | `text-base md:text-lg` |
| Padding | `p-4` | `md:p-6` | `p-4 md:p-6` |
| Width | `w-full` | `md:w-1/2` | `w-full md:w-1/2` |

## Future Development Guidelines

1. **Always start with mobile design**
2. **Use the responsive utility file** for consistency
3. **Test on multiple screen sizes** before deploying
4. **Follow the established patterns** in the Header and Profile components
5. **Keep responsive logic simple** - avoid complex breakpoint combinations
6. **Document new patterns** if you create them

## Component Examples

The following components demonstrate good responsive patterns:
- `Header.tsx` - Complete navigation pattern
- `ProfilePage.tsx` - Grid and form layouts
- `OnboardingPage.tsx` - Responsive content cards

Refer to these components when implementing new responsive features. 
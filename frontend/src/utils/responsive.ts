// Responsive utility functions and constants for consistent mobile/desktop handling
// This makes it easier for future agents to understand responsive patterns

export const BREAKPOINTS = {
  mobile: '640px',  // sm in Tailwind
  tablet: '768px',  // md in Tailwind 
  desktop: '1024px', // lg in Tailwind
} as const;

// Common responsive class patterns
export const RESPONSIVE_CLASSES = {
  // Grid patterns
  gridMobileSingle: 'grid-cols-1',
  gridDesktopDouble: 'md:grid-cols-2',
  gridDesktopTriple: 'md:grid-cols-3',
  
  // Flex patterns
  flexMobileColumn: 'flex-col',
  flexDesktopRow: 'md:flex-row',
  
  // Spacing patterns
  paddingMobile: 'px-4 py-4',
  paddingDesktop: 'md:px-6 md:py-6',
  marginMobile: 'mx-4 my-4',
  marginDesktop: 'md:mx-6 md:my-6',
  
  // Text patterns
  textMobileBase: 'text-base',
  textDesktopLarge: 'md:text-lg',
  headingMobile: 'text-xl',
  headingDesktop: 'md:text-2xl',
  
  // Navigation patterns
  navMobileHidden: 'hidden',
  navDesktopShow: 'md:flex',
  navMobileShow: 'block',
  navDesktopHidden: 'md:hidden',
} as const;

// Helper function to combine mobile and desktop classes
export const responsiveClasses = (mobile: string, desktop: string = ''): string => {
  return desktop ? `${mobile} ${desktop}` : mobile;
};

// Helper function for conditional responsive rendering
export const isMobileViewport = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.innerWidth < parseInt(BREAKPOINTS.tablet);
};

// Custom hook for responsive state (to be used in components)
export const useResponsive = () => {
  const [isMobile, setIsMobile] = React.useState(isMobileViewport);
  
  React.useEffect(() => {
    const handleResize = () => {
      setIsMobile(isMobileViewport());
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return {
    isMobile,
    isDesktop: !isMobile,
  };
};

// Import React for the hook above
import React from 'react'; 
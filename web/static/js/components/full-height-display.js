/**
 * Full-Height Display Component
 * A modular, reusable component for displaying content in a full-height container
 * with a fixed header and scrollable body.
 */

const FullHeightDisplay = ({
    title,              // Header title
    icon,              // Optional header icon
    iconColor,         // Icon color class  
    headerActions,     // React element for header buttons
    children,          // Content to display
    className = '',    // Additional CSS classes
    contentRef,        // Optional ref for content area
    headerClassName = '', // Header styling
    bodyClassName = ''    // Body styling
}) => {
    return (
        <div className={`full-height-display flex flex-col h-full bg-gray-800 border border-gray-700 rounded-md overflow-hidden ${className}`}>
            {/* Fixed Header */}
            <div className={`display-header flex-shrink-0 flex justify-between items-center px-4 py-2 bg-gray-900 border-b border-gray-700 ${headerClassName}`}>
                <div className="flex items-center space-x-2">
                    {icon && <i className={`${icon} ${iconColor || 'text-gray-400'}`}></i>}
                    <h2 className="text-lg font-semibold text-green-400">{title}</h2>
                </div>
                <div className="flex items-center space-x-2">
                    {headerActions}
                </div>
            </div>
            
            {/* Scrollable Body */}
            <div 
                ref={contentRef}
                className={`display-body flex-1 overflow-y-auto p-4 ${bodyClassName}`}
            >
                {children}
            </div>
        </div>
    );
};

// Export for use in other components
window.FullHeightDisplay = FullHeightDisplay;
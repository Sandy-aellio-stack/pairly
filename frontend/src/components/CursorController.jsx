import { useLocation } from 'react-router-dom';
import HeartCursor from './HeartCursor';

/**
 * CursorController handles the lifecycle of the custom HeartCursor.
 * Since the landing page (Framer) has its own cursor listeners, we disable
 * the React custom cursor on the root route to prevent "freezing" or "lag" 
 * caused by multiple mousemove listeners in the same window.
 */
const CursorController = () => {
    const { pathname } = useLocation();

    // Only render HeartCursor if NOT on the landing page
    if (pathname === '/') {
        return null;
    }

    return <HeartCursor />;
};

export default CursorController;

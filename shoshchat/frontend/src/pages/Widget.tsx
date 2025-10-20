import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import ChatWidget from "../components/ChatWidget";

const Widget = () => {
  const [searchParams] = useSearchParams();
  const tenantId = searchParams.get("tenant") || "default";
  const accent = (searchParams.get("accent") as "retail" | "finance") || "retail";

  useEffect(() => {
    // Force transparent background for embedding
    const htmlElement = document.documentElement;
    const bodyElement = document.body;
    
    // Store original styles
    const originalHtmlClass = htmlElement.className;
    const originalHtmlStyle = htmlElement.getAttribute("style");
    const originalBodyClass = bodyElement.className;
    const originalBodyStyle = bodyElement.getAttribute("style");

    // Remove all dark backgrounds and apply transparent styling
    htmlElement.className = "";
    htmlElement.style.cssText = "background: transparent !important; color-scheme: light;";
    
    bodyElement.className = "";
    bodyElement.style.cssText = "background: transparent !important; color: inherit !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important;";

    // Cleanup function to restore original styles
    return () => {
      htmlElement.className = originalHtmlClass;
      if (originalHtmlStyle === null) {
        htmlElement.removeAttribute("style");
      } else {
        htmlElement.setAttribute("style", originalHtmlStyle);
      }
      
      bodyElement.className = originalBodyClass;
      if (originalBodyStyle === null) {
        bodyElement.removeAttribute("style");
      } else {
        bodyElement.setAttribute("style", originalBodyStyle);
      }
    };
  }, []);

  return (
    <div 
      className="w-screen h-screen"
      style={{ 
        background: "transparent", 
        margin: 0, 
        padding: 0,
        overflow: "hidden"
      }}
    >
      <ChatWidget tenantId={tenantId} accent={accent} />
    </div>
  );
};

export default Widget;

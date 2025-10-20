(function () {
  if (window.ShoshChatWidget) {
    return;
  }

  const createIframe = (config) => {
    const iframe = document.createElement("iframe");
    iframe.src = config.src;
    iframe.title = "ShoshChat AI";
    iframe.style.border = "0";
    iframe.style.width = "420px";
    iframe.style.height = "600px";
    iframe.style.position = "fixed";
    iframe.style.bottom = "24px";
    iframe.style.right = "24px";
    iframe.style.zIndex = "9999";
    iframe.style.background = "transparent";
    iframe.style.backgroundColor = "transparent";
    iframe.style.overflow = "visible";
    iframe.style.colorScheme = "light";
    iframe.allow = "clipboard-write";
    
    // Ensure iframe has transparent background
    iframe.setAttribute("allowtransparency", "true");
    
    document.body.appendChild(iframe);
  };

  window.ShoshChatWidget = {
    init(config) {
      const baseUrl = config.url ?? "https://app.shoshchat.ai";
      const tenantId = config.tenantId ?? "default";
      const accent = config.accent ?? "retail";
      const widgetUrl = `${baseUrl}/widget?tenant=${tenantId}&accent=${accent}`;
      createIframe({ src: widgetUrl });
    }
  };
})();

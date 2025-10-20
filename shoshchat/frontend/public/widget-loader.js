(function () {
  if (window.ShoshChatWidget) {
    return;
  }

  const createIframe = (config) => {
    const iframe = document.createElement("iframe");
    iframe.src = config.src;
    iframe.title = "ShoshChat AI";
    iframe.style.border = "0";
    iframe.style.width = "360px";
    iframe.style.height = "520px";
    iframe.style.position = "fixed";
    iframe.style.bottom = "24px";
    iframe.style.right = "24px";
    iframe.style.zIndex = "9999";
    document.body.appendChild(iframe);
  };

  window.ShoshChatWidget = {
    init(config) {
      createIframe({ src: config.url ?? "https://app.shoshchat.ai/widget" });
    }
  };
})();
